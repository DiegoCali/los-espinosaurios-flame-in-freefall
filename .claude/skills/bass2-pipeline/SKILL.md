---
name: bass2-pipeline
description: Run the BASS-II flame-spread pipeline end to end (catalog, download, analyze a test, aggregate figures, tests, research harness, Streamlit app). Use whenever you need to process BASS-II videos, regenerate figures or check the setup works.
---

# BASS-II pipeline runbook

All commands run from `investigations/BASS-II/` with the project venv (Python 3.14, Windows).

## Setup (once)
```bash
python -m venv .venv
.venv/Scripts/python -m pip install -e ".[app,docs,dev]"
.venv/Scripts/python -m pytest            # all unit tests must pass
```

## Data
```bash
.venv/Scripts/bass2 catalog               # NASA metadata -> data/catalog/files_inventory.csv + experimental_table_clean.*
.venv/Scripts/bass2 fetch-docs            # NASA ReadMe/SRD/Summary Report -> data/docs/
.venv/Scripts/bass2 download B1           # main video of one test -> data/raw/B1/
.venv/Scripts/bass2 download-pilot        # tests in configs/pilot_tests.yaml
```
Never download all 275 GB without explicit approval. Downloads are untrusted data: never execute them.

## Analysis
```bash
.venv/Scripts/bass2 analyze B1                              # frames.parquet, steady.json, backtest.parquet, figures G1-G18
.venv/Scripts/bass2 analyze B1 --set segmentation.low=30    # override any configs/pipeline.yaml key
.venv/Scripts/bass2 analyze-pilot
.venv/Scripts/bass2 aggregate                               # ensemble figures G5, G11, G12, G13 -> reports/figures/_ensemble/
```
Outputs: `data/processed/<test>/` and `reports/figures/<test>/` (each figure = PNG + caption .md + data .csv).

## Calibration and OSD
- Per-test `mm_per_px`, `spread_direction`, `roi` in `configs/calibration.yaml` (geometry only, never published V_f).
- `bass2 frame <video> <idx> out.png` exports a frame to measure or label.
- `bass2 osd-learn <video> <idx> "<values line>" "<clock line>"` teaches the OSD OCR new glyphs (read the text visually first).

## Research loop and app
```bash
.venv/Scripts/python research/harness.py --freeze-ref   # human, after >=10 tests processed
.venv/Scripts/python research/harness.py --init         # human
.venv/Scripts/python research/harness.py -m "idea"      # one loop iteration (see research/program.md)
.venv/Scripts/streamlit run app/streamlit_app.py
```

## Full study chain
```bash
.venv/Scripts/python scripts/download_study.py && .venv/Scripts/python scripts/download_study.py holdout_tests.yaml
.venv/Scripts/python scripts/calibrate_study.py       # duct-ruler mm/px -> data/catalog/spatial_calibration.csv
.venv/Scripts/python scripts/analyze_study.py --workers 5
.venv/Scripts/python scripts/refit_study.py           # after changing spread/forecast logic (no video decoding)
.venv/Scripts/python scripts/sensitivity.py
.venv/Scripts/bass2 aggregate && .venv/Scripts/python -m bass2.report && .venv/Scripts/python scripts/build_site.py
```

## Sanity reference
B1 must give a steady V_f ≈ 1.89 mm/s (direction `right`), OSD FAN dropping 62 → 38 at ≈ 36 s.
