"""Planted layer violations."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from framework.checks.layers import (
    entry_is_bootstrap,
    import_contracts,
    layers_present,
    logic_prints,
    stray_packages,
)
from tests.support import ROOT, copy_project


class LayersTest(unittest.TestCase):
    def test_missing_framework_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "app" / "commands").mkdir(parents=True)
            (root / "app" / "__main__.py").write_text("from app.commands.dispatch import main\n", encoding="utf-8")
            violations = layers_present(root)
        self.assertEqual(violations, ["framework: infrastructure layer is missing"])

    def test_empty_business_logic_layer_is_valid(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "app" / "commands").mkdir(parents=True)
            (root / "app" / "__main__.py").write_text("x = 1\n", encoding="utf-8")
            (root / "framework").mkdir()
            self.assertEqual(layers_present(root), [])

    def test_stray_root_file_is_rejected(self) -> None:
        from framework.checks.layers import root_python_files

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "scratch.py").write_text("x = 1\n", encoding="utf-8")
            self.assertEqual(
                root_python_files(root),
                ["scratch.py: source file is outside a layer directory"],
            )

    def test_second_package_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "app" / "billing").mkdir(parents=True)
            (root / "app" / "logic").mkdir()
            self.assertEqual(
                stray_packages(root),
                ["app/billing: package is outside the designated layers"],
            )

    def test_logic_print_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            logic = root / "app" / "logic"
            logic.mkdir(parents=True)
            (logic / "bad.py").write_text("def run() -> None:\n    print('x')\n", encoding="utf-8")
            self.assertEqual(
                logic_prints(root),
                ["app/logic/bad.py:2: layer writes a stream directly"],
            )

    def test_entry_import_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "app").mkdir()
            (root / "app" / "__main__.py").write_text("import argparse\n", encoding="utf-8")
            self.assertTrue(entry_is_bootstrap(root))

    def test_logic_importing_the_command_layer_is_broken(self) -> None:
        self._plant("app/logic/bad.py", "from app.commands.hello import run\n")

    def test_argparse_in_logic_is_broken(self) -> None:
        self._plant("app/logic/bad.py", "import argparse\n")

    def test_framework_importing_logic_is_broken(self) -> None:
        self._plant("framework/bad.py", "import app.logic.greeting\n")

    def test_nested_checkout_is_not_scanned(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "proj"
            copy_project(dest)
            nested = dest / "app" / "logic" / "vendor"
            nested.mkdir()
            (nested / ".git").mkdir()
            (nested / "bad.py").write_text("import argparse\n", encoding="utf-8")
            self.assertEqual(import_contracts(dest), [])

    def _plant(self, relative: str, text: str) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "proj"
            copy_project(dest)
            path = dest / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")
            violations = import_contracts(dest)
        self.assertTrue(violations, relative)
        self.assertIn("BROKEN", violations[0])

    def test_this_tree_imports_are_kept(self) -> None:
        self.assertEqual(import_contracts(ROOT), [])


if __name__ == "__main__":
    unittest.main()
