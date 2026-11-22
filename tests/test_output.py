"""Renderer streams, envelope, and audit order."""

from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from io import StringIO
from pathlib import Path

from framework.config import load
from framework.output import render
from tests.support import ROOT, run


class OutputTest(unittest.TestCase):
    def test_text_success_splits_the_streams(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            out, err = StringIO(), StringIO()
            code = render(
                command="hello",
                data={"message": "hello"},
                text="hello\n",
                settings=load(root),
                out=out,
                err=err,
            )
            self.assertEqual(code, 0)
            self.assertEqual(out.getvalue(), "hello\n")
            self.assertEqual(err.getvalue(), "")
            record = json.loads((root / "logs" / "app.log").read_text(encoding="utf-8"))
        self.assertEqual(record["level"], "info")
        self.assertEqual(record["rendered"], "hello\n")
        self.assertEqual(record["data"], {"message": "hello"})

    def test_json_envelope_keeps_nulls(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            out, err = StringIO(), StringIO()
            render(
                command="hello",
                data={"message": "hello"},
                text="hello\n",
                settings=load(root, output="json"),
                out=out,
                err=err,
            )
            payload = json.loads(out.getvalue())
            self.assertEqual(set(payload), {"command", "data", "error", "status"})
            self.assertIsNone(payload["error"])
            self.assertEqual(err.getvalue(), "")
            out, err = StringIO(), StringIO()
            code = render(
                command="hello",
                data={"message": "hello"},
                text="hello\n",
                settings=load(root, output="json"),
                error=("nope", "bad"),
                out=out,
                err=err,
            )
            payload = json.loads(out.getvalue())
        self.assertEqual(code, 1)
        self.assertIsNone(payload["data"])
        self.assertEqual(payload["error"], {"code": "nope", "message": "bad"})
        self.assertEqual(err.getvalue(), "")

    def test_text_error_uses_stderr(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out, err = StringIO(), StringIO()
            code = render(
                command="hello",
                data={"message": "hello"},
                text="hello\n",
                settings=load(Path(tmp)),
                error=("nope", "bad"),
                out=out,
                err=err,
            )
        self.assertEqual(code, 1)
        self.assertEqual(out.getvalue(), "")
        self.assertEqual(err.getvalue(), "bad\n")

    def test_audit_write_follows_the_user_write(self) -> None:
        events: list[str] = []

        class Out(StringIO):
            def write(self, text: str) -> int:
                events.append("user")
                return super().write(text)

        class Handle(StringIO):
            def write(self, text: str) -> int:
                events.append("log")
                return super().write(text)

        def opener(mode: str, encoding: str = "utf-8") -> Handle:
            return Handle()

        with tempfile.TemporaryDirectory() as tmp:
            render(
                command="hello",
                data={"message": "hello"},
                text="hello\n",
                settings=load(Path(tmp)),
                out=Out(),
                opener=opener,
            )
        self.assertLess(events.index("user"), events.index("log"))

    def test_audit_init_failure_is_an_error(self) -> None:
        def opener(mode: str, encoding: str = "utf-8") -> StringIO:
            raise OSError(13, "Permission denied")

        with tempfile.TemporaryDirectory() as tmp:
            out, err = StringIO(), StringIO()
            code = render(
                command="hello",
                data={"message": "hello"},
                text="hello\n",
                settings=load(Path(tmp)),
                out=out,
                err=err,
                opener=opener,
            )
        self.assertEqual(code, 1)
        self.assertEqual(out.getvalue(), "")
        self.assertIn("audit log", err.getvalue())

    def test_user_write_failure_does_not_log(self) -> None:
        class Boom(StringIO):
            def write(self, text: str) -> int:
                raise OSError("disk")

        written: list[str] = []

        class Handle:
            def write(self, text: str) -> int:
                written.append(text)
                return len(text)

            def close(self) -> None:
                return None

        def opener(mode: str, encoding: str = "utf-8") -> Handle:
            return Handle()

        with tempfile.TemporaryDirectory() as tmp:
            code = render(
                command="hello",
                data={"message": "hello"},
                text="hello\n",
                settings=load(Path(tmp)),
                out=Boom(),
                opener=opener,
            )
        self.assertEqual(code, 1)
        self.assertEqual(written, [])

    def test_flag_beats_config(self) -> None:
        env = os.environ.copy()
        env["PYTHONPATH"] = str(ROOT)
        env["CKELETIN_APP_OUTPUT_FORMAT"] = "json"
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "opt.toml").write_text(
                '[options]\n"app.output_format" = "json"\n',
                encoding="utf-8",
            )
            text = run(
                [sys.executable, "-m", "app", "--output", "text", "--config", "opt.toml", "hello"],
                root,
                env,
            )
            data = run(
                [sys.executable, "-m", "app", "--output", "json", "--config", "opt.toml", "hello"],
                root,
                env,
            )
        self.assertEqual(text.returncode, 0, text.stderr)
        self.assertEqual(text.stdout, "hello\n")
        payload = json.loads(data.stdout)
        self.assertEqual(payload["data"]["message"], "hello")
        self.assertIsNone(payload["error"])


if __name__ == "__main__":
    unittest.main()
