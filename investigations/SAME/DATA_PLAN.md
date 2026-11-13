# SAME data plan: extraction decisions, targets and assumptions

## Sources and identity

The local download (repository `data/`, 230 files, 5.4 GB) is **SAME-R / PSI-101**: TEM grids are labelled
`SAMERFLT <n><material>`, telemetry is GMT day 210–252 of 2010 (ISS Expedition 24), and test numbers run
48–108. No SAME-1 (PSI-102, 2007) flight data are present. See `data/inventory/INVENTORY.md`.

## Pipeline (`extraction/run_all.py`)

| Step | Module | Output |
|---|---|---|
| Inventory, SHA-256, run/sample parsing | `inventory.py` | `data/inventory/files.csv`, `INVENTORY.md` |
| NASA/NIST reduced tables | `reduced_tables.py` | `nasa_moment_table.csv`, `nasa_flow_aging_table.csv`, `thermal_precipitator_map.csv`, `coagulation_reference.csv`, `published_table1_baseline.csv` |
| 1 Hz telemetry → phases and responses | `housekeeping.py` | `hkp_timeseries_clean.csv.gz`, `tests.csv`, `pushes.csv`, `hkp_provenance.csv` |
| TEM particle sizing | `tem.py` | `tem_particles.csv`, `tem_summary.csv` |
| Fixed modelling tables | `model_data.py` | `size_dataset.csv`, `detection_dataset.csv` |

## Decisions

1. **Calibrated moments come from NASA**, not from raw voltages. The P-Trak is diluted by a variable dynamic
   diluter and the ionization/DustTrak calibrations are per size/material; recomputing calibrated moments from
   telemetry would invent calibration factors. Raw channels are used as **detector responses**.
2. **Aging state of a grid**: docx label → precipitator-map pre/post label (also when the docx gives the same
   label twice, run 58) → row order within a run → `unknown` (excluded from models).
3. **Rt/R0** is inherited by the post-age row of the same run (written once per run in the docx).
4. **QC**: AMD > 2 µm, σg outside 1–4, Dm ≤ 0, or Dm < AMD are flagged; flagged values are set to null in the
   clean columns (raw values kept in `*_raw`). Nothing is silently corrected.
5. **Test segmentation**: fill end = last closing of the piston vacuum valve before the first push; pushes =
   rising edges of the piston GN2 valve; aging = push − fill end; `aged` if ≥ 120 s. Test 63 (log starts after
   the fill) uses first push + 38 s. Agreement with NASA's "net aging": median ≤ 6 s; run 54 differs by 19 s.
6. **Flow velocity** = median MFC fill flow during heating × 8.1 / 4.29 cm/s per L/min (NASA nominal anchor).
   Documents call runs 107–108 "low flow", but the MFC reads 0 → treated as no-flow (flagged in `flow_source`).
7. **Detector responses** are peak changes within 180 s after each push relative to the pre-heating clean-air
   median: ISS scatter drop, ISS obscuration drop (%), Ion B rise, DustTrak peak, P-Trak peak, STS alarm bit.
8. **Proxy detection thresholds** (not flight alarm logic): ISS scatter drop ≥ 1.0 V (≈16% of its 6.1 V range),
   ionization rise ≥ 0.5 V. Sensitivity over 0.25–3 V and 0.1–1.5 V is exported and plotted.
9. **Materials** come from the moment table, precipitator map or TEM file names. Ten tests (59, 61, 65, 66, 86, 90,
   91, 99, 102, 103) have none of these and stay `unknown` in the frozen model data; see "The 10 unlabeled tests".
   Test 92 was assigned lampwick from a video start time; the heater fingerprint contradicts that (below).
10. **Duplicates**: the three run-55 spreadsheets and the "run59 wrong seems to be 60" file are identical
    copies identified by `TestNumber`; the first copy is used and the others are logged in `hkp_provenance.csv`.

## Modelling targets (fixed in `prepare.py`)

- **Size** (52 grids / 35 runs): log10 Dg, log10 Dm, log10 AMD, ln σg, log10 M0 from material, aged, aging time,
  flow velocity, no-flow flag and Rt/R0. Metric: mean NRMSE (RMSE / SD of each target), leave-one-run-out.
- **Detection** (65 pushes / 36 tests): probability that the ISS photoelectric response and the ionization
  response exceed their proxy thresholds, from material, aging, flow, Rt/R0 and push index. Metric: mean Brier
  ratio (Brier / Brier of the prevalence), leave-one-test-out.
- `val_score = 0.5·size + 0.5·detection`; a constant-mean model scores ≈ 1.

Why these targets: they are the quantities a detector designer needs (how big and how many particles reach the
detector after a given transport time, and which sensing principle will respond), they exist for every usable
run, and NASA's reduction makes them comparable across materials.

## The 10 unlabeled tests (audit, 2026-11-13)

Full evidence and tables: [data/processed/VALIDATION.md](data/processed/VALIDATION.md); per-test values:
`data/processed/test_material_audit.csv`; code: `extraction/material_audit.py`.

- **They are not blank, calibration or purge runs.** Those periods are the `TestNumber = 0` records between tests,
  already excluded. All ten are numbered tests with 52–54 s of heating, plume temperatures of 61–115 °C and one or
  two smoke pushes. Nine gave a measurable detector response; test 90 produced almost no smoke (DustTrak 0.1 mg/m³).
- **No document names their material.** None of the ten appears in `Sample descriptions tables.docx` or
  `thermal precipitator map updated.xlsx` (no grid was analysed), and `ISS Coagulation.doc` has no run ids. GMT
  timestamps cannot be matched to these documents, whose dates are TEM viewing dates.
- **The telemetry can still identify the material.** The heater wire's cold resistance and Rt/R0 match NASA's
  Rt/R0 within 0.02 and cluster by material. A 1-nearest-neighbour fingerprint agrees with the known material on
  34 of 36 labelled tests (leave-one-out). Inferred: silicone for 59, 65, 66, 86, 91, 99, 103 (DBP on wick cannot be
  excluded; 91 has the lowest margin) and Kapton for 61, 90, 102.
- **Use.** These are inferences, exported as `material_inferred`; they are **not** NASA labels and were **not** used in
  `size_dataset.csv`, `detection_dataset.csv` or the model search. Adding them to the detection task changes the
  frozen model's Brier ratio from 0.491 to 0.499.
- **Test 92 correction.** Its fingerprint (0.645 Ω, Rt/R0 1.368) matches Kapton, not lampwick (≈0.76 Ω, 1.27). The frozen
  run keeps the original label so the archived evaluation is not rewritten; relabelling gives 0.511
  (`runs/verification/material_audit_sensitivity.json`). A new study should rerun the search with audited labels.
