"""Conformance subject. A derived project is told that nothing was verified."""

from __future__ import annotations

from framework.config import Settings
from framework.conform import run_conform
from framework.output import render


def run(settings: Settings, ns=None) -> int:
    code, message = run_conform(settings.root)
    if code != 0:
        return render(
            command="conform",
            data=None,
            text="",
            settings=settings,
            error=("conform", message),
        )
    return render(command="conform", data={"message": message}, text=f"{message}\n", settings=settings)
