"""Optional helpers for writing verifiers that emit the language-agnostic protocol."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .models import CheckResult, CheckStatus, VerifierOutput, WarningRecord
from .util import dump_json


def scored_result(
    check_id: str,
    score: float,
    summary: str,
    *,
    measurements: dict[str, Any] | None = None,
    evidence: list[str] | None = None,
) -> CheckResult:
    if score == 1:
        status = CheckStatus.PASSED
    elif score == 0:
        status = CheckStatus.FAILED
    else:
        status = CheckStatus.PARTIAL
    return CheckResult(
        id=check_id,
        status=status,
        score=score,
        summary=summary,
        measurements=measurements or {},
        evidence=evidence or [],
    )


def exact(
    check_id: str, actual: Any, expected: Any, summary: str = "Exact comparison"
) -> CheckResult:
    return scored_result(
        check_id,
        float(actual == expected),
        summary,
        measurements={"actual": actual, "expected": expected},
    )


def tolerance(
    check_id: str,
    actual: float,
    expected: float,
    tolerance_value: float,
    summary: str = "Tolerance comparison",
) -> CheckResult:
    error = abs(actual - expected)
    return scored_result(
        check_id,
        float(error <= tolerance_value),
        summary,
        measurements={
            "actual": actual,
            "expected": expected,
            "absolute_error": error,
            "tolerance": tolerance_value,
        },
    )


@dataclass
class Results:
    checks: list[CheckResult] = field(default_factory=list)
    warnings: list[WarningRecord] = field(default_factory=list)

    def add(self, result: CheckResult) -> CheckResult:
        self.checks.append(result)
        return result

    def warn(self, code: str, message: str) -> None:
        self.warnings.append(WarningRecord(code=code, message=message))

    def write(self, output_path: Path) -> None:
        output = VerifierOutput(checks=self.checks, warnings=self.warnings)
        dump_json(output_path, output.model_dump(mode="json"))
