# los-espinosaurios-flame-in-freefall

Automatic detection, measurement and forecasting of **flame spread in microgravity** from NASA's
**BASS-II** (Burning and Suppression of Solids II, [PSI-25](https://psi.nasa.gov/physci/repo/data/investigations/PSI-25))
ISS videos, with a scientific report of explained figures.

## Main deliverable
| What | Where |
|---|---|
| Full project (code, data catalog, knowledge base, results) | [`investigations/BASS-II/`](investigations/BASS-II/README.md) |
| Scientific report (generated from the pipeline outputs) | [`investigations/BASS-II/reports/REPORT.md`](investigations/BASS-II/reports/REPORT.md) |
| Physics review of every test | [`investigations/BASS-II/reports/physics_review.md`](investigations/BASS-II/reports/physics_review.md) |
| Shareable report page | `investigations/BASS-II/reports/site/index.html` (built by `scripts/build_site.py`) |
| Interactive app | `investigations/BASS-II/app/streamlit_app.py` |

## Key results
- 83 tests analysed (70 study tests across all PIs and fuel types + 13 hold-out slab tests).
- Spatial scale from the duct's own ruler (≈ 0.209 mm/px, ≈ 0.8 % spread over 12 rulers), without using published values.
- Thin-film spread rate follows the de Ris thickness law: slope −0.99 ± 0.05 over 11 films (theory −1).
- Spread rates agree with published NASA/SDSU values within ≈ 4.5 % (median) on the development tests (in-sample);
  on 13 hold-out slab tests the median error is ≈ 18 % overall, ≈ 15 % on first/single flow steps and ≈ 64 % on later
  flow steps, which are not yet reliable (see report §4, §9).
- Forecasting ensemble promoted from an autonomous research loop (fixed harness, val_score 1.19 → 0.64).

## Quick start
```bash
cd investigations/BASS-II
python -m venv .venv
.venv/Scripts/python -m pip install -e ".[app,docs,dev]"
.venv/Scripts/python -m pytest
.venv/Scripts/bass2 analyze B1
```
The full study chain is documented in `.claude/skills/bass2-pipeline/SKILL.md`.

## Repository layout
- `investigations/BASS-II/` — the project (see its `README.md` and `CLAUDE.md`).
- `investigations/BASS-II/autoresearch/` — Karpathy's original autoresearch template, kept as reference.
- `investigations/flex/` — placeholder for a FLEX investigation.
- `.claude/agents/` — the project's agent team (`bass2-*`); `.claude/skills/` — project skills.

## Data and license
Data: NASA Physical Sciences Informatics, investigation PSI-25 (DOI 10.60555/4qc4-de67), CC0-1.0. Videos are not
stored in the repository; `scripts/download_study.py` fetches them from the public PSI API. Code: see `LICENSE`.
