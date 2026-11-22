"""Walk a project's own sources. Nested checkouts are not part of the project."""

from __future__ import annotations

from pathlib import Path


def _inside_nested(path: Path, root: Path) -> bool:
    """True when a parent between the file and the walk root is its own checkout."""
    for parent in path.parents:
        if parent == root:
            return False
        if (parent / ".git").exists():
            return True
    return False


def python_files(root: Path, *relative: str) -> list[Path]:
    """Python files under the named directories, skipping nested repositories."""
    resolved = root.resolve()
    found: list[Path] = []
    for name in relative:
        base = root / name
        if not base.exists():
            continue
        for path in sorted(base.rglob("*.py")):
            if _inside_nested(path.resolve(), resolved):
                continue
            if "__pycache__" in path.parts:
                continue
            found.append(path)
    return found
