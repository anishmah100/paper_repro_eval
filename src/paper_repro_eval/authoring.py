"""Paper-first, reference-first capsule authoring and publication."""

from __future__ import annotations

import shutil
from pathlib import Path

from .catalog import load_registry, resolve_capsule, resolve_paper
from .errors import ConfigurationError, IntegrityError
from .models import (
    CapsuleEntry,
    CapsuleManifest,
    CapsuleStatus,
    PaperManifest,
    PaperRegistryEntry,
)
from .repository import Repository
from .util import dump_yaml, load_yaml, slugify, tree_digest

TEMPLATE_TYPES = (
    "software-conformance",
    "algorithmic-property",
    "exact-mathematical",
    "formal-proof",
    "fixed-data-analysis",
    "small-training",
    "comparative-method",
    "interpretability",
    "visual-graphics",
    "simulation-physics",
    "systems-engineering",
    "proxy-reproduction",
)


def _paper_author_root(repository: Repository, paper_id: str) -> Path:
    return repository.authoring_dir / slugify(paper_id)


def _capsule_author_root(repository: Repository, paper_id: str, capsule_id: str) -> Path:
    return _paper_author_root(repository, paper_id) / "capsules" / slugify(capsule_id)


def paper_init(repository: Repository, paper_id: str) -> Path:
    root = _paper_author_root(repository, paper_id)
    if root.exists():
        raise IntegrityError(f"Paper authoring workspace already exists: {root}")
    (root / "paper").mkdir(parents=True)
    (root / "resources").mkdir()
    manifest = {
        "schema_version": 1,
        "id": paper_id,
        "metadata": {
            "id": paper_id,
            "title": "TODO",
            "authors": [],
            "published": None,
            "source_url": None,
            "local_files": [],
        },
        "summary": "TODO",
        "domains": [],
        "capsules": [],
    }
    dump_yaml(root / "paper.yaml", manifest)
    (root / "NOTES.md").write_text(
        "# Paper-level authoring notes\n\nStore shared paper files in paper/ and resources/.\n",
        encoding="utf-8",
    )
    return root


def author_init(repository: Repository, paper_id: str, capsule_id: str) -> Path:
    paper_root = _paper_author_root(repository, paper_id)
    if not (paper_root / "paper.yaml").is_file():
        raise ConfigurationError(f"Initialize paper {paper_id!r} before creating its capsules")
    root = _capsule_author_root(repository, paper_id, capsule_id)
    if root.exists():
        raise IntegrityError(f"Capsule authoring workspace already exists: {root}")
    root.mkdir(parents=True)
    proposal = {
        "schema_version": 1,
        "paper_id": paper_id,
        "capsule_id": capsule_id,
        "claim": "TODO: exact claim to reproduce",
        "verification_form": "TODO",
        "fidelity": "TODO",
        "why_small_is_informative": "TODO",
        "expected_runtime_note": "Targeted for an interactive local run; not enforced",
        "positive_reference": "TODO",
        "negative_controls": ["TODO"],
        "human_learning_value": "TODO",
        "scope_approved": False,
    }
    dump_yaml(root / "proposal.yaml", proposal)
    (root / "NOTES.md").write_text(
        "# Capsule authoring notes\n\nApprove scientific scope before scaffolding.\n",
        encoding="utf-8",
    )
    return root


def approve_scope(repository: Repository, paper_id: str, capsule_id: str) -> Path:
    path = _capsule_author_root(repository, paper_id, capsule_id) / "proposal.yaml"
    proposal = load_yaml(path)
    proposal["scope_approved"] = True
    dump_yaml(path, proposal)
    return path


def scaffold(
    repository: Repository,
    paper_id: str,
    capsule_id: str,
    version: str,
    templates: list[str],
) -> Path:
    unknown = set(templates) - set(TEMPLATE_TYPES)
    if unknown:
        raise ConfigurationError(f"Unknown authoring templates: {sorted(unknown)}")
    author_root = _capsule_author_root(repository, paper_id, capsule_id)
    proposal = load_yaml(author_root / "proposal.yaml")
    if not proposal.get("scope_approved"):
        raise ConfigurationError("Scientific scope must be approved before scaffolding")
    pack = author_root / f"v{version}"
    if pack.exists():
        raise IntegrityError(f"Authoring version already exists: {pack}")
    for path in (
        pack / "public" / "resources",
        pack / "public" / "starter",
        pack / "private" / "verifier",
        pack / "private" / "hidden_inputs",
        pack / "private" / "reference",
        pack / "private" / "calibration",
    ):
        path.mkdir(parents=True)
    fidelity = "proxy" if "proxy-reproduction" in templates else "faithful-scale-reduced"
    manifest = {
        "schema_version": 1,
        "id": capsule_id,
        "version": version,
        "status": "draft",
        "paper_id": paper_id,
        "capsule": {
            "title": "TODO",
            "summary": "TODO",
            "domains": [],
            "research_types": templates,
            "verification_forms": [],
            "fidelity": {
                "level": fidelity,
                "rationale": "TODO",
                **({"transfer_argument": "TODO"} if fidelity == "proxy" else {}),
                "limitations": [],
            },
        },
        "competition": {
            "mode": "independent-score",
            "primary_metric": {
                "id": "objective_score",
                "title": "Normalized objective score",
                "direction": "higher-is-better",
                "unit": "score in [0, 1]",
                "description": "Weighted score produced by the private verifier.",
            },
            "tiebreakers": [],
            "qualification_checks": ["core-result"],
            "tie_tolerance": 1e-6,
            "winner_rule": "Highest qualifying objective score wins; scores within tolerance tie.",
        },
    }
    dump_yaml(pack / "capsule.yaml", manifest)
    (pack / "public" / "TASK.md").write_text(
        "# Reproduction task\n\nTODO: claim, deliverables, constraints, and artifact contract.\n",
        encoding="utf-8",
    )
    dump_yaml(
        pack / "private" / "checks.yaml",
        {
            "schema_version": 1,
            "checks": [
                {
                    "id": "core-result",
                    "title": "Core reproduced result",
                    "kind": "objective",
                    "weight": 1,
                    "depends_on": [],
                }
            ],
        },
    )
    dump_yaml(
        pack / "private" / "verifier.yaml",
        {
            "schema_version": 1,
            "command": ["python", "verify.py", "--context", "{context}", "--output", "{output}"],
            "timeout_seconds": 300,
        },
    )
    (pack / "private" / "verifier" / "verify.py").write_text(
        '"""TODO: trusted verifier. Build a reference first, then calibrate mutants."""\n',
        encoding="utf-8",
    )
    (pack / "private" / "REVIEW_GUIDE.md").write_text(
        "# Capsule review guide\n\nTODO: scientific questions, failure modes, and evidence.\n",
        encoding="utf-8",
    )
    dump_yaml(
        pack / "private" / "calibration" / "calibration.yaml",
        {
            "schema_version": 1,
            "positive_reference_passes": False,
            "repeatability_checked": False,
            "mutants": [],
            "hidden_case_coverage": [],
            "human_packet_reviewed": False,
        },
    )
    (pack / "AUTHORING.md").write_text(
        "# Authoring gates\n\nReference → mutants → hidden cases → repeatability → human packet.\n",
        encoding="utf-8",
    )
    return pack


def _ensure_published_paper(repository: Repository, paper_id: str) -> Path:
    source = _paper_author_root(repository, paper_id)
    PaperManifest.model_validate(load_yaml(source / "paper.yaml"))
    destination = repository.papers_dir / slugify(paper_id)
    registry = load_registry(repository)
    registered = [entry for entry in registry.papers if entry.id == paper_id]
    if registered:
        return resolve_paper(repository, paper_id).paper_dir
    destination.mkdir(parents=True)
    shutil.copy2(source / "paper.yaml", destination / "paper.yaml")
    for name in ("paper", "resources"):
        shutil.copytree(source / name, destination / name)
    (destination / "capsules").mkdir()
    registry.papers.append(
        PaperRegistryEntry(
            id=paper_id,
            path=destination.relative_to(repository.papers_dir).as_posix(),
        )
    )
    registry.papers.sort(key=lambda entry: entry.id)
    dump_yaml(repository.registry_path, registry.model_dump(mode="json"))
    return destination


def publish(repository: Repository, paper_id: str, capsule_id: str, version: str) -> Path:
    source = _capsule_author_root(repository, paper_id, capsule_id) / f"v{version}"
    if not source.is_dir():
        raise ConfigurationError(f"Missing authoring pack: {source}")
    manifest = CapsuleManifest.model_validate(load_yaml(source / "capsule.yaml"))
    if manifest.status not in {CapsuleStatus.BENCHMARK_READY, CapsuleStatus.AUDITED}:
        raise ConfigurationError("Only benchmark-ready or audited capsules may be published")
    calibration = load_yaml(source / "private" / "calibration" / "calibration.yaml")
    required = ("positive_reference_passes", "repeatability_checked", "human_packet_reviewed")
    if not all(calibration.get(item) is True for item in required):
        raise ConfigurationError(f"Calibration gates are incomplete; required: {required}")
    if not calibration.get("mutants") or not calibration.get("hidden_case_coverage"):
        raise ConfigurationError("Publication requires mutants and hidden-case coverage")
    if manifest.paper_id != paper_id or manifest.id != capsule_id or manifest.version != version:
        raise IntegrityError("Authoring capsule identity does not match publish target")
    paper_dir = _ensure_published_paper(repository, paper_id)
    destination = paper_dir / "capsules" / slugify(capsule_id) / f"v{version}"
    if destination.exists():
        raise IntegrityError("Published versions are immutable; create a new version")
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source, destination)
    paper_manifest_path = paper_dir / "paper.yaml"
    paper_manifest = PaperManifest.model_validate(load_yaml(paper_manifest_path))
    paper_manifest.capsules.append(
        CapsuleEntry(
            id=capsule_id,
            version=version,
            status=manifest.status,
            path=destination.relative_to(paper_dir).as_posix(),
        )
    )
    paper_manifest.capsules.sort(key=lambda entry: (entry.id, entry.version))
    dump_yaml(paper_manifest_path, paper_manifest.model_dump(mode="json"))
    resolve_capsule(repository, paper_id, capsule_id, version)
    return destination


def validate_authoring(repository: Repository, paper_id: str, capsule_id: str, version: str) -> str:
    paper_root = _paper_author_root(repository, paper_id)
    PaperManifest.model_validate(load_yaml(paper_root / "paper.yaml"))
    pack = _capsule_author_root(repository, paper_id, capsule_id) / f"v{version}"
    CapsuleManifest.model_validate(load_yaml(pack / "capsule.yaml"))
    for required in (
        "public/TASK.md",
        "private/checks.yaml",
        "private/verifier.yaml",
        "private/REVIEW_GUIDE.md",
        "private/calibration/calibration.yaml",
    ):
        if not (pack / required).is_file():
            raise ConfigurationError(f"Missing required authoring file: {required}")
    return tree_digest(pack)
