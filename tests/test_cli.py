"""Drive the command layer in process so the gate can see it."""

from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from contextlib import chdir, redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path

from app.__main__ import entry
from app.commands.catalog import _flag
from app.commands.dispatch import main
from app.commands.surface import Flag
from app.public.api import surface
from framework.conform import main as conform_main
from framework.notice import Notice, look_for_update, upstream_version
from framework.release import main as release_main
from framework.update import main as update_main
from framework.update import perform, replace_framework
from tests.support import ROOT, commit_all, git_init, temporary_env


class InProcessCliTest(unittest.TestCase):
    def test_commands_run(self) -> None:
        out, err = StringIO(), StringIO()
        with temporary_env(CKELETIN_COVERAGE_CHILD="1"):
            with chdir(ROOT), redirect_stdout(out), redirect_stderr(err):
                self.assertEqual(main([]), 0)
                self.assertEqual(main(["version"]), 0)
                self.assertEqual(main(["catalog"]), 0)
                self.assertEqual(main(["--output", "json", "hello"]), 0)
                self.assertEqual(main(["conform"]), 0)
                self.assertEqual(main(["release"]), 0)
                self.assertEqual(main(["check"]), 0)
                self.assertEqual(main(["update"]), 1)
                self.assertEqual(conform_main([]), 0)
                self.assertEqual(release_main([]), 0)
                self.assertEqual(conform_main(["--write"]), 0)
        self.assertIn("hello", out.getvalue())

    def test_usage_error_exits_before_a_command(self) -> None:
        with redirect_stderr(StringIO()):
            with self.assertRaises(SystemExit):
                main(["--output", "json"])

    def test_bad_config_exits(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "ckeletin-project.toml").write_text("defaults = [\n", encoding="utf-8")
            err = StringIO()
            with chdir(root), redirect_stderr(err):
                code = main(["hello"])
        self.assertEqual(code, 2)
        self.assertTrue(err.getvalue())

    def test_entry_calls_the_command(self) -> None:
        old = sys.argv
        sys.argv = ["app", "hello"]
        try:
            with tempfile.TemporaryDirectory() as tmp:
                with chdir(tmp), redirect_stdout(StringIO()), redirect_stderr(StringIO()):
                    self.assertEqual(entry(), 0)
        finally:
            sys.argv = old

    def test_public_surface_and_short_flag(self) -> None:
        self.assertEqual(surface(), "ckeletin-py")
        payload = _flag(Flag("--output", False, True, short="-o", description="text or json"))
        self.assertEqual(payload["short"], "-o")

    def test_hidden_notice_has_no_prose(self) -> None:
        self.assertEqual(Notice(False, "disabled").prose(), "")

    def test_broken_project_file_does_not_crash_the_notice(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "ckeletin-project.toml").write_text("role = [\n", encoding="utf-8")
            notice = look_for_update(root)
        self.assertEqual(notice.reason, "unavailable")

    def test_fetch_reads_a_bare_remote(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            origin = root / "origin"
            bare = root / "bare.git"
            project = root / "proj"
            (origin / "framework").mkdir(parents=True)
            (origin / "framework" / "VERSION").write_text("0.4.0\n", encoding="utf-8")
            git_init(origin)
            commit_all(origin, "version")
            subprocess.run(
                ["git", "clone", "--bare", str(origin), str(bare)],
                check=True,
                capture_output=True,
            )
            project.mkdir()
            git_init(project)
            subprocess.run(
                ["git", "-C", str(project), "remote", "add", "origin", str(bare)],
                check=True,
                capture_output=True,
            )
            self.assertEqual(upstream_version(project), "0.4.0")

    def test_missing_framework_stops(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = perform(Path(tmp) / "missing", Path(tmp) / "upstream")
        self.assertIn("framework tree is missing", result.message)
        self.assertTrue(result.stopped)

    def test_module_main_usage_and_replace(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            project = root / "project"
            upstream = root / "upstream"
            (project / "framework").mkdir(parents=True)
            (project / "app").mkdir()
            (project / "app" / "keep.py").write_text("keep\n", encoding="utf-8")
            (project / "framework" / "marker.py").write_text("old\n", encoding="utf-8")
            upstream.mkdir()
            (upstream / "marker.py").write_text("new\n", encoding="utf-8")
            err = StringIO()
            with redirect_stderr(err), redirect_stdout(StringIO()):
                self.assertEqual(update_main([]), 2)
                self.assertEqual(update_main([str(project), str(upstream)]), 0)
                self.assertEqual(replace_framework(project, root / "absent"), 1)
        self.assertIn("usage", err.getvalue())


if __name__ == "__main__":
    unittest.main()
