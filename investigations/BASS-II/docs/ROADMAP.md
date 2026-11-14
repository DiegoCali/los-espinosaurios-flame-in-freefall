# Implementation roadmap

Status as of 2026-11-13: full study set (70 tests, all PIs and regimes) processed and validated against published
spread rates. Each task names the responsible agent (`.claude/agents/`).

## Done ✅
### Data
- NASA PSI API access (metadata + presigned S3 URLs), resumable downloads; 694-file inventory (274.6 GB).
- Study set: 70 main videos (1.5 GB, `configs/study_tests.yaml`, `scripts/download_study.py`); irregular names
  (`TESTB6`, `test T13`) classified correctly.
- B14, B18, B20 main MP4s are truncated on the NASA server (no `moov` atom): recovered from `original videos.zip` (MPEG-TS).
- M3 has only a rack-camera video recorded during loss of signal: excluded from validation.
- Experimental table parser rebuilt (flow steps in cm/s, as-run cross-check, O2 convention, regime, geometry; 46 tests).

### Measurement
- **Spatial calibration** from the duct ruler in illuminated frames: global fixed-FOV scale 0.2094 mm/px (±0.6 %,
  n = 10 rulers, 4 PIs, 5 months) — `knowledge/methods/spatial_calibration.md`.
- Illuminated (lights-on) frames detected and excluded; static artefacts (LEDs, hot pixels) masked per video.
- **Adaptive segmentation**: noise-relative hysteresis + blue-excess channel (faint blue edges of thick films).
- **Spread regimes**: median-binned leading edge split by optimal piecewise-linear segmentation; steady V_f =
  Theil-Sen slope of the longest significantly advancing regime (≥ 2 mm advance); per-FAN-plateau rates.
- **OSD OCR** with per-video layout detection and per-line character sets (FAN/AIR read on almost every video).
- Adaptive frame step (≤ 2500 frames per video) for 20-minute slab tests.

### Review-driven fixes (2026-11-13)
- Independent review (bass2-reviewer) → disclosure of in-sample development tests, hold-out slab set evaluated once
  with frozen settings, QC shown with and without exclusions, Hungarian step matching, Hampel edge filter,
  autocorrelation-aware CIs, Kalman floors, harness guard during module load and in worker processes.
- Physics review (bass2-combustion-physicist) → `configs/qc.yaml` verdicts for all 70 tests; anemometer lag 20 s;
  G5 at the steady-window air velocity.
- Autonomous loop: 14 evaluations, val_score 1.187 → 0.643; ensemble forecaster promoted (`kalman_conformal`);
  1 px erosion rejected (helps synthetic D only).
- Shareable report page: https://claude.ai/artifact/2M7xntZqjqgXsTVzLwwf6y (private until shared).

### Validation, forecasting, reporting
- External validation vs. SDSU (B) and NASA TM Table 5.1 (M) values; scale-free thickness law; O2 trend checks.
- Forecasting: persistence, drift, damped Holt, physics-linear, Kalman CV, **Kalman with ML-estimated noise**.
- Research harness with components D, R (spread-rate accuracy), C, M, P; snapshots instead of git.
- Figures G1–G7, G9–G16, G18, G19 with captions; `reports/REPORT.md` and the shareable page (`scripts/build_site.py`).
- 58 unit tests.

## Next
1. **`bass2-vision-scientist` + human** Gold set (`evaluation_protocol.md` §2): ~150 frames stratified by PI/material,
   masks `data/gold/<test>/<frame>_frame.png` + `_mask.png` (128 = flame, 255 = ignore), and gold edge tracks.
   Adds component E and replaces the synthetic D.
2. **`bass2-literature-researcher`** More published per-test values (T fabric, O/P rods) to widen validation beyond B/M,
   ideally values not used in any modelling choice (true hold-out).
3. **`bass2-vision-scientist`** Faint-flame edge for thick films (B12 still −8 %); second view (`2ND_VIEW`) for standoff (G8).
4. **`bass2-timeseries-modeler`** Global models across tests with O2/flow/material covariates (LOTO/LOPO);
   conformal intervals; Chronos/TimesFM zero-shot references in a separate environment.
5. **`bass2-autoresearcher`** Continue `research/program.md` with a larger frozen reference set.
6. **`bass2-reviewer`** Independent review before any external publication.
