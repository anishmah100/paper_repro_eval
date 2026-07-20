#!/usr/bin/env python3
"""Calibrate persistent control and adversarial-game protocols."""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "templates" / "arena_kit"), str(ROOT / "authoring")]
import arena_kit as kit  # noqa: E402
import arena_verifier  # noqa: E402
import control_verifier  # noqa: E402


def run(output_path: Path | None = None) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    control_tasks = [
        ("multipole", "dm-control-suite", "multipole-control"),
        ("world_mpc", "differentiable-world-model-mpc", "visual-offline-control"),
    ]
    for index, (task, paper, capsule) in enumerate(control_tasks):
        case = kit.case(task, 8341 + index * 101, 2)
        root = ROOT / "papers" / paper / "capsules" / capsule / "v1.0.0"
        baseline, baseline_metrics = control_verifier.quality(
            task, root / "public" / "starter", case
        )
        frontier, frontier_metrics = control_verifier.quality(
            task, root / "private" / "reference", case
        )
        mutant, mutant_metrics = control_verifier.quality(
            task, root / "private" / "calibration" / "mutants" / "zero", case
        )
        assert frontier > baseline + 0.01, (task, baseline, frontier)
        assert frontier > mutant + 0.01, (task, mutant, frontier)
        assert baseline_metrics["protocol_errors"] == 0
        assert frontier_metrics["protocol_errors"] == 0
        rows.append(
            {
                "task": task,
                "zero_mutant": mutant,
                "public_baseline": baseline,
                "private_frontier": frontier,
                "frontier_headroom": frontier - baseline,
                "baseline_metrics": baseline_metrics,
                "frontier_metrics": frontier_metrics,
                "mutant_metrics": mutant_metrics,
            }
        )

    lightcycle = (
        ROOT / "papers" / "lightcycle-agents" / "capsules" / "adversarial-tournament" / "v1.0.0"
    )
    case = kit.case("lightcycle", 9137, 1)
    with tempfile.TemporaryDirectory() as temporary:
        evidence = Path(temporary)
        baseline, baseline_metrics = arena_verifier.lightcycle_quality(
            lightcycle / "public" / "starter", case, evidence
        )
        reference, reference_metrics = arena_verifier.lightcycle_quality(
            lightcycle / "private" / "reference", case, evidence
        )
        illegal, illegal_metrics = arena_verifier.lightcycle_quality(
            lightcycle / "private" / "calibration" / "mutants" / "illegal",
            case,
            evidence,
        )
        slow_case = dict(case)
        slow_case["matches"] = 2
        slow, slow_metrics = arena_verifier.lightcycle_quality(
            lightcycle / "private" / "calibration" / "mutants" / "slow",
            slow_case,
            evidence,
        )
    assert baseline_metrics["illegal"] == 0
    assert reference_metrics["illegal"] == 0
    assert reference >= baseline
    assert illegal == 0 and illegal_metrics["illegal"] > 0
    assert slow == 0 and slow_metrics["timeouts"] > 0
    rows.append(
        {
            "task": "lightcycle",
            "illegal_mutant": illegal,
            "timeout_mutant": slow,
            "public_baseline": baseline,
            "private_reference": reference,
            "baseline_metrics": baseline_metrics,
            "reference_metrics": reference_metrics,
            "illegal_metrics": illegal_metrics,
            "timeout_metrics": slow_metrics,
        }
    )
    if output_path is not None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(rows, indent=2) + "\n", encoding="utf-8")
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    print(json.dumps(run(args.output), indent=2))


if __name__ == "__main__":
    main()
