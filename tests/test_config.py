"""Config precedence and unknown keys."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

from framework.config import KEY_APP_MESSAGE, KEY_APP_OUTPUT_FORMAT, load
from framework.update import replace_framework
from tests.support import ROOT, run, temporary_env


class ConfigTest(unittest.TestCase):
    def test_precedence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "ckeletin-project.toml").write_text(
                '[defaults]\n"app.message" = "from-project"\n',
                encoding="utf-8",
            )
            config = root / "opt.toml"
            config.write_text('[options]\n"app.message" = "from-file"\n', encoding="utf-8")
            self.assertEqual(load(root).value(KEY_APP_MESSAGE), "from-project")
            self.assertEqual(load(root, config_path=config).value(KEY_APP_MESSAGE), "from-file")
            with temporary_env(CKELETIN_APP_MESSAGE="from-env"):
                chosen = load(root, config_path=config)
                self.assertEqual(chosen.value(KEY_APP_MESSAGE), "from-env")
                flagged = load(root, output="json", config_path=config)
                self.assertEqual(flagged.value(KEY_APP_OUTPUT_FORMAT), "json")

    def test_unknown_project_default_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "ckeletin-project.toml").write_text(
                '[defaults]\n"nope" = "x"\n',
                encoding="utf-8",
            )
            with self.assertRaises(KeyError) as caught:
                load(root)
        self.assertIn("unknown config key: nope", str(caught.exception))

    def test_unknown_config_file_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = root / "opt.toml"
            config.write_text('[options]\n"nope" = "x"\n', encoding="utf-8")
            with self.assertRaises(KeyError):
                load(root, config_path=config)

    def test_dotted_key_is_the_registry_name(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "ckeletin-project.toml").write_text(
                "[defaults]\napp.message = \"dotted\"\n",
                encoding="utf-8",
            )
            self.assertEqual(load(root).value(KEY_APP_MESSAGE), "dotted")

    def test_cli_unknown_key_exits(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "ckeletin-project.toml").write_text(
                '[defaults]\n"nope" = "x"\n',
                encoding="utf-8",
            )
            env = dict(**{key: value for key, value in __import__("os").environ.items()})
            env["PYTHONPATH"] = str(ROOT)
            proc = run([sys.executable, "-m", "app", "hello"], root, env)
        self.assertEqual(proc.returncode, 2)
        self.assertIn("unknown config key: nope", proc.stderr)

    def test_project_default_survives_replacement(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            project = root / "project"
            upstream = root / "upstream"
            (project / "framework").mkdir(parents=True)
            (project / "app").mkdir()
            (project / "framework" / "marker.py").write_text("old\n", encoding="utf-8")
            (upstream).mkdir()
            (upstream / "marker.py").write_text("new\n", encoding="utf-8")
            defaults = '[defaults]\n"app.message" = "kept"\n'
            (project / "ckeletin-project.toml").write_text(defaults, encoding="utf-8")
            code = replace_framework(project, upstream, quiet=True)
            self.assertEqual(code, 0)
            self.assertEqual((project / "ckeletin-project.toml").read_text(encoding="utf-8"), defaults)
            self.assertEqual((project / "framework" / "marker.py").read_text(encoding="utf-8"), "new\n")


if __name__ == "__main__":
    unittest.main()
