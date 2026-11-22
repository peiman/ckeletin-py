"""Build the conformance report from the mapping. A gap fails the generator."""

from __future__ import annotations

import ast
import json
import re
import sys
import tomllib
from pathlib import Path

from framework.mapping import CLAIMS
from framework.project import REFERENCE_NAME, is_reference, read_identity

SPEC_FILE = Path(__file__).with_name("spec-requirements.json")
LEVELS = {"compile-time", "structural", "linter", "sast", "script", "test", "ci", "honor-system"}
ANCHOR = re.compile(
    r"((?:[\w.-]+/)*[\w.-]+\.(?:py|md|toml|json))"
    r"(?:::([A-Za-z_][\w]*(?:\.[A-Za-z_][\w]*)*))?"
)


def spec_document() -> tuple[str, list[str]]:
    payload = json.loads(SPEC_FILE.read_text(encoding="utf-8"))
    return str(payload["spec_version"]), [str(item["id"]) for item in payload["requirements"]]


def _symbols(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    names: set[str] = set()
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names.add(node.name)
        if isinstance(node, ast.ClassDef):
            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    names.add(f"{node.name}.{item.name}")
    return names


def _resolve(root: Path, file: str, symbol: str | None) -> str | None:
    path = root / file
    if not path.is_file():
        return f"missing file {file}"
    if symbol is None:
        return None
    if symbol not in _symbols(path):
        return f"missing symbol {file}::{symbol}"
    return None


def _anchors(text: str) -> list[tuple[str, str | None]]:
    return [(match.group(1), match.group(2)) for match in ANCHOR.finditer(text or "")]


def feedback_for(claims: dict[str, dict]) -> list[dict[str, str]]:
    """Signals the generator adds. They are not typed into the report by hand."""
    rows = []
    for req_id in sorted(claims):
        claim = claims[req_id]
        reasons = []
        if claim.get("enforcement_level") != "compile-time" and claim.get("gap"):
            reasons.append(str(claim["gap"]))
        if not claim.get("checks"):
            reasons.append("no automated check is named")
        if reasons:
            rows.append({"id": req_id, "reason": " ".join(reasons)})
    return rows


def validate(root: Path, claims: dict[str, dict] | None = None) -> list[str]:
    version, ids = spec_document()
    claims = CLAIMS if claims is None else claims
    errors: list[str] = []
    missing = [item for item in ids if item not in claims]
    extra = sorted(set(claims) - set(ids))
    if missing:
        errors.append("unmapped requirements: " + ", ".join(missing))
    if extra:
        errors.append("unknown requirements: " + ", ".join(extra))
    if version != "0.13.1":
        errors.append(f"spec version {version} is not 0.13.1")
    for req_id in sorted(claims):
        if req_id not in ids:
            continue
        claim = claims[req_id]
        level = str(claim.get("enforcement_level", ""))
        if level not in LEVELS:
            errors.append(f"{req_id}: unknown enforcement level {level}")
            continue
        if level != "compile-time" and not str(claim.get("gap") or "").strip():
            errors.append(f"{req_id}: enforcement gap is not documented")
        tests = [str(item) for item in claim.get("violation_tests") or []]
        proof = str(claim.get("violation_evidence") or "")
        if level != "honor-system" and not tests and not proof.strip():
            errors.append(f"{req_id}: enforcement claim has no violation proof")
        evidence = str(claim.get("evidence") or "")
        if not _anchors(evidence):
            errors.append(f"{req_id}: evidence names no file")
        for file, symbol in _anchors(evidence) + _anchors(proof):
            problem = _resolve(root, file, symbol)
            if problem:
                errors.append(f"{req_id}: {problem}")
        for test in tests:
            found = _anchors(test)
            if len(found) != 1 or found[0][1] is None:
                errors.append(f"{req_id}: violation test is not file::symbol ({test})")
                continue
            problem = _resolve(root, found[0][0], found[0][1])
            if problem:
                errors.append(f"{req_id}: {problem}")
        for check in claim.get("checks") or []:
            for file, symbol in _anchors(str(check)):
                problem = _resolve(root, file, symbol)
                if problem:
                    errors.append(f"{req_id}: {problem}")
    return errors


def _report(claims: dict[str, dict]) -> dict:
    version, ids = spec_document()
    counts = {"met": 0, "partial": 0, "deferred": 0, "not-met": 0}
    requirements = {}
    for req_id in sorted(ids):
        claim = claims[req_id]
        status = str(claim["status"])
        counts[status] = counts.get(status, 0) + 1
        requirements[req_id] = {
            "checks": [str(item) for item in claim.get("checks") or []],
            "enforcement_level": claim["enforcement_level"],
            "evidence": claim["evidence"],
            "status": status,
            "violation_evidence": claim.get("violation_evidence") or None,
            "violation_tests": [str(item) for item in claim.get("violation_tests") or []],
        }
    return {
        "implementation": REFERENCE_NAME,
        "spec_version": version,
        "requirements": requirements,
        "summary": {
            "deferred": counts["deferred"],
            "met": counts["met"],
            "not-met": counts["not-met"],
            "partial": counts["partial"],
            "passed": counts["met"] == len(ids),
            "total": len(ids),
        },
        "feedback": feedback_for(claims),
    }


def enforcement_text(claims: dict[str, dict] | None = None) -> str:
    claims = CLAIMS if claims is None else claims
    lines = [
        "# Enforcement audit",
        "",
        "Generated from `framework/mapping.py` and `framework/spec-requirements.json`.",
        "A rung below compile-time is recorded here. The requirement itself is unchanged.",
        "",
        "| Requirement | Status | Enforcement | Gap |",
        "| --- | --- | --- | --- |",
    ]
    for req_id in sorted(claims):
        claim = claims[req_id]
        gap = str(claim.get("gap") or "").replace("|", "/")
        lines.append(
            f"| {req_id} | {claim['status']} | {claim['enforcement_level']} | {gap} |"
        )
    lines.extend(["", "## Honor system", ""])
    for req_id in sorted(claims):
        claim = claims[req_id]
        if claim.get("enforcement_level") == "honor-system":
            lines.append(f"- {req_id}: {claim['gap']}")
    lines.append("")
    return "\n".join(lines)


def generate(root: Path, claims: dict[str, dict] | None = None) -> tuple[str, str, list[str]]:
    claims = CLAIMS if claims is None else claims
    errors = validate(root, claims)
    if errors:
        return "", "", errors
    report = json.dumps(_report(claims), indent=2) + "\n"
    return report, enforcement_text(claims), []


def run_conform(root: Path) -> tuple[int, str]:
    try:
        identity = read_identity(root)
    except (tomllib.TOMLDecodeError, OSError) as exc:
        return 0, f"conform subject: unknown; verified nothing; {exc}"
    if not is_reference(root):
        name = identity.name or "unknown"
        return 0, (
            f"conform subject: {name}; verified nothing; "
            f"this repository is not the {REFERENCE_NAME} implementation"
        )
    report, audit, errors = generate(root)
    if errors:
        return 1, "conform refused: " + "; ".join(errors)
    report_path = root / "conformance-report.json"
    audit_path = root / "ENFORCEMENT.md"
    disk_report = report_path.read_text(encoding="utf-8") if report_path.is_file() else ""
    disk_audit = audit_path.read_text(encoding="utf-8") if audit_path.is_file() else ""
    if disk_report != report or disk_audit != audit:
        return 1, "conform drift: conformance-report.json or ENFORCEMENT.md does not match the mapping"
    return 0, f"conform subject: {identity.name}; conform passed"


def write_outputs(root: Path) -> list[str]:
    report, audit, errors = generate(root)
    if errors:
        return errors
    (root / "conformance-report.json").write_text(report, encoding="utf-8")
    (root / "ENFORCEMENT.md").write_text(audit, encoding="utf-8")
    return []


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    root = Path.cwd()
    if "--write" in args:
        errors = write_outputs(root)
        if errors:
            print("conform refused: " + "; ".join(errors), file=sys.stderr)
            return 1
        print("wrote conformance-report.json and ENFORCEMENT.md")
        return 0
    code, message = run_conform(root)
    print(message)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
