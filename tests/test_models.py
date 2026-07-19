from __future__ import annotations

import pytest
from hypothesis import given
from hypothesis import strategies as st
from pydantic import ValidationError

from paper_repro_eval.models import (
    CheckGraph,
    CheckKind,
    CheckResult,
    CheckSpec,
    CheckStatus,
    Fidelity,
    FidelityLevel,
)
from paper_repro_eval.util import slugify


def test_proxy_requires_transfer_argument() -> None:
    with pytest.raises(ValidationError):
        Fidelity(level=FidelityLevel.PROXY, rationale="small proxy")


def test_check_graph_rejects_cycles() -> None:
    with pytest.raises(ValidationError):
        CheckGraph.model_validate(
            {
                "schema_version": 1,
                "checks": [
                    {
                        "id": "a",
                        "title": "a",
                        "kind": "objective",
                        "weight": 1,
                        "depends_on": ["b"],
                    },
                    {
                        "id": "b",
                        "title": "b",
                        "kind": "objective",
                        "weight": 1,
                        "depends_on": ["a"],
                    },
                ],
            }
        )


def test_dependency_blocking_is_independent_of_manifest_order() -> None:
    from paper_repro_eval.verification import _block_dependencies

    graph = CheckGraph(
        checks=[
            CheckSpec(
                id="dependent",
                title="dependent",
                kind=CheckKind.OBJECTIVE,
                weight=1,
                depends_on=["root"],
            ),
            CheckSpec(id="root", title="root", kind=CheckKind.OBJECTIVE, weight=1),
        ]
    )
    results = [
        CheckResult(id="dependent", status=CheckStatus.PASSED, score=1, summary="raw pass"),
        CheckResult(id="root", status=CheckStatus.FAILED, score=0, summary="failed"),
    ]
    blocked = {result.id: result for result in _block_dependencies(graph, results)}
    assert blocked["dependent"].status is CheckStatus.BLOCKED


def test_result_status_and_score_are_consistent() -> None:
    with pytest.raises(ValidationError):
        CheckResult(id="x", status=CheckStatus.PASSED, score=0.5, summary="wrong")


@given(st.text(min_size=1).filter(lambda value: bool(value.strip())))
def test_slugify_never_emits_path_separator(value: str) -> None:
    try:
        slug = slugify(value)
    except Exception:
        return
    assert "/" not in slug
    assert "\\" not in slug
    assert slug not in {".", ".."}
