"""Zero-friction candidate workspace readiness checks and launch sheets."""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path

from .errors import ConfigurationError, IntegrityError
from .models import RunRecord, RunState
from .repository import Repository
from .run_store import list_runs
from .util import slugify, tree_digest, utc_now

REQUIRED_WORKSPACE_PATHS = (
    "AGENTS.md",
    "CLAUDE.md",
    "WORK_PLAN.md",
    "TASK.md",
    "EXECUTABLE_CONTRACT.md",
    "paper",
    "paper_resources",
    "resources",
    "starter",
    "arena_kit/arena_kit.py",
    "submission",
    ".git",
)

ONE_LINE_PROMPT = (
    "Read WORK_PLAN.md, EXECUTABLE_CONTRACT.md, and TASK.md, then complete the task autonomously."
)


def workspace_readiness(repository: Repository, record: RunRecord) -> list[str]:
    """Return concrete reasons a prepared workspace is not safe to hand to an agent."""
    workspace = repository.root / record.workspace
    errors = [
        f"missing {relative}"
        for relative in REQUIRED_WORKSPACE_PATHS
        if not (workspace / relative).exists()
    ]
    for forbidden in ("private", "checks.yaml"):
        if (workspace / forbidden).exists():
            errors.append(f"forbidden private path present: {forbidden}")
    if workspace.exists():
        symlinks = [
            path.relative_to(workspace).as_posix()
            for path in workspace.rglob("*")
            if path.is_symlink()
        ]
        if symlinks:
            errors.append(f"symlinks present: {', '.join(symlinks[:5])}")
    submission = workspace / "submission"
    if submission.is_dir() and any(submission.iterdir()):
        errors.append("submission is not empty")
    if record.state is not RunState.PREPARED:
        errors.append(f"run state is {record.state}, expected prepared")
    if (
        workspace.exists()
        and tree_digest(workspace, exclude_names={".git"}) != record.initial_digest
    ):
        errors.append("workspace differs from its initial public digest")
    return errors


def latest_prepared_records(
    repository: Repository, suite_id: str, agents: set[str] | None = None
) -> list[RunRecord]:
    """Select each requested agent/capsule's latest still-pristine prepared attempt."""
    latest: dict[tuple[str, str, str], RunRecord] = {}
    for stored in list_runs(repository):
        record = stored.record
        if record.suite_id != suite_id or (agents is not None and record.agent not in agents):
            continue
        key = (record.paper_id, record.capsule_id, record.agent)
        previous = latest.get(key)
        if previous is None or record.attempt > previous.attempt:
            latest[key] = record
    records = sorted(
        latest.values(),
        key=lambda record: (record.agent, record.paper_id, record.capsule_id),
    )
    if not records:
        raise ConfigurationError(f"No runs found for suite {suite_id}")
    return records


def write_launch_sheet(repository: Repository, records: list[RunRecord]) -> Path:
    """Validate prepared workspaces and write an exact operator handoff sheet."""
    if not records:
        raise ConfigurationError("Cannot create a launch sheet without runs")
    problems: list[str] = []
    for record in records:
        problems.extend(
            f"{record.run_id}: {message}" for message in workspace_readiness(repository, record)
        )
    if problems:
        raise IntegrityError("Workspaces are not ready for handoff:\n- " + "\n- ".join(problems))

    suite_id = records[0].suite_id
    if any(record.suite_id != suite_id for record in records):
        raise IntegrityError("A launch sheet may contain only one suite")
    created = utc_now()
    stamp = created.replace(":", "").replace("+", "-")
    destination = (
        repository.reports_dir / slugify(suite_id) / "launch-sheets" / f"launch-{stamp}.md"
    )
    destination.parent.mkdir(parents=True, exist_ok=True)
    grouped: dict[str, list[RunRecord]] = defaultdict(list)
    for record in records:
        grouped[record.agent].append(record)

    lines = [
        f"# Agent launch sheet: {suite_id}",
        "",
        f"Generated: {created}",
        "",
        "Every listed workspace passed the pristine-workspace readiness check. Open exactly one",
        "workspace in the corresponding native coding assistant. Do not expose any other run.",
        "",
        "Use this prompt verbatim:",
        "",
        f"> {ONE_LINE_PROMPT}",
        "",
    ]
    for agent, agent_records in sorted(grouped.items()):
        lines.extend(
            [
                f"## {agent}",
                "",
                "| Run ID | Paper / capsule | Absolute workspace | Enter command |",
                "|---|---|---|---|",
            ]
        )
        for record in agent_records:
            workspace = (repository.root / record.workspace).resolve()
            lines.append(
                f"| `{record.run_id}` | `{record.paper_id}/{record.capsule_id}` | "
                f"`{workspace}` | `uv run paper_repro_eval enter {record.run_id}` |"
            )
        lines.append("")
    lines.extend(
        [
            "## Operator boundary",
            "",
            "Internet search and normal native-agent tools are allowed. The only prohibited",
            "information flow is a candidate reading another candidate's workspace, result, score,",
            "or review. The full boundary and completion checklist are inside every workspace in",
            "`WORK_PLAN.md`.",
            "",
        ]
    )
    destination.write_text("\n".join(lines), encoding="utf-8")
    return destination
