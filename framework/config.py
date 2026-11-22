"""The only config registry. Call sites pass these names, not string literals."""

from __future__ import annotations

import os
import tomllib
from dataclasses import dataclass
from pathlib import Path

KEY_APP_MESSAGE = "app.message"
KEY_APP_OUTPUT_FORMAT = "app.output_format"
KEY_APP_LOG_FILE = "app.log_file"

REGISTRY: dict[str, str] = {
    KEY_APP_MESSAGE: "hello",
    KEY_APP_OUTPUT_FORMAT: "text",
    KEY_APP_LOG_FILE: "logs/app.log",
}

ENV_PREFIX = "CKELETIN_"


def get(key: str) -> str:
    """Return the framework default. Unknown names fail."""
    try:
        return REGISTRY[key]
    except KeyError:
        raise KeyError(f"unknown config key: {key}") from None


def _env_name(key: str) -> str:
    return ENV_PREFIX + key.upper().replace(".", "_")


def _flatten(raw: dict, path: Path, table: str) -> dict[str, object]:
    """Accept a quoted key or a single dotted key. TOML nests the dotted form."""
    flat: dict[str, object] = {}
    for key, value in raw.items():
        if isinstance(value, dict):
            for child, inner in value.items():
                if isinstance(inner, dict):
                    raise KeyError(f"{path}: [{table}] values must be scalars")
                flat[f"{key}.{child}"] = inner
            continue
        flat[str(key)] = value
    return flat


def _table(path: Path, table: str) -> dict[str, str]:
    if not path.is_file():
        return {}
    loaded = tomllib.loads(path.read_text(encoding="utf-8"))
    raw = loaded.get(table, {})
    if not isinstance(raw, dict):
        raise KeyError(f"{path}: [{table}] must be a table")
    flat = _flatten(raw, path, table)
    unknown = sorted(set(flat) - set(REGISTRY))
    if unknown:
        raise KeyError(f"unknown config key: {unknown[0]}")
    return {str(key): str(value) for key, value in flat.items()}


@dataclass(frozen=True)
class Settings:
    root: Path
    values: dict[str, str]

    def value(self, key: str) -> str:
        if key not in REGISTRY:
            raise KeyError(f"unknown config key: {key}")
        return self.values[key]


def load(root: Path, *, output: str | None = None, config_path: Path | None = None) -> Settings:
    """flag > environment > project config file > project default > framework default."""
    root = root.resolve()
    values = dict(REGISTRY)
    values.update(_table(root / "ckeletin-project.toml", "defaults"))
    if config_path is not None:
        values.update(_table(Path(config_path), "options"))
    for key in REGISTRY:
        env = os.environ.get(_env_name(key))
        if env is not None:
            values[key] = env
    if output is not None:
        values[KEY_APP_OUTPUT_FORMAT] = output
    return Settings(root=root, values=values)
