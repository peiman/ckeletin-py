"""Layer checks: designated directories, import contracts, and no direct writes."""

from __future__ import annotations

import ast
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from framework.walk import python_files

ALLOWED_APP_PACKAGES = {"commands", "logic", "public"}
_SKIP = {"__pycache__", ".git", ".venv", "logs", "htmlcov"}


def _lint_bin() -> str | None:
    # Do not resolve the interpreter: a venv python is often a symlink into
    # Homebrew, and the console script lives next to the symlink.
    for parent in (Path(sys.executable).parent, Path(sys.executable).resolve().parent):
        candidate = parent / "lint-imports"
        if candidate.is_file():
            return str(candidate)
    return shutil.which("lint-imports")


def root_python_files(root: Path) -> list[str]:
    violations = []
    for path in sorted(root.glob("*.py")):
        violations.append(f"{path.name}: source file is outside a layer directory")
    return violations


def layers_present(root: Path) -> list[str]:
    """Entry, command, and infrastructure must exist. Logic and public may be empty."""
    missing = []
    if not (root / "app" / "__main__.py").is_file():
        missing.append("app/__main__.py: entry layer is missing")
    if not (root / "app" / "commands").is_dir():
        missing.append("app/commands: command layer is missing")
    if not (root / "framework").is_dir():
        missing.append("framework: infrastructure layer is missing")
    return missing


def stray_packages(root: Path) -> list[str]:
    """Business logic is one package, app.logic. A sibling package is rejected."""
    app = root / "app"
    if not app.is_dir():
        return ["app: application tree is missing"]
    violations = []
    for path in sorted(app.iterdir()):
        if not path.is_dir() or path.name in _SKIP:
            continue
        if path.name not in ALLOWED_APP_PACKAGES:
            violations.append(f"app/{path.name}: package is outside the designated layers")
    return violations


def entry_is_bootstrap(root: Path) -> list[str]:
    path = root / "app" / "__main__.py"
    if not path.is_file():
        return ["app/__main__.py: entry is missing"]
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in tree.body:
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant):
            continue
        if isinstance(node, ast.ImportFrom):
            if node.module != "app.commands.dispatch":
                return [f"app/__main__.py:{node.lineno}: entry imports {node.module}"]
            continue
        if isinstance(node, ast.FunctionDef) and node.name == "entry":
            continue
        if isinstance(node, ast.If):
            continue
        return [f"app/__main__.py:{getattr(node, 'lineno', 1)}: entry is not bootstrap"]
    return []


def _writes_stream(node: ast.Call) -> bool:
    func = node.func
    if isinstance(func, ast.Name) and func.id == "print":
        return True
    if not isinstance(func, ast.Attribute) or func.attr not in {"write", "writelines"}:
        return False
    value = func.value
    if isinstance(value, ast.Name) and value.id in {"stdout", "stderr"}:
        return True
    return isinstance(value, ast.Attribute) and value.attr in {"stdout", "stderr"}


def direct_writes(root: Path) -> list[str]:
    violations = []
    files = python_files(root, "app/logic", "app/public", "app/commands")
    entry = root / "app" / "__main__.py"
    if entry.is_file():
        files.append(entry)
    for path in files:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        rel = path.relative_to(root).as_posix()
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and _writes_stream(node):
                violations.append(f"{rel}:{node.lineno}: layer writes a stream directly")
    return violations


def logic_prints(root: Path) -> list[str]:
    """Kept for the business-logic half of the stream rule."""
    return [item for item in direct_writes(root) if item.startswith("app/logic/")]


def _has_nested_repo(root: Path) -> bool:
    for name in ("app", "framework"):
        base = root / name
        if not base.is_dir():
            continue
        for git in base.rglob(".git"):
            if git.parent != root:
                return True
    return False


def _copy_without_nested(root: Path) -> Path:
    dest = Path(tempfile.mkdtemp(prefix="ckeletin-lint-"))

    def ignore(directory: str, names: list[str]) -> list[str]:
        skipped = []
        for name in names:
            if name in _SKIP or (Path(directory) / name / ".git").exists():
                skipped.append(name)
        return skipped

    for item in (".importlinter", "app", "framework"):
        src = root / item
        if not src.exists():
            continue
        target = dest / item
        if src.is_dir():
            shutil.copytree(src, target, ignore=ignore)
        else:
            shutil.copy2(src, target)
    return dest


def import_contracts(root: Path) -> list[str]:
    binary = _lint_bin()
    if binary is None:
        return ["lint-imports is not installed"]
    target = root
    cleanup: Path | None = None
    if _has_nested_repo(root):
        target = _copy_without_nested(root)
        cleanup = target
    try:
        result = subprocess.run(
            [binary],
            cwd=target,
            capture_output=True,
            text=True,
            check=False,
        )
    finally:
        if cleanup is not None:
            shutil.rmtree(cleanup, ignore_errors=True)
    if result.returncode == 0:
        return []
    return [result.stdout.strip() or result.stderr.strip() or "import contract broken"]


def find_layer_violations(root: Path) -> list[str]:
    return (
        layers_present(root)
        + root_python_files(root)
        + stray_packages(root)
        + entry_is_bootstrap(root)
        + direct_writes(root)
        + import_contracts(root)
    )
