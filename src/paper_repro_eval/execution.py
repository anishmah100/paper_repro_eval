"""Small, auditable process runner used by candidate and trusted code."""

from __future__ import annotations

import os
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ExecutionResult:
    exit_code: int | None
    elapsed_seconds: float
    stdout: str
    stderr: str
    timed_out: bool = False
    infrastructure_error: str | None = None


def execute(
    command: list[str],
    *,
    cwd: Path,
    environment: dict[str, str] | None = None,
    timeout_seconds: float | None = None,
) -> ExecutionResult:
    env = os.environ.copy()
    env.update(environment or {})
    started = time.monotonic()
    try:
        process = subprocess.run(
            command,
            cwd=cwd,
            env=env,
            capture_output=True,
            text=True,
            check=False,
            timeout=timeout_seconds,
        )
        return ExecutionResult(
            exit_code=process.returncode,
            elapsed_seconds=time.monotonic() - started,
            stdout=process.stdout,
            stderr=process.stderr,
        )
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout.decode() if isinstance(exc.stdout, bytes) else (exc.stdout or "")
        stderr = exc.stderr.decode() if isinstance(exc.stderr, bytes) else (exc.stderr or "")
        return ExecutionResult(
            exit_code=None,
            elapsed_seconds=time.monotonic() - started,
            stdout=stdout,
            stderr=stderr,
            timed_out=True,
        )
    except OSError as exc:
        return ExecutionResult(
            exit_code=None,
            elapsed_seconds=time.monotonic() - started,
            stdout="",
            stderr="",
            infrastructure_error=str(exc),
        )
