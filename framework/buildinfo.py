"""CLI provenance. A field that cannot be resolved is the string unknown."""

from __future__ import annotations

import subprocess
from pathlib import Path


def _git(root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(root), *args],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def _one(root: Path, *args: str) -> str:
    try:
        value = _git(root, *args)
    except (OSError, subprocess.CalledProcessError):
        return "unknown"
    return value or "unknown"


def provenance(root: Path) -> dict[str, str]:
    version_file = root / "VERSION"
    if version_file.is_file():
        version = version_file.read_text(encoding="utf-8").strip() or "unknown"
    else:
        version = "unknown"
    commit = _one(root, "rev-parse", "HEAD")
    date = _one(root, "log", "-1", "--format=%cs")
    try:
        porcelain = _git(root, "status", "--porcelain")
        dirty = "true" if porcelain else "false"
    except (OSError, subprocess.CalledProcessError):
        dirty = "unknown"
    return {"version": version, "commit": commit, "date": date, "dirty": dirty}
