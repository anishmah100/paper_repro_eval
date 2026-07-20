"""Competitive per-capsule leaderboard construction."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from .catalog import resolve_capsule
from .models import MetricDirection
from .repository import Repository


def build_leaderboards(
    repository: Repository, rows: Sequence[dict[str, object]]
) -> list[dict[str, Any]]:
    """Rank the latest attempt per agent independently within every capsule."""
    latest: dict[tuple[str, str, str], dict[str, object]] = {}
    for row in rows:
        key = (str(row["paper"]), str(row["capsule"]), str(row["agent"]))
        previous = latest.get(key)
        if previous is None or int(str(row["attempt"])) > int(str(previous["attempt"])):
            latest[key] = row

    boards: list[dict[str, Any]] = []
    capsule_keys = sorted({(key[0], key[1]) for key in latest})
    for paper_id, capsule_id in capsule_keys:
        group = [
            row
            for (paper, capsule, _), row in latest.items()
            if paper == paper_id and capsule == capsule_id
        ]
        resolved = resolve_capsule(repository, paper_id, capsule_id, str(group[0]["version"]))
        contract = resolved.manifest.competition
        direction = (
            contract.primary_metric.direction if contract is not None else MetricDirection.HIGHER
        )
        tolerance = contract.tie_tolerance if contract is not None else 1e-6
        qualifying = [
            row
            for row in group
            if bool(row.get("qualified")) and row.get("objective_score") is not None
        ]
        qualifying.sort(
            key=lambda row: float(str(row["objective_score"])),
            reverse=direction is MetricDirection.HIGHER,
        )

        standings: list[dict[str, object]] = []
        previous_score: float | None = None
        previous_rank = 0
        for index, row in enumerate(qualifying, start=1):
            score = float(str(row["objective_score"]))
            rank = (
                previous_rank
                if previous_score is not None and abs(score - previous_score) <= tolerance
                else index
            )
            standings.append({"rank": rank, **row})
            previous_rank = rank
            previous_score = score

        boards.append(
            {
                "paper": paper_id,
                "capsule": capsule_id,
                "competition_mode": str(contract.mode) if contract is not None else None,
                "primary_metric": (
                    contract.primary_metric.model_dump(mode="json")
                    if contract is not None
                    else {
                        "id": "objective_score",
                        "title": "Objective score",
                        "direction": "higher-is-better",
                        "unit": "normalized score",
                        "description": "",
                    }
                ),
                "tie_tolerance": tolerance,
                "winner_rule": contract.winner_rule if contract is not None else "",
                "standings": standings,
                "unqualified": [row for row in group if row not in qualifying],
            }
        )
    return boards


def render_leaderboards(suite_id: str, boards: Sequence[dict[str, Any]]) -> str:
    lines = [f"# Leaderboards: {suite_id}", ""]
    for board in boards:
        metric = board["primary_metric"]
        lines.extend(
            [
                f"## {board['paper']} / {board['capsule']}",
                "",
                f"Primary metric: {metric['title']} ({metric['direction']}).",
                "",
                str(board["winner_rule"]),
                "",
                "| Rank | Agent | Attempt | Score | Status |",
                "|---:|---|---:|---:|---|",
            ]
        )
        for row in board["standings"]:
            lines.append(
                f"| {row['rank']} | {row['agent']} | {row['attempt']} | "
                f"{row['objective_score']} | {row['status']} |"
            )
        if not board["standings"]:
            lines.append("| — | No qualifying runs | — | — | — |")
        lines.append("")
    return "\n".join(lines) + "\n"
