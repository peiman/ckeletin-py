"""Tests inject dependencies. A mock-generation framework is a violation."""

from __future__ import annotations

import ast
from pathlib import Path

from framework.walk import python_files

FORBIDDEN_MODULES = ("unittest.mock", "pytest_mock")


def find_mock_violations(root: Path) -> list[str]:
    violations: list[str] = []
    for path in python_files(root, "tests"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        rel = path.relative_to(root).as_posix()
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module in FORBIDDEN_MODULES:
                violations.append(f"{rel}:{node.lineno}: mock framework import")
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name in FORBIDDEN_MODULES:
                        violations.append(f"{rel}:{node.lineno}: mock framework import")
    return violations
