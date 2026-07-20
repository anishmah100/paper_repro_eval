from __future__ import annotations

from typer.testing import CliRunner

from paper_repro_eval.cli import app
from paper_repro_eval.repository import Repository


def test_cli_lists_and_validates(repository: Repository, monkeypatch) -> None:
    monkeypatch.chdir(repository.root)
    runner = CliRunner()
    listed = runner.invoke(app, ["capsules", "list"])
    assert listed.exit_code == 0
    assert "robust-line" in listed.stdout
    papers = runner.invoke(app, ["papers", "list"])
    assert papers.exit_code == 0
    assert "Poisson Image" in papers.stdout
    validated = runner.invoke(app, ["suites", "validate", "synthetic-smoke"])
    assert validated.exit_code == 0
    assert "valid" in validated.stdout


def test_cli_help_names_the_command_surface() -> None:
    result = CliRunner().invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "prepare" in result.stdout
    assert "evaluate" in result.stdout
    assert "author" in result.stdout


def test_prepare_prints_a_regenerable_pristine_launch_sheet(
    repository: Repository, monkeypatch
) -> None:
    monkeypatch.chdir(repository.root)
    runner = CliRunner()
    prepared = runner.invoke(app, ["prepare", "synthetic-smoke", "-a", "model-a"])
    assert prepared.exit_code == 0, prepared.stdout
    assert "Launch sheet:" in prepared.stdout
    sheet = next(repository.reports_dir.rglob("launch-*.md"))
    assert "WORK_PLAN.md" in sheet.read_text(encoding="utf-8")

    regenerated = runner.invoke(app, ["launch-sheet", "synthetic-smoke", "-a", "model-a"])
    assert regenerated.exit_code == 0, regenerated.stdout
    assert "launch-sheets" in regenerated.stdout
