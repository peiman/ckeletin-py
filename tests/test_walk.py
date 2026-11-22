"""Tree walks do not enter a nested checkout."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from framework.checks.config_keys import find_raw_config_gets
from framework.checks.thin_commands import find_fat_commands
from framework.walk import python_files


def _fat(lines: int) -> str:
    body = lines - 2
    rows = ["def run() -> int:"]
    rows.extend(f"    value = {i}" for i in range(body))
    rows.append("    return value")
    return "\n".join(rows) + "\n"


class WalkTest(unittest.TestCase):
    def test_nested_git_is_skipped(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            nested = root / "app" / "vendor"
            nested.mkdir(parents=True)
            (nested / ".git").mkdir()
            (nested / "evil.py").write_text('get("app.message")\n', encoding="utf-8")
            (root / "app" / "ok.py").write_text("value = 1\n", encoding="utf-8")
            files = python_files(root, "app")
            self.assertTrue(all("vendor" not in path.parts for path in files))
            self.assertEqual(find_raw_config_gets(root), [])

    def test_raw_key_outside_the_nested_checkout_still_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            nested = root / "app" / "vendor"
            nested.mkdir(parents=True)
            (nested / ".git").mkdir()
            (nested / "evil.py").write_text('get("app.message")\n', encoding="utf-8")
            (root / "app" / "bad.py").write_text('get("app.message")\n', encoding="utf-8")
            self.assertEqual(
                find_raw_config_gets(root),
                ["app/bad.py:1: config get uses a raw string 'app.message'"],
            )

    def test_fat_command_inside_a_nested_checkout_is_ignored(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            nested = root / "app" / "commands" / "vendor"
            nested.mkdir(parents=True)
            (nested / ".git").mkdir()
            (nested / "hello.py").write_text(_fat(36), encoding="utf-8")
            (root / "app" / "commands" / "ok.py").write_text("def run() -> int:\n    return 0\n", encoding="utf-8")
            self.assertEqual(find_fat_commands(root), [])


if __name__ == "__main__":
    unittest.main()
