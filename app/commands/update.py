"""Update command. It replaces the framework tree and leaves application code."""

from __future__ import annotations

from pathlib import Path

from framework.config import Settings
from framework.output import render
from framework.update import perform


def run(settings: Settings, ns=None) -> int:
    upstream = Path(ns.upstream).resolve() if ns is not None and ns.upstream else None
    if upstream is None:
        return render(
            command="update",
            data=None,
            text="",
            settings=settings,
            error=("update", "--upstream is required"),
        )
    result = perform(
        settings.root,
        upstream,
        ref=ns.ref,
        dry_run=bool(ns.dry_run),
        compatibility=bool(ns.check),
        discard=bool(ns.discard),
    )
    return render(command="update", data=result.as_dict(), text=f"{result.message}\n", settings=settings)
