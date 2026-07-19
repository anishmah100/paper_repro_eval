"""The paper_repro_eval command-line interface."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table

from .authoring import (
    TEMPLATE_TYPES,
    approve_scope,
    author_init,
    publish,
    scaffold,
    validate_authoring,
)
from .catalog import load_registry, load_suite, resolve_capsule, validate_registry
from .errors import PaperReproEvalError
from .lifecycle import reproduce_run, seal_run
from .materialize import prepare_suite
from .repository import discover_repository
from .review import create_review_packet, curate as curate_run, suite_report
from .run_store import find_run, list_runs
from .verification import verify_run

app = typer.Typer(no_args_is_help=True, pretty_exceptions_enable=False)
capsules_app = typer.Typer(no_args_is_help=True)
suites_app = typer.Typer(no_args_is_help=True)
runs_app = typer.Typer(no_args_is_help=True)
author_app = typer.Typer(no_args_is_help=True)
app.add_typer(capsules_app, name="capsules")
app.add_typer(suites_app, name="suites")
app.add_typer(runs_app, name="runs")
app.add_typer(author_app, name="author")
console = Console()


def _repo():
    return discover_repository()


@capsules_app.command("list")
def capsules_list() -> None:
    registry = load_registry(_repo())
    table = Table("ID", "Version", "Status", "Path")
    for entry in registry.capsules:
        table.add_row(entry.id, entry.version, entry.status, entry.path)
    console.print(table)


@capsules_app.command("show")
def capsules_show(capsule_id: str, version: str | None = None) -> None:
    capsule = resolve_capsule(_repo(), capsule_id, version)
    console.print_json(data={**capsule.manifest.model_dump(mode="json"), "digest": capsule.digest})


@capsules_app.command("validate")
def capsules_validate(capsule_id: str | None = None, version: str | None = None) -> None:
    resolved = (
        [resolve_capsule(_repo(), capsule_id, version)]
        if capsule_id
        else validate_registry(_repo())
    )
    for capsule in resolved:
        console.print(f"[green]valid[/green] {capsule.manifest.id}@{capsule.manifest.version} {capsule.digest}")


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
    suite = load_suite(_repo(), suite_id)
    for reference in suite.capsules:
        resolve_capsule(_repo(), reference.id, reference.version)
    console.print(f"[green]valid[/green] {suite_id} ({len(suite.capsules)} capsules)")


@app.command()
def prepare(
    suite_id: Annotated[str, typer.Argument(help="Suite ID")],
    agent: Annotated[list[str], typer.Option("--agent", "-a", help="Repeat for each model/agent")],
    isolation: Annotated[str, typer.Option(help="directory or container")] = "directory",
) -> None:
    if isolation not in {"directory", "container"}:
        raise typer.BadParameter("isolation must be directory or container")
    records = prepare_suite(_repo(), suite_id, agent, isolation=isolation)
    table = Table("Run ID", "Capsule", "Agent", "Workspace")
    for record in records:
        table.add_row(record.run_id, record.capsule_id, record.agent, record.workspace)
    console.print(table)


@app.command("path")
def run_path(run_id: str) -> None:
    console.print(find_run(_repo(), run_id).workspace.resolve())


@app.command()
def enter(
    run_id: str,
    shell: Annotated[str, typer.Option(help="Interactive shell executable")] = "zsh",
) -> None:
    workspace = find_run(_repo(), run_id).workspace
    console.print(
        "[yellow]Isolation rule:[/yellow] do not inspect any other candidate workspace or output."
    )
    subprocess.run([shell], cwd=workspace, check=False)


@app.command()
def status(run_id: str | None = None) -> None:
    runs = [find_run(_repo(), run_id)] if run_id else list_runs(_repo())
    table = Table("Run ID", "Suite", "Capsule", "Agent", "Attempt", "State")
    for run in runs:
        record = run.record
        table.add_row(
            record.run_id,
            record.suite_id,
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
    record = seal_run(_repo(), run_id)
    console.print_json(data=record.model_dump(mode="json"))


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
def curate(run_id: str) -> None:
    console.print(curate_run(_repo(), run_id))


@author_app.command("init")
def author_init_command(capsule_id: str) -> None:
    console.print(author_init(_repo(), capsule_id))


@author_app.command("proposals")
def author_proposals() -> None:
    for path in sorted(_repo().authoring_dir.glob("*/proposal.yaml")):
        console.print(path)


@author_app.command("approve-scope")
def author_approve_scope(capsule_id: str) -> None:
    console.print(approve_scope(_repo(), capsule_id))


@author_app.command("scaffold")
def author_scaffold(
    capsule_id: str,
    version: str,
    template: Annotated[
        list[str],
        typer.Option("--template", "-t", help="Composable authoring template"),
    ],
) -> None:
    console.print(scaffold(_repo(), capsule_id, version, template))


@author_app.command("templates")
def author_templates() -> None:
    console.print("\n".join(TEMPLATE_TYPES))


@author_app.command("validate")
def author_validate(capsule_id: str, version: str) -> None:
    console.print(validate_authoring(_repo(), capsule_id, version))


@author_app.command("review")
def author_review(capsule_id: str, version: str) -> None:
    root = _repo().authoring_dir / capsule_id / f"v{version}"
    console.print(root / "AUTHORING.md")
    console.print(root / "private" / "calibration" / "calibration.yaml")


@author_app.command("publish")
def author_publish(capsule_id: str, version: str) -> None:
    console.print(publish(_repo(), capsule_id, version))


@author_app.command("revise")
def author_revise(capsule_id: str, from_version: str, new_version: str) -> None:
    source = resolve_capsule(_repo(), capsule_id, from_version).pack_dir
    destination = _repo().authoring_dir / capsule_id / f"v{new_version}"
    if destination.exists():
        raise typer.BadParameter(f"Destination already exists: {destination}")
    import shutil

    shutil.copytree(source, destination)
    manifest_path = destination / "capsule.yaml"
    from .util import dump_yaml, load_yaml

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
