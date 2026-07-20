from __future__ import annotations

from paper_repro_eval.catalog import resolve_suite, validate_registry
from paper_repro_eval.competition import build_leaderboards, render_leaderboards
from paper_repro_eval.materialize import prepare_suite
from paper_repro_eval.repository import Repository


def test_visual_arcade_registers_ten_competitive_ready_capsules(
    repository: Repository,
) -> None:
    suite, resolved = resolve_suite(repository, "visual-research-arcade-v0")
    assert len(suite.capsules) == 10
    assert len(resolved) == 10
    assert all(capsule.manifest.status == "benchmark-ready" for capsule in resolved)
    assert all(capsule.manifest.competition is not None for capsule in resolved)
    assert all(len((capsule.public_dir / "TASK.md").read_text()) > 1000 for capsule in resolved)
    assert len(validate_registry(repository)) == 11


def test_leaderboard_uses_latest_attempt_qualification_and_tie_tolerance(
    repository: Repository,
) -> None:
    rows: list[dict[str, object]] = [
        {
            "run_id": "old-a",
            "paper": "poisson-image-editing",
            "capsule": "competitive-editing",
            "version": "1.0.0",
            "agent": "a",
            "attempt": 1,
            "status": "success",
            "objective_score": 0.99,
            "qualified": True,
        },
        {
            "run_id": "new-a",
            "paper": "poisson-image-editing",
            "capsule": "competitive-editing",
            "version": "1.0.0",
            "agent": "a",
            "attempt": 2,
            "status": "success",
            "objective_score": 0.80,
            "qualified": True,
        },
        {
            "run_id": "b",
            "paper": "poisson-image-editing",
            "capsule": "competitive-editing",
            "version": "1.0.0",
            "agent": "b",
            "attempt": 1,
            "status": "success",
            "objective_score": 0.8005,
            "qualified": True,
        },
        {
            "run_id": "unqualified",
            "paper": "poisson-image-editing",
            "capsule": "competitive-editing",
            "version": "1.0.0",
            "agent": "c",
            "attempt": 1,
            "status": "success",
            "objective_score": 1.0,
            "qualified": False,
        },
    ]
    boards = build_leaderboards(repository, rows)
    assert len(boards) == 1
    assert [(row["agent"], row["rank"]) for row in boards[0]["standings"]] == [
        ("b", 1),
        ("a", 1),
    ]
    assert [row["agent"] for row in boards[0]["unqualified"]] == ["c"]
    assert "Hidden editing quality" in render_leaderboards("suite", boards)


def test_visual_arcade_materializes_identical_isolated_public_workspaces(
    repository: Repository,
) -> None:
    records = prepare_suite(repository, "visual-research-arcade-v0", ["model-a", "model-b"])
    assert len(records) == 20
    assert len({record.capsule_id for record in records}) == 10
    for record in records:
        workspace = repository.root / record.workspace
        assert (workspace / "TASK.md").is_file()
        assert (workspace / "paper" / "SOURCE.md").is_file()
        assert (workspace / "starter" / "README.md").is_file()
        assert (workspace / "submission").is_dir()
        assert not (workspace / "private").exists()
