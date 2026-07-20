#!/usr/bin/env python3
"""Deterministic calibration audit for every batch visual arena."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "templates" / "arena_kit"), str(ROOT / "authoring")]
import arena_kit as kit  # noqa: E402
import trusted_poisson  # noqa: E402


def plausible_mutant(task: str, case: dict[str, Any]) -> dict[str, Any]:
    if task == "poisson":
        image = np.array(case["target"])
        mask = np.array(case["mask"], dtype=bool)
        image[mask] = np.array(case["source"])[mask]
        return {"image": image.tolist()}
    if task == "multipole":
        count = case["poles"]
        return {"gains": [0, 0] + [30] * count + [0] * count}
    if task == "pathtracer":
        return {"image": np.ones((case["height"], case["width"], 3)).tolist()}
    if task == "mpm":
        static = np.repeat(np.array(case["positions"])[None, :, :], case["steps"], axis=0)
        return {"frames": static.tolist()}
    if task == "world_mpc":
        return {"actions": [[0, 0]] * case["steps"]}
    if task == "topology":
        return {"density": np.ones((case["height"], case["width"])).tolist()}
    if task == "smoke":
        return {"controls": [[0, 0]] * case["steps"]}
    if task == "softrobot":
        return {
            "morphology": np.eye(case["height"], case["width"]).tolist(),
            "frequency": 2,
            "phase_gradient": 1,
        }
    if task == "inverse_render":
        return {"objects": [[0.5, 0.5, 0.4, 1, 0, 1]]}
    raise ValueError(task)


def trusted_score(task: str, case: dict[str, Any], output: dict[str, Any]) -> float:
    metrics = (
        trusted_poisson.score(case, output) if task == "poisson" else kit.score(task, case, output)
    )
    return float(metrics["quality"])


def run(output_path: Path | None = None) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        for index, task in enumerate(value for value in kit.TASKS if value != "lightcycle"):
            case = kit.case(task, 90210 + index * 101, 2)
            input_path = root / f"{task}.json"
            reference_path = root / f"{task}-reference.json"
            input_path.write_text(json.dumps(case), encoding="utf-8")
            command = [
                sys.executable,
                str(ROOT / "authoring" / "arena_reference.py"),
                task,
                str(input_path),
                str(reference_path),
            ]
            subprocess.run(command, check=True, capture_output=True, text=True)
            reference = json.loads(reference_path.read_text(encoding="utf-8"))
            reference_repeat = subprocess.run(command, check=True, capture_output=True, text=True)
            assert reference_repeat.returncode == 0
            assert reference_path.read_text(encoding="utf-8") == json.dumps(reference)
            baseline_score = trusted_score(task, case, kit.baseline(task, case))
            mutant_score = trusted_score(task, case, plausible_mutant(task, case))
            frontier_score = trusted_score(task, case, reference)
            assert 0 <= mutant_score <= 1
            assert frontier_score > baseline_score + 0.015, (task, baseline_score, frontier_score)
            assert frontier_score > mutant_score + 0.015, (task, mutant_score, frontier_score)
            rows.append(
                {
                    "task": task,
                    "malformed": 0.0,
                    "plausible_mutant": mutant_score,
                    "public_baseline": baseline_score,
                    "private_frontier": frontier_score,
                    "frontier_headroom": frontier_score - baseline_score,
                    "deterministic": True,
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
