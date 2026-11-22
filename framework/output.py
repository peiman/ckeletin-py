"""Three streams: data on stdout, status on stderr, audit in the log file.

The user-facing write happens before the shadow-log write. Opening the log
file is initialization: if that fails, the command returns an error and does
not claim success.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import IO, TextIO

from framework.config import KEY_APP_LOG_FILE, KEY_APP_OUTPUT_FORMAT, Settings


def write_status(text: str, err: TextIO | None = None) -> None:
    """Status text belongs on stderr. Commands use this instead of writing the stream."""
    (sys.stderr if err is None else err).write(text)


def _envelope(command: str, data, error: dict | None) -> dict:
    return {
        "status": "error" if error else "success",
        "command": command,
        "data": None if error else data,
        "error": error,
    }


def _write_user(text: str, blob: dict, settings: Settings, out: TextIO, err: TextIO) -> None:
    if settings.value(KEY_APP_OUTPUT_FORMAT) == "json":
        out.write(json.dumps(blob, sort_keys=True) + "\n")
        return
    if blob["status"] == "error":
        message = blob["error"]["message"]
        err.write(f"{message}\n")
        return
    out.write(text)


def render(
    *,
    command: str,
    data,
    text: str,
    settings: Settings,
    error: tuple[str, str] | None = None,
    out: TextIO | None = None,
    err: TextIO | None = None,
    opener=None,
) -> int:
    out = sys.stdout if out is None else out
    err = sys.stderr if err is None else err
    log_path = settings.root / settings.value(KEY_APP_LOG_FILE)
    try:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        handle: IO[str] = (opener or log_path.open)("a", encoding="utf-8")
    except OSError as exc:
        failure = {"code": "audit_log", "message": f"audit log: {exc.strerror or exc}"}
        blob = _envelope(command, None, failure)
        _write_user("", blob, settings, out, err)
        return 1

    err_obj = None if error is None else {"code": error[0], "message": error[1]}
    blob = _envelope(command, data, err_obj)
    try:
        _write_user(text, blob, settings, out, err)
    except OSError:
        handle.close()
        return 1
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "command": command,
        "level": "error" if err_obj else "info",
        "data": blob["data"],
        "rendered": text if err_obj is None else err_obj["message"],
    }
    handle.write(json.dumps(record, sort_keys=True) + "\n")
    handle.close()
    return 0 if err_obj is None else 1
