from __future__ import annotations

from typer.testing import CliRunner

from paper_repro_eval.cli import app
from paper_repro_eval.repository import Repository


def test_cli_lists_and_validates(repository: Repository, monkeypatch) -> None:
    monkeypatch.chdir(repository.root)
    runner = CliRunner()
    listed = runner.invoke(app, ["capsules", "list"])
    assert listed.exit_code == 0
    assert "synthetic-robust-e" in listed.stdout
    assert "robust-line" in listed.stdout
    papers = runner.invoke(app, ["papers", "list"])
    assert papers.exit_code == 0
    assert "synthetic-robust-es" in papers.stdout
    validated = runner.invoke(app, ["suites", "validate", "synthetic-smoke"])
    assert validated.exit_code == 0
    assert "valid" in validated.stdout


def test_cli_help_names_the_command_surface() -> None:
    result = CliRunner().invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "prepare" in result.stdout
    assert "evaluate" in result.stdout
    assert "author" in result.stdout
