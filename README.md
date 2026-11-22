# ckeletin-py

The Python implementation of the ckeletin spec. It is the frame for a bespoke Python CLI: the same requirements Go and Rust meet, with Python tools. Each requirement's enforcement rung is recorded in `ENFORCEMENT.md` and `conformance-report.json`. A lower rung is a recorded fact. It is not a smaller requirement.

This checkout is local. The spec stays 0.13.1.

## Run

```sh
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python -m unittest discover -s tests
.venv/bin/python -m app check
```

`python -m app` prints the configured message.

## Layout

- `app/__main__.py` is the entry.
- `app/commands/` is the only layer that imports argparse.
- `app/logic/` is business logic.
- `app/public/` is the public surface.
- `framework/` is replaced by `python -m app update --upstream PATH`.

The 2026-11-09 four-check probe is recorded in [RESULTS.md](RESULTS.md). `lint-imports` still has to be run with its working directory at the package root.
