"""The four probe checks, each with a planted violation."""

from __future__ import annotations

import ast
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from framework.checks.config_keys import find_raw_config_gets
from framework.checks.thin_commands import LIMIT, find_fat_commands, span
from framework.config import KEY_APP_MESSAGE, get

ROOT = Path(__file__).resolve().parents[1]
LINT = ROOT / ".venv" / "bin" / "lint-imports"
FIXTURES = ROOT / "tests" / "fixtures"


def run(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )


class PublicImportTest(unittest.TestCase):
    def test_good_tree_is_kept(self) -> None:
        proc = run([str(LINT)], ROOT)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("KEPT", proc.stdout)

    def test_planted_absolute_import_is_broken(self) -> None:
        fixture = FIXTURES / "public_imports_private"
        proc = run([str(LINT)], fixture)
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertIn("BROKEN", proc.stdout)
        self.assertIn("app.public.leak", proc.stdout)
        self.assertIn("app.private.secret", proc.stdout)

    def test_planted_relative_import_is_broken(self) -> None:
        fixture = FIXTURES / "public_imports_private"
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            shutil.copytree(fixture, project, dirs_exist_ok=True)
            leak = project / "app" / "public" / "leak.py"
            leak.write_text("from ..private.secret import NAME\n\n\ndef surface() -> str:\n    return NAME\n", encoding="utf-8")
            proc = run([str(LINT)], project)
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertIn("BROKEN", proc.stdout)
        self.assertIn("app.private.secret", proc.stdout)


class ConfigKeyTest(unittest.TestCase):
    def test_registry_returns_its_value(self) -> None:
        self.assertEqual(get(KEY_APP_MESSAGE), "hello")

    def test_unknown_key_fails(self) -> None:
        with self.assertRaises(KeyError):
            get("app.missing")

    def test_good_tree_has_no_raw_gets(self) -> None:
        self.assertEqual(find_raw_config_gets(ROOT), [])

    def test_planted_raw_string_fails(self) -> None:
        violations = find_raw_config_gets(FIXTURES / "raw_config_key")
        self.assertEqual(
            violations,
            ["app/commands/hello.py:5: config get uses a raw string 'app.message'"],
        )

    def test_key_defined_outside_the_registry_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            app = Path(tmp) / "app"
            app.mkdir()
            (app / "extra.py").write_text('KEY_APP_MESSAGE = "app.message"\n', encoding="utf-8")
            violations = find_raw_config_gets(Path(tmp))
        self.assertEqual(
            violations,
            ["app/extra.py:1: config key KEY_APP_MESSAGE is defined outside the registry"],
        )

    def test_command_exits_nonzero_on_the_fixture(self) -> None:
        proc = run(
            [sys.executable, "-m", "framework.checks.config_keys", str(FIXTURES / "raw_config_key")],
            ROOT,
        )
        self.assertEqual(proc.returncode, 1)
        self.assertIn("raw string 'app.message'", proc.stdout)


class ThinCommandTest(unittest.TestCase):
    def test_good_command_is_within_the_limit(self) -> None:
        self.assertEqual(find_fat_commands(ROOT), [])
        tree = ast.parse((ROOT / "app" / "commands" / "hello.py").read_text(encoding="utf-8"))
        run_fn = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "run")
        self.assertLessEqual(span(run_fn), LIMIT)

    def test_span_of_thirty_five_passes_and_thirty_six_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            commands = Path(tmp) / "app" / "commands"
            commands.mkdir(parents=True)
            path = commands / "hello.py"
            path.write_text(self._function(35), encoding="utf-8")
            self.assertEqual(find_fat_commands(Path(tmp)), [])
            path.write_text(self._function(36), encoding="utf-8")
            violations = find_fat_commands(Path(tmp))
        self.assertEqual(violations, [f"app/commands/hello.py:1: run is 36 lines (limit {LIMIT})"])

    def test_planted_fixture_fails(self) -> None:
        proc = run(
            [sys.executable, "-m", "framework.checks.thin_commands", str(FIXTURES / "fat_command")],
            ROOT,
        )
        self.assertEqual(proc.returncode, 1)
        self.assertIn("run is 36 lines", proc.stdout)

    def test_entry_does_not_import_argparse(self) -> None:
        entry = ast.parse((ROOT / "app" / "__main__.py").read_text(encoding="utf-8"))
        command = ast.parse((ROOT / "app" / "commands" / "dispatch.py").read_text(encoding="utf-8"))
        hello = ast.parse((ROOT / "app" / "commands" / "hello.py").read_text(encoding="utf-8"))
        self.assertFalse(self._imports_argparse(entry))
        self.assertFalse(self._imports_argparse(hello))
        self.assertTrue(self._imports_argparse(command))

    @staticmethod
    def _function(lines: int) -> str:
        body = lines - 2
        rows = ["def run() -> int:"]
        rows.extend(f"    value = {i}" for i in range(body))
        rows.append("    return value")
        return "\n".join(rows) + "\n"

    @staticmethod
    def _imports_argparse(tree: ast.AST) -> bool:
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                if any(alias.name == "argparse" for alias in node.names):
                    return True
            if isinstance(node, ast.ImportFrom) and node.module == "argparse":
                return True
        return False


class UpdateTest(unittest.TestCase):
    def test_replace_leaves_application_bytes_and_replaces_framework(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            project = root / "project"
            upstream = root / "upstream"
            (project / "framework").mkdir(parents=True)
            (project / "app").mkdir()
            (project / "framework" / "marker.py").write_text("old\n", encoding="utf-8")
            (project / "framework" / "extra.py").write_text("gone\n", encoding="utf-8")
            (project / "app" / "keep.py").write_text("keep\n", encoding="utf-8")
            (upstream).mkdir()
            (upstream / "marker.py").write_text("new\n", encoding="utf-8")
            before = (project / "app" / "keep.py").read_bytes()
            proc = run(
                [sys.executable, "-m", "framework.update", str(project), str(upstream)],
                ROOT,
            )
            after = (project / "app" / "keep.py").read_bytes()
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertEqual(proc.stdout.strip(), "framework replaced; application files unchanged: 1")
            self.assertEqual(before, after)
            self.assertEqual((project / "framework" / "marker.py").read_text(encoding="utf-8"), "new\n")
            self.assertFalse((project / "framework" / "extra.py").exists())
            self.assertFalse((project / ".framework-old").exists())
            self.assertFalse((project / ".framework-next").exists())


class CliTest(unittest.TestCase):
    def test_cli_prints_the_registry_message(self) -> None:
        proc = run([sys.executable, "-m", "app"], ROOT)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(proc.stdout, "hello\n")


if __name__ == "__main__":
    unittest.main()
