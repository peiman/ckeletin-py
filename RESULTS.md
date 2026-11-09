# Probe results

Run on 2026-11-09 with Python 3.15.2 and import-linter 2.16. `python -m unittest discover -s tests` passed 15 tests. The spec was not edited.

None of the four checks assumed a compiler. Each planted violation failed a tool.

## Public must not import private

Met. Enforcement is a linter.

CKSPEC-ARCH-007 already says a public package must not import a private one. Import Linter's forbidden contract checks `app.public` against `app.private`. The good tree is kept (exit 0). The planted import fails:

```sh
cd tests/fixtures/public_imports_private && ../../../.venv/bin/lint-imports
```

```
Public must not import private BROKEN
Contracts: 0 kept, 1 broken.

app.public is not allowed to import app.private:

-   app.public.leak -> app.private.secret (l.1)
```

Exit 1. The same command also fails `from ..private.secret import NAME`. Passing `--config` at the repo root does not switch trees: the linter still reads the packages in the working directory.

Go and Rust meet this rule earlier on the ladder, at compile time. Principle 9: this probe records `linter`. The MUST stays as it is.

## One config registry

Met. Enforcement is a script.

`framework/config.py` is the only registry. `get` returns `hello` for `KEY_APP_MESSAGE` and raises `KeyError` for an unknown name. The checker parses `app/` and fails a string literal passed to a function named `get`, and a `KEY_*` assignment outside the registry.

The good tree exits 0. The planted call fails:

```sh
.venv/bin/python -m framework.checks.config_keys tests/fixtures/raw_config_key
```

```
app/commands/hello.py:5: config get uses a raw string 'app.message'
```

Exit 1.

The rule can be stated without naming a language: config keys have one registry, and call sites do not pass string literals. It does not assume a compiler. The spec does not say this today. Principle 10: this run does not add it. One probe is not yet a rule both Go and Rust must share.

The checker sees a literal argument. It does not see a string built by concatenation.

## Update replaces the framework tree

Met.

`python -m framework.update PROJECT UPSTREAM` replaces `framework/` with the upstream tree and then compares every application file with the bytes it had before. On the run, the command printed `framework replaced; application files unchanged: 1` and exited 0. `app/keep.py` had the same checksum before and after (`704589907`, 5 bytes). The framework marker changed from `old` to `new`. `extra.py`, which was only in the old tree, was removed.

This is the outcome in CKSPEC-UPD-002: the framework is replaced and application code is left in place. The notice, dry run, and discard matrix were not part of this probe.

## A command function can be measured

Met. Enforcement is a script.

The checker measures a `run*` function from its `def` line through the last line of the body. More than 35 lines fails. That number is this probe's hard fail, chosen so it matches Go's ADR-001 hard fail. It is not a spec number.

A generated function of 35 lines passes. One of 36 lines fails. The planted fixture fails:

```sh
.venv/bin/python -m framework.checks.thin_commands tests/fixtures/fat_command
```

```
app/commands/hello.py:1: run is 36 lines (limit 35)
```

Exit 1. The real `run` in `app/commands/hello.py` is 5 lines, and the good tree exits 0. `app/__main__.py` does not import argparse. `app/commands/hello.py` does.

## What this says about the spec

These four rules hold in Python. The public-import rule is met by a linter. The registry check and the command measurement are met by scripts. The update is the command itself. Principle 9: a lower rung is recorded. It does not weaken a MUST and it does not add a Python exception.

No requirement had to be stated by naming a language, so the spec stays at 0.13.1.

Principle 5: the spec plus Go and Rust carried this layer. That is not a reason to build the rest of a framework. Logging, a TUI, release tooling, license checks, and SBOM checks were left out, and this repo does not claim conformance to the other 42 requirements.
