from __future__ import annotations

import argparse
import json
import math
import statistics
import subprocess
import sys
from pathlib import Path
from typing import Any


def estimate(points: list[list[float]]) -> dict[str, float]:
    slopes = [
        (right[1] - left[1]) / (right[0] - left[0])
        for index, left in enumerate(points)
        for right in points[index + 1 :]
        if right[0] != left[0]
    ]
    slope = statistics.median(slopes)
    return {
        "slope": slope,
        "intercept": statistics.median(y - slope * x for x, y in points),
    }


def close_result(actual: Any, expected: dict[str, float]) -> bool:
    try:
        return all(
            math.isfinite(float(actual[key]))
            and math.isclose(float(actual[key]), value, abs_tol=1e-9, rel_tol=1e-9)
            for key, value in expected.items()
        )
    except (KeyError, TypeError, ValueError):
        return False


def result(
    check_id: str, passed: bool, summary: str, measurements: dict[str, Any]
) -> dict[str, Any]:
    return {
        "id": check_id,
        "status": "passed" if passed else "failed",
        "score": 1 if passed else 0,
        "summary": summary,
        "measurements": measurements,
        "evidence": ["comparison.json"],
    }


def invoke_candidate(
    submission: Path, case: dict[str, Any], evidence: Path
) -> tuple[dict[str, Any] | None, str]:
    name = str(case["name"])
    source = evidence / f"{name}-input.json"
    output = evidence / f"{name}-candidate.json"
    source.write_text(json.dumps({"points": case["points"]}), encoding="utf-8")
    try:
        process = subprocess.run(
            [sys.executable, "solution.py", str(source), str(output)],
            cwd=submission,
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        if process.returncode != 0 or not output.is_file():
            return None, f"exit={process.returncode}; stderr={process.stderr[-500:]}"
        value = json.loads(output.read_text(encoding="utf-8"))
        return value, ""
    except (OSError, subprocess.TimeoutExpired, json.JSONDecodeError) as exc:
        return None, str(exc)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--context", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    context = json.loads(args.context.read_text(encoding="utf-8"))
    submission = Path(context["submission_dir"])
    artifacts = Path(context["artifact_dir"])
    evidence = Path(context["evidence_dir"])
    hidden = json.loads(
        (Path(context["hidden_inputs_dir"]) / "cases.json").read_text(encoding="utf-8")
    )

    visible_expected = {"slope": 2.0, "intercept": 1.0}
    visible_path = artifacts / "visible_result.json"
    try:
        visible_actual = json.loads(visible_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        visible_actual = None
    visible_pass = close_result(visible_actual, visible_expected)

    comparisons: list[dict[str, Any]] = []
    all_exact = True
    robust_pass = False
    for case in hidden:
        expected = estimate(case["points"])
        actual, error = invoke_candidate(submission, case, evidence)
        passed = close_result(actual, expected)
        all_exact = all_exact and passed
        if case["name"] == "robust":
            robust_pass = passed and abs(float(actual["slope"]) - 2.0) <= 0.1
        comparisons.append(
            {
                "name": case["name"],
                "expected": expected,
                "actual": actual,
                "passed": passed,
                "error": error,
            }
        )
    report_exists = (submission / "REPORT.md").is_file()
    comparison_path = evidence / "comparison.json"
    comparison_path.write_text(
        json.dumps(
            {
                "visible": {"expected": visible_expected, "actual": visible_actual},
                "hidden": comparisons,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    output = {
        "schema_version": 1,
        "checks": [
            result(
                "visible-artifact",
                visible_pass,
                "Visible artifact agrees with the specified estimator"
                if visible_pass
                else "Visible artifact is missing or incorrect",
                {"actual": visible_actual, "expected": visible_expected},
            ),
            result(
                "hidden-exact",
                all_exact,
                "Candidate agrees on all hidden cases"
                if all_exact
                else "Candidate disagrees or fails on at least one hidden case",
                {"cases": comparisons},
            ),
            result(
                "robustness-property",
                robust_pass,
                "Recovered slope 2 despite the adversarial outlier"
                if robust_pass
                else "Robustness property was not demonstrated",
                {"robust_case_passed": robust_pass},
            ),
            result(
                "educational-report",
                report_exists,
                "Educational report is present"
                if report_exists
                else "Educational report is missing",
                {"exists": report_exists},
            ),
        ],
        "warnings": [],
    }
    args.output.write_text(json.dumps(output, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
