"""Small, dependency-light helpers shared by trusted visual-arena verifiers."""

from __future__ import annotations

import json
import math
import subprocess
from pathlib import Path
from typing import Any


def clamp01(value: float) -> float:
    """Clamp a numeric score to the leaderboard's canonical range."""
    return max(0.0, min(1.0, float(value)))


def geometric_mean(values: list[float], floor: float = 1e-9) -> float:
    """Aggregate metrics without allowing one very large value to hide a failure."""
    if not values:
        return 0.0
    return math.exp(sum(math.log(max(floor, clamp01(v))) for v in values) / len(values))


def check(
    check_id: str,
    score: float,
    summary: str,
    measurements: dict[str, Any],
    evidence: list[str] | None = None,
    *,
    threshold: float = 0.5,
) -> dict[str, Any]:
    """Construct one verifier result using the framework schema."""
    normalized = clamp01(score)
    return {
        "id": check_id,
        "status": "passed" if normalized >= threshold else "failed",
        "score": normalized,
        "summary": summary,
        "measurements": measurements,
        "evidence": evidence or [],
    }


def run(
    command: list[str], cwd: Path, timeout: float, env: dict[str, str] | None = None
) -> subprocess.CompletedProcess[str]:
    """Run an untrusted candidate with bounded time and captured diagnostics."""
    return subprocess.run(
        command,
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )


def read_context(path: Path) -> dict[str, Any]:
    value: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    return value


def write_output(
    path: Path, checks: list[dict[str, Any]], warnings: list[str] | None = None
) -> None:
    path.write_text(
        json.dumps({"schema_version": 1, "checks": checks, "warnings": warnings or []}, indent=2),
        encoding="utf-8",
    )
