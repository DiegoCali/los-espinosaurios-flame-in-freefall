# autoresearch-flame — agent program

Adaptation of the autoresearch pattern (`../autoresearch/`, Karpathy) to BASS-II: an agent edits **a single
file** (`research/experiment.py`) and keeps only the changes that improve a **fixed metric**
(`val_score`, lower is better) computed by a harness it cannot touch (`research/harness.py`).

**Key difference from the original: NO git.** The harness snapshots every attempt in `research/runs/NNN/`,
keeps the best in `research/best/`, and automatically reverts `experiment.py` when an attempt does not improve.
Never run `git commit`, `git checkout`, `git reset` or create branches.

## Setup (done by a human, or by the agent after confirmation)

1. Read for context: `CLAUDE.md`, `knowledge/README.md`, `knowledge/methods/evaluation_protocol.md`,
   `knowledge/methods/computer_vision.md`, `knowledge/methods/time_series_forecasting.md`,
   `knowledge/physics/flame_spread_physics.md`, `src/bass2/forecast.py`, `src/bass2/segmentation.py`.
2. Check that processed tests exist: `ls data/processed/` (if not: `bass2 download-pilot && bass2 analyze-pilot`).
3. Freeze the reference series (human): `.venv/Scripts/python research/harness.py --freeze-ref`.
4. Measure the v0 baseline (human): `.venv/Scripts/python research/harness.py --init`.
5. Confirm and start the loop.

## What you CAN do
- Edit `research/experiment.py`: segmentation parameters and function, choice and parameters of the
  forecaster, resampling rate. You may write new models *inside* that file using
  numpy/scipy/statsmodels/scikit-learn/opencv/scikit-image (already installed).
- Read any file under `knowledge/` and `src/` for ideas.

## What you CANNOT do
- Modify `research/harness.py`, `src/bass2/evaluation.py`, or the frozen series.
- Read `data/reference/`, `data/gold/`, `data/holdout/` from `experiment.py` (an audit hook blocks it).
- Per-test parameters (`if test_id == ...`), constants tuned to one specific test, or using the published
  spread rates as features.
- Install packages. Run any git operation.

## Loop (repeat until the human interrupts)
1. Read `research/results.tsv` and `research/best/experiment.py` to know where you are.
2. Formulate ONE concrete hypothesis (see ideas below) and edit `research/experiment.py`.
3. Run: `.venv/Scripts/python research/harness.py -m "<short description>" > research/run.log 2>&1`
4. Read the result: `tail -n 9 research/run.log`. If it is empty or shows a traceback: `tail -n 40 research/run.log`,
   fix it if trivial; if the idea is unworkable, move on (the harness has already logged it).
5. The harness decides `keep` (improvement > 0.005) or `discard` (it reverts by itself). Nothing else to do.
6. Every 10 `keep`s: generate control figures (`bass2 analyze <test>` on 2–3 tests with the segmentation
   parameters of the best experiment via `--set`) and look at them: a numerical gain with worse overlays is
   discarded manually (copy `research/runs/<previous>/experiment.py` back).

**Simplicity**: at equal score, the simpler code wins. Deleting code without getting worse is a win.
**Scepticism**: with few tests in the reference, large sudden gains are usually overfitting.
Prefer changes with a physical or statistical justification, not magic numbers.

## Where things stand (2026-11-13)
- `experiment.py` v0 = fixed hysteresis 40/90 + constant-velocity Kalman with heuristic noise. It is the
  reference point of the loop (v0 ≈ 1.0 in every normalised component).
- The production pipeline (`configs/pipeline.yaml`) already uses the noise-relative `adaptive` segmenter
  (+ static-artefact mask) and offers `kalman_mle` (maximum-likelihood q, r). On the 8 reference tests the
  adaptive segmenter gives mean |ln V/V_pub| ≈ 0.04 vs ≈ 0.5 for v0. Reproducing and then beating these is
  the first goal of the loop.
- The harness now has component **R** (spread-rate accuracy on B1, B2, B3, B4, B5, B7, B12, M1; cached per
  segmenter hash) and a gate: the candidate must measure at least 7 of the 8 tests.

## Starting ideas (ordered by expected value)
Forecasting (C, M, P weigh 0.45):
- Calibrate the intervals: v0 (constant-velocity Kalman) has coverage ≈ 1.0 (too wide; P = 1). Estimate `q`
  and `r` by maximum likelihood of the innovations on the history itself (unit-invariant) instead of fixing
  them. Conformal intervals from in-history one-step residuals.
- Blend Kalman + `physics_linear` (Theil-Sen) weighted by recent error.
- For `log_area`: damped ETS, or a logistic (growth to plateau) / exponential-decay fit.
- Detect regime changes (flow steps) and restart the model window after a change.
Segmentation (D weighs 0.15; E and R switch on with gold data and calibration):
- Background-relative thresholds (μ + kσ, MAD) instead of absolute 40/90.
- `blue_excess` channel combined with `value` (faint blue base vs. saturated core).
- Reduce edge dilation (known ~1 px bias from blur + low threshold).

## Harness output format
```
---
val_score:  0.932212
D:          1.0000
C:          0.9004
M:          0.8422
P:          1.0000
status:     keep
runtime_s:  1.1
```
`results.tsv` (tab-separated): `run  val_score  D  C  M  P  cov90  D_source  runtime_s  status  description`.

## Design notes
- Components are normalised by v0 (D) or by the local linear model `drift` (C, M), so 1.0 ≈ "same as the
  baseline" and < 1 is an improvement.
- `D_source = synthetic` until a human gold set exists in `data/gold/`; with real gold data D changes scale:
  re-run `--init` (human) when it is introduced.
- R uses the geometric ruler calibration (`data/catalog/spatial_calibration.csv`); E (edge vs. gold tracks)
  will be added once a hand-labelled gold set exists; see `docs/ROADMAP.md`.
- Demonstration on B1 only (2026-11-12): setting the Kalman `q=1e-3` took val_score 0.932 → 0.601 and
  coverage 1.00 → 0.906 — but `q` is unit-dependent and one test is not enough evidence, so the state was
  reset to v0. Prefer the unit-invariant MLE approach above.


## Outcome of the first loop phase (2026-11-13, 14 evaluations)
- val_score 1.187 → **0.643** (run 013). Kept changes: KalmanMLE → conformal intervals → Kalman/local-trend blend →
  normalised conformal → adaptive segmentation (R 1.00 → 0.37) → 1 px erosion (synthetic D only) → per-horizon
  inverse-MSE weights over Kalman, local linear trend and persistence.
- Promoted to production: the forecaster (`bass2.forecast_ensemble`, model `kalman_conformal`).
- **Not** promoted: the 1 px erosion. It improves the synthetic D score but worsens real spread-rate accuracy on faint
  flames (B3, B12); real data take precedence until a hand-labelled gold set replaces the synthetic D.
- Caveat for the next phase: R uses the development tests, so gains on R are in-sample; keep the hold-out
  (`configs/holdout_tests.yaml`) out of the loop.
