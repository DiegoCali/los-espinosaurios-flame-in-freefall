# Raw data for the SAME module

The extraction looks for the NASA PSI files in this order:

1. the folder in the `SAME_RAW_DATA` environment variable;
2. this folder (`investigations/SAME/data/raw/`);
3. the repository-level `data/` folder (git-ignored), where the team's SAME-R download already lives.

Files are only read, never modified. Put them flat in one folder (no sub-folders), with their original names.

## PSI-101 — SAME-R (2010 reflight) · required

| File(s) | Used for |
|---|---|
| `HKPData_gmt*.csv` (44 files) | 1 Hz telemetry of tests 58–108: phases, aging, flow, every detector response |
| `Sample descriptions tables.docx` | NASA/NIST moment results per TEM grid (M0, AMD, Dm, σg, Rt/R0, morphology) — **main size table** |
| `thermal precipitator map updated.xlsx` | Grid ↔ run ↔ sample (`SAMERFLT nnX`) mapping and pre/post-age labels |

## PSI-101 — recommended

| File(s) | Used for |
|---|---|
| `2010_210_10_lampwick_run54.xls`, `2010_210_10_lampwick_run55.xls` | Telemetry for runs 54 and 55 (other `2010_*.xls` copies are detected as duplicates) |
| `TEMflowvsnoflow.xls` | Reduced flow/no-flow table: inlet velocity, net aging (validation of the telemetry segmentation) |
| `ISS Coagulation.doc` | Coagulation reference cases (needs LibreOffice `soffice`; a transcription is used otherwise) |
| `54 lampwick binneddatacorr from GWM.xlsx`, `55 Lampwick.xlsx`, `SPV of 54-7L_21 all quarters (3).xlsx` | TEM per-particle sizing |
| TEM `*.pptx`, `*.pdf`, `#nn ….zip`, `*.tif` | Only inventoried (run/material labels for tests without a moment row) |
| `SAME Verification Plan & Engineering Requirements Document (VPRED), Jan 2007.pdf` | Hardware reference (knowledge base) |

`*.mp4` / `vlc-record*.zip` videos (~4 GB) are optional: only their names and start times are inventoried.

## PSI-102 — SAME (2007 first flight) · not yet present

No SAME-1 flight files were found in the local download. If the team adds them, the module needs the
equivalent of the files above: the housekeeping CSV/XLS telemetry for SAME-1 tests and NASA's reduced
moment table. SAME-1 used two DustTraks (1 µm and 10 µm impactors) and no MPASS, so its column names may
differ; `extraction/housekeeping.py` (`HKP_CHANNELS`) is the single place to map them.

## Run

```bash
cd investigations/SAME
.venv/bin/python -m extraction.run_all          # or: SAME_RAW_DATA=/path/to/files .venv/bin/python -m extraction.run_all
```
