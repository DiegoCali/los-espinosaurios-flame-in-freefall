# BASS-II flame-spread analysis

Detection and measurement of flame spread in NASA **BASS-II** (Burning and Suppression of Solids II,
[PSI-25](https://psi.nasa.gov/physci/repo/data/investigations/PSI-25), DOI 10.60555/4qc4-de67) ISS videos,
followed by time-series forecasting of the measurements and a scientific visualisation layer.

```
NASA PSI API ──► catalog + download ──► frames (SAR-corrected, OSD masked)
                                          │            └─► OSD OCR: AIR / FAN / RAD / clock telemetry
                                          ▼
                              flame segmentation ──► per-frame metrics (area, centroid, sub-pixel edges, intensity)
                                                          ▼
                              leading/trailing edge ──► spread rate V_f(t) + steady Theil-Sen V_f with 95 % CI
                                                          ▼
                              forecasting (persistence, drift, Holt, Kalman, physics-linear) + rolling-origin backtest
                                                          ▼
                              figures G1–G18 with captions ──► Streamlit app / report
```

## Quick start (Windows, Python 3.14)
```bash
cd investigations/BASS-II
python -m venv .venv
.venv/Scripts/python -m pip install -e ".[app,docs,dev]"
.venv/Scripts/python -m pytest
.venv/Scripts/bass2 catalog
.venv/Scripts/bass2 fetch-docs
.venv/Scripts/bass2 analyze B1          # downloads the 5.8 MB B1 video and produces all per-test figures
.venv/Scripts/bass2 aggregate
.venv/Scripts/streamlit run app/streamlit_app.py
```
Full study chain (70 tests + hold-out): see `.claude/skills/bass2-pipeline/SKILL.md` or `reports/REPORT.md` §10.

## Results (see `reports/REPORT.md`, generated from the pipeline outputs)
- 83 tests processed: 70 study tests (all PIs and fuel types) + 13 hold-out slab tests; physics-review verdicts for
  the 70 study tests in `configs/qc.yaml` (the hold-out tests were not reviewed).
- Spatial scale from the duct ruler: ≈ 0.209 mm/px (≈ 0.8 % spread over 12 rulers); no published value used.
- Thin-film thickness law over 11 QC-trusted films (4 never used for tuning): slope ≈ −0.99 ± 0.05 (theory −1).
- Development tests (used to choose settings, in-sample): median error ≈ 4.5 % against published spread rates.
- Hold-out (13 slab tests, frozen settings; 12 gave a comparison, M15 showed no steady spread): median error ≈ 18 %
  over 14 flow-step comparisons — ≈ 15 % on first/single flow steps, ≈ 64 % on later steps after a flow change
  (thick slabs need minutes to re-equilibrate; not yet handled).
- Forecasting: the `kalman_conformal` ensemble promoted from the autonomous loop (val_score 1.19 → 0.64, run 013).

## Where things are
See `CLAUDE.md` (layout and invariants), `knowledge/README.md` (science and data), `docs/ROADMAP.md` (next steps),
`research/program.md` (autonomous improvement loop, no git).

## Agent team (`../../.claude/agents/`)
| Agent | Role |
|---|---|
| `bass2-literature-researcher` | papers, NASA reports, published reference values, knowledge base |
| `bass2-data-engineer` | PSI API, downloads, inventory, experimental-table parsing, fan calibration |
| `bass2-vision-scientist` | segmentation, edges, calibration, OSD OCR, gold set |
| `bass2-timeseries-modeler` | forecasting models, intervals, validation, harness metrics |
| `bass2-combustion-physicist` | physical plausibility, interpretation, priors |
| `bass2-viz-reporter` | figures, captions, report, Streamlit |
| `bass2-autoresearcher` | runs `research/program.md` loop |
| `bass2-reviewer` | independent scientific and code review |

## License
Code: MIT (see repository LICENSE). Data: NASA PSI-25, CC0-1.0.
