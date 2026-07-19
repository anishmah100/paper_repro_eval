"""Static human-review packets, suite reports, and educational curation."""

from __future__ import annotations

import csv
import shutil
from pathlib import Path

import bleach
from markdown_it import MarkdownIt

from .catalog import resolve_capsule
from .errors import ConfigurationError, IntegrityError
from .lifecycle import latest_reproduction, latest_seal, update_state
from .models import RunState
from .repository import Repository
from .run_store import find_run, list_runs
from .util import atomic_directory, copy_tree_safe, dump_json
from .verification import latest_verification


def _safe_markdown(value: str) -> str:
    rendered = MarkdownIt("commonmark").render(value)
    return bleach.clean(
        rendered,
        tags=set(bleach.sanitizer.ALLOWED_TAGS)
        | {"p", "h1", "h2", "h3", "pre", "code", "table", "thead", "tbody", "tr", "th", "td"},
        attributes={"a": ["href", "title"]},
    )


def create_review_packet(repository: Repository, run_id: str) -> Path:
    run = find_run(repository, run_id)
    seal_dir, seal = latest_seal(run)
    reproduction_dir, reproduction = latest_reproduction(run)
    verification_dir, verification = latest_verification(repository, run_id)
    capsule = resolve_capsule(repository, run.record.capsule_id, run.record.capsule_version)
    destination = run.review_dir / f"verification-{reproduction.attempt:03d}"
    if destination.exists():
        return destination
    with atomic_directory(destination) as stage:
        shutil.copy2(seal_dir / "submission" / "REPORT.md", stage / "CANDIDATE_REPORT.md")
        shutil.copy2(capsule.private_dir / "REVIEW_GUIDE.md", stage / "CAPSULE_REVIEW_GUIDE.md")
        shutil.copy2(repository.root / "REVIEWING.md", stage / "REVIEWING.md")
        if (reproduction_dir / "artifacts").exists():
            copy_tree_safe(reproduction_dir / "artifacts", stage / "artifacts")
        if (verification_dir / "evidence").exists():
            copy_tree_safe(verification_dir / "evidence", stage / "evidence")
        lines = [
            f"# Review: {run.record.capsule_id} — {run.record.agent}",
            "",
            f"- Run: {run_id}",
            f"- Seal revision: {seal.revision}",
            f"- Reproduction: {reproduction.status}",
            f"- Verification: {verification.status}",
            f"- Objective score: {verification.objective_score}",
            "",
            "## Objective checks",
            "",
            "| Check | Status | Score | Summary |",
            "|---|---:|---:|---|",
        ]
        for check in verification.checks:
            lines.append(
                f"| {check.id} | {check.status} | {check.score} | "
                f"{check.summary.replace('|', '&#124;')} |"
            )
        lines.extend(
            [
                "",
                "## Human review prompts",
                "",
                "- Does the artifact demonstrate the paper's claim, not merely pass a superficial test?",
                "- Are assumptions, deviations, limitations, and negative results candidly reported?",
                "- Do the code and evidence agree with the narrative?",
                "- Is the result educational and independently inspectable?",
                "",
                "Record qualitative conclusions in NOTES.md. They are deliberately not auto-scored.",
                "",
            ]
        )
        summary = "\n".join(lines)
        (stage / "SUMMARY.md").write_text(summary, encoding="utf-8")
        (stage / "NOTES.md").write_text("# Human review notes\n\n", encoding="utf-8")
        (stage / "index.html").write_text(
            "<!doctype html><meta charset='utf-8'><title>Review packet</title>"
            "<style>body{max-width:960px;margin:2rem auto;font:16px system-ui;line-height:1.5}"
            "table{border-collapse:collapse}td,th{border:1px solid #bbb;padding:.4rem}"
            "code,pre{background:#f4f4f4}</style>"
            + _safe_markdown(summary)
            + "<h2>Candidate report</h2>"
            + _safe_markdown((stage / "CANDIDATE_REPORT.md").read_text(encoding="utf-8")),
            encoding="utf-8",
        )
    update_state(run, RunState.REVIEW_READY)
    return destination


def suite_report(repository: Repository, suite_id: str) -> Path:
    rows: list[dict[str, object]] = []
    for run in list_runs(repository):
        if run.record.suite_id != suite_id:
            continue
        try:
            _, verification = latest_verification(repository, run.record.run_id)
            status = verification.status
            score = verification.objective_score
        except ConfigurationError:
            status = run.record.state
            score = None
        rows.append(
            {
                "run_id": run.record.run_id,
                "capsule": run.record.capsule_id,
                "version": run.record.capsule_version,
                "agent": run.record.agent,
                "attempt": run.record.attempt,
                "status": str(status),
                "objective_score": score,
            }
        )
    destination = repository.reports_dir / suite_id
    destination.mkdir(parents=True, exist_ok=True)
    dump_json(destination / "report.json", {"schema_version": 1, "suite": suite_id, "runs": rows})
    with (destination / "report.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]) if rows else ["run_id"])
        writer.writeheader()
        writer.writerows(rows)
    md = [
        f"# Suite report: {suite_id}",
        "",
        "| Capsule | Agent | Status | Score |",
        "|---|---|---:|---:|",
    ]
    for row in rows:
        md.append(
            f"| {row['capsule']} | {row['agent']} | {row['status']} | "
            f"{row['objective_score']} |"
        )
    markdown = "\n".join(md) + "\n"
    (destination / "report.md").write_text(markdown, encoding="utf-8")
    (destination / "index.html").write_text(
        "<!doctype html><meta charset='utf-8'><title>Suite report</title>" + _safe_markdown(markdown),
        encoding="utf-8",
    )
    return destination


def curate(repository: Repository, run_id: str) -> Path:
    run = find_run(repository, run_id)
    packet = create_review_packet(repository, run_id)
    destination = (
        repository.learning_dir
        / run.record.capsule_id
        / run.record.capsule_version
        / f"{run.record.agent}-attempt-{run.record.attempt:03d}"
    )
    if destination.exists():
        raise IntegrityError(f"Curated artifact already exists: {destination}")
    copy_tree_safe(packet, destination)
    dump_json(
        destination / "CURATION.json",
        {
            "schema_version": 1,
            "run_id": run_id,
            "capsule": run.record.capsule_id,
            "version": run.record.capsule_version,
            "agent": run.record.agent,
        },
    )
    return destination
