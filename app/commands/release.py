"""Release gate. It refuses a reference whose conformance report has drifted."""

from __future__ import annotations

from framework.config import Settings
from framework.output import render
from framework.release import release_gate


def run(settings: Settings, ns=None) -> int:
    code, message = release_gate(settings.root)
    if code != 0:
        return render(
            command="release",
            data=None,
            text="",
            settings=settings,
            error=("release", message),
        )
    return render(command="release", data={"message": message}, text=f"{message}\n", settings=settings)
