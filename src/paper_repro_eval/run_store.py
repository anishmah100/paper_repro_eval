"""Filesystem-native run discovery and lifecycle persistence."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from pydantic import ValidationError

from .errors import ConfigurationError
from .models import RunRecord
from .repository import Repository
from .util import dump_json, load_json


@dataclass(frozen=True)
class StoredRun:
    directory: Path
    record: RunRecord

    @property
    def workspace(self) -> Path:
        return self.directory / "workspace"

    @property
    def sealed_dir(self) -> Path:
        return self.directory / "sealed-submission"

    @property
    def evaluation_dir(self) -> Path:
        return self.directory / "evaluation"

    @property
    def review_dir(self) -> Path:
        return self.directory / "review"

    def save(self) -> None:
        dump_json(self.directory / "run.json", self.record.model_dump(mode="json"))


def list_runs(repository: Repository) -> list[StoredRun]:
    if not repository.runs_dir.exists():
        return []
    runs: list[StoredRun] = []
    for path in repository.runs_dir.rglob("run.json"):
        try:
            record = RunRecord.model_validate(load_json(path))
        except ValidationError as exc:
            raise ConfigurationError(f"Invalid run record {path}: {exc}") from exc
        runs.append(StoredRun(path.parent, record))
    return sorted(runs, key=lambda item: item.record.created_at)


def find_run(repository: Repository, run_id: str) -> StoredRun:
    matches = [run for run in list_runs(repository) if run.record.run_id == run_id]
    if not matches:
        raise ConfigurationError(f"Unknown run ID: {run_id}")
    if len(matches) > 1:
        raise ConfigurationError(f"Duplicate run ID detected: {run_id}")
    return matches[0]

