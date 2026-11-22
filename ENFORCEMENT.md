# Enforcement audit

Generated from `framework/mapping.py` and `framework/spec-requirements.json`.
A rung below compile-time is recorded here. The requirement itself is unchanged.

| Requirement | Status | Enforcement | Gap |
| --- | --- | --- | --- |
| CKSPEC-AGENT-001 | met | script | The checker can require the file and its section labels. It cannot judge whether the prose is true. |
| CKSPEC-AGENT-002 | met | script | A provider instruction on the same line as CLAUDE.md is skipped with the cross-reference. That residual is reviewed, not hidden. |
| CKSPEC-AGENT-003 | met | script | The checker sees the reference. It does not score whether a provider file repeats a rule in different words. |
| CKSPEC-AGENT-004 | met | script | Section labels are checked. Completeness of every command description is editorial. |
| CKSPEC-AGENT-005 | met | script | The absence of a second interface is an analysis of the tree. A new transport would be a new module, which this check does not forbid by name. |
| CKSPEC-AGENT-006 | met | test | The catalog is a runtime registry. Registration completeness is a test, which is the strongest check this layout has. |
| CKSPEC-AGENT-007 | met | script | Ownership is by path. A file added outside the classified set is dropped on init, which is safe and may surprise a new artifact until it is classified. |
| CKSPEC-ARCH-001 | met | script | Python packages are directories. The checker sees the directories, not a build graph. |
| CKSPEC-ARCH-002 | met | linter | Import Linter is a linter. Python has no compile-time visibility between these packages. |
| CKSPEC-ARCH-003 | met | linter | The entry imports the command layer, and that layer imports argparse. A forbidden-import contract on the entry would treat that intended chain as a violation, so the entry is checked as source text. |
| CKSPEC-ARCH-004 | met | script | Python does not give one distribution a crate boundary inside app.logic. The recorded check is one package. A second package fails the script. |
| CKSPEC-ARCH-005 | met | linter | The guarantee is the linter, not the compiler. |
| CKSPEC-ARCH-006 | met | script | The entry is small by inspection of its syntax tree. The checker does not measure what the called command does. |
| CKSPEC-ARCH-007 | met | linter | Public-must-not-import-private is a linter contract. The planted fixture tests/fixtures/public_imports_private still uses its own app.private package. |
| CKSPEC-CL-001 | met | script | The checker requires the file. It does not judge the importance of each entry. |
| CKSPEC-CL-002 | met | script | The words are checked. Faithfulness to the Keep a Changelog categories is editorial. |
| CKSPEC-CL-003 | met | script | Unreleased has no date. A released heading with a bad date fails. |
| CKSPEC-CL-004 | met | script | The statement is checked. The checker does not parse every version number against the SemVer grammar. |
| CKSPEC-CL-005 | met | script | The heading is checked. An empty Unreleased section is still a section. |
| CKSPEC-CL-006 | met | script | A git log pasted without commit headings would not match the pattern. The file in this tree is curated. |
| CKSPEC-CL-007 | met | script | The link is present. This checkout is local, so the link is the compare shape rather than a fetched page. |
| CKSPEC-ENF-001 | met | script | Whether a decision can be automated is a judgment. The audit table shows what the gate actually runs. |
| CKSPEC-ENF-002 | met | script | The ladder is data in the generator. Python does not make the top rung available for imports. |
| CKSPEC-ENF-003 | met | script | The gap is a sentence in the mapping. The generator requires it. It does not prove the sentence is the real limit. |
| CKSPEC-ENF-004 | met | script | The table is only as current as the last generate. The drift check is the guard. |
| CKSPEC-ENF-005 | met | script | Completeness is against the vendored id list. A spec release newer than that file is a drift this checkout must pick up on purpose. |
| CKSPEC-ENF-006 | met | script | The generator checks that the proof field is present and that the named test exists. It does not re-run every violation test itself. |
| CKSPEC-ENF-007 | met | script | The signal is automatic. Acting on it, by changing the spec or the tool, is still a separate decision. |
| CKSPEC-ENF-008 | met | script | Anchors that are shell commands are named, not executed, by the generator. The unit tests execute the checks. |
| CKSPEC-ENF-009 | met | script | The gate is a local command, not a hosted release pipeline. This checkout is not published. |
| CKSPEC-ENF-010 | met | script | The report is local. It is not added to the spec aggregator until it is published, which this tree does not do. |
| CKSPEC-ENF-011 | met | script | The tests cover a nested checkout under app/. They do not prove every future scanner shares the helper. |
| CKSPEC-OUT-001 | met | test | The split is tested at the renderer. A command that bypasses it is caught by framework/checks/layers.py::direct_writes. |
| CKSPEC-OUT-002 | met | test | Parser errors before a command resolves stay argparse text. Every command after that uses the renderer. |
| CKSPEC-OUT-003 | met | test | The envelope is one function. A command that prints its own JSON would be a direct write and fail framework/checks/layers.py::direct_writes. |
| CKSPEC-OUT-004 | met | test | The audit line stores the rendered text. Commands in this tree do not emit generated artifacts, so the metadata-only case is unused. |
| CKSPEC-OUT-005 | met | linter | The linter sees imports. The script sees print and stdout writes. A write through a renamed builtin is outside both. |
| CKSPEC-OUT-006 | met | test | The values come from a version file and from git. A dirty tree is reported. It is not compared to a published release. |
| CKSPEC-TEST-001 | met | honor-system | Test-first order is not recoverable after the files exist. The rule is documented and unenforced. |
| CKSPEC-TEST-002 | met | script | Statement coverage is the floor. Branch coverage is not configured. The .coveragerc file has no exclude_lines and no omit. |
| CKSPEC-TEST-003 | met | script | import unittest is the runner and is not a violation. A hand-rolled fake is not a mock generator and is not flagged. |
| CKSPEC-TEST-004 | met | honor-system | Atomic commits cannot be proven from the current tree. The rule is documented and unenforced. |
| CKSPEC-UPD-001 | met | test | A network remote that cannot be fetched in a few seconds is reported as unavailable. The notice does not guess a version. |
| CKSPEC-UPD-002 | met | test | REWRITTEN_NAMES in framework/update.py is empty because this framework does not rewrite paths during an update. |
| CKSPEC-UPD-003 | met | test | The command renders that dict. A reader still has the prose line as well. |
| CKSPEC-UPD-004 | met | test | An unknown key fails at load. A dotted TOML key and a quoted key both name the same option. |

## Honor system

- CKSPEC-TEST-001: Test-first order is not recoverable after the files exist. The rule is documented and unenforced.
- CKSPEC-TEST-004: Atomic commits cannot be proven from the current tree. The rule is documented and unenforced.
