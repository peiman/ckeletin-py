# ckeletin-py

## Purpose

This repository is the Python implementation of the ckeletin spec. It is the frame a bespoke Python CLI should start from. The spec stays language-neutral. This tree records how Python meets each requirement, including the enforcement rung.

## Directory

- `app/__main__.py` is the entry. It only calls the command layer.
- `app/commands/` is the command layer. argparse is imported only there.
- `app/logic/` is the business logic. It returns data and does not print.
- `app/public/` is the public surface.
- `framework/` is infrastructure. An update replaces this tree and leaves `app/` byte for byte.
- `tests/` holds the checks.

## Commands

- Build with `python -m compileall -q app framework`.
- Test with `python -m unittest discover -s tests`.
- Check with `python -m app check`.
- `python -m app` runs the default command.
- `python -m app version` prints version, commit, date, and dirty.
- `python -m app catalog` prints the command surface.
- `python -m app conform` checks the conformance report against the mapping.
- `python -m app release` runs the release gate.
- `python -m app update --upstream PATH` replaces `framework/` only.

## Conventions

- Write the failing test first. The test and the implementation land together.
- Config keys live in `framework/config.py`. Call sites pass those names.
- Business logic returns values. `framework/output.py` writes stdout, stderr, and the audit log.
- `--output text` and `--output json` select the user-facing stream. The flag beats the environment, which beats the project config file, which beats the project default, which beats the framework default.
- Do not import a mock generator in tests.
- A provider note belongs in CLAUDE.md, which points here.

## Troubleshooting

- `lint-imports` must run with its working directory at the package root.
- An unknown config key fails at load.
- `CKELETIN_NO_UPDATE_NOTICE=1` turns the update notice off. The notice does not run when `CI=true`.
- Coverage is statement coverage of `app` and `framework` with a floor of 85 percent. `.coveragerc` has no exclusions.
- `python -m app conform` on a derived project says it verified nothing. It does not fail the release.
