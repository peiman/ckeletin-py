"""CHANGELOG.md shape. Dates are ISO. The file is not a git log dump."""

from __future__ import annotations

import re
from pathlib import Path

VERSION_HEADING = re.compile(r"^## \[(\d+\.\d+\.\d+)\] - (\d{4}-\d{2}-\d{2})\s*$")


def find_changelog_violations(root: Path) -> list[str]:
    path = root / "CHANGELOG.md"
    if not path.is_file():
        return ["CHANGELOG.md is missing"]
    text = path.read_text(encoding="utf-8")
    violations: list[str] = []
    if "## [Unreleased]" not in text:
        violations.append("CHANGELOG.md has no [Unreleased] section")
    if "Keep a Changelog" not in text:
        violations.append("CHANGELOG.md does not follow Keep a Changelog")
    if "Semantic Versioning" not in text and "SemVer" not in text:
        violations.append("CHANGELOG.md does not state Semantic Versioning")
    linked = any(line.startswith("[Unreleased]:") and "://" in line for line in text.splitlines())
    if not linked:
        violations.append("CHANGELOG.md has no Unreleased link")
    if re.search(r"(?m)^commit [0-9a-f]{7,40}\b", text):
        violations.append("CHANGELOG.md looks like a raw git log")
    for number, line in enumerate(text.splitlines(), start=1):
        if line.startswith("## [") and not line.startswith("## [Unreleased]"):
            if not VERSION_HEADING.match(line):
                violations.append(f"CHANGELOG.md:{number}: version heading is not ISO 8601")
    return violations
