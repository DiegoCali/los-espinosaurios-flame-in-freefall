# FLEX autoresearch

This is an experiment to improve a structured predictor for NASA FLEX
combustion experiments. The goal is to support fire-safety analysis, not to
invent scientific claims or replace human review.

## Setup

1. Agree on a run tag and create a fresh `autoresearch/<tag>` branch.
2. Read `README.md`, `prepare.py`, `train.py`, and `data/manifest.json`.
3. Run `uv run prepare.py` and verify the generated Markdown and manifest.
4. Initialize `results.tsv` with:

   ```text
   commit	objective_rmse	status	description
   ```

## Experimentation

Each experiment must finish within 2 minutes. This baseline is CPU-oriented;
GPU utilization is not an optimization target unless a future model explicitly
uses CUDA.

### Allowed changes

- Modify `train.py` for feature engineering, model family, or hyperparameters.
- Add focused tests when an experiment introduces behavior that needs coverage.

### Constraints

- Do not change source measurements or silently impute target labels.
- Do not change the campaign-based validation split to improve a score.
- Do not generate safety recommendations without source evidence and uncertainty.
- Do not modify `data/manifest.json` by hand.

The objective is `objective_rmse`, the mean RMSE across available validation
targets: burning rate and burn time. Lower is better. Missing targets are
masked independently per task. The validation campaign is fixed by date.

## Output

Run:

```bash
timeout 120 uv run train.py > run.log 2>&1
```

The script prints:

```text
objective_rmse: 0.123456
burning_rate_mm2_s_rmse: 0.012345
burn_time_s_rmse: 0.234567
predictions: predictions.json
```

Record each experiment in `results.tsv`. Use `inf` and status `crash` when
the run fails.

## Experiment loop

1. Inspect the current git state and `results.tsv`.
2. Make one focused change in `train.py`.
3. Commit it.
4. Run the bounded experiment.
5. If `objective_rmse` improves, keep the commit; otherwise revert it.
6. Record the result and a short description.

Never turn a predictive correlation into a safety recommendation automatically.
Insights must later be generated from source evidence, explicit uncertainty,
and human review.
