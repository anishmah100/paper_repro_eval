"""Capsule and suite catalog loading, resolution, and validation."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from pydantic import BaseModel, ValidationError

from .errors import ConfigurationError, IntegrityError
from .models import CapsuleManifest, CapsuleRef, CapsuleRegistry, RegistryEntry, SuiteManifest
from .repository import Repository
from .util import load_yaml, tree_digest


@dataclass(frozen=True)
class ResolvedCapsule:
    entry: RegistryEntry
    manifest: CapsuleManifest
    pack_dir: Path
    digest: str

    @property
    def public_dir(self) -> Path:
        return self.pack_dir / "public"

    @property
    def private_dir(self) -> Path:
        return self.pack_dir / "private"


def _validate[T: BaseModel](model_type: type[T], path: Path) -> T:
    try:
        return model_type.model_validate(load_yaml(path))
    except ValidationError as exc:
        raise ConfigurationError(f"Schema validation failed for {path}:\n{exc}") from exc


def load_registry(repository: Repository) -> CapsuleRegistry:
    return _validate(CapsuleRegistry, repository.registry_path)


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


def resolve_capsule(
    repository: Repository, capsule_id: str, version: str | None = None
) -> ResolvedCapsule:
    registry = load_registry(repository)
    matches = [entry for entry in registry.capsules if entry.id == capsule_id]
    if version is not None:
        matches = [entry for entry in matches if entry.version == version]
    if not matches:
        suffix = f" version {version}" if version else ""
        raise ConfigurationError(f"Unknown capsule {capsule_id!r}{suffix}")
    if len(matches) > 1:
        raise ConfigurationError(
            f"Capsule {capsule_id!r} has multiple versions; specify one explicitly"
        )
    entry = matches[0]
    # Registry paths are relative to capsules/, so packs/foo is conventional.
    pack_dir = repository.capsules_dir / entry.path
    manifest_path = pack_dir / "capsule.yaml"
    manifest = _validate(CapsuleManifest, manifest_path)
    if manifest.id != entry.id or manifest.version != entry.version or manifest.status != entry.status:
        raise IntegrityError(
            f"Registry and capsule manifest disagree for {entry.id}@{entry.version}"
        )
    public_dir = pack_dir / "public"
    private_dir = pack_dir / "private"
    if not (public_dir / "TASK.md").is_file():
        raise ConfigurationError(f"Capsule is missing public/TASK.md: {pack_dir}")
    if not private_dir.is_dir():
        raise ConfigurationError(f"Capsule is missing private/: {pack_dir}")
    digest = tree_digest(pack_dir)
    return ResolvedCapsule(entry=entry, manifest=manifest, pack_dir=pack_dir, digest=digest)


def resolve_suite(repository: Repository, suite_id: str) -> tuple[SuiteManifest, list[ResolvedCapsule]]:
    suite = load_suite(repository, suite_id)
    capsules: list[ResolvedCapsule] = []
    for reference in suite.capsules:
        resolved = resolve_capsule(repository, reference.id, reference.version)
        if reference.digest and reference.digest != resolved.digest:
            raise IntegrityError(
                f"Suite digest mismatch for {reference.id}@{reference.version}: "
                f"expected {reference.digest}, found {resolved.digest}"
            )
        capsules.append(resolved)
    return suite, capsules


def validate_registry(repository: Repository) -> list[ResolvedCapsule]:
    registry = load_registry(repository)
    return [resolve_capsule(repository, entry.id, entry.version) for entry in registry.capsules]


def pin_capsule(reference: CapsuleRef, resolved: ResolvedCapsule) -> CapsuleRef:
    return reference.model_copy(update={"digest": resolved.digest})

