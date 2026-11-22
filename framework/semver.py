"""Semantic version precedence. A pre-release is older than its release."""

from __future__ import annotations


def _parse(value: str) -> tuple[tuple[int, int, int], str]:
    text = value.strip().lstrip("v")
    core, _, pre = text.partition("-")
    parts = [int(piece) for piece in core.split(".") if piece != ""]
    while len(parts) < 3:
        parts.append(0)
    return (parts[0], parts[1], parts[2]), pre


def is_newer(upstream: str, local: str) -> bool:
    """True when upstream is a newer semantic version than local."""
    up_core, up_pre = _parse(upstream)
    local_core, local_pre = _parse(local)
    if up_core != local_core:
        return up_core > local_core
    # A release is newer than a pre-release of the same core. Two
    # pre-releases of that core are not an update by themselves.
    return up_pre == "" and local_pre != ""
