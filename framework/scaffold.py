"""Copy a derived project without the reference implementation's own truth."""

from __future__ import annotations

import re
import shutil
from pathlib import Path

SKIP_DIRS = {".git", ".venv", "__pycache__", "logs", "htmlcov"}

FRESH_CHANGELOG = """# Changelog

The format is based on Keep a Changelog, and this project adheres to Semantic Versioning.

## [Unreleased]

- Derived project.

[Unreleased]: https://example.com/compare/unreleased
"""


def classify(relative: str) -> str:
    """framework-owned, consumer-owned, generated-evidence, or upstream-only."""
    rel = relative.replace("\\", "/")
    if rel in {"conformance-report.json", "ENFORCEMENT.md"}:
        return "generated-evidence"
    if rel in {"RESULTS.md", "README.md", "CHANGELOG.md", "AGENTS.md"}:
        return "upstream-only"
    if rel.startswith("framework/"):
        return "framework-owned"
    if rel.startswith("app/") or rel.startswith("tests/") or rel in {
        "ckeletin-project.toml",
        "VERSION",
        "LICENSE",
        "CLAUDE.md",
        ".importlinter",
        ".coveragerc",
        ".gitignore",
        "requirements.txt",
    }:
        return "consumer-owned"
    return "upstream-only"


def _agents(name: str) -> str:
    return f"""# {name}

## Purpose

This is a Python CLI. Application code is `app/`. The framework tree is `framework/` and an update replaces that tree only.

## Directory

- `app/__main__.py` is the entry.
- `app/commands/` is the command layer.
- `app/logic/` is business logic and returns data.
- `framework/` is infrastructure.

## Commands

- Build with `python -m compileall -q app framework`.
- Test with `python -m unittest discover -s tests`.
- Check with `python -m app check`.
- `python -m app update --upstream PATH` replaces `framework/` only.

## Conventions

- Config keys come from `framework/config.py`.
- Business logic does not print.

## Troubleshooting

- `python -m app conform` verifies nothing in a derived project and says so.
- `CKELETIN_NO_UPDATE_NOTICE=1` turns the update notice off. `CI=true` skips it too.
"""


def init_project(source: Path, dest: Path, name: str) -> list[str]:
    """Copy source into dest. Drop reference-only truth and mark the project derived."""
    if not re.fullmatch(r"[A-Za-z0-9._-]+", name):
        raise ValueError("project name must be a single token")
    removed: list[str] = []
    for path in sorted(source.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(source).as_posix()
        if any(part in SKIP_DIRS for part in Path(rel).parts):
            continue
        if classify(rel) in {"upstream-only", "generated-evidence"}:
            removed.append(rel)
            continue
        target = dest / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target)
    (dest / "ckeletin-project.toml").write_text(
        f'role = "derived"\nname = "{name}"\n\n[defaults]\n',
        encoding="utf-8",
    )
    (dest / "AGENTS.md").write_text(_agents(name), encoding="utf-8")
    (dest / "CHANGELOG.md").write_text(FRESH_CHANGELOG, encoding="utf-8")
    (dest / "README.md").write_text(
        f"# {name}\n\nApplication code lives in `app/`. The framework lives in `framework/`.\n",
        encoding="utf-8",
    )
    (dest / "CLAUDE.md").write_text(
        "# Claude Code\n\nProject rules live in [AGENTS.md](AGENTS.md).\n",
        encoding="utf-8",
    )
    return removed
