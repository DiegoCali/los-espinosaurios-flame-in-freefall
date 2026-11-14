# AutoResearch SAME: bounded experiment (`same-run-01`)

These instructions replace the upstream text preserved in `upstream_reference/program.md`
(karpathy/autoresearch @ `228791fb`). The upstream loop trains a GPT for 5 minutes and keeps or
`git reset`s each change. This adaptation keeps the same idea — **one fixed evaluator, one editable
file, keep only what improves the metric** — but applies it to a small scientific dataset and
**never uses git**: every attempt is archived as files.

## Setup (already done for `same-run-01`)

1. Read `DATA_PLAN.md`, `knowledge/SAME_KNOWLEDGE_BASE.md`, `prepare.py` and `train.py`.
2. `prepare.py`, `data/processed/size_dataset.csv`, `data/processed/detection_dataset.csv`,
   `scripts/run_experiment.py` and `tests/test_experiment_gate.py` are frozen by SHA-256 in
   `runs/autoresearch/same-run-01/protected_manifest.json` (written by attempt 1).
3. Attempt 1 is the baseline: training-fold means and training prevalences.

## What the agent may do

- Edit **only `train.py`**. Python, NumPy, SciPy and scikit-learn are available; no new packages.
- Implement `fit_predict_size`, `fit_predict_detection` and `describe_model()` (model name,
  parameter count, formula or notes).
- Use the provided condition features only: `material`, `aged`, `aging_s`, `flow_velocity_cm_s`,
  `no_flow`, `rt_r0` (+ `push_index` for detection). Physics-motivated transforms are encouraged:
  Brownian coagulation predicts `M0 ∝ 1/(1 + K·N0·t)` and `Dm ∝ (1 + K·N0·t)^(1/3)`; quiescent
  (no-flow) smoke is ~50× more concentrated, coagulates faster and loses part of the plume.

## What the agent may not do

- Edit `prepare.py`, data, folds, metric, tests or the experiment script.
- Read files, use run/test identifiers, or encode rules for individual tests (`run_experiment.py`
  rejects candidates containing file access or identifier look-ups).
- Run more than **15 attempts** in total, including the baseline.

## Loop

```
edit train.py
.venv/bin/python scripts/run_experiment.py --description "<what changed and why>"
```

The script runs the contract tests, evaluates leave-one-run-out (size) and leave-one-test-out
(detection) cross-validation, snapshots `train.py` to `attempt-XX.train.py`, appends `results.tsv`
and writes `attempt-XX.json`. If `val_score` improves on the best by at least 0.1 % the attempt is
`keep` and `best_train.py` / `best.json` are updated; otherwise it is `discard` (or `crash`) and
`train.py` is restored from `best_train.py` automatically — the file-based equivalent of
`git reset`.

**Simplicity rule.** All else equal, simpler is better. Do not keep a change that adds parameters
for a gain below about 1 % of `val_score`; prefer removing terms when the score is unchanged.

**Stop rule.** Stop at attempt 15 (or earlier when ideas are exhausted), make sure `train.py`
equals `best_train.py` (`--restore-best`), then regenerate the analysis
(`analysis/build_analysis_json.py`). Report the selected model with its baseline comparison and
acknowledge selection optimism: with ~50 rows, choosing the best of 15 attempts on the same folds
inflates the apparent gain.
