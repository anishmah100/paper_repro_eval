"""The paper_repro_eval command-line interface."""

from __future__ import annotations

import shutil
import subprocess
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table

from .authoring import (
    TEMPLATE_TYPES,
    approve_scope,
    author_init,
    paper_init,
    publish,
    scaffold,
    validate_authoring,
)
from .catalog import (
    load_registry,
    load_suite,
    resolve_capsule,
    resolve_paper,
    resolve_suite,
    validate_registry,
)
from .errors import PaperReproEvalError
from .lifecycle import reproduce_run, seal_run
from .materialize import prepare_suite
from .repository import Repository, discover_repository
from .review import create_review_packet, suite_report, visual_gallery
from .review import curate as curate_run
from .run_store import find_run, list_runs
from .sandbox import container_command
from .tournament import run_lightcycle_tournament
from .util import dump_yaml, load_yaml, slugify
from .verification import verify_run

app = typer.Typer(no_args_is_help=True, pretty_exceptions_enable=False)
papers_app = typer.Typer(no_args_is_help=True)
capsules_app = typer.Typer(no_args_is_help=True)
suites_app = typer.Typer(no_args_is_help=True)
runs_app = typer.Typer(no_args_is_help=True)
author_app = typer.Typer(no_args_is_help=True)
app.add_typer(papers_app, name="papers")
app.add_typer(capsules_app, name="capsules")
app.add_typer(suites_app, name="suites")
app.add_typer(runs_app, name="runs")
app.add_typer(author_app, name="author")
console = Console()


def _repo() -> Repository:
    return discover_repository()


@papers_app.command("list")
def papers_list() -> None:
    table = Table("Paper", "Title", "Capsules", "Path")
    for entry in load_registry(_repo()).papers:
        paper = resolve_paper(_repo(), entry.id)
        table.add_row(
            paper.manifest.id,
            paper.manifest.metadata.title,
            str(len(paper.manifest.capsules)),
            entry.path,
        )
    console.print(table)


@papers_app.command("show")
def papers_show(paper_id: str) -> None:
    paper = resolve_paper(_repo(), paper_id)
    console.print_json(data={**paper.manifest.model_dump(mode="json"), "digest": paper.digest})


@papers_app.command("validate")
def papers_validate(paper_id: str | None = None) -> None:
    paper_ids = [paper_id] if paper_id else [entry.id for entry in load_registry(_repo()).papers]
    for selected in paper_ids:
        paper = resolve_paper(_repo(), selected)
        for entry in paper.manifest.capsules:
            resolve_capsule(_repo(), selected, entry.id, entry.version)
        console.print(f"[green]valid[/green] {selected} ({len(paper.manifest.capsules)} capsules)")


@capsules_app.command("list")
def capsules_list(paper_id: str | None = None) -> None:
    table = Table("Paper", "Capsule", "Version", "Status", "Path")
    papers = (
        [resolve_paper(_repo(), paper_id)]
        if paper_id
        else [resolve_paper(_repo(), entry.id) for entry in load_registry(_repo()).papers]
    )
    for paper in papers:
        for entry in paper.manifest.capsules:
            table.add_row(
                paper.manifest.id,
                entry.id,
                entry.version,
                entry.status,
                entry.path,
            )
    console.print(table)


@capsules_app.command("show")
def capsules_show(paper_id: str, capsule_id: str, version: str | None = None) -> None:
    capsule = resolve_capsule(_repo(), paper_id, capsule_id, version)
    console.print_json(data={**capsule.manifest.model_dump(mode="json"), "digest": capsule.digest})


@capsules_app.command("validate")
def capsules_validate(
    paper_id: str | None = None,
    capsule_id: str | None = None,
    version: str | None = None,
) -> None:
    if (paper_id is None) != (capsule_id is None):
        raise typer.BadParameter("paper_id and capsule_id must be supplied together")
    resolved = (
        [resolve_capsule(_repo(), paper_id, capsule_id, version)]
        if paper_id and capsule_id
        else validate_registry(_repo())
    )
    for capsule in resolved:
        console.print(
            f"[green]valid[/green] {capsule.paper.manifest.id}/"
            f"{capsule.manifest.id}@{capsule.manifest.version} {capsule.digest}"
        )


@suites_app.command("list")
def suites_list() -> None:
    table = Table("ID", "Title", "Capsules")
    for path in sorted(_repo().suites_dir.glob("*.y*ml")):
        suite = load_suite(_repo(), path.stem)
        table.add_row(suite.id, suite.title, str(len(suite.capsules)))
    console.print(table)


@suites_app.command("show")
def suites_show(suite_id: str) -> None:
    console.print_json(data=load_suite(_repo(), suite_id).model_dump(mode="json"))


@suites_app.command("validate")
def suites_validate(suite_id: str) -> None:
    suite, capsules = resolve_suite(_repo(), suite_id)
    console.print(f"[green]valid[/green] {suite.id} ({len(capsules)} capsules)")


@app.command()
def prepare(
    suite_id: Annotated[str, typer.Argument(help="Suite ID")],
    agent: Annotated[list[str], typer.Option("--agent", "-a", help="Repeat for each model/agent")],
    isolation: Annotated[str, typer.Option(help="directory or container")] = "directory",
) -> None:
    if isolation not in {"directory", "container"}:
        raise typer.BadParameter("isolation must be directory or container")
    records = prepare_suite(_repo(), suite_id, agent, isolation=isolation)
    table = Table("Run ID", "Paper", "Capsule", "Agent", "Workspace")
    for record in records:
        table.add_row(
            record.run_id,
            record.paper_id,
            record.capsule_id,
            record.agent,
            record.workspace,
        )
    console.print(table)


@app.command("path")
def run_path(run_id: str) -> None:
    console.print(find_run(_repo(), run_id).workspace.resolve())


@app.command()
def enter(
    run_id: str,
    image: Annotated[
        str, typer.Option(help="Image for container-isolated runs")
    ] = "python:3.12-slim",
    shell: Annotated[str, typer.Option(help="Interactive shell executable")] = "zsh",
) -> None:
    run = find_run(_repo(), run_id)
    console.print(
        "[yellow]Isolation rule:[/yellow] do not inspect any other candidate workspace or output."
    )
    if run.record.isolation == "container":
        subprocess.run(container_command(run.workspace, image, shell), check=False)
    else:
        subprocess.run([shell], cwd=run.workspace, check=False)


@app.command()
def status(run_id: str | None = None) -> None:
    runs = [find_run(_repo(), run_id)] if run_id else list_runs(_repo())
    table = Table("Run ID", "Suite", "Paper", "Capsule", "Agent", "Attempt", "State")
    for run in runs:
        record = run.record
        table.add_row(
            record.run_id,
            record.suite_id,
            record.paper_id,
            record.capsule_id,
            record.agent,
            str(record.attempt),
            record.state,
        )
    console.print(table)


@runs_app.command("list")
def runs_list() -> None:
    status()


@app.command()
def seal(run_id: str) -> None:
    console.print_json(data=seal_run(_repo(), run_id).model_dump(mode="json"))


@app.command()
def reproduce(
    run_id: str,
    timeout: Annotated[float | None, typer.Option(help="Optional wall timeout in seconds")] = None,
) -> None:
    record = reproduce_run(_repo(), run_id, timeout_seconds=timeout)
    console.print_json(data=record.model_dump(mode="json"))


@app.command()
def verify(run_id: str) -> None:
    record = verify_run(_repo(), run_id)
    console.print_json(data=record.model_dump(mode="json"))
    if record.status == "evaluator-error":
        raise typer.Exit(2)


@app.command()
def evaluate(
    run_id: str,
    timeout: Annotated[float | None, typer.Option(help="Optional reproduction timeout")] = None,
) -> None:
    seal_record = seal_run(_repo(), run_id)
    if seal_record.missing_required:
        console.print(f"[yellow]Missing required files:[/yellow] {seal_record.missing_required}")
    reproduction = reproduce_run(_repo(), run_id, timeout_seconds=timeout)
    verification = verify_run(_repo(), run_id)
    packet = create_review_packet(_repo(), run_id)
    console.print(
        f"reproduction={reproduction.status} score={verification.objective_score} review={packet}"
    )
    if verification.status == "evaluator-error":
        raise typer.Exit(2)


@app.command()
def review(run_id: str) -> None:
    console.print(create_review_packet(_repo(), run_id))


@app.command()
def report(suite_id: str) -> None:
    console.print(suite_report(_repo(), suite_id))


@app.command()
def gallery(
    suite_id: Annotated[str, typer.Argument(help="Suite ID")],
    agent: Annotated[
        list[str] | None, typer.Option("--agent", "-a", help="Limit to named agents")
    ] = None,
) -> None:
    console.print(visual_gallery(_repo(), suite_id, agents=set(agent or []) or None))


@app.command()
def tournament(
    suite_id: Annotated[str, typer.Argument(help="Suite ID")],
    seeds: Annotated[int, typer.Option(help="Deterministic maps per pairing")] = 4,
    agent: Annotated[
        list[str] | None, typer.Option("--agent", "-a", help="Limit to named qualifying agents")
    ] = None,
    turn_timeout: Annotated[float, typer.Option(help="Per-turn bot deadline in seconds")] = 0.25,
) -> None:
    destination = run_lightcycle_tournament(
        _repo(), suite_id, seeds=seeds, turn_timeout=turn_timeout, agents=set(agent or []) or None
    )
    console.print(destination)


@app.command()
def curate(run_id: str) -> None:
    console.print(curate_run(_repo(), run_id))


@author_app.command("paper-init")
def author_paper_init(paper_id: str) -> None:
    console.print(paper_init(_repo(), paper_id))


@author_app.command("init")
def author_init_command(paper_id: str, capsule_id: str) -> None:
    console.print(author_init(_repo(), paper_id, capsule_id))


@author_app.command("proposals")
def author_proposals() -> None:
    for path in sorted(_repo().authoring_dir.glob("*/capsules/*/proposal.yaml")):
        console.print(path)


@author_app.command("approve-scope")
def author_approve_scope(paper_id: str, capsule_id: str) -> None:
    console.print(approve_scope(_repo(), paper_id, capsule_id))


@author_app.command("scaffold")
def author_scaffold(
    paper_id: str,
    capsule_id: str,
    version: str,
    template: Annotated[
        list[str],
        typer.Option("--template", "-t", help="Composable authoring template"),
    ],
) -> None:
    console.print(scaffold(_repo(), paper_id, capsule_id, version, template))


@author_app.command("templates")
def author_templates() -> None:
    console.print("\n".join(TEMPLATE_TYPES))


@author_app.command("validate")
def author_validate(paper_id: str, capsule_id: str, version: str) -> None:
    console.print(validate_authoring(_repo(), paper_id, capsule_id, version))


@author_app.command("review")
def author_review(paper_id: str, capsule_id: str, version: str) -> None:
    root = (
        _repo().authoring_dir / slugify(paper_id) / "capsules" / slugify(capsule_id) / f"v{version}"
    )
    console.print(root / "AUTHORING.md")
    console.print(root / "private" / "calibration" / "calibration.yaml")


@author_app.command("publish")
def author_publish(paper_id: str, capsule_id: str, version: str) -> None:
    console.print(publish(_repo(), paper_id, capsule_id, version))


@author_app.command("revise")
def author_revise(
    paper_id: str,
    capsule_id: str,
    from_version: str,
    new_version: str,
) -> None:
    capsule = resolve_capsule(_repo(), paper_id, capsule_id, from_version)
    paper_author_root = _repo().authoring_dir / slugify(paper_id)
    if not paper_author_root.exists():
        paper_author_root.mkdir(parents=True)
        shutil.copy2(capsule.paper.paper_dir / "paper.yaml", paper_author_root / "paper.yaml")
        for name in ("paper", "resources"):
            shutil.copytree(capsule.paper.paper_dir / name, paper_author_root / name)
    destination = paper_author_root / "capsules" / slugify(capsule_id) / f"v{new_version}"
    if destination.exists():
        raise typer.BadParameter(f"Destination already exists: {destination}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(capsule.pack_dir, destination)
    manifest_path = destination / "capsule.yaml"
    manifest = load_yaml(manifest_path)
    manifest["version"] = new_version
    manifest["status"] = "draft"
    dump_yaml(manifest_path, manifest)
    console.print(destination)


def main() -> None:
    try:
        app()
    except PaperReproEvalError as exc:
        console.print(f"[red]error:[/red] {exc}")
        raise typer.Exit(1) from exc


if __name__ == "__main__":
    main()
