"""Optional container entry that mounts exactly one candidate workspace."""

from __future__ import annotations

import shutil
from pathlib import Path

from .errors import ConfigurationError


def container_command(workspace: Path, image: str, shell: str) -> list[str]:
    if not shutil.which("docker"):
        raise ConfigurationError("Docker is required for container isolation")
    if not image.strip():
        raise ConfigurationError("Container image cannot be empty")
    return [
        "docker",
        "run",
        "--rm",
        "-it",
        "--network",
        "bridge",
        "--security-opt",
        "no-new-privileges",
        "--mount",
        f"type=bind,source={workspace.resolve()},target=/workspace",
        "--workdir",
        "/workspace",
        image,
        shell,
    ]
