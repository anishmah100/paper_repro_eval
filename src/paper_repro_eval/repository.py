"""Repository discovery and canonical paths."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from .errors import ConfigurationError


@dataclass(frozen=True)
class Repository:
    root: Path

    @property
    def registry_path(self) -> Path:
        return self.root / "papers" / "registry.yaml"

    @property
    def papers_dir(self) -> Path:
        return self.root / "papers"

    @property
    def suites_dir(self) -> Path:
        return self.root / "suites"

    @property
    def runs_dir(self) -> Path:
        return self.root / "runs"

    @property
    def reports_dir(self) -> Path:
        return self.root / "reports"

    @property
    def authoring_dir(self) -> Path:
        return self.root / "authoring"

    @property
    def learning_dir(self) -> Path:
        return self.root / "learning"

    @property
    def templates_dir(self) -> Path:
        return self.root / "templates"

    def relative(self, path: Path) -> str:
        return path.resolve().relative_to(self.root.resolve()).as_posix()


def discover_repository(start: Path | None = None) -> Repository:
    configured = os.environ.get("PAPER_REPRO_EVAL_ROOT")
    if configured:
        candidate = Path(configured).expanduser().resolve()
        if _is_repository(candidate):
            return Repository(candidate)
        raise ConfigurationError(f"PAPER_REPRO_EVAL_ROOT is not a valid repository: {candidate}")

    current = (start or Path.cwd()).resolve()
    for candidate in [current, *current.parents]:
        if _is_repository(candidate):
            return Repository(candidate)
    raise ConfigurationError(
        "Could not find a paper_repro_eval repository. Run the command inside the repository "
        "or set PAPER_REPRO_EVAL_ROOT."
    )


def _is_repository(path: Path) -> bool:
    return (path / "pyproject.toml").is_file() and (path / "papers" / "registry.yaml").is_file()
