"""Static human-review packets, suite reports, and educational curation."""

from __future__ import annotations

import csv
import html
import shutil
from pathlib import Path

import bleach
from markdown_it import MarkdownIt

from .catalog import resolve_capsule
from .competition import build_leaderboards, render_leaderboards
from .errors import ConfigurationError, IntegrityError
from .lifecycle import latest_reproduction, latest_seal, update_state
from .models import CheckStatus, RunState
from .repository import Repository
from .run_store import StoredRun, find_run, list_runs
from .util import atomic_directory, copy_tree_safe, dump_json, slugify, utc_now
from .verification import latest_verification


def _safe_markdown(value: str) -> str:
    rendered = MarkdownIt("commonmark").render(value)
    return str(
        bleach.clean(
            rendered,
            tags=set(bleach.sanitizer.ALLOWED_TAGS)
            | {"p", "h1", "h2", "h3", "pre", "code", "table", "thead", "tbody", "tr", "th", "td"},
            attributes={"a": ["href", "title"]},
        )
    )


def create_review_packet(repository: Repository, run_id: str) -> Path:
    run = find_run(repository, run_id)
    seal_dir, seal = latest_seal(run)
    reproduction_dir, reproduction = latest_reproduction(run)
    verification_dir, verification = latest_verification(repository, run_id)
    capsule = resolve_capsule(
        repository, run.record.paper_id, run.record.capsule_id, run.record.capsule_version
    )
    destination = run.review_dir / f"verification-{reproduction.attempt:03d}"
    if destination.exists():
        return destination
    with atomic_directory(destination) as stage:
        candidate_report = seal_dir / "submission" / "REPORT.md"
        if candidate_report.is_file():
            shutil.copy2(candidate_report, stage / "CANDIDATE_REPORT.md")
        else:
            (stage / "CANDIDATE_REPORT.md").write_text(
                "# Missing candidate report\n", encoding="utf-8"
            )
        shutil.copy2(capsule.private_dir / "REVIEW_GUIDE.md", stage / "CAPSULE_REVIEW_GUIDE.md")
        shutil.copy2(repository.root / "REVIEWING.md", stage / "REVIEWING.md")
        if (reproduction_dir / "artifacts").exists():
            copy_tree_safe(reproduction_dir / "artifacts", stage / "artifacts")
        if (verification_dir / "evidence").exists():
            copy_tree_safe(verification_dir / "evidence", stage / "evidence")
        lines = [
            f"# Review: {run.record.paper_id}/{run.record.capsule_id} — {run.record.agent}",
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
                "- Does the artifact demonstrate the claim rather than a superficial test?",
                "- Are deviations, limitations, and negative results candidly reported?",
                "- Do the code and evidence agree with the narrative?",
                "- Is the result educational and independently inspectable?",
                "",
                "Record conclusions in NOTES.md. They are deliberately not auto-scored.",
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
        status_text: str
        qualified = False
        try:
            _, verification = latest_verification(repository, run.record.run_id)
            status_text = verification.status
            score = verification.objective_score
            capsule = resolve_capsule(
                repository,
                run.record.paper_id,
                run.record.capsule_id,
                run.record.capsule_version,
            )
            required = (
                set(capsule.manifest.competition.qualification_checks)
                if capsule.manifest.competition is not None
                else set()
            )
            result_by_id = {check.id: check for check in verification.checks}
            qualified = all(
                check_id in result_by_id and result_by_id[check_id].status is CheckStatus.PASSED
                for check_id in required
            )
        except ConfigurationError:
            status_text = str(run.record.state)
            score = None
        rows.append(
            {
                "run_id": run.record.run_id,
                "paper": run.record.paper_id,
                "capsule": run.record.capsule_id,
                "version": run.record.capsule_version,
                "agent": run.record.agent,
                "attempt": run.record.attempt,
                "status": status_text,
                "objective_score": score,
                "qualified": qualified,
            }
        )
    destination = repository.reports_dir / suite_id
    destination.mkdir(parents=True, exist_ok=True)
    leaderboards = build_leaderboards(repository, rows)
    dump_json(
        destination / "report.json",
        {"schema_version": 1, "suite": suite_id, "runs": rows, "leaderboards": leaderboards},
    )
    with (destination / "report.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]) if rows else ["run_id"])
        writer.writeheader()
        writer.writerows(rows)
    md = [
        f"# Suite report: {suite_id}",
        "",
        "| Paper / capsule | Agent | Status | Score |",
        "|---|---|---:|---:|",
    ]
    for row in rows:
        md.append(
            f"| {row['paper']} / {row['capsule']} | {row['agent']} | "
            f"{row['status']} | {row['objective_score']} |"
        )
    markdown = "\n".join(md) + "\n"
    (destination / "report.md").write_text(markdown, encoding="utf-8")
    (destination / "index.html").write_text(
        "<!doctype html><meta charset='utf-8'><title>Suite report</title>"
        + _safe_markdown(markdown),
        encoding="utf-8",
    )
    (destination / "LEADERBOARD.md").write_text(
        render_leaderboards(suite_id, leaderboards), encoding="utf-8"
    )
    return destination


def visual_gallery(
    repository: Repository, suite_id: str, *, agents: set[str] | None = None
) -> Path:
    """Build a self-contained side-by-side gallery from latest verified attempts."""
    latest: dict[tuple[str, str, str], StoredRun] = {}
    for run in list_runs(repository):
        if run.record.suite_id != suite_id or (
            agents is not None and run.record.agent not in agents
        ):
            continue
        key = (run.record.paper_id, run.record.capsule_id, run.record.agent)
        previous = latest.get(key)
        if previous is None or run.record.attempt > previous.record.attempt:
            latest[key] = run
    verified = []
    for run in latest.values():
        try:
            _, verification = latest_verification(repository, run.record.run_id)
        except ConfigurationError:
            continue
        verified.append((run, verification))
    if not verified:
        raise ConfigurationError(f"No verified runs for suite {suite_id}")
    stamp = utc_now().replace(":", "").replace("+", "-")
    destination = repository.reports_dir / slugify(suite_id) / "galleries" / stamp
    entries = destination / "entries"
    entries.mkdir(parents=True)
    cards = []
    for run, verification in sorted(
        verified,
        key=lambda item: (
            item[0].record.paper_id,
            item[0].record.capsule_id,
            item[0].record.agent,
        ),
    ):
        packet = create_review_packet(repository, run.record.run_id)
        name = slugify(f"{run.record.paper_id}--{run.record.capsule_id}--{run.record.agent}")
        copied = entries / name
        copy_tree_safe(packet, copied)
        images = [
            path.relative_to(destination).as_posix()
            for path in sorted(copied.rglob("*"))
            if path.suffix.lower() in {".png", ".jpg", ".jpeg", ".gif", ".svg"}
        ]
        thumbnails = (
            "".join(
                f"<a href='{html.escape(path)}'><img loading='lazy' src='{html.escape(path)}'></a>"
                for path in images[:8]
            )
            or "<p class='missing'>No image artifact; inspect the review packet.</p>"
        )
        cards.append(
            "<article>"
            f"<h2>{html.escape(run.record.paper_id)} / "
            f"{html.escape(run.record.capsule_id)}</h2>"
            f"<h3>{html.escape(run.record.agent)}</h3>"
            f"<p>Score: <strong>{verification.objective_score}</strong> · "
            f"<a href='entries/{name}/index.html'>review packet</a> · "
            f"<a href='entries/{name}/NOTES.md'>notes</a></p>"
            f"<div class='images'>{thumbnails}</div>"
            "</article>"
        )
    page = (
        "<!doctype html><meta charset='utf-8'><title>Visual comparison gallery</title>"
        "<style>body{background:#0b1020;color:#e5e7eb;font:15px system-ui;margin:24px}"
        "main{display:grid;grid-template-columns:repeat(auto-fit,minmax(420px,1fr));gap:18px}"
        "article{background:#151c2f;border:1px solid #334155;border-radius:10px;padding:16px}"
        "h2{font-size:17px}h3{color:#93c5fd}a{color:#67e8f9}"
        ".images{display:grid;grid-template-columns:repeat(2,1fr);gap:8px}"
        "img{width:100%;height:220px;object-fit:contain;background:#050816}"
        ".missing{color:#fca5a5}</style>"
        f"<h1>Visual comparison: {html.escape(suite_id)}</h1>"
        "<p>Latest verified attempt per agent and capsule. Click an image for full resolution "
        "or open the review packet for metrics, reports, hidden evidence, and notes.</p>"
        f"<main>{''.join(cards)}</main>"
    )
    (destination / "index.html").write_text(page, encoding="utf-8")
    return destination


def curate(repository: Repository, run_id: str) -> Path:
    run = find_run(repository, run_id)
    packet = create_review_packet(repository, run_id)
    destination = (
        repository.learning_dir
        / run.record.paper_id
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
            "paper": run.record.paper_id,
            "run_id": run_id,
            "capsule": run.record.capsule_id,
            "version": run.record.capsule_version,
            "agent": run.record.agent,
        },
    )
    return destination
