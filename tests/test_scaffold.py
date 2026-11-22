"""Scaffold init drops the reference project's own conformance truth."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from framework.checks.agents import find_agent_violations
from framework.checks.changelog import find_changelog_violations
from framework.conform import run_conform
from framework.release import release_gate
from framework.scaffold import classify, init_project
from tests.support import ROOT


class ScaffoldTest(unittest.TestCase):
    def test_classification_uses_four_owners(self) -> None:
        self.assertEqual(classify("framework/config.py"), "framework-owned")
        self.assertEqual(classify("app/logic/greeting.py"), "consumer-owned")
        self.assertEqual(classify("conformance-report.json"), "generated-evidence")
        self.assertEqual(classify("RESULTS.md"), "upstream-only")

    def test_init_drops_upstream_truth(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "demo"
            removed = init_project(ROOT, dest, "demo")
            self.assertIn("RESULTS.md", removed)
            self.assertIn("AGENTS.md", removed)
            self.assertFalse((dest / "RESULTS.md").exists())
            self.assertFalse((dest / "conformance-report.json").exists())
            self.assertTrue((dest / "framework" / "config.py").is_file())
            text = (dest / "ckeletin-project.toml").read_text(encoding="utf-8")
            self.assertIn('role = "derived"', text)
            self.assertIn('name = "demo"', text)
            self.assertEqual(find_agent_violations(dest), [])
            self.assertEqual(find_changelog_violations(dest), [])

    def test_derived_conform_verifies_nothing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "demo"
            init_project(ROOT, dest, "demo")
            code, message = run_conform(dest)
        self.assertEqual(code, 0)
        self.assertIn("verified nothing", message)
        self.assertIn("demo", message)

    def test_derived_release_does_not_fail(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "demo"
            init_project(ROOT, dest, "demo")
            code, message = release_gate(dest)
        self.assertEqual(code, 0)
        self.assertIn("verified nothing", message)
        self.assertIn("release subject: demo", message)

    def test_bad_name_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                init_project(ROOT, Path(tmp) / "demo", "has a space")


if __name__ == "__main__":
    unittest.main()
