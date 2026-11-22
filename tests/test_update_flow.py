"""Framework update: stop, dry run, discard, and restore."""

from __future__ import annotations

import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from framework.update import REWRITTEN_NAMES, perform, replace_framework, tree_diff
from tests.support import commit_all, git_init


def base_pair(tmp: Path) -> tuple[Path, Path]:
    upstream = tmp / "up"
    project = tmp / "proj"
    framework = upstream / "framework"
    framework.mkdir(parents=True)
    (framework / "VERSION").write_text("0.1.0\n", encoding="utf-8")
    (framework / "marker.py").write_text("base\n", encoding="utf-8")
    git_init(upstream)
    commit_all(upstream, "base")
    subprocess.run(["git", "-C", str(upstream), "tag", "v0.1.0"], check=True, capture_output=True)
    shutil.copytree(framework, project / "framework")
    (project / "app").mkdir()
    (project / "app" / "keep.py").write_text("keep\n", encoding="utf-8")
    git_init(project)
    commit_all(project, "project")
    (framework / "VERSION").write_text("0.2.0\n", encoding="utf-8")
    (framework / "marker.py").write_text("new\n", encoding="utf-8")
    commit_all(upstream, "next")
    return project, upstream


class UpdateFlowTest(unittest.TestCase):
    def test_replace_reports_versions(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project, upstream = base_pair(Path(tmp))
            keep = (project / "app" / "keep.py").read_bytes()
            result = perform(project, upstream)
            self.assertTrue(result.kept, result.message)
            self.assertEqual(result.before, "0.1.0")
            self.assertEqual(result.after, "0.2.0")
            self.assertEqual((project / "framework" / "marker.py").read_text(encoding="utf-8"), "new\n")
            self.assertEqual((project / "app" / "keep.py").read_bytes(), keep)

    def test_dry_run_shows_a_difference(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project, upstream = base_pair(Path(tmp))
            (project / "framework" / "marker.py").write_text("local\n", encoding="utf-8")
            commit_all(project, "local")
            before = (project / "framework" / "marker.py").read_bytes()
            result = perform(project, upstream, dry_run=True)
            self.assertFalse(result.stopped, result.message)
            self.assertFalse(result.kept)
            self.assertIn("dry run", result.message)
            self.assertIn("local difference", result.message)
            self.assertIn("marker.py", result.difference)
            self.assertEqual(result.after, "0.2.0")
            self.assertEqual((project / "framework" / "marker.py").read_bytes(), before)

    def test_committed_difference_stops(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project, upstream = base_pair(Path(tmp))
            (project / "framework" / "marker.py").write_text("local\n", encoding="utf-8")
            commit_all(project, "local")
            result = perform(project, upstream)
            self.assertTrue(result.stopped)
            self.assertFalse(result.kept)
            self.assertIn("stopped", result.message)
            self.assertEqual((project / "framework" / "marker.py").read_text(encoding="utf-8"), "local\n")

    def test_discard_says_so(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project, upstream = base_pair(Path(tmp))
            (project / "framework" / "marker.py").write_text("local\n", encoding="utf-8")
            commit_all(project, "local")
            result = perform(project, upstream, discard=True)
            self.assertTrue(result.kept, result.message)
            self.assertTrue(result.discarded)
            self.assertIn("discarded", result.message)
            self.assertEqual((project / "framework" / "marker.py").read_text(encoding="utf-8"), "new\n")

    def test_dirty_tree_is_not_discarded(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project, upstream = base_pair(Path(tmp))
            (project / "framework" / "marker.py").write_text("dirty\n", encoding="utf-8")
            result = perform(project, upstream, discard=True)
            self.assertTrue(result.stopped)
            self.assertIn("uncommitted", result.message)
            self.assertEqual((project / "framework" / "marker.py").read_text(encoding="utf-8"), "dirty\n")

    def test_compatibility_restores_a_difference(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project, upstream = base_pair(Path(tmp))
            (project / "framework" / "marker.py").write_text("local\n", encoding="utf-8")
            commit_all(project, "local")
            result = perform(project, upstream, compatibility=True)
            self.assertFalse(result.kept, result.message)
            self.assertFalse(result.stopped)
            self.assertIn("restored", result.message)
            self.assertIn("local difference restored", result.message)
            self.assertEqual((project / "framework" / "marker.py").read_text(encoding="utf-8"), "local\n")

    def test_missing_recorded_ref_stops(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project, upstream = base_pair(Path(tmp))
            subprocess.run(["git", "-C", str(upstream), "tag", "-d", "v0.1.0"], check=True, capture_output=True)
            result = perform(project, upstream)
            self.assertTrue(result.stopped)
            self.assertFalse(result.kept)
            self.assertEqual((project / "framework" / "marker.py").read_text(encoding="utf-8"), "base\n")

    def test_unreadable_git_status_stops(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project, upstream = base_pair(Path(tmp))
            shutil.rmtree(project / ".git")
            result = perform(project, upstream)
            self.assertIn("cannot read git status", result.message)
            self.assertTrue(result.stopped)

    def test_result_fields(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project, upstream = base_pair(Path(tmp))
            body = perform(project, upstream).as_dict()
        for key in ("before", "after", "kept", "stopped", "discarded", "difference", "message"):
            self.assertIn(key, body)
        self.assertTrue(body["kept"])
        self.assertFalse(body["stopped"])
        self.assertIsNone(body["difference"])

    def test_rewritten_names_are_not_a_difference(self) -> None:
        self.assertEqual(REWRITTEN_NAMES, frozenset())
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            local = root / "local"
            upstream = root / "upstream"
            local.mkdir()
            upstream.mkdir()
            (local / "keep.py").write_text("same", encoding="utf-8")
            (upstream / "keep.py").write_text("same", encoding="utf-8")
            (local / "skip.py").write_text("old", encoding="utf-8")
            (upstream / "skip.py").write_text("new", encoding="utf-8")
            self.assertEqual(tree_diff(local, upstream, ignore=frozenset({"skip.py"})), "")
            self.assertEqual(tree_diff(local, upstream), "skip.py")

    def test_replace_rejects_a_nested_tree(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / "project"
            (project / "framework").mkdir(parents=True)
            (project / "app").mkdir()
            code = replace_framework(project, project / "framework")
        self.assertEqual(code, 1)


if __name__ == "__main__":
    unittest.main()
