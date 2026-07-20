"""Paper-first catalog loading, capsule ownership, and suite resolution."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import TypeVar

from pydantic import BaseModel, ValidationError

from .errors import ConfigurationError, IntegrityError
from .models import (
    CapsuleEntry,
    CapsuleManifest,
    CapsuleRef,
    PaperManifest,
    PaperRegistry,
    PaperRegistryEntry,
    SuiteManifest,
)
from .repository import Repository
from .util import ensure_within, load_yaml, tree_digest

ModelT = TypeVar("ModelT", bound=BaseModel)


@dataclass(frozen=True)
class ResolvedPaper:
    entry: PaperRegistryEntry
    manifest: PaperManifest
    paper_dir: Path
    digest: str

    @property
    def materials_dir(self) -> Path:
        return self.paper_dir / "paper"

    @property
    def resources_dir(self) -> Path:
        return self.paper_dir / "resources"


@dataclass(frozen=True)
class ResolvedCapsule:
    paper: ResolvedPaper
    entry: CapsuleEntry
    manifest: CapsuleManifest
    pack_dir: Path
    digest: str

    @property
    def public_dir(self) -> Path:
        return self.pack_dir / "public"

    @property
    def private_dir(self) -> Path:
        return self.pack_dir / "private"


def _validate(model_type: type[ModelT], path: Path) -> ModelT:
    try:
        return model_type.model_validate(load_yaml(path))
    except ValidationError as exc:
        raise ConfigurationError(f"Schema validation failed for {path}:\n{exc}") from exc


def load_registry(repository: Repository) -> PaperRegistry:
    return _validate(PaperRegistry, repository.registry_path)


def load_suite(repository: Repository, suite_id: str) -> SuiteManifest:
    candidates = [
        repository.suites_dir / f"{suite_id}.yaml",
        repository.suites_dir / f"{suite_id}.yml",
    ]
    for path in candidates:
        if path.is_file():
            suite = _validate(SuiteManifest, path)
            if suite.id != suite_id:
                raise ConfigurationError(
                    f"Suite ID mismatch: requested {suite_id!r}, manifest contains {suite.id!r}"
                )
            return suite
    raise ConfigurationError(f"Unknown suite: {suite_id}")


def _paper_digest(manifest: PaperManifest, paper_dir: Path) -> str:
    metadata = manifest.model_dump(mode="json", exclude={"capsules"})
    digest = hashlib.sha256(json.dumps(metadata, sort_keys=True).encode())
    for name in ("paper", "resources"):
        digest.update(name.encode())
        digest.update(tree_digest(paper_dir / name).encode())
    return digest.hexdigest()


def resolve_paper(repository: Repository, paper_id: str) -> ResolvedPaper:
    registry = load_registry(repository)
    matches = [entry for entry in registry.papers if entry.id == paper_id]
    if not matches:
        raise ConfigurationError(f"Unknown paper {paper_id!r}")
    entry = matches[0]
    paper_dir = ensure_within(repository.papers_dir / entry.path, repository.papers_dir)
    manifest = _validate(PaperManifest, paper_dir / "paper.yaml")
    if manifest.id != entry.id:
        raise IntegrityError(f"Registry and paper manifest disagree for {entry.id}")
    for relative in manifest.metadata.local_files:
        if not ensure_within(paper_dir / relative, paper_dir).is_file():
            raise ConfigurationError(f"Paper declares missing local file: {relative}")
    return ResolvedPaper(
        entry=entry,
        manifest=manifest,
        paper_dir=paper_dir,
        digest=_paper_digest(manifest, paper_dir),
    )


def resolve_capsule(
    repository: Repository,
    paper_id: str,
    capsule_id: str,
    version: str | None = None,
) -> ResolvedCapsule:
    paper = resolve_paper(repository, paper_id)
    matches = [entry for entry in paper.manifest.capsules if entry.id == capsule_id]
    if version is not None:
        matches = [entry for entry in matches if entry.version == version]
    if not matches:
        suffix = f" version {version}" if version else ""
        raise ConfigurationError(f"Unknown capsule {paper_id}/{capsule_id}{suffix}")
    if len(matches) > 1:
        raise ConfigurationError(
            f"Capsule {paper_id}/{capsule_id} has multiple versions; specify one explicitly"
        )
    entry = matches[0]
    pack_dir = ensure_within(paper.paper_dir / entry.path, paper.paper_dir)
    manifest = _validate(CapsuleManifest, pack_dir / "capsule.yaml")
    if (
        manifest.id != entry.id
        or manifest.version != entry.version
        or manifest.status != entry.status
        or manifest.paper_id != paper_id
    ):
        raise IntegrityError(
            f"Paper and capsule manifests disagree for {paper_id}/{entry.id}@{entry.version}"
        )
    if not (pack_dir / "public" / "TASK.md").is_file():
        raise ConfigurationError(f"Capsule is missing public/TASK.md: {pack_dir}")
    if not (pack_dir / "private").is_dir():
        raise ConfigurationError(f"Capsule is missing private/: {pack_dir}")
    digest = hashlib.sha256(f"{paper.digest}:{tree_digest(pack_dir)}".encode()).hexdigest()
    return ResolvedCapsule(
        paper=paper,
        entry=entry,
        manifest=manifest,
        pack_dir=pack_dir,
        digest=digest,
    )


def resolve_suite(
    repository: Repository, suite_id: str
) -> tuple[SuiteManifest, list[ResolvedCapsule]]:
    suite = load_suite(repository, suite_id)
    capsules: list[ResolvedCapsule] = []
    for reference in suite.capsules:
        resolved = resolve_capsule(
            repository,
            reference.paper_id,
            reference.capsule_id,
            reference.version,
        )
        if reference.digest and reference.digest != resolved.digest:
            raise IntegrityError(
                f"Suite digest mismatch for {reference.paper_id}/"
                f"{reference.capsule_id}@{reference.version}: "
                f"expected {reference.digest}, found {resolved.digest}"
            )
        capsules.append(resolved)
    return suite, capsules


def validate_registry(repository: Repository) -> list[ResolvedCapsule]:
    capsules: list[ResolvedCapsule] = []
    registry = load_registry(repository)
    for paper_entry in registry.papers:
        paper = resolve_paper(repository, paper_entry.id)
        capsules.extend(
            resolve_capsule(repository, paper.manifest.id, entry.id, entry.version)
            for entry in paper.manifest.capsules
        )
    return capsules


def pin_capsule(reference: CapsuleRef, resolved: ResolvedCapsule) -> CapsuleRef:
    return reference.model_copy(update={"digest": resolved.digest})
