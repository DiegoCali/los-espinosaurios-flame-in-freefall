# AutoResearch Saffire: bounded experiment

These instructions replace the upstream text preserved in `upstream_reference/program.md`.

They describe the experimental search, which has already completed 15 attempts. Subsequent documentation and publication include JSON, reports, figures and run records in Git. The search restrictions continue to describe the original experimental commits; this English translation does not restart the search.

1. Read `DATA_PLAN.md` and `protocol.md`. Keep preparation, data, extraction, analysis and tests protected during the experimental loop.
2. Use the training-data mean as the baseline. Evaluate it as attempt 1 from `baseline-v1` on `autoresearch/saffire-run-01`.
3. Only `train.py` is editable during the loop. Use Python and NumPy; importing `prepare` is permitted for the CLI launcher. Provide `fit_predict(train_X: dict, train_y, eval_X: dict, seed) -> np.ndarray` and `describe_model()` with formula, coefficients, model name and fitted parameter count.
4. Limit the search to 15 attempts including the baseline. Favor material groups, regime-specific linear models, ridge, airflow/thickness relationships and physical sign constraints. Do not claim O2/pressure effects without validated variation.
5. Do not read data files or IDs in the candidate, access held-out targets, encode rules by test ID, or change the data, folds or metrics.
6. Follow the sequence: edit → `.venv/bin/python -m pytest -q` → `git add train.py` → `git commit` → `.venv/bin/python scripts/run_experiment.py --description '...'`. Retain a `keep` result; preserve an attempt reference and return to the best commit for `discard` or `crash`. The gate requires a clean tree and a baseline diff limited to `train.py`.
7. Simplicity rule: discard improvements below 0.1%; added parameters require at least 2% relative RMSE improvement each. Do not expand the budget or change these rules during a run.
8. Do not ask the human whether to continue. Stop by attempt 15, restore the best commit, generate the analysis JSON and reports, and verify reproducibility and raw-data integrity. The final interpretation must acknowledge sample size and selection optimism.

The historical best experimental commit is `2af682a96609f938a023eb5bf94d62441d4e0d4d`. Publication and translation work follows that experiment and preserves its model, evaluation and evidence.
