from __future__ import annotations

import sys
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "authoring"))
sys.path.insert(0, str(ROOT / "templates" / "arena_kit"))

import arena_kit as kit  # noqa: E402
import arena_verifier  # noqa: E402
import control_verifier  # noqa: E402

from paper_repro_eval.catalog import resolve_capsule  # noqa: E402
from paper_repro_eval.repository import Repository  # noqa: E402

NATIVE = {
    ("poisson-image-editing", "competitive-editing"): "run_case.sh",
    ("dm-control-suite", "multipole-control"): "agent.sh",
    ("multiple-importance-sampling", "progressive-path-tracer"): "render.sh",
    ("mls-mpm", "multimaterial-simulator"): "simulate.sh",
    ("differentiable-world-model-mpc", "visual-offline-control"): "agent.sh",
    ("topology-optimization", "robust-structure-design"): "optimize.sh",
    ("lightcycle-agents", "adversarial-tournament"): "bot.sh",
    ("stable-fluids", "inverse-smoke-control"): "control.sh",
    ("evolutionary-soft-robots", "morphology-control-codesign"): "design.sh",
    ("inverse-rendering", "procedural-scene-recovery"): "recover.sh",
}


@pytest.mark.parametrize(
    ("paper", "capsule", "script"), [(*key, value) for key, value in NATIVE.items()]
)
def test_every_arena_exposes_its_task_native_entrypoint(
    repository: Repository, paper: str, capsule: str, script: str
) -> None:
    resolved = resolve_capsule(repository, paper, capsule, "1.0.0")
    assert (resolved.public_dir / "starter" / script).is_file()
    task = (resolved.public_dir / "TASK.md").read_text(encoding="utf-8")
    contract = (resolved.public_dir / "EXECUTABLE_CONTRACT.md").read_text(encoding="utf-8")
    assert script in task
    assert script in contract
    assert "score" in contract.lower()


@pytest.mark.parametrize(
    "task",
    [value for value in kit.TASKS if value not in {"lightcycle", "multipole", "world_mpc"}],
)
def test_malformed_batch_output_fails_closed(task: str) -> None:
    case = kit.case(task, 414, 2)
    assert kit.score(task, case, {})["quality"] == 0


def test_native_dispatch_uses_output_directory_where_contract_requires(tmp_path: Path) -> None:
    source = tmp_path / "case.json"
    output = tmp_path / "candidate.json"
    command, produced = arena_verifier.native_command("mpm", source, output)
    assert command[:2] == ["bash", "simulate.sh"]
    assert produced == tmp_path / "candidate-files" / "result.json"
    assert produced.parent.is_dir()


def test_persistent_controller_timeout_fails_closed(tmp_path: Path) -> None:
    submission = tmp_path / "submission"
    submission.mkdir()
    (submission / "agent.py").write_text(
        "import json,sys,time\n"
        "for line in sys.stdin:\n"
        " m=json.loads(line)\n"
        " if m.get('type')!='reset':\n"
        "  time.sleep(1);print(json.dumps({'action':[0,0]}),flush=True)\n",
        encoding="utf-8",
    )
    (submission / "agent.sh").write_text("#!/usr/bin/env bash\nexec python agent.py\n")
    started = time.monotonic()
    quality, metrics = control_verifier.quality(
        "world_mpc", submission, kit.case("world_mpc", 19, 1), turn_timeout=0.02
    )
    assert time.monotonic() - started < 2
    assert quality == 0
    assert metrics["timeouts"] == 1
    assert metrics["protocol_errors"] == 1


def test_continuous_check_status_matches_framework_schema() -> None:
    partial = arena_verifier.result("quality", 0.4, "partial", {})
    failed = arena_verifier.result("quality", 0, "failed", {})
    passed = arena_verifier.result("quality", 1, "passed", {})
    assert [partial["status"], failed["status"], passed["status"]] == [
        "partial",
        "failed",
        "passed",
    ]


@pytest.mark.parametrize(
    ("task", "metrics"),
    [
        ("poisson", {"quality": 0.0, "mse": float("inf")}),
        ("mpm", {"quality": 0.0, "invalid": 1}),
        ("world_mpc", {"quality": 0.0, "protocol_errors": 1, "timeouts": 0}),
        ("lightcycle", {"quality": 0.0, "illegal": 1, "timeouts": 0}),
        ("lightcycle", {"quality": 0.0, "illegal": 0, "timeouts": 1}),
    ],
)
def test_invalid_measurements_fail_qualification(task: str, metrics: dict[str, float]) -> None:
    assert not arena_verifier.measurements_valid(task, metrics)


def test_valid_but_low_quality_measurements_can_still_qualify() -> None:
    assert arena_verifier.measurements_valid("topology", {"quality": 0.0, "connectivity": 0.0})


def test_inverse_rendering_scores_genuinely_heldout_views() -> None:
    case = kit.case("inverse_render", 73, 2)
    assert set(case["views"]).isdisjoint(case["heldout_views"])
    public_case = dict(case)
    public_case.pop("truth")
    assert "truth" not in public_case
    metrics = kit.score("inverse_render", case, {"objects": case["truth"]})
    assert metrics["observed_mse"] == 0
    assert metrics["heldout_mse"] == 0


def test_softrobot_objective_changes_with_hidden_terrain() -> None:
    first = kit.case("softrobot", 11, 1)
    second = kit.case("softrobot", 29, 3)
    candidate = kit.baseline("softrobot", first)
    first_metrics = kit.score("softrobot", first, candidate)
    second_metrics = kit.score("softrobot", second, candidate)
    assert first_metrics["target_frequency"] != second_metrics["target_frequency"]
    assert first_metrics["quality"] != second_metrics["quality"]
