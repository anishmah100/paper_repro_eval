"""Trusted verifier protocol, dependency handling, and core scoring."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import ValidationError

from .catalog import resolve_capsule
from .errors import ConfigurationError, IntegrityError
from .execution import execute
from .lifecycle import latest_reproduction, numbered_directories, update_state
from .models import (
    CheckGraph,
    CheckKind,
    CheckResult,
    CheckStatus,
    RunState,
    VerificationRecord,
    VerifierConfig,
    VerifierOutput,
    WarningRecord,
)
from .repository import Repository
from .run_store import find_run
from .util import atomic_directory, dump_json, ensure_within, load_json, load_yaml, utc_now


def _load_inputs(private_dir: Path) -> tuple[CheckGraph, VerifierConfig]:
    try:
        checks = CheckGraph.model_validate(load_yaml(private_dir / "checks.yaml"))
        config = VerifierConfig.model_validate(load_yaml(private_dir / "verifier.yaml"))
    except ValidationError as exc:
        raise ConfigurationError(f"Invalid trusted verifier configuration: {exc}") from exc
    return checks, config


def _block_dependencies(graph: CheckGraph, results: list[CheckResult]) -> list[CheckResult]:
    raw = {result.id: result for result in results}
    specs = {check.id: check for check in graph.checks}
    resolved: dict[str, CheckResult] = {}

    def resolve(check_id: str) -> CheckResult:
        if check_id in resolved:
            return resolved[check_id]
        check = specs[check_id]
        blocking = [
            dependency
            for dependency in check.depends_on
            if resolve(dependency).status
            in {CheckStatus.FAILED, CheckStatus.BLOCKED, CheckStatus.ERROR}
        ]
        if blocking:
            result = CheckResult(
                id=check_id,
                status=CheckStatus.BLOCKED,
                score=0,
                summary=f"Blocked by prerequisite checks: {', '.join(blocking)}",
            )
        else:
            result = raw[check_id]
        resolved[check_id] = result
        return result

    return [resolve(check.id) for check in graph.checks]


def _score(graph: CheckGraph, results: list[CheckResult]) -> float | None:
    by_id = {result.id: result for result in results}
    objective = [check for check in graph.checks if check.kind is CheckKind.OBJECTIVE]
    if any(by_id[check.id].status is CheckStatus.ERROR for check in objective):
        return None
    denominator = sum(check.weight for check in objective)
    if denominator == 0:
        return 1.0
    return sum(check.weight * (by_id[check.id].score or 0) for check in objective) / denominator


def verify_run(repository: Repository, run_id: str) -> VerificationRecord:
    run = find_run(repository, run_id)
    reproduction_dir, reproduction = latest_reproduction(run)
    capsule = resolve_capsule(
        repository, run.record.paper_id, run.record.capsule_id, run.record.capsule_version
    )
    if capsule.digest != run.record.capsule_digest:
        raise IntegrityError(
            "Capsule changed since preparation; restore the pinned capsule before verification"
        )
    graph, config = _load_inputs(capsule.private_dir)
    root = run.evaluation_dir / "verifications"
    existing = numbered_directories(root, "attempt")
    attempt = existing[-1][0] + 1 if existing else 1
    destination = root / f"attempt-{attempt:03d}"
    with atomic_directory(destination) as stage:
        evidence = stage / "evidence"
        evidence.mkdir()
        output_path = stage / "verifier-output.json"
        context = {
            "schema_version": 1,
            "run_id": run_id,
            "reproduction_status": reproduction.status,
            "submission_dir": str((reproduction_dir / "work").resolve()),
            "artifact_dir": str((reproduction_dir / "artifacts").resolve()),
            "private_dir": str(capsule.private_dir.resolve()),
            "hidden_inputs_dir": str((capsule.private_dir / "hidden_inputs").resolve()),
            "reference_dir": str((capsule.private_dir / "reference").resolve()),
            "evidence_dir": str(evidence.resolve()),
        }
        context_path = stage / "context.json"
        dump_json(context_path, context)
        command = [
            argument.replace("{context}", str(context_path.resolve())).replace(
                "{output}", str(output_path.resolve())
            )
            for argument in config.command
        ]
        process = execute(
            command,
            cwd=capsule.private_dir / "verifier",
            timeout_seconds=config.timeout_seconds,
        )
        (stage / "stdout.txt").write_text(process.stdout, encoding="utf-8")
        (stage / "stderr.txt").write_text(process.stderr, encoding="utf-8")
        warnings: list[WarningRecord] = []
        checks: list[CheckResult] = []
        score: float | None = None
        status: Literal["success", "candidate-failure", "evaluator-error"] = "evaluator-error"
        error: str | None = None
        if process.infrastructure_error:
            error = process.infrastructure_error
        elif process.timed_out:
            error = "Trusted verifier timed out"
        elif process.exit_code != 0:
            error = f"Trusted verifier exited with code {process.exit_code}"
        elif not output_path.is_file():
            error = "Trusted verifier did not create verifier-output.json"
        else:
            try:
                output = VerifierOutput.model_validate(load_json(output_path))
                expected = {check.id for check in graph.checks}
                actual = [result.id for result in output.checks]
                if len(actual) != len(set(actual)) or set(actual) != expected:
                    raise IntegrityError(
                        f"Verifier check IDs differ from checks.yaml: expected {sorted(expected)}, "
                        f"received {sorted(actual)}"
                    )
                for result in output.checks:
                    for relative in result.evidence:
                        evidence_path = ensure_within(evidence / relative, evidence)
                        if not evidence_path.is_file():
                            raise IntegrityError(
                                f"Verifier declared missing evidence file: {relative}"
                            )
                checks = _block_dependencies(graph, output.checks)
                warnings = output.warnings
                score = _score(graph, checks)
                status = (
                    "evaluator-error"
                    if score is None
                    else (
                        "candidate-failure"
                        if reproduction.status == "candidate-failure"
                        else "success"
                    )
                )
                if reproduction.status == "infrastructure-error":
                    status = "evaluator-error"
                    score = None
                    warnings.append(
                        WarningRecord(
                            code="infrastructure-error",
                            message="Reproduction infrastructure failed",
                        )
                    )
            except (ValidationError, ConfigurationError, IntegrityError) as exc:
                error = str(exc)
        if error:
            warnings.append(WarningRecord(code="evaluator-error", message=error))
        record = VerificationRecord(
            run_id=run_id,
            reproduction_attempt=reproduction.attempt,
            created_at=utc_now(),
            status=status,
            objective_score=score,
            checks=checks,
            warnings=warnings,
        )
        dump_json(stage / "verification.json", record.model_dump(mode="json"))
    update_state(run, RunState.VERIFIED)
    return record


def latest_verification(repository: Repository, run_id: str) -> tuple[Path, VerificationRecord]:
    run = find_run(repository, run_id)
    values = numbered_directories(run.evaluation_dir / "verifications", "attempt")
    if not values:
        raise ConfigurationError(f"Run {run_id} has not been verified")
    path = values[-1][1]
    return path, VerificationRecord.model_validate(load_json(path / "verification.json"))
