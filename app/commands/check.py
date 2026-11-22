"""Quality gate. An available framework update is reported and does not fail it."""

from __future__ import annotations

from framework.checks.gate import gate_result
from framework.config import KEY_APP_OUTPUT_FORMAT, Settings
from framework.notice import look_for_update
from framework.output import render, write_status


def _status(settings: Settings, notice) -> None:
    if notice.shown and settings.value(KEY_APP_OUTPUT_FORMAT) == "text":
        write_status(notice.prose() + "\n")


def run(settings: Settings, ns=None) -> int:
    code, failures = gate_result(settings.root)
    notice = look_for_update(settings.root)
    data = {"ok": code == 0, "failures": failures, "framework_update": notice.as_dict()}
    if code != 0:
        message = "\n".join(failures)
        if notice.shown and settings.value(KEY_APP_OUTPUT_FORMAT) == "json":
            message = f"{message}\n{notice.prose()}" if message else notice.prose()
        rendered = render(
            command="check",
            data=data,
            text="",
            settings=settings,
            error=("check", message),
        )
        _status(settings, notice)
        return 1 if rendered == 0 else rendered
    rendered = render(command="check", data=data, text="ok\n", settings=settings)
    _status(settings, notice)
    return rendered
