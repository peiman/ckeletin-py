"""Update notice: shown, skipped, and never a failed gate."""

from __future__ import annotations

import subprocess
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path

from app.commands.check import run as run_check
from framework.config import load
from framework.notice import look_for_update
from framework.semver import is_newer
from tests.support import ROOT, copy_project, git_init, temporary_env


def _derived(root: Path, version: str = "0.1.0") -> None:
    (root / "framework").mkdir(parents=True, exist_ok=True)
    (root / "framework" / "VERSION").write_text(version + "\n", encoding="utf-8")
    (root / "ckeletin-project.toml").write_text(
        'role = "derived"\nname = "demo"\n\n[defaults]\n',
        encoding="utf-8",
    )


class NoticeTest(unittest.TestCase):
    def test_disabled(self) -> None:
        with temporary_env(CKELETIN_NO_UPDATE_NOTICE="1"):
            notice = look_for_update(ROOT)
        self.assertEqual(notice.reason, "disabled")
        self.assertFalse(notice.shown)

    def test_ci_skips(self) -> None:
        with temporary_env(CKELETIN_NO_UPDATE_NOTICE=None, CI="true"):
            self.assertEqual(look_for_update(ROOT).reason, "ci")
        with temporary_env(CKELETIN_NO_UPDATE_NOTICE=None, CI=None, GITHUB_ACTIONS="true"):
            self.assertEqual(look_for_update(ROOT).reason, "ci")

    def test_implementation_is_exempt(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            upstream = Path(tmp)
            (upstream / "framework").mkdir()
            (upstream / "framework" / "VERSION").write_text("9.0.0\n", encoding="utf-8")
            notice = look_for_update(ROOT, upstream)
        self.assertEqual(notice.reason, "upstream")
        self.assertFalse(notice.shown)

    def test_offline_is_unavailable(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _derived(root)
            notice = look_for_update(root)
        self.assertEqual(notice.reason, "unavailable")
        self.assertEqual(notice.current, "0.1.0")
        self.assertFalse(notice.shown)

    def test_newer_framework_is_shown(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "proj"
            upstream = Path(tmp) / "up"
            root.mkdir()
            _derived(root, "0.1.0")
            (upstream / "framework").mkdir(parents=True)
            (upstream / "framework" / "VERSION").write_text("0.2.0\n", encoding="utf-8")
            notice = look_for_update(root, upstream)
        self.assertTrue(notice.shown)
        self.assertIn("0.2.0", notice.prose())
        self.assertIn("python -m app update", notice.prose())
        self.assertTrue(notice.as_dict()["update_available"])
        self.assertEqual(notice.as_dict()["command"], "python -m app update")

    def test_prerelease_is_not_newer(self) -> None:
        self.assertTrue(is_newer("1.2.3", "1.2.3-rc.1"))
        self.assertFalse(is_newer("1.2.3-rc.1", "1.2.3"))
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "proj"
            upstream = Path(tmp) / "up"
            root.mkdir()
            _derived(root, "1.2.3")
            (upstream / "framework").mkdir(parents=True)
            (upstream / "framework" / "VERSION").write_text("1.2.3-rc.1\n", encoding="utf-8")
            notice = look_for_update(root, upstream)
        self.assertEqual(notice.reason, "current")
        self.assertFalse(notice.shown)

    def test_two_prereleases_are_not_an_update(self) -> None:
        self.assertFalse(is_newer("1.2.3-rc.2", "1.2.3-rc.1"))
        self.assertFalse(is_newer("1.2.3", "1.2.3"))
        self.assertTrue(is_newer("1.3.0-rc.1", "1.2.9"))

    def test_release_beats_prerelease(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "proj"
            upstream = Path(tmp) / "up"
            root.mkdir()
            _derived(root, "1.2.3-rc.1")
            (upstream / "framework").mkdir(parents=True)
            (upstream / "framework" / "VERSION").write_text("1.2.3\n", encoding="utf-8")
            notice = look_for_update(root, upstream)
        self.assertTrue(notice.shown)
        self.assertEqual(notice.latest, "1.2.3")

    def test_bad_version_is_unavailable(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "proj"
            upstream = Path(tmp) / "up"
            root.mkdir()
            _derived(root, "nope")
            (upstream / "framework").mkdir(parents=True)
            (upstream / "framework" / "VERSION").write_text("1.0.0\n", encoding="utf-8")
            notice = look_for_update(root, upstream)
        self.assertEqual(notice.reason, "unavailable")

    def test_notice_on_stderr_does_not_fail_the_gate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "proj"
            copy_project(dest)
            (dest / "ckeletin-project.toml").write_text(
                'role = "derived"\nname = "demo"\n\n[defaults]\n',
                encoding="utf-8",
            )
            upstream = Path(tmp) / "up"
            (upstream / "framework").mkdir(parents=True)
            (upstream / "framework" / "VERSION").write_text("0.2.0\n", encoding="utf-8")
            git_init(dest)
            subprocess.run(
                ["git", "-C", str(dest), "remote", "add", "origin", str(upstream)],
                check=True,
                capture_output=True,
            )
            out, err = StringIO(), StringIO()
            with temporary_env(CKELETIN_COVERAGE_CHILD="1", CKELETIN_NO_UPDATE_NOTICE=None, CI=None):
                with redirect_stdout(out), redirect_stderr(err):
                    code = run_check(load(dest))
        self.assertEqual(code, 0, err.getvalue())
        self.assertEqual(out.getvalue(), "ok\n")
        self.assertIn("0.2.0", err.getvalue())


if __name__ == "__main__":
    unittest.main()
