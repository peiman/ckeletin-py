"""Call sites pass registry names to get(). A raw string is a violation."""

from __future__ import annotations

import ast
import sys
from pathlib import Path

from framework.walk import python_files


def find_raw_config_gets(root: Path) -> list[str]:
    root = root.resolve()
    app = root / "app"
    if not app.is_dir():
        return [f"{app}: application tree is missing"]
    violations: list[str] = []
    for path in python_files(root, "app"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        rel = path.relative_to(root).as_posix()
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id.startswith("KEY_"):
                        violations.append(
                            f"{rel}:{node.lineno}: config key {target.id} is defined outside the registry"
                        )
            if not isinstance(node, ast.Call):
                continue
            if not isinstance(node.func, ast.Name) or node.func.id != "get":
                continue
            if not node.args:
                continue
            arg = node.args[0]
            if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                violations.append(
                    f"{rel}:{arg.lineno}: config get uses a raw string {arg.value!r}"
                )
    return violations


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    root = Path(args[0]) if args else Path(".")
    violations = find_raw_config_gets(root)
    for item in violations:
        print(item)
    return 1 if violations else 0


if __name__ == "__main__":
    raise SystemExit(main())
