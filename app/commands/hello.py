"""Hello command."""

from __future__ import annotations

from framework.config import KEY_APP_MESSAGE, Settings
from framework.output import render

from app.logic.greeting import greet


def run(settings: Settings, ns=None) -> int:
    message = greet(settings.value(KEY_APP_MESSAGE))
    return render(command="hello", data={"message": message}, text=f"{message}\n", settings=settings)
