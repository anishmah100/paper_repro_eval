"""Isolated round-robin execution for persistent Lightcycle submissions."""

from __future__ import annotations

import json
import math
import random
import selectors
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, TextIO, cast

from .errors import ConfigurationError
from .lifecycle import latest_seal
from .models import CheckStatus
from .repository import Repository
from .run_store import StoredRun, list_runs
from .util import dump_json, slugify, utc_now
from .verification import latest_verification

DIRECTIONS = {"U": (0, -1), "D": (0, 1), "L": (-1, 0), "R": (1, 0)}


@dataclass
class BotProcess:
    process: subprocess.Popen[str]
    stdout: TextIO
    selector: selectors.BaseSelector

    @classmethod
    def start(cls, submission: Path, script_name: str = "bot.sh") -> BotProcess:
        script = submission / script_name
        if not script.is_file():
            raise ConfigurationError(f"Persistent submission lacks {script_name}: {submission}")
        process = subprocess.Popen(
            ["bash", script_name],
            cwd=submission,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )
        if process.stdin is None or process.stdout is None:
            process.kill()
            raise ConfigurationError("Could not open bot protocol streams")
        selector = selectors.DefaultSelector()
        selector.register(process.stdout, selectors.EVENT_READ)
        return cls(
            process=process,
            stdout=cast(TextIO, process.stdout),
            selector=selector,
        )

    def send(self, message: dict[str, Any]) -> None:
        if self.process.stdin is None:
            raise BrokenPipeError("Bot stdin is closed")
        self.process.stdin.write(json.dumps(message, separators=(",", ":")) + "\n")
        self.process.stdin.flush()

    def response(
        self, message: dict[str, Any], timeout: float
    ) -> tuple[dict[str, Any] | None, str | None]:
        try:
            self.send(message)
            if not self.selector.select(timeout):
                return None, "timeout"
            line = self.stdout.readline()
            if not line:
                return None, "closed-stream"
            value = json.loads(line)
            if not isinstance(value, dict):
                return None, "malformed-response"
            return value, None
        except (BrokenPipeError, json.JSONDecodeError, OSError) as exc:
            return None, type(exc).__name__

    def action(self, message: dict[str, Any], timeout: float) -> tuple[str | None, str | None]:
        value, error = self.response(message, timeout)
        if value is None:
            return None, error
        action = value.get("move")
        if not isinstance(action, str):
            return None, "malformed-action"
        return action, None

    def close(self) -> None:
        self.selector.close()
        if self.process.poll() is None:
            self.process.kill()
        try:
            self.process.wait(timeout=1)
        except subprocess.TimeoutExpired:
            self.process.kill()


def _obstacles(width: int, height: int, seed: int) -> set[tuple[int, int]]:
    rng = random.Random(seed)
    blocked: set[tuple[int, int]] = set()
    forbidden = {(2, height // 2), (width - 3, height // 2)}
    for _ in range((width * height) // 22):
        x = rng.randrange(3, width - 3)
        y = rng.randrange(2, height - 2)
        mirror = (width - 1 - x, height - 1 - y)
        if (x, y) not in forbidden and mirror not in forbidden:
            blocked.update({(x, y), mirror})
    return blocked


def play_match(
    first_submission: Path,
    second_submission: Path,
    *,
    seed: int,
    width: int = 19,
    height: int = 19,
    turn_timeout: float = 0.25,
    max_turns: int | None = None,
) -> dict[str, Any]:
    """Play one simultaneous-action match and return a deterministic replay."""
    bots = [BotProcess.start(first_submission), BotProcess.start(second_submission)]
    positions = [[2, height // 2], [width - 3, height // 2]]
    occupied = _obstacles(width, height, seed) | {tuple(positions[0]), tuple(positions[1])}
    errors = [0, 0]
    timeouts = [0, 0]
    frames: list[dict[str, Any]] = []
    winner: int | None = None
    reason = "turn-limit"
    limit = max_turns or width * height
    reset = {
        "type": "reset",
        "board": [width, height],
        "seed": seed,
        "max_turns": limit,
    }
    try:
        for bot in bots:
            bot.send(reset)
        for turn in range(limit):
            messages = [
                {
                    "type": "turn",
                    "board": [width, height],
                    "you": positions[index],
                    "opponents": [positions[1 - index]],
                    "occupied": [list(cell) for cell in sorted(occupied)],
                    "turn": turn,
                    "seed": seed,
                }
                for index in range(2)
            ]
            responses = [bots[index].action(messages[index], turn_timeout) for index in range(2)]
            actions = [response[0] for response in responses]
            protocol_errors = [response[1] for response in responses]
            targets: list[tuple[int, int] | None] = []
            alive = [True, True]
            for index, action in enumerate(actions):
                if protocol_errors[index] is not None:
                    errors[index] += 1
                    timeouts[index] += int(protocol_errors[index] == "timeout")
                    alive[index] = False
                    targets.append(None)
                    continue
                delta = DIRECTIONS.get(action or "")
                if delta is None:
                    errors[index] += 1
                    alive[index] = False
                    targets.append(None)
                    continue
                target = (positions[index][0] + delta[0], positions[index][1] + delta[1])
                targets.append(target)
                if not 0 <= target[0] < width or not 0 <= target[1] < height or target in occupied:
                    alive[index] = False
            if alive == [True, True] and targets[0] == targets[1]:
                alive = [False, False]
                reason = "head-on"
            frame = {
                "turn": turn,
                "positions": [position[:] for position in positions],
                "actions": actions,
                "targets": [list(target) if target is not None else None for target in targets],
                "alive": alive,
                "protocol_errors": protocol_errors,
            }
            frames.append(frame)
            if not all(alive):
                winner = 0 if alive[0] else (1 if alive[1] else None)
                if reason != "head-on":
                    reason = "elimination"
                break
            positions = [list(targets[0]), list(targets[1])]  # type: ignore[arg-type]
            occupied.update({tuple(positions[0]), tuple(positions[1])})
        return {
            "schema_version": 1,
            "seed": seed,
            "board": [width, height],
            "winner": winner,
            "reason": reason,
            "turns": len(frames),
            "errors": errors,
            "timeouts": timeouts,
            "initial_obstacles": [list(cell) for cell in sorted(_obstacles(width, height, seed))],
            "frames": frames,
        }
    finally:
        for bot in bots:
            bot.close()


def _eligible_runs(
    repository: Repository, suite_id: str, agents: set[str] | None = None
) -> list[StoredRun]:
    latest: dict[str, StoredRun] = {}
    for run in list_runs(repository):
        record = run.record
        if (
            record.suite_id != suite_id
            or record.paper_id != "lightcycle-agents"
            or record.capsule_id != "adversarial-tournament"
        ):
            continue
        previous = latest.get(record.agent)
        if agents is not None and record.agent not in agents:
            continue
        if previous is None or record.attempt > previous.record.attempt:
            latest[record.agent] = run
    eligible: list[StoredRun] = []
    for run in latest.values():
        try:
            _, verification = latest_verification(repository, run.record.run_id)
            seal_dir, seal = latest_seal(run)
        except ConfigurationError:
            continue
        protocol = next(
            (check for check in verification.checks if check.id == "bot-protocol"), None
        )
        if (
            verification.status == "success"
            and protocol is not None
            and protocol.status is CheckStatus.PASSED
            and not seal.missing_required
            and (seal_dir / "submission" / "bot.sh").is_file()
        ):
            eligible.append(run)
    return sorted(eligible, key=lambda item: item.record.agent)


def _render_markdown(report: dict[str, Any]) -> str:
    lines = [
        f"# Lightcycle tournament: {report['suite_id']}",
        "",
        f"Generated: {report['created_at']}",
        "",
        "| Rank | Agent | Points | W-D-L | Rating | 95% score interval | Errors | Timeouts |",
        "|---:|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in report["standings"]:
        lines.append(
            f"| {row['rank']} | {row['agent']} | {row['points']:.1f} | "
            f"{row['wins']}-{row['draws']}-{row['losses']} | {row['rating']:.1f} | "
            f"{row['score_rate']:.3f} ± {row['score_margin_95']:.3f} | "
            f"{row['errors']} | {row['timeouts']} |"
        )
    lines.extend(
        [
            "",
            "Each pair plays every deterministic seed twice with starting sides exchanged. "
            "A win is one point and a draw is half a point.",
            "",
        ]
    )
    return "\n".join(lines)


def _replay_html(match: dict[str, Any]) -> str:
    payload = json.dumps(match, separators=(",", ":")).replace("</", "<\\/")
    return f"""<!doctype html>
<meta charset="utf-8">
<title>Lightcycle replay {match["id"]}</title>
<style>
body {{ background:#10131a;color:#e8edf5;font:16px system-ui;margin:24px }}
canvas {{ border:1px solid #4b5568;image-rendering:pixelated;max-width:90vmin }}
input {{ width:min(720px,90vw) }} .meta {{ margin:12px 0 }}
</style>
<h1>Match {match["id"]}: {match["agents"][0]} vs {match["agents"][1]}</h1>
<div class="meta" id="meta"></div>
<canvas id="board" width="760" height="760"></canvas><br>
<input id="turn" type="range" min="0" value="0"><output id="value"></output>
<script>
const match={payload}, replay=match.replay, frames=replay.frames;
const slider=document.getElementById("turn"), canvas=document.getElementById("board");
slider.max=Math.max(0,frames.length-1); const ctx=canvas.getContext("2d");
function draw(index) {{
 const [w,h]=replay.board, sx=canvas.width/w, sy=canvas.height/h;
 ctx.fillStyle="#111827";ctx.fillRect(0,0,canvas.width,canvas.height);
 ctx.fillStyle="#64748b";
 for(const [x,y] of replay.initial_obstacles) ctx.fillRect(x*sx,y*sy,sx,sy);
 const trails=[[],[]];
 for(let i=0;i<=index && i<frames.length;i++) {{
   for(let p=0;p<2;p++) {{
     const target=frames[i].targets[p]; if(target) trails[p].push(target);
   }}
 }}
 for(let p=0;p<2;p++) {{
   ctx.fillStyle=p===0?"#22d3ee":"#fb7185";
   for(const [x,y] of trails[p]) ctx.fillRect(x*sx,y*sy,sx,sy);
 }}
 const frame=frames[index]||{{positions:[[2,h/2],[w-3,h/2]],actions:["-","-"]}};
 for(let p=0;p<2;p++) {{
   const [x,y]=frame.positions[p];ctx.fillStyle=p===0?"#67e8f9":"#fda4af";
   ctx.fillRect(x*sx,y*sy,sx,sy);
 }}
 document.getElementById("value").textContent=" turn "+(index+1)+"/"+frames.length;
 document.getElementById("meta").textContent=
  "winner: "+(replay.winner===null?"draw":match.agents[replay.winner])+
  " · reason: "+replay.reason+" · actions: "+frame.actions.join(" / ");
}}
slider.addEventListener("input",()=>draw(Number(slider.value)));draw(0);
</script>
"""


def run_lightcycle_tournament(
    repository: Repository,
    suite_id: str,
    *,
    seeds: int = 4,
    turn_timeout: float = 0.25,
    agents: set[str] | None = None,
) -> Path:
    runs = _eligible_runs(repository, suite_id, agents)
    if len(runs) < 2:
        raise ConfigurationError(
            "Tournament requires at least two latest qualifying Lightcycle runs"
        )
    entries: list[dict[str, Any]] = []
    for run in runs:
        seal_dir, _ = latest_seal(run)
        entries.append(
            {
                "agent": run.record.agent,
                "run_id": run.record.run_id,
                "submission": seal_dir / "submission",
            }
        )
    stats: dict[str, dict[str, Any]] = {
        entry["agent"]: {
            "wins": 0,
            "draws": 0,
            "losses": 0,
            "points": 0.0,
            "errors": 0,
            "timeouts": 0,
            "rating": 1500.0,
        }
        for entry in entries
    }
    matches: list[dict[str, Any]] = []
    seed_values = [1729 + index * 7919 for index in range(seeds)]
    for left in range(len(entries)):
        for right in range(left + 1, len(entries)):
            for seed in seed_values:
                for swapped in (False, True):
                    order = [entries[left], entries[right]]
                    if swapped:
                        order.reverse()
                    replay = play_match(
                        order[0]["submission"],
                        order[1]["submission"],
                        seed=seed,
                        turn_timeout=turn_timeout,
                    )
                    winner_index = replay["winner"]
                    outcome = 0.5 if winner_index is None else (1.0 if winner_index == 0 else 0.0)
                    first_agent = order[0]["agent"]
                    second_agent = order[1]["agent"]
                    for index, agent in enumerate((first_agent, second_agent)):
                        stats[agent]["errors"] += replay["errors"][index]
                        stats[agent]["timeouts"] += replay["timeouts"][index]
                    if winner_index is None:
                        stats[first_agent]["draws"] += 1
                        stats[second_agent]["draws"] += 1
                        stats[first_agent]["points"] += 0.5
                        stats[second_agent]["points"] += 0.5
                    else:
                        winner_agent = order[winner_index]["agent"]
                        loser_agent = order[1 - winner_index]["agent"]
                        stats[winner_agent]["wins"] += 1
                        stats[loser_agent]["losses"] += 1
                        stats[winner_agent]["points"] += 1.0
                    expected = 1 / (
                        1
                        + 10
                        ** ((stats[second_agent]["rating"] - stats[first_agent]["rating"]) / 400)
                    )
                    stats[first_agent]["rating"] += 24 * (outcome - expected)
                    stats[second_agent]["rating"] += 24 * ((1 - outcome) - (1 - expected))
                    matches.append(
                        {
                            "id": len(matches) + 1,
                            "agents": [first_agent, second_agent],
                            "run_ids": [order[0]["run_id"], order[1]["run_id"]],
                            "replay": replay,
                        }
                    )
    standings: list[dict[str, Any]] = []
    for agent, values in stats.items():
        games = values["wins"] + values["draws"] + values["losses"]
        rate = values["points"] / games
        margin = 1.96 * math.sqrt(max(1e-9, rate * (1 - rate)) / games)
        standings.append(
            {
                "agent": agent,
                **values,
                "games": games,
                "score_rate": rate,
                "score_margin_95": margin,
            }
        )
    standings.sort(
        key=lambda row: (row["points"], row["rating"], -row["timeouts"], -row["errors"]),
        reverse=True,
    )
    previous: tuple[float, float] | None = None
    rank = 0
    for index, row in enumerate(standings, start=1):
        key = (row["points"], row["rating"])
        if previous is None or key != previous:
            rank = index
        row["rank"] = rank
        previous = key
    created = utc_now()
    report = {
        "schema_version": 1,
        "suite_id": suite_id,
        "created_at": created,
        "seed_values": seed_values,
        "turn_timeout_seconds": turn_timeout,
        "standings": standings,
        "matches": matches,
    }
    stamp = created.replace(":", "").replace("+", "-")
    destination = repository.reports_dir / slugify(suite_id) / "tournaments" / f"lightcycle-{stamp}"
    destination.mkdir(parents=True)
    dump_json(destination / "tournament.json", report)
    replay_dir = destination / "replays"
    replay_dir.mkdir()
    for match in matches:
        stem = f"match-{match['id']:04d}"
        dump_json(replay_dir / f"{stem}.json", match)
        (replay_dir / f"{stem}.html").write_text(_replay_html(match), encoding="utf-8")
    standings_csv = ["rank,agent,points,wins,draws,losses,rating,errors,timeouts"]
    standings_csv.extend(
        f"{row['rank']},{row['agent']},{row['points']},{row['wins']},{row['draws']},"
        f"{row['losses']},{row['rating']},{row['errors']},{row['timeouts']}"
        for row in standings
    )
    (destination / "standings.csv").write_text("\n".join(standings_csv) + "\n", encoding="utf-8")
    (destination / "TOURNAMENT.md").write_text(_render_markdown(report), encoding="utf-8")
    return destination
