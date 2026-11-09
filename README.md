# ckeletin-python

A probe of four ckeletin rules in Python. This is not a framework and not a product.

Imports are not rejected by the compiler here. Each check has to fail a planted violation with a tool. The result of that run is [RESULTS.md](RESULTS.md). The spec is unchanged.

## Run

```sh
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python -m unittest discover -s tests
.venv/bin/python -m app
```

`python -m app` prints `hello`.

## Checks

| Rule | Command | Planted violation |
| --- | --- | --- |
| Public must not import private | `.venv/bin/lint-imports` | `cd tests/fixtures/public_imports_private && ../../../.venv/bin/lint-imports` |
| Config call sites use the registry | `.venv/bin/python -m framework.checks.config_keys` | `tests/fixtures/raw_config_key` |
| Update replaces `framework/` only | `.venv/bin/python -m framework.update PROJECT UPSTREAM` | covered by `tests/test_probe.py` |
| A `run` function can be measured | `.venv/bin/python -m framework.checks.thin_commands` | `tests/fixtures/fat_command` |

The config registry is `framework/config.py`. The command layer is `app/commands/`. The entry point does not import argparse.
