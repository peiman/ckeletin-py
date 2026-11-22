"""The conformance generator fails closed and the report matches the mapping."""

from __future__ import annotations

import json
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path

from framework.checks.gate import coverage_failures, static_failures
from framework.conform import feedback_for, generate, run_conform
from framework.mapping import CLAIMS
from framework.release import release_gate
from tests.support import ROOT


class ConformTest(unittest.TestCase):
    def test_missing_requirement_fails_closed(self) -> None:
        claims = {key: value for key, value in CLAIMS.items() if key != "CKSPEC-ARCH-001"}
        report, _audit, errors = generate(ROOT, claims)
        self.assertEqual(report, "")
        self.assertTrue(any("CKSPEC-ARCH-001" in item for item in errors))

    def test_dangling_anchor_fails(self) -> None:
        claims = deepcopy(CLAIMS)
        claims["CKSPEC-ARCH-001"]["violation_tests"] = ["tests/test_layers.py::LayersTest.missing"]
        report, _audit, errors = generate(ROOT, claims)
        self.assertEqual(report, "")
        self.assertTrue(any("missing" in item for item in errors))

    def test_enforcement_without_proof_fails(self) -> None:
        claims = deepcopy(CLAIMS)
        claims["CKSPEC-ARCH-001"]["violation_tests"] = []
        claims["CKSPEC-ARCH-001"]["violation_evidence"] = ""
        _report, _audit, errors = generate(ROOT, claims)
        self.assertTrue(any("no violation proof" in item for item in errors))

    def test_unknown_rung_fails(self) -> None:
        claims = deepcopy(CLAIMS)
        claims["CKSPEC-ENF-002"]["enforcement_level"] = "design"
        _report, _audit, errors = generate(ROOT, claims)
        self.assertTrue(any("unknown enforcement level" in item for item in errors))

    def test_gap_is_required(self) -> None:
        claims = deepcopy(CLAIMS)
        claims["CKSPEC-ENF-003"]["gap"] = ""
        _report, _audit, errors = generate(ROOT, claims)
        self.assertTrue(any("enforcement gap" in item for item in errors))

    def test_feedback_is_generated(self) -> None:
        rows = feedback_for(
            {
                "CKSPEC-ARCH-001": {
                    "enforcement_level": "script",
                    "gap": "python has no crate boundary",
                    "checks": ["framework/checks/layers.py::layers_present"],
                }
            }
        )
        self.assertIn("python has no crate boundary", rows[0]["reason"])
        quiet = feedback_for(
            {
                "CKSPEC-TEST-001": {
                    "enforcement_level": "honor-system",
                    "gap": "order is not recoverable",
                    "checks": [],
                }
            }
        )
        self.assertIn("no automated check is named", quiet[0]["reason"])

    def test_report_is_deterministic(self) -> None:
        first, audit_first, errors = generate(ROOT)
        second, audit_second, _errors = generate(ROOT)
        self.assertEqual(errors, [])
        self.assertEqual(first, second)
        self.assertEqual(audit_first, audit_second)
        payload = json.loads(first)
        self.assertEqual(payload["spec_version"], "0.13.1")
        self.assertEqual(payload["summary"]["total"], 46)
        self.assertEqual(payload["summary"]["met"], 46)
        self.assertTrue(payload["summary"]["passed"])
        self.assertEqual(len(payload["feedback"]), 46)

    def test_report_matches_the_mapping(self) -> None:
        code, message = run_conform(ROOT)
        self.assertEqual(code, 0, message)

    def test_release_refuses_drift(self) -> None:
        path = ROOT / "conformance-report.json"
        original = path.read_text(encoding="utf-8")
        try:
            path.write_text(original + "\n", encoding="utf-8")
            code, message = release_gate(ROOT)
            self.assertNotEqual(code, 0)
            self.assertIn("refused", message)
            self.assertIn("drift", message)
        finally:
            path.write_text(original, encoding="utf-8")

    def test_static_gate_passes_here(self) -> None:
        self.assertEqual(static_failures(ROOT), [])

    def test_coverage_floor_fails_a_partial_suite(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "sample.py").write_text(
                "def used():\n    return 1\n\ndef unused():\n    return 2\n",
                encoding="utf-8",
            )
            tests = root / "tests"
            tests.mkdir()
            (tests / "test_sample.py").write_text(
                "import sample\nimport unittest\n\n"
                "class T(unittest.TestCase):\n"
                "    def test_used(self):\n"
                "        self.assertEqual(sample.used(), 1)\n",
                encoding="utf-8",
            )
            (root / ".coveragerc").write_text(
                "[run]\nsource = sample\n\n[report]\nfail_under = 85\n",
                encoding="utf-8",
            )
            failures = coverage_failures(root)
        self.assertTrue(failures)
        self.assertIn("85", failures[0])

    def test_coveragerc_has_no_exclusions(self) -> None:
        text = (ROOT / ".coveragerc").read_text(encoding="utf-8")
        self.assertNotIn("exclude", text)
        self.assertNotIn("omit", text)


if __name__ == "__main__":
    unittest.main()
