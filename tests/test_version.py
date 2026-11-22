"""Version output names every field, including the ones it cannot resolve."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

from framework.buildinfo import provenance
from tests.support import ROOT, run


class VersionTest(unittest.TestCase):
    def test_unknown_fields_are_explicit(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            info = provenance(Path(tmp))
        self.assertEqual(
            info,
            {"version": "unknown", "commit": "unknown", "date": "unknown", "dirty": "unknown"},
        )

    def test_version_file_is_read(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "VERSION").write_text("1.2.3\n", encoding="utf-8")
            info = provenance(root)
        self.assertEqual(info["version"], "1.2.3")
        self.assertEqual(info["commit"], "unknown")

    def test_cli_prints_four_fields(self) -> None:
        proc = run([sys.executable, "-m", "app", "version"], ROOT)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        lines = proc.stdout.splitlines()
        self.assertEqual(lines[0], "0.1.0")
        self.assertTrue(lines[1].startswith("commit: "))
        self.assertNotEqual(lines[1].split(": ", 1)[1], "")
        self.assertTrue(lines[2].startswith("date: "))
        self.assertIn(lines[3], {"dirty: true", "dirty: false"})


if __name__ == "__main__":
    unittest.main()
