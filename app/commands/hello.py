"""Hello command. argparse stays in this module."""

from __future__ import annotations

import argparse

from app.private.greeting import greet
from framework.config import KEY_APP_MESSAGE, get


def run(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="ckeletin-python")
    parser.parse_args(argv)
    print(greet(get(KEY_APP_MESSAGE)))
    return 0
