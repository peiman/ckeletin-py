"""Measure run* functions from the def line through the last line of the body.

The hard fail is 35 lines, the same hard fail Go uses for run* functions.
The number is this probe's choice. It is not a spec requirement.
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

LIMIT = 35


def span(node: ast.FunctionDef | ast.AsyncFunctionDef) -> int:
    start = node.lineno
    if node.decorator_list:
        last = node.decorator_list[-1]
        start = (last.end_lineno or last.lineno) + 1
    end = node.end_lineno or start
    return end - start + 1


def find_fat_commands(root: Path) -> list[str]:
    commands = root / "app" / "commands"
    if not commands.is_dir():
        return [f"{commands}: command layer is missing"]
    violations: list[str] = []
    for path in sorted(commands.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        rel = path.relative_to(root).as_posix()
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            if not node.name.startswith("run"):
                continue
            lines = span(node)
            if lines > LIMIT:
                violations.append(
                    f"{rel}:{node.lineno}: {node.name} is {lines} lines (limit {LIMIT})"
                )
    return violations


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    root = Path(args[0]) if args else Path(".")
    violations = find_fat_commands(root)
    for item in violations:
        print(item)
    return 1 if violations else 0


if __name__ == "__main__":
    raise SystemExit(main())
