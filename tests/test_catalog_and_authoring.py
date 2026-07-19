from __future__ import annotations

import pytest

from paper_repro_eval.authoring import (
    approve_scope,
    author_init,
    publish,
    scaffold,
    validate_authoring,
)
from paper_repro_eval.catalog import resolve_suite, validate_registry
from paper_repro_eval.errors import ConfigurationError
from paper_repro_eval.repository import Repository


def test_synthetic_registry_and_suite_are_valid(repository: Repository) -> None:
    capsules = validate_registry(repository)
    suite, resolved = resolve_suite(repository, "synthetic-smoke")
    assert suite.id == "synthetic-smoke"
    assert [item.manifest.id for item in resolved] == ["synthetic-robust-line"]
    assert capsules[0].digest == resolved[0].digest


def test_authoring_requires_scope_approval(repository: Repository) -> None:
    author_init(repository, "future-paper")
    with pytest.raises(ConfigurationError, match="scope"):
        scaffold(repository, "future-paper", "1.0.0", ["software-conformance"])
    approve_scope(repository, "future-paper")
    pack = scaffold(
        repository,
        "future-paper",
        "1.0.0",
        ["software-conformance", "algorithmic-property"],
    )
    assert pack.is_dir()
    assert len(validate_authoring(repository, "future-paper", "1.0.0")) == 64
    with pytest.raises(ConfigurationError, match="benchmark-ready"):
        publish(repository, "future-paper", "1.0.0")
