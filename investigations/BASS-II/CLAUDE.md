# BASS-II — flame-spread detection, measurement and forecasting

NASA PSI-25 "Burning and Suppression of Solids II" (ISS Microgravity Science Glovebox, 2012–2014, CC0).
Goal: computer vision on the experiment videos → flame area / position / shape / spread rate time series →
forecasting models → well-explained scientific figures, validated against published values.

## Read first
1. `knowledge/README.md` — index of the knowledge base and the facts every agent must remember.
2. `docs/ROADMAP.md` — status and next tasks (with the responsible agent).
3. `.claude/skills/bass2-pipeline/SKILL.md` (repo root) — commands.

## Layout
| Path | Content |
|---|---|
| `src/bass2/` | package: catalog, download, video, osd, segmentation, metrics, spread, forecast, evaluation, viz, pipeline, cli |
| `configs/` | `pipeline.yaml` (all parameters), `calibration.yaml` (per test), `pilot_tests.yaml`, OSD OCR grid/templates |
| `data/catalog/` | NASA metadata JSON, file inventory, cleaned experimental table, test matrices, fan calibration (tracked) |
| `data/reference/` | published spread rates (ground truth) — read only on the evaluation side: `src/bass2/validation.py`, `research/harness.py`, `scripts/compare_segmenters.py` |
| `data/docs/`, `data/raw/`, `data/processed/` | NASA documents, downloaded videos, per-test outputs (git-ignored, regenerable) |
| `knowledge/` | dataset, physics, literature, methods, evaluation protocol (+ raw text of NASA docs) |
| `research/` | autoresearch loop without git: `program.md`, `harness.py` (fixed), `experiment.py` (edited by the agent) |
| `reports/` | figures (`figures/<test>/G*.png|md|csv`, `figures/_ensemble/`) and the final report |
| `app/streamlit_app.py` | scientific visualisation interface |
| `tests/` | synthetic unit tests (`.venv/Scripts/python -m pytest`) |

## Invariants
- Use `.venv` (Python 3.14). Run commands from this directory.
- Video is 720×480 @ 29.97 fps with **SAR 10:11**; OSD band (y < 90 px) masked; OSD date is +1 day.
- `mm_per_px` only from geometry; never derived from published spread rates (circular validation).
- Measurement code (`src/bass2/` except `validation.py`) and `research/experiment.py` must not read `data/reference/`,
  `data/gold/`, `data/holdout/`. Hold-out tests (`configs/holdout_tests.yaml`) are evaluated once, with frozen settings.
- Physics QC verdicts live in `configs/qc.yaml` (source: `reports/physics_review.md`).
- Figures: fixed palette, no dual y-axis, uncertainty shown, caption explains what to conclude (`bass2-figures` skill).
- No git write operations. Everything written in English.
