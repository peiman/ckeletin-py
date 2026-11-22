"""AGENTS.md is the universal guide and does not carry provider instructions."""

from __future__ import annotations

import re
from pathlib import Path

PROVIDERS = ("Claude", "Gemini", "Copilot", "ChatGPT", "Anthropic", "OpenAI", "Cursor")
CROSS_REFERENCE = re.compile(r"CLAUDE\.md|GEMINI\.md|\.cursorrules|copilot-instructions\.md", re.I)


def find_agent_violations(root: Path) -> list[str]:
    path = root / "AGENTS.md"
    violations: list[str] = []
    if not path.is_file():
        return ["AGENTS.md is missing"]
    text = path.read_text(encoding="utf-8")
    for label in ("Purpose", "Directory", "Commands", "Conventions", "Troubleshoot"):
        if label.lower() not in text.lower():
            violations.append(f"AGENTS.md is missing a {label} section")
    for number, line in enumerate(text.splitlines(), start=1):
        if CROSS_REFERENCE.search(line):
            continue
        for provider in PROVIDERS:
            if provider.lower() in line.lower():
                violations.append(f"AGENTS.md:{number}: provider instruction mentions {provider}")
                break
    claude = root / "CLAUDE.md"
    if claude.is_file() and "AGENTS.md" not in claude.read_text(encoding="utf-8"):
        violations.append("CLAUDE.md does not reference AGENTS.md")
    return violations
