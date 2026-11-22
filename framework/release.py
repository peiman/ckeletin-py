"""Release gate. The subject of a green result is part of the result."""

from __future__ import annotations

import sys
import tomllib
from pathlib import Path

from framework.conform import run_conform
from framework.project import REFERENCE_NAME, is_reference, read_identity


def release_gate(root: Path) -> tuple[int, str]:
    try:
        identity = read_identity(root)
    except (OSError, tomllib.TOMLDecodeError) as exc:
        return 0, f"release subject: unknown; verified nothing; {exc}"
    name = identity.name or "unknown"
    if not is_reference(root):
        return 0, (
            f"release subject: {name}; verified nothing; "
            f"this repository is not the {REFERENCE_NAME} implementation"
        )
    code, message = run_conform(root)
    if code != 0:
        return code, f"release subject: {name}; refused: {message}"
    return 0, f"release subject: {name}; conform passed"


def main(argv: list[str] | None = None) -> int:
    code, message = release_gate(Path.cwd())
    print(message)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
