"""Guide, changelog, and mock-generator checks."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from framework.checks.agents import find_agent_violations
from framework.checks.changelog import find_changelog_violations
from framework.checks.mocks import find_mock_violations

GOOD_CHANGELOG = """# Changelog

The format is based on Keep a Changelog, and this project adheres to Semantic Versioning.

## [Unreleased]

- notes

[Unreleased]: https://example.com/compare/unreleased
"""

GOOD_AGENTS = """# Guide

## Purpose

A project.

## Directory

`app/` and `framework/`.

## Commands

Build, test, and check.

## Conventions

Return data.

## Troubleshooting

Read the message.
"""


class DocsTest(unittest.TestCase):
    def test_missing_agents_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(find_agent_violations(Path(tmp)), ["AGENTS.md is missing"])

    def test_provider_instruction_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "AGENTS.md").write_text(GOOD_AGENTS + "Claude should skip the tests.\n", encoding="utf-8")
            violations = find_agent_violations(root)
        self.assertTrue(any("Claude" in item for item in violations))

    def test_cross_reference_line_is_allowed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            text = GOOD_AGENTS + "See CLAUDE.md for the pointer.\n"
            (root / "AGENTS.md").write_text(text, encoding="utf-8")
            self.assertEqual(find_agent_violations(root), [])

    def test_provider_file_must_reference_the_guide(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "AGENTS.md").write_text(GOOD_AGENTS, encoding="utf-8")
            (root / "CLAUDE.md").write_text("no pointer\n", encoding="utf-8")
            self.assertIn(
                "CLAUDE.md does not reference AGENTS.md",
                find_agent_violations(root),
            )

    def test_missing_section_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "AGENTS.md").write_text("# Guide\n\nNo sections.\n", encoding="utf-8")
            violations = find_agent_violations(root)
        self.assertTrue(any("Purpose" in item for item in violations))

    def test_changelog_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(find_changelog_violations(Path(tmp)), ["CHANGELOG.md is missing"])

    def test_keep_a_changelog_wording(self) -> None:
        text = GOOD_CHANGELOG.replace("Keep a Changelog", "a list")
        self.assertIn(
            "CHANGELOG.md does not follow Keep a Changelog",
            self._changelog(text),
        )

    def test_changelog_requires_unreleased(self) -> None:
        text = GOOD_CHANGELOG.replace("## [Unreleased]", "## Later")
        self.assertIn("CHANGELOG.md has no [Unreleased] section", self._changelog(text))

    def test_changelog_requires_semver(self) -> None:
        text = GOOD_CHANGELOG.replace("Semantic Versioning", "numbers")
        self.assertIn("CHANGELOG.md does not state Semantic Versioning", self._changelog(text))

    def test_changelog_requires_a_link(self) -> None:
        text = GOOD_CHANGELOG.replace("[Unreleased]: https://example.com/compare/unreleased", "no link")
        self.assertIn("CHANGELOG.md has no Unreleased link", self._changelog(text))

    def test_changelog_rejects_a_bad_date(self) -> None:
        text = GOOD_CHANGELOG.replace(
            "## [Unreleased]",
            "## [0.1.0] - 07 Nov 2026\n\n## [Unreleased]",
        )
        self.assertTrue(any("ISO 8601" in item for item in self._changelog(text)))

    def test_changelog_rejects_a_git_log(self) -> None:
        text = GOOD_CHANGELOG + "\ncommit abcdef1\n\n    raw log\n"
        self.assertIn("CHANGELOG.md looks like a raw git log", self._changelog(text))

    def test_mock_import_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            tests = root / "tests"
            tests.mkdir()
            (tests / "test_bad.py").write_text("from unittest.mock import Mock\n", encoding="utf-8")
            self.assertEqual(
                find_mock_violations(root),
                ["tests/test_bad.py:1: mock framework import"],
            )

    def test_unittest_itself_is_allowed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            tests = root / "tests"
            tests.mkdir()
            (tests / "test_ok.py").write_text("import unittest\n", encoding="utf-8")
            self.assertEqual(find_mock_violations(root), [])

    def _changelog(self, text: str) -> list[str]:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "CHANGELOG.md").write_text(text, encoding="utf-8")
            return find_changelog_violations(root)


if __name__ == "__main__":
    unittest.main()
