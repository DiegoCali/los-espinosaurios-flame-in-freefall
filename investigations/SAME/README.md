# SAME-R: smoke particle size, aging and detector response in microgravity

This module processes NASA's **Smoke Aerosol Measurement Experiment Reflight (SAME-R, PSI-101)** — smoke from
overheated spacecraft materials measured on the ISS in 2010 — into dashboard-ready JSON, clean CSVs, reports and
figures. It reproduces NASA's moment-method particle sizes, quantifies smoke aging by Brownian coagulation,
compares the ISS photoelectric and ionization (Space Shuttle-type) detector principles, and selects a predictive
model with an adapted **karpathy/autoresearch** loop.

The local download contains **47 SAME-R tests with 1 Hz telemetry (86 smoke pushes)** and **70 NASA moment
measurements**. No SAME-1 (PSI-102, 2007) flight data are present yet — see [data/raw/README.md](data/raw/README.md).

## Where to start

| File | What it contains |
|---|---|
| [SAME_EXPLICADO.md](SAME_EXPLICADO.md) | **Start here:** plain-English explanation of what was measured, calculated and found. (The `_EXPLICADO` file name mirrors `SAFFIRE_EXPLICADO.md`; the content is English.) |
| [analysis-same-summary.json](analysis-same-summary.json) | **Dashboard input** (English, `schema_version 1.0.0`). |
| [analysis/output/insights.json](analysis/output/insights.json) | Findings by theme + key insights with evidence and confidence. |
| [analysis/output/same-summary.png](analysis/output/same-summary.png) | Overview figure. |
| [SAME_ANALYSIS_REPORT_EN.md](SAME_ANALYSIS_REPORT_EN.md) | Long English report: methods, all metric definitions, all 15 attempts, exact selected architecture, data quality. |
| [analysis-same.md](analysis-same.md) | Compact technical report: tables, model ledger, data-quality notes, limitations. |
| [data/processed/VALIDATION.md](data/processed/VALIDATION.md) | Automated checks plus the audit of the 10 unlabeled tests and test 92. |
| [analysis-same.json](analysis-same.json) | Full scientific export (per-test, per-push, per-grid values; methods; CV predictions; scenarios). |
| [knowledge/SAME_KNOWLEDGE_BASE.md](knowledge/SAME_KNOWLEDGE_BASE.md) | SAME/SAME-R hardware, materials, moment method, coagulation, detectors, DAFT relation, data dictionary. |
| [DATA_PLAN.md](DATA_PLAN.md) | Extraction decisions, thresholds, modelling targets. |
| [program.md](program.md) | AutoResearch instructions (adapted, no git). |

## Key results

- Moment statistics reproduce the published SAME-2 Table 1 (Dm within 11% for all 10 material × aging cases).
- Kapton and Teflon (wire insulation) make the smallest smoke (Dm 0.10–0.23 µm); lampwick, Pyrell and silicone
  0.29–0.56 µm.
- With flow, ~9–13 min of aging leaves 27–50% of the particles and grows Dm ×1.25–1.56, exactly as mass-conserving
  coagulation predicts (K ≈ 9×10⁻¹⁰ cm³/s, consistent with NASA's note and Brownian theory); σg narrows in 11/12 runs.
- Without flow (microgravity-only) smoke has ×1.4–3.3 larger Dm and 7–18× fewer particles.
- **Detectors fail in opposite regimes**: with flow, ISS photoelectric 71% vs ionization 93% of pushes (Kapton: ISS
  27%); without flow, ISS 90% vs ionization 10%. Either: 95%. Shuttle detector alarmed in 6/9 powered pushes.
- Selected model (attempt 11 of 15): held-out Dm within a typical factor ×1.23, M0 ×1.35; detection Brier −51%;
  `val_score` 0.529 vs 1.043 for the mean baseline.

## Dashboard JSON: format and use

Load **`analysis-same-summary.json`**. Top-level layout matches `analysis-saffire-summary.json`.

| Field | Dashboard use |
|---|---|
| `title`, `summary`, `scope` | Header, mission, PSI ids and record counts. |
| `reading_guide` | Measured / published / calculated / insight / predicted / null semantics. |
| `measurements[]` | Cards: label, origin, result, why it matters, `detail_ref`. |
| `moment_method` | Explains AMD, Dm, Dg, σg with a real example (run 63). |
| `material_summary[]` | Median Dg, AMD, Dm, σg, M0 per material and aging state (8 cm/s flow). |
| `test_results[]` | One entry per test: material, flow, heater, STS installed, and `pushes[]` with aging and each detector's response and proxy decision. |
| `size_results[]` | One entry per NASA moment measurement with quality flags and `used_in_model`. |
| `detector_comparison` | Overall and per material × flow detection rates, thresholds, median response delays. |
| `coagulation` | Coefficient from this study, NASA's note and Brownian theory. |
| `insights[]` | Title, evidence, meaning, why it matters, confidence, `evidence_refs`. |
| `predictive_model` | Model, inputs, evaluation, score vs baseline, errors, `cv_predictions`, `scenarios`, limitations. |
| `unavailable_results[]` | Missing items with `value: null`, status and reason. |
| `source`, `charts[]`, `files` | Citation, figure paths with descriptions, supporting files. |

Integration rules:

- `null` means unavailable or not applicable — never render it as zero.
- `iss_detect_proxy` / `ionization_detect_proxy` are **proxy** decisions (ISS scatter drop ≥ 1.0 V; ionization
  rise ≥ 0.5 V vs clean air), not flight alarms. `sts_alarm` is the real Shuttle-detector alarm bit (9 pushes).
- `predictive_model.scenarios[]` gives predicted Dg/Dm/AMD/σg/M0 and detection probabilities per material,
  flow regime and aging time; `iss_false_negative_risk` = 1 − P(ISS response). Rows with `extrapolated: true`
  are outside the trained aging range.
- Paths are relative to this folder; copy the JSON and the PNGs keeping the paths, or resolve them against the
  dashboard's asset base.

```javascript
const same = await (await fetch("/investigations/SAME/analysis-same-summary.json")).json();
if (same.schema_version !== "1.0.0") throw new Error("Unsupported SAME summary format");
const kapton = same.detector_comparison.by_material_and_flow
  .filter(r => r.material === "Kapton")
  .map(r => ({ flow: r.flow_regime, iss: r.iss_rate, ionization: r.ion_rate }));
```

## Figures and how to read them

All figures use one colour and marker shape per material (Kapton ●, Lampwick ■, Pyrell ▲, Silicone ◆,
Teflon ▼); filled = unaged or with flow, hollow = aged or no flow.

1. **[Overview](analysis/output/same-summary.png)** — left: Dm before → after aging per material with published
   ticks; middle: share of pushes each detector type responded to, with and without flow; right: held-out error of
   the selected model vs the mean baseline (1.0 = no better than the average).
2. **[Moments by material](data/processed/figures/moments_by_material.png)** — Dg, AMD, Dm and σg for every grid
   (8 cm/s). Kapton/Teflon are smallest; aging moves points up and narrows σg.
3. **[Aging and coagulation](data/processed/figures/aging_coagulation.png)** — left: particle count ratio vs aging
   time with Smoluchowski curves; right: observed Dm growth vs the mass-conservation prediction — points on the 1:1
   line mean coagulation alone explains growth.
4. **[Flow effect](data/processed/figures/flow_effect.png)** — still-air smoke is coarser but far more dilute.
5. **[Detector comparison](data/processed/figures/detector_comparison.png)** — each push placed by ionization (x)
   and ISS scatter (y) response; the upper-left cluster is no-flow smoke only the ISS saw, the lower-right cluster
   is Kapton/Teflon smoke only ionization saw.
6. **[Threshold sensitivity](data/processed/figures/threshold_sensitivity.png)** — the opposite failure modes hold
   for every threshold tested.
7. **[Anatomy of a test](data/processed/figures/example_timeseries.png)** — heating, fill, aging and two pushes in
   test 64 across five instruments.
8. **[Size distributions](data/processed/figures/size_distributions.png)** — reconstructed log-normals vs the
   light-scattering-efficient range; TEM sizing of run 54 vs the moment method (TEM misses small particles).
9. **[Model cross-validation](data/processed/figures/model_cv.png)** — observed vs held-out predictions for Dm, σg,
   M0 and calibration of the detection probabilities.
10. **[AutoResearch progress](data/processed/figures/autoresearch_progress.png)** — the 15 attempts.
11. **[Model scenarios](data/processed/figures/model_scenarios.png)** — predicted Dm growth with transport time and
    false-negative risk of each detector type by material and flow.

## Reproduce

Requirements: Python ≥ 3.10 and [uv](https://docs.astral.sh/uv/) (the system Python here lacks `ensurepip`);
LibreOffice `soffice` is optional (coagulation `.doc`; a transcription is used otherwise).

```bash
cd investigations/SAME
uv venv .venv && uv pip install --python .venv/bin/python -r pyproject.toml --extra dev
.venv/bin/python -m extraction.run_all                 # raw → data/processed (finds ../../data automatically)
.venv/bin/python prepare.py --check                    # dataset summary + protected-file hashes
.venv/bin/python analysis/build_analysis_json.py       # JSON, reports, all figures
.venv/bin/python -m pytest -q                          # physics, extraction and gate tests
.venv/bin/python scripts/verify_reproducibility.py     # re-extract, compare hashes, re-score best model
.venv/bin/python scripts/final_audit.py                # full audit suite -> runs/verification/ (8 artefacts)
```

## AutoResearch adaptation (no git)

`upstream_reference/` keeps the original karpathy/autoresearch files (commit in `UPSTREAM_COMMIT.txt`). As upstream,
`prepare.py` is fixed (data, folds, metric) and `train.py` is the only file the agent edits. Instead of
`git commit` / `git reset`, `scripts/run_experiment.py` archives each attempt in
`runs/autoresearch/same-run-01/` (`attempt-XX.json`, `attempt-XX.train.py`, `results.tsv`, `best.json`,
`best_train.py`) and restores `train.py` from `best_train.py` after a discard. A SHA-256 manifest protects
the evaluator and data. The run is complete (15/15 attempts); a new study needs a new run directory.

## Layout

```
extraction/   inventory, reduced NASA tables, telemetry segmentation, TEM, model tables
analysis/     physics (moments, coagulation), insights, figures, JSON/report builders
scripts/      run_experiment.py (AutoResearch launcher), verify_reproducibility.py
tests/        physics, extraction science checks, train.py contract gate
data/         raw/ (git-ignored), inventory/, processed/ (CSVs, figures)
runs/         autoresearch/same-run-01/, verification/
knowledge/    SAME knowledge base
```

## What belongs in Git

Commit code, JSON exports, Markdown, processed CSVs, figures, inventory and `runs/`. `data/raw/`, `.venv/` and
caches (`__pycache__`, `.pytest_cache`, `.mplconfig`) are ignored. `data/processed/` stays visible on purpose: the
dashboard JSON links to its figures and CSVs (SAFFIRE does the same). (No commits were made while building this module.)

## Source and attribution

NASA Physical Sciences Informatics, PSI-101 *Smoke Aerosol Measurement Experiment Reflight (SAME-R)*, PI D. L.
Urban (NASA Glenn). Urban DL et al., AIAA 2012-3536 (NTRS 20130000422). NASA supplied telemetry, reduced moment
tables, TEM analyses and documents; extraction, segmentation, detector metrics, coagulation analysis, modelling and
interpretation were produced in this project.
