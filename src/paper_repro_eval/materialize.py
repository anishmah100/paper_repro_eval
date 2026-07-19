"""Automated, deterministic candidate-workspace materialization."""

from __future__ import annotations

import shutil
import uuid
from pathlib import Path

from .catalog import ResolvedCapsule, resolve_suite
from .errors import IntegrityError
from .git_ops import initialize_workspace
from .models import RunRecord, RunState
from .repository import Repository
from .util import atomic_directory, copy_tree_safe, dump_json, slugify, tree_digest, utc_now

PUBLIC_MAPPINGS = {
    "paper": "paper",
    "resources": "resources",
    "starter": "starter",
}


def _next_attempt(agent_dir: Path) -> int:
    attempts: list[int] = []
    if agent_dir.exists():
        for path in agent_dir.glob("attempt-*"):
            try:
                attempts.append(int(path.name.split("-", 1)[1]))
            except (IndexError, ValueError):
                continue
    return max(attempts, default=0) + 1


def _materialize_public(capsule: ResolvedCapsule, workspace: Path) -> None:
    task = capsule.public_dir / "TASK.md"
    shutil.copy2(task, workspace / "TASK.md")
    for source_name, destination_name in PUBLIC_MAPPINGS.items():
        source = capsule.public_dir / source_name
        destination = workspace / destination_name
        if source.is_dir():
            copy_tree_safe(source, destination)
        else:
            destination.mkdir(parents=True, exist_ok=True)
    (workspace / "submission").mkdir()


def prepare_suite(
    repository: Repository,
    suite_id: str,
    agents: list[str],
    *,
    isolation: str = "directory",
) -> list[RunRecord]:
    if not agents:
        raise IntegrityError("At least one agent label is required")
    if len(agents) != len(set(agents)):
        raise IntegrityError("Agent labels must be unique within one prepare operation")
    suite, capsules = resolve_suite(repository, suite_id)
    records: list[RunRecord] = []
    digests_by_capsule: dict[str, set[str]] = {}

    for capsule in capsules:
        capsule_slug = slugify(capsule.manifest.id)
        for agent in agents:
            agent_slug = slugify(agent)
            agent_dir = repository.runs_dir / slugify(suite.id) / capsule_slug / agent_slug
            attempt = _next_attempt(agent_dir)
            attempt_dir = agent_dir / f"attempt-{attempt:03d}"
            run_id = uuid.uuid4().hex[:12]
            now = utc_now()
            with atomic_directory(attempt_dir) as stage:
                workspace = stage / "workspace"
                workspace.mkdir()
                _materialize_public(capsule, workspace)
                initial_digest = tree_digest(workspace, exclude_names={".git"})
                initialize_workspace(workspace)
                record = RunRecord(
                    run_id=run_id,
                    suite_id=suite.id,
                    capsule_id=capsule.manifest.id,
                    capsule_version=capsule.manifest.version,
                    capsule_digest=capsule.digest,
                    agent=agent,
                    attempt=attempt,
                    state=RunState.PREPARED,
                    isolation="container" if isolation == "container" else "directory",
                    created_at=now,
                    updated_at=now,
                    workspace=(attempt_dir / "workspace").relative_to(repository.root).as_posix(),
                    initial_digest=initial_digest,
                )
                dump_json(stage / "run.json", record.model_dump(mode="json"))
            records.append(record)
            digests_by_capsule.setdefault(capsule.manifest.id, set()).add(record.initial_digest)

    mismatches = {
        capsule_id: digests
        for capsule_id, digests in digests_by_capsule.items()
        if len(digests) != 1
    }
    if mismatches:
        raise IntegrityError(f"Prepared workspaces are not identical: {mismatches}")
    return records

