"""Reference-first capsule authoring and immutable publication."""

from __future__ import annotations

import shutil
from pathlib import Path

from .catalog import load_registry, resolve_capsule
from .errors import ConfigurationError, IntegrityError
from .models import CapsuleManifest, CapsuleStatus, RegistryEntry
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


def author_init(repository: Repository, capsule_id: str) -> Path:
    root = repository.authoring_dir / slugify(capsule_id)
    if root.exists():
        raise IntegrityError(f"Authoring workspace already exists: {root}")
    root.mkdir(parents=True)
    proposal = {
        "schema_version": 1,
        "id": capsule_id,
        "paper": {"title": "TODO", "source_url": None},
        "candidate_capsules": [
            {
                "claim": "TODO: exact claim to reproduce",
                "verification_form": "TODO",
                "fidelity": "TODO",
                "why_small_is_informative": "TODO",
                "expected_runtime_note": "Targeted for an interactive local run; not enforced",
                "positive_reference": "TODO",
                "negative_controls": ["TODO"],
                "human_learning_value": "TODO",
            }
        ],
        "scope_approved": False,
    }
    dump_yaml(root / "proposal.yaml", proposal)
    (root / "NOTES.md").write_text(
        "# Authoring notes\n\nStart with proposal.yaml; approve scientific scope "
        "before scaffolding.\n",
        encoding="utf-8",
    )
    return root


def approve_scope(repository: Repository, capsule_id: str) -> Path:
    path = repository.authoring_dir / slugify(capsule_id) / "proposal.yaml"
    proposal = load_yaml(path)
    proposal["scope_approved"] = True
    dump_yaml(path, proposal)
    return path


def scaffold(repository: Repository, capsule_id: str, version: str, templates: list[str]) -> Path:
    unknown = set(templates) - set(TEMPLATE_TYPES)
    if unknown:
        raise ConfigurationError(f"Unknown authoring templates: {sorted(unknown)}")
    author_root = repository.authoring_dir / slugify(capsule_id)
    proposal = load_yaml(author_root / "proposal.yaml")
    if not proposal.get("scope_approved"):
        raise ConfigurationError("Scientific scope must be approved before scaffolding")
    pack = author_root / f"v{version}"
    if pack.exists():
        raise IntegrityError(f"Authoring version already exists: {pack}")
    for path in (
        pack / "public" / "paper",
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
        "paper": {
            "id": capsule_id,
            "title": proposal.get("paper", {}).get("title", "TODO"),
            "authors": [],
            "source_url": proposal.get("paper", {}).get("source_url"),
            "local_files": [],
        },
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
        "# Capsule review guide\n\nTODO: scientific questions, likely failure "
        "modes, and evidence.\n",
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


def publish(repository: Repository, capsule_id: str, version: str) -> Path:
    source = repository.authoring_dir / slugify(capsule_id) / f"v{version}"
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
    destination = repository.packs_dir / slugify(capsule_id) / f"v{version}"
    if destination.exists():
        raise IntegrityError("Published versions are immutable; create a new version")
    shutil.copytree(source, destination)
    registry = load_registry(repository)
    registry.capsules.append(
        RegistryEntry(
            id=capsule_id,
            version=version,
            status=manifest.status,
            path=destination.relative_to(repository.capsules_dir).as_posix(),
        )
    )
    registry.capsules.sort(key=lambda entry: (entry.id, entry.version))
    dump_yaml(repository.registry_path, registry.model_dump(mode="json"))
    resolve_capsule(repository, capsule_id, version)
    return destination


def validate_authoring(repository: Repository, capsule_id: str, version: str) -> str:
    pack = repository.authoring_dir / slugify(capsule_id) / f"v{version}"
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
