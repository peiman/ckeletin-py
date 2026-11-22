"""The quality gate. It reports an available update and does not fail for one."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from framework.checks.agents import find_agent_violations
from framework.checks.changelog import find_changelog_violations
from framework.checks.config_keys import find_raw_config_gets
from framework.checks.layers import find_layer_violations
from framework.checks.mocks import find_mock_violations
from framework.checks.thin_commands import find_fat_commands
from framework.conform import run_conform
from framework.project import is_reference


def static_failures(root: Path) -> list[str]:
    failures: list[str] = []
    failures += find_layer_violations(root)
    failures += find_raw_config_gets(root)
    failures += find_fat_commands(root)
    failures += find_agent_violations(root)
    failures += find_changelog_violations(root)
    failures += find_mock_violations(root)
    if is_reference(root):
        code, message = run_conform(root)
        if code != 0:
            failures.append(message)
    return failures


def coverage_failures(root: Path) -> list[str]:
    """Run the suite under coverage. The floor lives in .coveragerc. No exclusions."""
    rc = root / ".coveragerc"
    if not rc.is_file():
        return [".coveragerc is missing"]
    env = os.environ.copy()
    env["CKELETIN_COVERAGE_CHILD"] = "1"
    env["COVERAGE_FILE"] = str(root / ".coverage")
    command = [
        sys.executable,
        "-m",
        "coverage",
        "run",
        f"--rcfile={rc}",
        "-m",
        "unittest",
        "discover",
        "-s",
        "tests",
    ]
    run = subprocess.run(command, cwd=root, env=env, capture_output=True, text=True, check=False)
    if run.returncode != 0:
        return [(run.stderr or run.stdout).strip() or "tests failed under coverage"]
    report = subprocess.run(
        [sys.executable, "-m", "coverage", "report", f"--rcfile={rc}"],
        cwd=root,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    if report.returncode != 0:
        return [(report.stdout or report.stderr).strip() or "coverage is below the floor"]
    return []


def gate_result(root: Path) -> tuple[int, list[str]]:
    failures = static_failures(root)
    if os.environ.get("CKELETIN_COVERAGE_CHILD") != "1":
        failures.extend(coverage_failures(root))
    return (1 if failures else 0, failures)
