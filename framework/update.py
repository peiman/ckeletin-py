"""Replace the framework tree. Application files stay byte for byte."""

from __future__ import annotations

import shutil
import sys
from pathlib import Path


def _files(root: Path) -> dict[str, bytes]:
    if not root.is_dir():
        return {}
    found: dict[str, bytes] = {}
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if "__pycache__" in path.parts or path.suffix == ".pyc":
            continue
        found[path.relative_to(root).as_posix()] = path.read_bytes()
    return found


def replace_framework(project: Path, upstream: Path) -> int:
    project = project.resolve()
    upstream = upstream.resolve()
    dest = project / "framework"
    app = project / "app"
    if not dest.is_dir():
        print("framework tree is missing", file=sys.stderr)
        return 1
    if not upstream.is_dir():
        print("upstream framework is missing", file=sys.stderr)
        return 1
    if dest == upstream or dest in upstream.parents or upstream in dest.parents:
        print("upstream must be a separate framework tree", file=sys.stderr)
        return 1
    if app == upstream or app in upstream.parents or upstream in app.parents:
        print("upstream must be a separate framework tree", file=sys.stderr)
        return 1

    before = _files(app)
    tmp = project / ".framework-next"
    backup = project / ".framework-old"
    if tmp.exists():
        shutil.rmtree(tmp)
    try:
        shutil.copytree(
            upstream,
            tmp,
            symlinks=False,
            ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
        )
        if backup.exists():
            shutil.rmtree(backup)
        dest.rename(backup)
        try:
            tmp.rename(dest)
        except Exception:
            backup.rename(dest)
            raise
        shutil.rmtree(backup)
    finally:
        if tmp.exists():
            shutil.rmtree(tmp)

    after = _files(app)
    if before != after:
        print("update changed application files", file=sys.stderr)
        return 1
    print(f"framework replaced; application files unchanged: {len(before)}")
    return 0


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if len(args) != 2:
        print("usage: python -m framework.update PROJECT UPSTREAM", file=sys.stderr)
        return 2
    return replace_framework(Path(args[0]), Path(args[1]))


if __name__ == "__main__":
    raise SystemExit(main())
