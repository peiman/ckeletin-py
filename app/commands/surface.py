"""The command surface. The parser and the catalog both read this list."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from framework.config import Settings

from app.commands.hello import run as run_hello
from app.commands.version import run as run_version


@dataclass(frozen=True)
class Flag:
    long: str
    required: bool
    takes_value: bool
    short: str | None = None
    description: str | None = None


@dataclass(frozen=True)
class Command:
    name: str
    description: str
    run: Callable[[Settings], int]
    flags: tuple[Flag, ...] = ()


GLOBAL_FLAGS: tuple[Flag, ...] = (
    Flag("--output", False, True, description="text or json"),
    Flag("--config", False, True, description="project config file"),
)


def command_list() -> tuple[Command, ...]:
    from app.commands.catalog import run as run_catalog
    from app.commands.check import run as run_check
    from app.commands.conform import run as run_conform
    from app.commands.release import run as run_release
    from app.commands.update import run as run_update

    return (
        Command("hello", "Print the configured message", run_hello),
        Command("version", "Print build provenance", run_version),
        Command("catalog", "Print the command surface", run_catalog),
        Command("check", "Run the quality gate", run_check),
        Command("conform", "Show the conformance subject", run_conform),
        Command("release", "Run the release gate", run_release),
        Command(
            "update",
            "Replace the framework tree",
            run_update,
            (
                Flag("--ref", False, True, description="upstream ref"),
                Flag("--upstream", False, True, description="upstream repository"),
                Flag("--dry-run", False, False),
                Flag("--check", False, False, description="apply the candidate, then restore"),
                Flag("--discard", False, False, description="discard a committed local difference"),
            ),
        ),
    )
