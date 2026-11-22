"""The catalog is the same list the parser uses."""

from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

from app.commands.catalog import payload
from app.commands.surface import command_list
from tests.support import ROOT, run


class CatalogTest(unittest.TestCase):
    def test_catalog_matches_the_command_list(self) -> None:
        body = payload()
        self.assertEqual([item["name"] for item in body["commands"]], [item.name for item in command_list()])
        proc = run([sys.executable, "-m", "app", "--help"], ROOT)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        for command in command_list():
            self.assertIn(command.name, proc.stdout)
        for flag in body["global_flags"]:
            self.assertCountEqual(["long", "required", "takes_value", "description"], flag.keys())

    def test_optional_fields_are_omitted(self) -> None:
        update = next(item for item in payload()["commands"] if item["name"] == "update")
        dry = next(flag for flag in update["flags"] if flag["long"] == "dry-run")
        self.assertNotIn("description", dry)
        self.assertNotIn("short", dry)
        self.assertFalse(dry["takes_value"])
        self.assertEqual(update["commands"], [])

    def test_every_command_has_json(self) -> None:
        env = os.environ.copy()
        env["CKELETIN_COVERAGE_CHILD"] = "1"
        for command in command_list():
            if command.name == "update":
                with tempfile.TemporaryDirectory() as tmp:
                    proc = run(
                        [sys.executable, "-m", "app", "--output", "json", "update", "--upstream", tmp],
                        Path(tmp),
                        {**env, "PYTHONPATH": str(ROOT)},
                    )
            else:
                proc = run(
                    [sys.executable, "-m", "app", "--output", "json", command.name],
                    ROOT,
                    env,
                )
            self.assertEqual(proc.returncode, 0, command.name + "\n" + proc.stdout + proc.stderr)
            body = json.loads(proc.stdout)
            self.assertEqual(body["command"], command.name)
            self.assertIn("data", body)
            self.assertIn("error", body)
            self.assertIn(body["status"], {"success", "error"})


if __name__ == "__main__":
    unittest.main()
