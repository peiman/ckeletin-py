"""Catalog derived from the command list the parser uses."""

from __future__ import annotations

from framework.config import Settings
from framework.project import REFERENCE_NAME
from framework.output import render

from app.commands.surface import GLOBAL_FLAGS, Command, Flag, command_list


def _flag(flag: Flag) -> dict:
    payload = {
        "long": flag.long.lstrip("-"),
        "required": flag.required,
        "takes_value": flag.takes_value,
    }
    if flag.short:
        payload["short"] = flag.short
    if flag.description:
        payload["description"] = flag.description
    return payload


def _command(command: Command) -> dict:
    return {
        "name": command.name,
        "description": command.description,
        "flags": [_flag(flag) for flag in command.flags],
        "commands": [],
    }


def payload() -> dict:
    return {
        "name": REFERENCE_NAME,
        "description": "A ckeletin CLI.",
        "global_flags": [_flag(flag) for flag in GLOBAL_FLAGS],
        "commands": [_command(command) for command in command_list()],
    }


def run(settings: Settings, ns=None) -> int:
    body = payload()
    names = ", ".join(command["name"] for command in body["commands"])
    return render(command="catalog", data=body, text=f"{names}\n", settings=settings)
