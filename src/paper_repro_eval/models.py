"""Versioned Pydantic schemas for repositories, runs, and verification."""

from __future__ import annotations

from enum import StrEnum
from pathlib import PurePosixPath
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class CapsuleStatus(StrEnum):
    DRAFT = "draft"
    BENCHMARK_READY = "benchmark-ready"
    AUDITED = "audited"
    DEPRECATED = "deprecated"


class FidelityLevel(StrEnum):
    FULL = "full-fidelity"
    SCALED = "faithful-scale-reduced"
    PROXY = "proxy"


class RunState(StrEnum):
    PREPARED = "prepared"
    SEALED = "sealed"
    REPRODUCED = "reproduced"
    VERIFIED = "verified"
    REVIEW_READY = "review-ready"


class CheckKind(StrEnum):
    OBJECTIVE = "objective"
    DIAGNOSTIC = "diagnostic"


class CheckStatus(StrEnum):
    PASSED = "passed"
    PARTIAL = "partial"
    FAILED = "failed"
    BLOCKED = "blocked"
    ERROR = "error"


def _relative_safe_path(value: str) -> str:
    path = PurePosixPath(value)
    if path.is_absolute() or ".." in path.parts:
        raise ValueError(f"Path must be safe and relative: {value!r}")
    return value


class RegistryEntry(StrictModel):
    id: str
    version: str
    status: CapsuleStatus
    path: str

    _validate_path = field_validator("path")(_relative_safe_path)


class CapsuleRegistry(StrictModel):
    schema_version: Literal[1] = 1
    capsules: list[RegistryEntry] = Field(default_factory=list)

    @model_validator(mode="after")
    def unique_entries(self) -> "CapsuleRegistry":
        keys = [(entry.id, entry.version) for entry in self.capsules]
        if len(keys) != len(set(keys)):
            raise ValueError("Capsule registry contains duplicate id/version entries")
        return self


class PaperMetadata(StrictModel):
    id: str
    title: str
    authors: list[str] = Field(default_factory=list)
    published: str | None = None
    source_url: str | None = None
    local_files: list[str] = Field(default_factory=list)

    @field_validator("local_files")
    @classmethod
    def safe_local_files(cls, values: list[str]) -> list[str]:
        return [_relative_safe_path(value) for value in values]


class Fidelity(StrictModel):
    level: FidelityLevel
    rationale: str
    transfer_argument: str | None = None
    limitations: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def proxy_requires_transfer_argument(self) -> "Fidelity":
        if self.level is FidelityLevel.PROXY and not self.transfer_argument:
            raise ValueError("Proxy capsules require a transfer_argument")
        return self


class CapsuleDetails(StrictModel):
    title: str
    summary: str
    domains: list[str] = Field(default_factory=list)
    research_types: list[str] = Field(default_factory=list)
    verification_forms: list[str] = Field(default_factory=list)
    fidelity: Fidelity


class SubmissionContract(StrictModel):
    reproduce: str = "submission/reproduce.sh"
    report: str = "submission/REPORT.md"
    demo: str | None = "submission/demo.sh"

    @field_validator("reproduce", "report", "demo")
    @classmethod
    def safe_paths(cls, value: str | None) -> str | None:
        return _relative_safe_path(value) if value is not None else None


class CapsuleManifest(StrictModel):
    schema_version: Literal[1] = 1
    id: str
    version: str
    status: CapsuleStatus
    paper: PaperMetadata
    capsule: CapsuleDetails
    submission: SubmissionContract = Field(default_factory=SubmissionContract)


class CapsuleRef(StrictModel):
    id: str
    version: str
    digest: str | None = None


class SuiteManifest(StrictModel):
    schema_version: Literal[1] = 1
    id: str
    title: str
    description: str = ""
    capsules: list[CapsuleRef]

    @model_validator(mode="after")
    def unique_capsules(self) -> "SuiteManifest":
        keys = [(capsule.id, capsule.version) for capsule in self.capsules]
        if len(keys) != len(set(keys)):
            raise ValueError("Suite contains duplicate capsule references")
        return self


class CheckSpec(StrictModel):
    id: str
    title: str
    kind: CheckKind
    weight: float = Field(ge=0)
    depends_on: list[str] = Field(default_factory=list)


class CheckGraph(StrictModel):
    schema_version: Literal[1] = 1
    checks: list[CheckSpec]

    @model_validator(mode="after")
    def valid_graph(self) -> "CheckGraph":
        ids = [check.id for check in self.checks]
        if len(ids) != len(set(ids)):
            raise ValueError("Check graph contains duplicate IDs")
        known = set(ids)
        for check in self.checks:
            missing = set(check.depends_on) - known
            if missing:
                raise ValueError(f"Check {check.id!r} has unknown dependencies: {sorted(missing)}")

        edges = {check.id: check.depends_on for check in self.checks}
        visiting: set[str] = set()
        visited: set[str] = set()

        def visit(node: str) -> None:
            if node in visiting:
                raise ValueError("Check graph contains a dependency cycle")
            if node in visited:
                return
            visiting.add(node)
            for dependency in edges[node]:
                visit(dependency)
            visiting.remove(node)
            visited.add(node)

        for node in ids:
            visit(node)
        return self


class CheckResult(StrictModel):
    id: str
    status: CheckStatus
    score: float | None = Field(default=None, ge=0, le=1)
    summary: str
    measurements: dict[str, Any] = Field(default_factory=dict)
    evidence: list[str] = Field(default_factory=list)

    @field_validator("evidence")
    @classmethod
    def safe_evidence_paths(cls, values: list[str]) -> list[str]:
        return [_relative_safe_path(value) for value in values]

    @model_validator(mode="after")
    def status_matches_score(self) -> "CheckResult":
        if self.status is CheckStatus.ERROR:
            if self.score is not None:
                raise ValueError("Errored checks must not have a score")
        elif self.score is None:
            raise ValueError("Non-error checks require a score")
        if self.status is CheckStatus.PASSED and self.score != 1:
            raise ValueError("Passed checks require score 1")
        if self.status in {CheckStatus.FAILED, CheckStatus.BLOCKED} and self.score != 0:
            raise ValueError("Failed or blocked checks require score 0")
        if self.status is CheckStatus.PARTIAL and self.score is not None:
            if not 0 < self.score < 1:
                raise ValueError("Partial checks require a score strictly between 0 and 1")
        return self


class WarningRecord(StrictModel):
    code: str
    message: str


class VerifierOutput(StrictModel):
    schema_version: Literal[1] = 1
    checks: list[CheckResult]
    warnings: list[WarningRecord] = Field(default_factory=list)


class VerifierConfig(StrictModel):
    schema_version: Literal[1] = 1
    command: list[str]
    timeout_seconds: float | None = Field(default=None, gt=0)

    @field_validator("command")
    @classmethod
    def nonempty_command(cls, value: list[str]) -> list[str]:
        if not value or any(not item for item in value):
            raise ValueError("Verifier command must contain nonempty arguments")
        return value


class RunRecord(StrictModel):
    schema_version: Literal[1] = 1
    run_id: str
    suite_id: str
    capsule_id: str
    capsule_version: str
    capsule_digest: str
    agent: str
    attempt: int
    state: RunState
    isolation: Literal["directory", "container"]
    created_at: str
    updated_at: str
    workspace: str
    initial_digest: str


class SealRecord(StrictModel):
    schema_version: Literal[1] = 1
    run_id: str
    revision: int
    created_at: str
    submission_digest: str
    source_git_head: str | None = None
    source_git_diff: str = ""
    missing_required: list[str] = Field(default_factory=list)


class ReproductionRecord(StrictModel):
    schema_version: Literal[1] = 1
    run_id: str
    seal_revision: int
    attempt: int
    created_at: str
    status: Literal["success", "candidate-failure", "infrastructure-error"]
    exit_code: int | None
    elapsed_seconds: float
    artifact_digest: str
    stdout_path: str
    stderr_path: str
    work_dir: str
    artifact_dir: str


class VerificationRecord(StrictModel):
    schema_version: Literal[1] = 1
    run_id: str
    reproduction_attempt: int
    created_at: str
    status: Literal["success", "candidate-failure", "evaluator-error"]
    objective_score: float | None = Field(default=None, ge=0, le=1)
    checks: list[CheckResult] = Field(default_factory=list)
    warnings: list[WarningRecord] = Field(default_factory=list)

