"""Entry point. It calls the command layer and does not import argparse."""

from app.commands.dispatch import main


def entry() -> int:
    return main()


if __name__ == "__main__":
    raise SystemExit(entry())
