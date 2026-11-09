"""The only config registry. Call sites use these names, not string literals."""

from __future__ import annotations

KEY_APP_MESSAGE = "app.message"

REGISTRY: dict[str, str] = {
    KEY_APP_MESSAGE: "hello",
}


def get(key: str) -> str:
    try:
        return REGISTRY[key]
    except KeyError:
        raise KeyError(f"unknown config key: {key}") from None
