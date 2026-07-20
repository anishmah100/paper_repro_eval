from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np
import pytest

from paper_repro_eval.materialize import prepare_suite
from paper_repro_eval.repository import Repository

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "arena_kit", ROOT / "templates/arena_kit/arena_kit.py"
)
assert SPEC and SPEC.loader
KIT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(KIT)

BATCH = [task for task in KIT.TASKS if task != "lightcycle"]


@pytest.mark.parametrize("task", BATCH)
def test_arena_baseline_is_finite_and_renderable(task: str, tmp_path: Path) -> None:
    case = KIT.case(task, 1234, 2)
    output = KIT.baseline(task, case)
    metrics = KIT.score(task, case, output)
    assert 0.0 <= metrics["quality"] <= 1.0
    assert np.isfinite(metrics["quality"])
    preview = tmp_path / f"{task}.png"
    KIT.render(task, case, output, preview)
    assert preview.read_bytes().startswith(b"\x89PNG")


def test_inverse_hidden_truth_can_be_removed() -> None:
    value = KIT.case("inverse_render", 8, 2)
    public = dict(value)
    public.pop("truth")
    assert "observations" in public and "truth" not in public
    assert KIT.score("inverse_render", value, {"objects": []})["quality"] < 1


def test_visual_suite_materializes_public_kit(tmp_path: Path) -> None:
    # Use the real repository because suite/capsule digests are part of preparation.
    repo = Repository(ROOT)
    records = prepare_suite(repo, "visual-research-arcade-v0", ["unit-test-materialize"])
    assert len(records) == 10
    for record in records:
        workspace = ROOT / record.workspace
        assert (workspace / "arena_kit" / "arena_kit.py").is_file()
        assert (workspace / "resources" / "visible-case.json").is_file()
        hidden_text = "\n".join(str(path) for path in workspace.rglob("*"))
        assert "hidden_inputs" not in hidden_text
