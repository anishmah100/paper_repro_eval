"""Git operations that deliberately rely only on global identity."""

from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass
from pathlib import Path

from .errors import ConfigurationError, EvaluationError


@dataclass(frozen=True)
class GitIdentity:
    name: str
    email: str


def _run_git(
    arguments: list[str], cwd: Path, *, check: bool = True, env: dict[str, str] | None = None
) -> subprocess.CompletedProcess[str]:
    process = subprocess.run(
        ["git", *arguments],
        cwd=cwd,
        check=False,
        capture_output=True,
        text=True,
        env=env or os.environ.copy(),
    )
    if check and process.returncode != 0:
        raise EvaluationError(
            f"Git command failed in {cwd}: git {' '.join(arguments)}\n{process.stderr.strip()}"
        )
    return process


def global_identity(cwd: Path) -> GitIdentity:
    name = _run_git(["config", "--global", "--get", "user.name"], cwd, check=False)
    email = _run_git(["config", "--global", "--get", "user.email"], cwd, check=False)
    if (
        name.returncode != 0
        or email.returncode != 0
        or not name.stdout.strip()
        or not email.stdout.strip()
    ):
        raise ConfigurationError(
            "Git global user.name and user.email are required. The framework never sets a local "
            "identity or substitutes an AI identity."
        )
    return GitIdentity(name=name.stdout.strip(), email=email.stdout.strip())


def initialize_workspace(repository: Path) -> str:
    global_identity(repository.parent)
    _run_git(["init", "--quiet"], repository)
    # Confirm no local identity was introduced by templates or environment.
    local_name = _run_git(["config", "--local", "--get", "user.name"], repository, check=False)
    local_email = _run_git(["config", "--local", "--get", "user.email"], repository, check=False)
    if local_name.returncode == 0 or local_email.returncode == 0:
        raise ConfigurationError("Workspace unexpectedly contains a local Git identity")
    _run_git(["add", "."], repository)
    _run_git(["commit", "--quiet", "-m", "Initial capsule workspace"], repository)
    commit_head = head(repository)
    if commit_head is None:
        raise EvaluationError("Initial workspace commit did not produce a Git HEAD")
    return commit_head


def head(repository: Path) -> str | None:
    result = _run_git(["rev-parse", "HEAD"], repository, check=False)
    return result.stdout.strip() if result.returncode == 0 else None


def diff(repository: Path) -> str:
    unstaged = _run_git(["diff", "--binary", "HEAD"], repository, check=False)
    untracked = _run_git(["ls-files", "--others", "--exclude-standard"], repository, check=False)
    pieces = [unstaged.stdout]
    if untracked.stdout.strip():
        pieces.append("\n# Untracked files\n" + untracked.stdout)
    return "".join(pieces)
