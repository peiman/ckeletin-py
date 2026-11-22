"""Project identity. The file lives outside the framework tree."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path

REFERENCE_NAME = "ckeletin-py"


@dataclass(frozen=True)
class Identity:
    role: str
    name: str


def read_identity(root: Path) -> Identity:
    path = root / "ckeletin-project.toml"
    if not path.is_file():
        return Identity("", "")
    loaded = tomllib.loads(path.read_text(encoding="utf-8"))
    return Identity(str(loaded.get("role", "")), str(loaded.get("name", "")))


def is_reference(root: Path) -> bool:
    identity = read_identity(root)
    return identity.role == "implementation" and identity.name == REFERENCE_NAME
