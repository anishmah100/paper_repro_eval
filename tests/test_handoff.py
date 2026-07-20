from __future__ import annotations

import pytest

from paper_repro_eval.errors import IntegrityError
from paper_repro_eval.handoff import (
    ONE_LINE_PROMPT,
    latest_prepared_records,
    workspace_readiness,
    write_launch_sheet,
)
from paper_repro_eval.materialize import prepare_suite
from paper_repro_eval.repository import Repository


def test_prepare_creates_pristine_zero_prompt_workspaces_and_launch_sheet(
    repository: Repository,
) -> None:
    records = prepare_suite(repository, "synthetic-smoke", ["model-a", "model-b"])
    assert all(workspace_readiness(repository, record) == [] for record in records)

    sheet = write_launch_sheet(repository, records)
    text = sheet.read_text(encoding="utf-8")
    assert ONE_LINE_PROMPT in text
    assert all(record.run_id in text for record in records)
    assert "model-a" in text and "model-b" in text
    for record in records:
        assert str((repository.root / record.workspace).resolve()) in text


def test_launch_sheet_refuses_a_modified_or_cross_contaminated_workspace(
    repository: Repository,
) -> None:
    record = prepare_suite(repository, "synthetic-smoke", ["model-a"])[0]
    workspace = repository.root / record.workspace
    (workspace / "submission" / "premade.txt").write_text("not pristine", encoding="utf-8")

    errors = workspace_readiness(repository, record)
    assert "submission is not empty" in errors
    assert "workspace differs from its initial public digest" in errors
    with pytest.raises(IntegrityError, match="not ready for handoff"):
        write_launch_sheet(repository, [record])


def test_latest_launch_selection_can_be_filtered_by_agent(repository: Repository) -> None:
    prepare_suite(repository, "synthetic-smoke", ["model-a", "model-b"])
    selected = latest_prepared_records(repository, "synthetic-smoke", {"model-b"})
    assert [record.agent for record in selected] == ["model-b"]
