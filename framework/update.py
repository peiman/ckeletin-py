"""Replace the framework tree. Application files stay byte for byte.

The names in REWRITTEN_NAMES are rewritten so the tree belongs to the derived
project. They are not a local difference. The set is empty: this framework
does not rewrite paths.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

REWRITTEN_NAMES: frozenset[str] = frozenset()


def _files(root: Path) -> dict[str, bytes]:
    if not root.is_dir():
        return {}
    found: dict[str, bytes] = {}
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if "__pycache__" in path.parts or path.suffix == ".pyc":
            continue
        if ".git" in path.parts:
            continue
        found[path.relative_to(root).as_posix()] = path.read_bytes()
    return found


def replace_framework(project: Path, upstream: Path, *, quiet: bool = False) -> int:
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
    if not quiet:
        print(f"framework replaced; application files unchanged: {len(before)}")
    return 0


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=True,
        text=True,
        check=False,
    )


def framework_status(project: Path) -> str | None:
    """Porcelain status, or None when git cannot be read."""
    result = _git(project, "status", "--porcelain", "--", "framework")
    if result.returncode != 0:
        return None
    return result.stdout


def tree_diff(local: Path, upstream: Path, ignore: frozenset[str] = REWRITTEN_NAMES) -> str:
    local_files = _files(local)
    upstream_files = _files(upstream)
    lines: list[str] = []
    names = sorted(set(local_files) | set(upstream_files))
    for name in names:
        if name in ignore:
            continue
        if local_files.get(name) != upstream_files.get(name):
            lines.append(name)
    return "\n".join(lines)


def _version_of(tree: Path) -> str:
    path = tree / "VERSION"
    if not path.is_file():
        return "unknown"
    return path.read_text(encoding="utf-8").strip() or "unknown"


def _default_ref(upstream_repo: Path) -> str:
    for candidate in ("main", "master"):
        found = _git(upstream_repo, "rev-parse", "--verify", "--quiet", candidate)
        if found.returncode == 0:
            return candidate
    return "HEAD"


def _extract(repo: Path, ref: str, dest: Path) -> str | None:
    raw = subprocess.run(
        ["git", "-C", str(repo), "archive", ref, "framework"],
        capture_output=True,
        check=False,
    )
    if raw.returncode != 0:
        return raw.stderr.decode(errors="replace").strip() or f"cannot read {ref}"
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True)
    untar = subprocess.run(
        ["tar", "-x", "-C", str(dest)],
        input=raw.stdout,
        capture_output=True,
        check=False,
    )
    if untar.returncode != 0 or not (dest / "framework").is_dir():
        shutil.rmtree(dest, ignore_errors=True)
        return "upstream framework tree is missing"
    return None


@dataclass(frozen=True)
class UpdateResult:
    before: str
    after: str
    kept: bool
    stopped: bool
    discarded: bool
    difference: str
    message: str

    def as_dict(self) -> dict:
        return {
            "before": self.before,
            "after": self.after,
            "kept": self.kept,
            "stopped": self.stopped,
            "discarded": self.discarded,
            "difference": self.difference or None,
            "message": self.message,
        }


def perform(
    project: Path,
    upstream_repo: Path,
    *,
    ref: str | None = None,
    dry_run: bool = False,
    compatibility: bool = False,
    discard: bool = False,
    recorded_ref: str | None = None,
) -> UpdateResult:
    """Compare, then replace only framework/. Application bytes are checked."""
    project = project.resolve()
    upstream_repo = upstream_repo.resolve()
    local = project / "framework"
    before = _version_of(local)
    if not local.is_dir():
        return UpdateResult(before, before, False, True, False, "", "framework tree is missing")

    target = ref or _default_ref(upstream_repo)
    recorded = recorded_ref or f"v{before}"
    baseline_dir = project / ".framework-baseline"
    error = _extract(upstream_repo, recorded, baseline_dir)
    if error is not None:
        if baseline_dir.exists():
            shutil.rmtree(baseline_dir)
        return UpdateResult(before, before, False, True, False, "", error)
    difference = tree_diff(local, baseline_dir / "framework")
    shutil.rmtree(baseline_dir)

    dirty = framework_status(project)
    if dirty is None:
        return UpdateResult(before, before, False, True, False, difference, "cannot read git status")
    if dirty.strip():
        shown = dirty.strip()
        if difference:
            shown = f"{shown}\n{difference}"
        return UpdateResult(
            before, before, False, True, False, shown, "stopped: uncommitted framework changes"
        )

    # A committed difference stops a replacement. A dry run reports it and
    # changes nothing. A compatibility check applies the candidate and then
    # restores the tree, including that difference.
    if difference and not discard and not dry_run and not compatibility:
        return UpdateResult(
            before,
            before,
            False,
            True,
            False,
            difference,
            "stopped: committed local framework difference",
        )

    candidate_dir = project / ".framework-candidate"
    extract_error = _extract(upstream_repo, target, candidate_dir)
    if extract_error is not None:
        if candidate_dir.exists():
            shutil.rmtree(candidate_dir)
        return UpdateResult(before, before, False, True, False, difference, extract_error)
    candidate = candidate_dir / "framework"
    after = _version_of(candidate)

    if dry_run:
        shutil.rmtree(candidate_dir)
        message = f"dry run: {before} -> {after}; nothing replaced"
        if difference:
            message += "; local difference"
        return UpdateResult(before, after, False, False, False, difference, message)

    snapshot = _files(local)
    code = replace_framework(project, candidate, quiet=True)
    shutil.rmtree(candidate_dir, ignore_errors=True)
    if code != 0:
        return UpdateResult(before, before, False, True, False, difference, "framework replace failed")

    if compatibility:
        _restore(local, snapshot)
        message = f"compatibility check: {before} -> {after}; framework tree restored"
        if difference:
            message += "; local difference restored"
        return UpdateResult(before, after, False, False, False, difference, message)

    message = f"framework replaced: {before} -> {after}"
    discarded = bool(difference and discard)
    if discarded:
        message += "; discarded a committed local difference"
    return UpdateResult(before, after, True, False, discarded, difference, message)


def _restore(dest: Path, snapshot: dict[str, bytes]) -> None:
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir()
    for name, payload in snapshot.items():
        path = dest / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if len(args) != 2:
        print("usage: python -m framework.update PROJECT UPSTREAM", file=sys.stderr)
        return 2
    return replace_framework(Path(args[0]), Path(args[1]))


if __name__ == "__main__":
    raise SystemExit(main())
