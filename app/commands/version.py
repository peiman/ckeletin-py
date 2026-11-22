"""Version command. Every provenance field is present."""

from __future__ import annotations

from framework.buildinfo import provenance
from framework.config import Settings
from framework.output import render


def run(settings: Settings, ns=None) -> int:
    info = provenance(settings.root)
    text = (
        f"{info['version']}\n"
        f"commit: {info['commit']}\n"
        f"date: {info['date']}\n"
        f"dirty: {info['dirty']}\n"
    )
    return render(command="version", data=info, text=text, settings=settings)
