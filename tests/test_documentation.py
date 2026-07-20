from __future__ import annotations

import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def test_operator_guide_covers_complete_visual_workflow() -> None:
    guide = (ROOT / "docs" / "RUNNING_AGENTS.md").read_text(encoding="utf-8")
    required = {
        "paper_repro_eval prepare",
        "paper_repro_eval launch",
        "paper_repro_eval enter",
        "paper_repro_eval evaluate",
        "paper_repro_eval report",
        "paper_repro_eval gallery",
        "paper_repro_eval tournament",
        "NOTES.md",
        "submission/",
        "EXECUTABLE_CONTRACT.md",
    }
    assert required <= set(
        re.findall(r"paper_repro_eval \w+|NOTES\.md|submission/|EXECUTABLE_CONTRACT\.md", guide)
    )
    assert "forbidden information flow" in guide
    assert "candidate's workspace" in guide
    assert "internet access" in guide


def test_public_markdown_file_links_resolve() -> None:
    documents = [ROOT / "README.md", *(ROOT / "docs").glob("*.md")]
    for document in documents:
        text = document.read_text(encoding="utf-8")
        for target in re.findall(r"\[[^]]+\]\(([^)]+)\)", text):
            if "://" in target or target.startswith("#"):
                continue
            relative = target.split("#", 1)[0]
            assert (document.parent / relative).exists(), (document, target)


def test_task_catalog_and_exact_contracts_cover_the_entire_visual_suite() -> None:
    suite_path = ROOT / "suites" / "visual-research-arcade-v0.yaml"
    suite = yaml.safe_load(suite_path.read_text(encoding="utf-8"))
    catalog = (ROOT / "docs" / "TASK_CATALOG.md").read_text(encoding="utf-8")
    human_guide = (ROOT / "docs" / "HUMAN_GUIDE.md").read_text(encoding="utf-8")
    for reference in suite["capsules"]:
        paper = reference["paper_id"]
        capsule = reference["capsule_id"]
        version = reference["version"]
        public = ROOT / "papers" / paper / "capsules" / capsule / f"v{version}" / "public"
        contract = (public / "EXECUTABLE_CONTRACT.md").read_text(encoding="utf-8")
        task = (public / "TASK.md").read_text(encoding="utf-8")
        assert f"`{capsule}`" in catalog
        assert len(contract) > 500
        assert "EXECUTABLE_CONTRACT.md" in task
    assert "prepared → sealed → reproduced → verified → review-ready" in human_guide
    assert "Public and private halves" in human_guide
