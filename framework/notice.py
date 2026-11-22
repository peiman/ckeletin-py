"""Tell a derived project that a newer framework exists. Never fails the gate."""

from __future__ import annotations

import os
import subprocess
import tomllib
from dataclasses import dataclass
from pathlib import Path

from framework.project import read_identity
from framework.semver import is_newer

UPDATE_COMMAND = "python -m app update"


@dataclass(frozen=True)
class Notice:
    shown: bool
    reason: str
    current: str | None = None
    latest: str | None = None
    update_available: bool = False

    def as_dict(self) -> dict:
        return {
            "shown": self.shown,
            "reason": self.reason,
            "current": self.current,
            "latest": self.latest,
            "update_available": self.update_available,
            "command": UPDATE_COMMAND if self.shown else None,
        }

    def prose(self) -> str:
        if not self.shown:
            return ""
        return (
            f"framework {self.latest} is available (you have {self.current}). "
            f"Run: {UPDATE_COMMAND}"
        )


def _ci() -> bool:
    return os.environ.get("CI") == "true" or os.environ.get("GITHUB_ACTIONS") == "true"


def _git(root: Path, *args: str, timeout: int = 2) -> subprocess.CompletedProcess[str] | None:
    try:
        return subprocess.run(
            ["git", "-C", str(root), *args],
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None


def _version_at(root: Path, ref: str) -> str | None:
    result = _git(root, "show", f"{ref}:framework/VERSION")
    if result is None or result.returncode != 0:
        return None
    return result.stdout.strip() or None


def upstream_version(root: Path) -> str | None:
    """Read origin's framework version. A missing remote or a failed read is unavailable."""
    result = _git(root, "remote", "get-url", "origin")
    if result is None or result.returncode != 0:
        return None
    remote = result.stdout.strip()
    local = Path(remote)
    if local.is_dir():
        version = local / "framework" / "VERSION"
        if version.is_file():
            text = version.read_text(encoding="utf-8").strip()
            if text:
                return text
    for ref in ("origin/main", "origin/master", "origin/HEAD"):
        found = _version_at(root, ref)
        if found:
            return found
    fetched = _git(root, "fetch", "--depth", "1", "origin", timeout=5)
    if fetched is None or fetched.returncode != 0:
        return None
    for ref in ("origin/main", "origin/master", "FETCH_HEAD"):
        found = _version_at(root, ref)
        if found:
            return found
    return None


def look_for_update(root: Path, upstream: Path | None = None) -> Notice:
    if os.environ.get("CKELETIN_NO_UPDATE_NOTICE") == "1":
        return Notice(False, "disabled")
    if _ci():
        return Notice(False, "ci")
    try:
        identity = read_identity(root)
    except tomllib.TOMLDecodeError:
        return Notice(False, "unavailable")
    if identity.role == "implementation":
        return Notice(False, "upstream")
    version_file = root / "framework" / "VERSION"
    if not version_file.is_file():
        return Notice(False, "unavailable")
    current = version_file.read_text(encoding="utf-8").strip()
    if upstream is not None and (upstream / "framework" / "VERSION").is_file():
        latest = (upstream / "framework" / "VERSION").read_text(encoding="utf-8").strip()
    elif upstream is None:
        latest = upstream_version(root)
    else:
        latest = None
    if not latest:
        return Notice(False, "unavailable", current=current)
    try:
        available = is_newer(latest, current)
    except ValueError:
        return Notice(False, "unavailable", current=current)
    if not available:
        return Notice(False, "current", current=current, latest=latest, update_available=False)
    return Notice(True, "available", current=current, latest=latest, update_available=True)
