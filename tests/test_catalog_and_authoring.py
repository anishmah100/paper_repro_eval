from __future__ import annotations

import shutil

import pytest

from paper_repro_eval.authoring import (
    approve_scope,
    author_init,
    paper_init,
    publish,
    scaffold,
    validate_authoring,
)
from paper_repro_eval.catalog import (
    resolve_capsule,
    resolve_paper,
    resolve_suite,
    validate_registry,
)
from paper_repro_eval.errors import ConfigurationError
from paper_repro_eval.materialize import prepare_suite
from paper_repro_eval.repository import Repository
from paper_repro_eval.util import dump_yaml, load_yaml


def test_synthetic_registry_and_suite_are_valid(repository: Repository) -> None:
    capsules = validate_registry(repository)
    suite, resolved = resolve_suite(repository, "synthetic-smoke")
    assert suite.id == "synthetic-smoke"
    assert [item.paper.manifest.id for item in resolved] == ["synthetic-robust-estimation"]
    assert [item.manifest.id for item in resolved] == ["robust-line"]
    synthetic = next(capsule for capsule in capsules if capsule.manifest.id == "robust-line")
    assert synthetic.digest == resolved[0].digest


def test_authoring_requires_scope_approval(repository: Repository) -> None:
    paper_init(repository, "future-paper")
    author_init(repository, "future-paper", "first-capsule")
    with pytest.raises(ConfigurationError, match="scope"):
        scaffold(repository, "future-paper", "first-capsule", "1.0.0", ["software-conformance"])
    approve_scope(repository, "future-paper", "first-capsule")
    pack = scaffold(
        repository,
        "future-paper",
        "first-capsule",
        "1.0.0",
        ["software-conformance", "algorithmic-property"],
    )
    assert pack.is_dir()
    assert len(validate_authoring(repository, "future-paper", "first-capsule", "1.0.0")) == 64
    with pytest.raises(ConfigurationError, match="benchmark-ready"):
        publish(repository, "future-paper", "first-capsule", "1.0.0")


def test_one_paper_can_own_multiple_independently_materialized_capsules(
    repository: Repository,
) -> None:
    paper_dir = repository.papers_dir / "synthetic-robust-estimation"
    source = paper_dir / "capsules" / "robust-line" / "v1.0.0"
    destination = paper_dir / "capsules" / "robust-line-diagnostic" / "v1.0.0"
    shutil.copytree(source, destination)
    capsule_manifest = load_yaml(destination / "capsule.yaml")
    capsule_manifest["id"] = "robust-line-diagnostic"
    dump_yaml(destination / "capsule.yaml", capsule_manifest)

    paper_manifest = load_yaml(paper_dir / "paper.yaml")
    paper_manifest["capsules"].append(
        {
            "id": "robust-line-diagnostic",
            "version": "1.0.0",
            "status": "audited",
            "path": "capsules/robust-line-diagnostic/v1.0.0",
        }
    )
    dump_yaml(paper_dir / "paper.yaml", paper_manifest)

    suite_path = repository.suites_dir / "synthetic-smoke.yaml"
    suite_manifest = load_yaml(suite_path)
    suite_manifest["capsules"].append(
        {
            "paper_id": "synthetic-robust-estimation",
            "capsule_id": "robust-line-diagnostic",
            "version": "1.0.0",
        }
    )
    dump_yaml(suite_path, suite_manifest)

    _, resolved = resolve_suite(repository, "synthetic-smoke")
    assert {capsule.manifest.id for capsule in resolved} == {
        "robust-line",
        "robust-line-diagnostic",
    }
    records = prepare_suite(repository, "synthetic-smoke", ["one-agent"])
    assert len(records) == 2
    assert {record.paper_id for record in records} == {"synthetic-robust-estimation"}
    assert {record.capsule_id for record in records} == {
        "robust-line",
        "robust-line-diagnostic",
    }


def test_publishing_places_capsule_under_owning_paper(repository: Repository) -> None:
    paper_init(repository, "publishable-paper")
    author_init(repository, "publishable-paper", "method")
    approve_scope(repository, "publishable-paper", "method")
    pack = scaffold(
        repository,
        "publishable-paper",
        "method",
        "1.0.0",
        ["software-conformance"],
    )
    manifest = load_yaml(pack / "capsule.yaml")
    manifest["status"] = "benchmark-ready"
    dump_yaml(pack / "capsule.yaml", manifest)
    calibration_path = pack / "private" / "calibration" / "calibration.yaml"
    calibration = load_yaml(calibration_path)
    calibration.update(
        {
            "positive_reference_passes": True,
            "repeatability_checked": True,
            "human_packet_reviewed": True,
            "mutants": ["known-bad"],
            "hidden_case_coverage": ["held-out-case"],
        }
    )
    dump_yaml(calibration_path, calibration)

    destination = publish(repository, "publishable-paper", "method", "1.0.0")
    assert destination.relative_to(repository.papers_dir).parts[:3] == (
        "publishable-paper",
        "capsules",
        "method",
    )
    paper = resolve_paper(repository, "publishable-paper")
    assert [(entry.id, entry.version) for entry in paper.manifest.capsules] == [("method", "1.0.0")]
    resolved = resolve_capsule(repository, "publishable-paper", "method", "1.0.0")
    assert resolved.pack_dir == destination
