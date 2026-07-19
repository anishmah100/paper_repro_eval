"""Immutable sealing and fresh reproduction lifecycle."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from .errors import ConfigurationError, IntegrityError
from .execution import execute
from .git_ops import diff, head
from .models import ReproductionRecord, RunState, SealRecord
from .repository import Repository
from .run_store import StoredRun, find_run
from .util import (
    atomic_directory,
    copy_tree_safe,
    dump_json,
    load_json,
    make_read_only,
    reject_symlinks,
    tree_digest,
    utc_now,
)


def numbered_directories(root: Path, prefix: str) -> list[tuple[int, Path]]:
    values: list[tuple[int, Path]] = []
    if root.is_dir():
        for path in root.glob(f"{prefix}-*"):
            try:
                values.append((int(path.name.removeprefix(f"{prefix}-")), path))
            except ValueError:
                continue
    return sorted(values)


def latest_seal(run: StoredRun) -> tuple[Path, SealRecord]:
    seals = numbered_directories(run.sealed_dir, "revision")
    if not seals:
        raise ConfigurationError(f"Run {run.record.run_id} has not been sealed")
    path = seals[-1][1]
    return path, SealRecord.model_validate(load_json(path / "seal.json"))


def latest_reproduction(run: StoredRun) -> tuple[Path, ReproductionRecord]:
    root = run.evaluation_dir / "reproductions"
    reproductions = numbered_directories(root, "attempt")
    if not reproductions:
        raise ConfigurationError(f"Run {run.record.run_id} has not been reproduced")
    path = reproductions[-1][1]
    return path, ReproductionRecord.model_validate(load_json(path / "reproduction.json"))


def update_state(run: StoredRun, state: RunState) -> None:
    updated = StoredRun(
        directory=run.directory,
        record=run.record.model_copy(update={"state": state, "updated_at": utc_now()}),
    )
    updated.save()


def seal_run(repository: Repository, run_id: str) -> SealRecord:
    run = find_run(repository, run_id)
    submission = run.workspace / "submission"
    reject_symlinks(submission)
    if not submission.is_dir():
        raise IntegrityError(f"Missing submission directory: {submission}")
    digest = tree_digest(submission)
    existing = numbered_directories(run.sealed_dir, "revision")
    if existing:
        previous = SealRecord.model_validate(load_json(existing[-1][1] / "seal.json"))
        if previous.submission_digest == digest:
            return previous
    revision = existing[-1][0] + 1 if existing else 1
    destination = run.sealed_dir / f"revision-{revision:03d}"
    required = ["reproduce.sh", "REPORT.md"]
    missing = [name for name in required if not (submission / name).is_file()]
    record = SealRecord(
        run_id=run_id,
        revision=revision,
        created_at=utc_now(),
        submission_digest=digest,
        source_git_head=head(run.workspace),
        source_git_diff=diff(run.workspace),
        missing_required=missing,
    )
    with atomic_directory(destination) as stage:
        copy_tree_safe(submission, stage / "submission")
        dump_json(stage / "seal.json", record.model_dump(mode="json"))
    make_read_only(destination)
    update_state(run, RunState.SEALED)
    return record


def reproduce_run(
    repository: Repository,
    run_id: str,
    *,
    timeout_seconds: float | None = None,
) -> ReproductionRecord:
    run = find_run(repository, run_id)
    seal_dir, seal = latest_seal(run)
    root = run.evaluation_dir / "reproductions"
    existing = numbered_directories(root, "attempt")
    attempt = existing[-1][0] + 1 if existing else 1
    destination = root / f"attempt-{attempt:03d}"
    with atomic_directory(destination) as stage:
        work = stage / "work"
        artifacts = stage / "artifacts"
        copy_tree_safe(seal_dir / "submission", work)
        result_status: Literal["success", "candidate-failure", "infrastructure-error"]
        artifacts.mkdir()
        script = work / "reproduce.sh"
        if not script.is_file():
            result_status = "candidate-failure"
            result = None
            stdout = ""
            stderr = "Required submission/reproduce.sh is missing."
        else:
            result = execute(
                ["bash", "reproduce.sh"],
                cwd=work,
                environment={"REPRO_OUTPUT_DIR": str(artifacts.resolve())},
                timeout_seconds=timeout_seconds,
            )
            stdout = result.stdout
            stderr = result.stderr
            if result.infrastructure_error:
                result_status = "infrastructure-error"
                stderr += f"\nInfrastructure error: {result.infrastructure_error}\n"
            elif result.exit_code == 0:
                result_status = "success"
            else:
                result_status = "candidate-failure"
                if result.timed_out:
                    stderr += "\nCandidate reproduction timed out.\n"
        (stage / "stdout.txt").write_text(stdout, encoding="utf-8")
        (stage / "stderr.txt").write_text(stderr, encoding="utf-8")
        record = ReproductionRecord(
            run_id=run_id,
            seal_revision=seal.revision,
            attempt=attempt,
            created_at=utc_now(),
            status=result_status,
            exit_code=result.exit_code if result else None,
            elapsed_seconds=result.elapsed_seconds if result else 0,
            artifact_digest=tree_digest(artifacts),
            stdout_path=(destination / "stdout.txt").relative_to(repository.root).as_posix(),
            stderr_path=(destination / "stderr.txt").relative_to(repository.root).as_posix(),
            work_dir=(destination / "work").relative_to(repository.root).as_posix(),
            artifact_dir=(destination / "artifacts").relative_to(repository.root).as_posix(),
        )
        dump_json(stage / "reproduction.json", record.model_dump(mode="json"))
    update_state(run, RunState.REPRODUCED)
    return record
