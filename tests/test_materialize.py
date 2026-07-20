from __future__ import annotations

from paper_repro_eval.materialize import prepare_suite
from paper_repro_eval.repository import Repository
from paper_repro_eval.run_store import find_run
from paper_repro_eval.sandbox import container_command


def test_prepare_makes_identical_physical_independent_repositories(
    repository: Repository,
) -> None:
    records = prepare_suite(repository, "synthetic-smoke", ["model-a", "model-b"])
    assert len(records) == 2
    assert records[0].initial_digest == records[1].initial_digest
    first = find_run(repository, records[0].run_id).workspace
    assert all(record.paper_id == "synthetic-robust-estimation" for record in records)
    assert all(record.capsule_id == "robust-line" for record in records)
    second = find_run(repository, records[1].run_id).workspace
    assert first != second
    assert (first / ".git").is_dir()
    assert (second / ".git").is_dir()
    assert not first.is_symlink()
    assert not second.is_symlink()
    assert not (first / "private").exists()
    assert not (first / "checks.yaml").exists()
    assert (first / "submission").is_dir()
    relative = first.relative_to(repository.root)
    assert relative.parts[:8] == (
        "runs",
        "synthetic-smoke",
        "papers",
        "synthetic-robust-estimation",
        "capsules",
        "robust-line",
        "agents",
        "model-a",
    )
    assert (first / "paper" / "SYNTHETIC.md").is_file()
    assert (first / "paper_resources" / "README.md").is_file()


def test_container_command_mounts_only_selected_workspace(
    repository: Repository, monkeypatch
) -> None:
    monkeypatch.setattr("paper_repro_eval.sandbox.shutil.which", lambda _: "/usr/bin/docker")
    workspace = repository.root / "one-workspace"
    command = container_command(workspace, "python:3.12-slim", "bash")
    joined = " ".join(command)
    assert str(workspace) in joined
    assert str(repository.runs_dir) not in joined
