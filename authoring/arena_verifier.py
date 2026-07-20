"""Generic trusted evaluator for the deterministic visual arenas."""

from __future__ import annotations

import argparse
import json
import math
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "templates" / "arena_kit"))
import arena_kit as kit  # noqa: E402
import control_verifier  # noqa: E402
import trusted_poisson  # noqa: E402

NATIVE_BATCH = {
    "poisson": ("run_case.sh", True),
    "pathtracer": ("render.sh", False),
    "mpm": ("simulate.sh", True),
    "topology": ("optimize.sh", True),
    "smoke": ("control.sh", False),
    "softrobot": ("design.sh", False),
    "inverse_render": ("recover.sh", True),
}


def native_command(task: str, inp: Path, out: Path) -> tuple[list[str], Path | None]:
    if task not in NATIVE_BATCH:
        return [sys.executable, "solve.py", str(inp), str(out)], None
    script, directory_output = NATIVE_BATCH[task]
    if directory_output:
        target = out.parent / (out.stem + "-files")
        target.mkdir()
        return ["bash", script, str(inp), str(target)], target / "result.json"
    if task == "pathtracer":
        return ["bash", script, str(inp), str(out), str(out.with_suffix(".metrics.json"))], None
    return ["bash", script, str(inp), str(out)], None


def invoke(
    task: str, sub: Path, inp: Path, out: Path, timeout: float = 12
) -> tuple[dict[str, Any] | None, str, float]:
    start = time.monotonic()
    try:
        command, directory_result = native_command(task, inp, out)
        p = subprocess.run(
            command,
            cwd=sub,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
            env={**os.environ, "PYTHONHASHSEED": "0"},
        )
        if directory_result is not None and directory_result.is_file():
            out.write_bytes(directory_result.read_bytes())
        elapsed = time.monotonic() - start
        if p.returncode or not out.is_file():
            return None, f"exit={p.returncode}; stderr={p.stderr[-600:]}", elapsed
        value = json.loads(out.read_text())
        if not isinstance(value, dict):
            return None, "candidate output must be a JSON object", elapsed
        return value, "", elapsed
    except Exception as exc:
        return None, str(exc), time.monotonic() - start


def measurements_valid(task: str, metrics: dict[str, Any]) -> bool:
    """Return whether measurements represent a protocol-valid, finite candidate result."""
    if metrics.get("error") or metrics.get("invalid"):
        return False
    if task in {"multipole", "world_mpc"} and (
        metrics.get("protocol_errors") or metrics.get("timeouts")
    ):
        return False
    if task == "lightcycle" and (metrics.get("illegal") or metrics.get("timeouts")):
        return False
    numeric = [value for value in metrics.values() if isinstance(value, (int, float))]
    return all(math.isfinite(float(value)) for value in numeric)


def lightcycle_quality(
    submission: Path, case: dict[str, Any], evidence: Path
) -> tuple[float, dict[str, Any]]:
    import random

    from paper_repro_eval.tournament import BotProcess

    bot: BotProcess | None = None
    try:
        bot = BotProcess.start(submission)
        rng = random.Random(case["seed"])
        wins = draws = illegal = timeouts = 0
        replay: list[dict[str, Any]] = []
        directions = {"U": (0, -1), "D": (0, 1), "L": (-1, 0), "R": (1, 0)}
        for match in range(case["matches"]):
            width, height = case["width"], case["height"]
            player = [2, height // 2]
            foe = [width - 3, height // 2]
            occupied = {tuple(player), tuple(foe)}
            frames = []
            bot.send({"type": "reset", "board": [width, height], "seed": case["seed"] + match})
            for turn in range(width * height):
                move, error = bot.action(
                    {
                        "type": "turn",
                        "board": [width, height],
                        "you": player,
                        "opponents": [foe],
                        "occupied": [list(cell) for cell in occupied],
                        "turn": turn,
                    },
                    0.25,
                )
                legal = []
                for name, (delta_x, delta_y) in directions.items():
                    target = (player[0] + delta_x, player[1] + delta_y)
                    if (
                        0 <= target[0] < width
                        and 0 <= target[1] < height
                        and target not in occupied
                    ):
                        legal.append(name)
                if not legal:
                    break
                if error is not None or move not in legal:
                    illegal += 1
                    timeouts += int(error == "timeout")
                    break
                delta_x, delta_y = directions[move]
                player = [player[0] + delta_x, player[1] + delta_y]
                foe_legal = []
                for name, (foe_x, foe_y) in directions.items():
                    target = (foe[0] + foe_x, foe[1] + foe_y)
                    if (
                        0 <= target[0] < width
                        and 0 <= target[1] < height
                        and target not in occupied
                        and target != tuple(player)
                    ):
                        foe_legal.append(name)
                if not foe_legal:
                    wins += 1
                    break
                foe_move = min(
                    foe_legal,
                    key=lambda name: (
                        abs(foe[0] + directions[name][0] - player[0])
                        + abs(foe[1] + directions[name][1] - player[1])
                        + 0.2 * rng.random()
                    ),
                )
                foe_x, foe_y = directions[foe_move]
                foe = [foe[0] + foe_x, foe[1] + foe_y]
                if tuple(foe) == tuple(player):
                    draws += 1
                    break
                occupied |= {tuple(player), tuple(foe)}
                if match == 0:
                    frames.append(
                        {
                            "you": player[:],
                            "foe": foe[:],
                            "occupied": [list(cell) for cell in occupied],
                        }
                    )
            else:
                draws += 1
            if match == 0:
                replay = frames
        metrics = {
            "wins": wins,
            "draws": draws,
            "illegal": illegal,
            "timeouts": timeouts,
            "replay": replay,
        }
        (evidence / "tournament.json").write_text(json.dumps(metrics, indent=2))
        quality = max(0.0, (wins + 0.35 * draws) / case["matches"] - 0.08 * illegal)
        return min(1.0, quality), {key: value for key, value in metrics.items() if key != "replay"}
    except (OSError, ValueError, TypeError) as exc:
        return 0.0, {"error": str(exc), "illegal": 1, "timeouts": 0}
    finally:
        if bot is not None:
            bot.close()


def result(
    cid: str, score: float, summary: str, measure: dict[str, Any], evidence: list[str] | None = None
) -> dict[str, Any]:
    score = max(0, min(1, score))
    status = "passed" if score == 1 else ("failed" if score == 0 else "partial")
    return {
        "id": cid,
        "status": status,
        "score": score,
        "summary": summary,
        "measurements": measure,
        "evidence": evidence or [],
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--task", required=True)
    p.add_argument("--context", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    ctx = json.loads(a.context.read_text())
    sub = Path(ctx["submission_dir"])
    art = Path(ctx["artifact_dir"])
    ev = Path(ctx["evidence_dir"])
    private = Path(ctx["private_dir"])
    specs = yaml.safe_load((private / "checks.yaml").read_text())["checks"]
    ids = [x["id"] for x in specs]
    report = (sub / "REPORT.md").is_file()
    artifact_ok = (art / "preview.png").is_file() and (art / "result.json").is_file()
    qualities = []
    details = []
    elapsed = 0.0
    successful = True
    for item in json.loads((private / "hidden_inputs" / "cases.json").read_text()):
        c = kit.case(a.task, int(item["seed"]), int(item["difficulty"]))
        cp = ev / f"{item['name']}-input.json"
        op = ev / f"{item['name']}-output.json"
        pp = ev / f"{item['name']}-preview.png"
        public_case = dict(c)
        if a.task == "inverse_render":
            public_case.pop("truth", None)
        cp.write_text(json.dumps(public_case))
        if a.task in {"multipole", "world_mpc"}:
            q, m = control_verifier.quality(a.task, sub, c)
            out = {"controller": "interactive"}
            err = ""
            successful = successful and measurements_valid(a.task, m)
        elif a.task == "lightcycle":
            q, m = lightcycle_quality(sub, c, ev)
            out = {"policy": "interactive"}
            err = ""
            successful = successful and measurements_valid(a.task, m)
        else:
            out, err, sec = invoke(a.task, sub, cp, op)
            elapsed += sec
            if out is None:
                q = 0.0
                m = {"error": err}
                successful = False
                out = {}
            else:
                m = (
                    trusted_poisson.score(c, out)
                    if a.task == "poisson"
                    else kit.score(a.task, c, out)
                )
                q = float(m.get("quality", 0))
                successful = successful and measurements_valid(a.task, m)
                kit.render(a.task, c, out, pp)
        qualities.append(q)
        details.append({"case": item["name"], "quality": q, **m})
    quality = float(
        __import__("math").prod(max(1e-6, x) for x in qualities) ** (1 / max(1, len(qualities)))
    )
    (ev / "metrics.json").write_text(
        json.dumps(
            {"objective_score": quality, "cases": details, "elapsed_seconds": elapsed}, indent=2
        )
    )
    checks = []
    for i, cid in enumerate(ids):
        if i == 0:
            checks.append(
                result(
                    cid,
                    float(successful and (artifact_ok or a.task == "lightcycle")),
                    "Candidate protocol and canonical artifacts",
                    {"successful": successful, "artifacts": artifact_ok},
                    ["metrics.json"],
                )
            )
        elif i == len(ids) - 1:
            checks.append(
                result(cid, float(report), "Human review report present", {"report": report})
            )
        else:
            adj = quality
            if "efficiency" in cid or "throughput" in cid:
                adj = quality * min(1, 12 / max(0.1, elapsed))
            checks.append(
                result(
                    cid,
                    adj,
                    f"Hidden {a.task} metric",
                    {"objective_score": quality, "cases": details},
                    ["metrics.json"],
                )
            )
    a.output.write_text(
        json.dumps({"schema_version": 1, "checks": checks, "warnings": []}, indent=2)
    )


if __name__ == "__main__":
    main()
