# Repository Guidelines

## Project Structure & Module Organization

This directory contains the NASA PSI-10 / ACME CPU pilot for predicting calculated adiabatic temperature (`Tad`), not measured flame temperature or soot.

- `prepare.py` normalizes source CSVs and creates fixed dataset partitions.
- `evaluate.py` validates inputs, scores candidates, and records experiments; `train.py` implements the candidate model.
- `tests/test_prepare.py` and `tests/test_evaluate.py` cover preparation and evaluation contracts.
- `data/raw/` holds original NASA files; `data/processed/` holds generated CSVs. Both datasets are ignored by Git. `data/metadata/acme_inventory.json` records provenance and splits.
- `knowledge/ACME_DATASET.md`, `protocol.md`, and `program.md` document data and research rules. `runs/` contains ignored experiment outputs; `analysis/` is reserved for reports.

## Build, Test, and Development Commands

Run from this directory with Python 3.13+ and uv:

```bash
uv sync                                      # Install locked dependencies
uv run python prepare.py --check              # Regenerate data and check invariants
uv run python -m unittest discover -s tests -v # Run all tests
uv run python evaluate.py --candidate --run-id pilot-01 --description "Explain hypothesis"
```

Preparation requires the two original NASA CSVs in `data/raw/`. Evaluation appends an attempt to the selected run. Inspect its ledger first: `pilot-01` already has a baseline and initial candidate; do not repeat them. Each run allows 12 attempts including baseline.

## Coding Style & Naming Conventions

Follow existing Python style: four-space indentation, `snake_case` functions and variables, `UPPER_CASE` constants, and type annotations on public functions. Preserve `fit_predict(X_train, y_train, X_eval, seed) -> np.ndarray`. Reuse NumPy and existing helpers; no formatter or linter is configured.

## Testing Guidelines

Use standard-library `unittest`, with files named `test_*.py` and methods named `test_*`. Cover split integrity, feature restrictions, and finite predictions when changing relevant behavior. No coverage threshold is configured. Preparation tests regenerate processed data and metadata; review resulting diffs.

## Commit & Pull Request Guidelines

History uses scoped Conventional Commit messages, such as `fix(acme): update ridge model parameters`. Keep changes focused. For pull requests, describe the change, validation commands and results, and relevant experiment metrics; link an issue when applicable. No PR template is provided here.

## Experiment Integrity

Read `protocol.md` and `program.md` before experiments. During searches, edit only `train.py`, use `feature/psi-10-acme-autoresearch`, fit transformations on training data only, and leave holdout unopened. Preserve append-only run records and protected files; never rewrite experiment history.
