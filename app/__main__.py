"""Entry point. It calls the command layer and does not import argparse."""

from app.commands.hello import run


def main() -> int:
    return run()


if __name__ == "__main__":
    raise SystemExit(main())
