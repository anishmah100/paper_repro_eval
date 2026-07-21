from __future__ import annotations

from typer.testing import CliRunner

from paper_repro_eval.cli import app
from paper_repro_eval.repository import Repository
from paper_repro_eval.run_store import list_runs


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
    assert "work" in result.stdout
    assert "evaluate" in result.stdout
    assert "author" in result.stdout


def test_bare_command_opens_the_human_dashboard(monkeypatch) -> None:
    opened: list[bool] = []
    monkeypatch.setattr(
        "paper_repro_eval.cli.work",
        lambda **kwargs: opened.append(kwargs["agent"] is None),
    )
    result = CliRunner().invoke(app, [])
    assert result.exit_code == 0, result.stdout
    assert opened == [True]


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


def test_work_prepares_selects_and_recovers_without_run_ids(
    repository: Repository, monkeypatch
) -> None:
    monkeypatch.chdir(repository.root)
    opened: list[str] = []

    def remember_workspace(run, image: str, shell: str) -> None:
        del image, shell
        opened.append(run.record.run_id)

    monkeypatch.setattr("paper_repro_eval.cli._open_workspace", remember_workspace)
    runner = CliRunner()
    first = runner.invoke(
        app,
        ["work", "grok-test", "--suite", "synthetic-smoke"],
        input="1\nn\n",
    )
    assert first.exit_code == 0, first.stdout
    assert "First use for grok-test" in first.stdout
    assert "Choose a task number" in first.stdout
    assert "WORK_PLAN.md" in first.stdout
    assert len(opened) == 1
    assert len(list_runs(repository)) == 1

    resumed = runner.invoke(
        app,
        ["work", "grok-test", "robust-line", "--suite", "synthetic-smoke"],
        input="n\n",
    )
    assert resumed.exit_code == 0, resumed.stdout
    assert "Choose a task number" not in resumed.stdout
    assert opened == [opened[0], opened[0]]
    assert len(list_runs(repository)) == 1
