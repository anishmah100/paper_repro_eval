from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_operator_guide_covers_complete_visual_workflow() -> None:
    guide = (ROOT / "docs" / "RUNNING_AGENTS.md").read_text(encoding="utf-8")
    required = {
        "paper_repro_eval prepare",
        "paper_repro_eval enter",
        "paper_repro_eval evaluate",
        "paper_repro_eval report",
        "paper_repro_eval gallery",
        "paper_repro_eval tournament",
        "NOTES.md",
        "submission/",
    }
    assert required <= set(re.findall(r"paper_repro_eval \w+|NOTES\.md|submission/", guide))
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
