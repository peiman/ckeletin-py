"""Parse argv and call the command. argparse stays in this module."""

from __future__ import annotations

import argparse
import sys
import tomllib
from pathlib import Path

from framework.config import load
from framework.project import REFERENCE_NAME
from framework.output import write_status

from app.commands.surface import command_list


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    parser = argparse.ArgumentParser(prog=REFERENCE_NAME)
    parser.add_argument("--output", choices=("text", "json"))
    parser.add_argument("--config")
    sub = parser.add_subparsers(dest="command")
    commands = command_list()
    for command in commands:
        command_parser = sub.add_parser(command.name, help=command.description)
        for flag in command.flags:
            dest = flag.long.lstrip("-").replace("-", "_")
            if flag.takes_value:
                command_parser.add_argument(flag.long, dest=dest, required=flag.required)
            else:
                command_parser.add_argument(flag.long, dest=dest, action="store_true")
    if not argv:
        argv = ["hello"]
    namespace = parser.parse_args(argv)
    if namespace.command is None:
        parser.error("a command is required")
    config_path = Path(namespace.config) if namespace.config else None
    try:
        settings = load(Path.cwd(), output=namespace.output, config_path=config_path)
    except (KeyError, tomllib.TOMLDecodeError) as exc:
        message = exc.args[0] if exc.args else "invalid configuration"
        write_status(f"{message}\n")
        return 2
    chosen = next(command for command in commands if command.name == namespace.command)
    return chosen.run(settings, namespace)
