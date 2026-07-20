from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from paper_repro_eval.repository import Repository

PROJECT_ROOT = Path(__file__).parents[1]


@pytest.fixture
def repository(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Repository:
    root = tmp_path / "evaluation"
    root.mkdir()
    shutil.copytree(PROJECT_ROOT / "papers", root / "papers")
    shutil.copytree(PROJECT_ROOT / "suites", root / "suites")
    shutil.copy2(PROJECT_ROOT / "REVIEWING.md", root / "REVIEWING.md")
    shutil.copy2(PROJECT_ROOT / "pyproject.toml", root / "pyproject.toml")
    git_home = tmp_path / "git-home"
    git_home.mkdir()
    (git_home / ".gitconfig").write_text(
        "[user]\n\tname = Test Operator\n\temail = operator@example.test\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("HOME", str(git_home))
    return Repository(root)
