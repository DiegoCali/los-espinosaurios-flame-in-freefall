# BASS-II knowledge base (index)

Read in this order if you are new (human or agent). Everything is in technical English with sources (URL) per claim.

| # | File | Purpose |
|---|---|---|
| 1 | [dataset/bass2_dataset.md](dataset/bass2_dataset.md) | **What the data are**: hardware, cameras, file types, fan calibration, spatial scales, materials, test procedure, naming conventions, caveats and analysis candidates |
| 2 | [dataset/video_format_probe.md](dataset/video_format_probe.md) | **Empirical** probe of real files: download API, 720×480 @ 29.97 fps, non-square pixel (SAR 10:11), burned-in OSD, NEF RAW |
| 3 | [dataset/test_matrix_notes.md](dataset/test_matrix_notes.md) | Dirty columns of the experimental table and proposed clean schema |
| 4 | [physics/flame_spread_physics.md](physics/flame_spread_physics.md) | **Physics**: opposed vs. concurrent, de Ris, kinetic/thermal/radiative regimes, extinction, which video observable corresponds to which quantity, priors for forecasting |
| 5 | [literature/publications.md](literature/publications.md) | 17+ publications, **table of reference values per test** (ground truth), prior art |
| 6 | [methods/computer_vision.md](methods/computer_vision.md) | Recommended vision pipeline and alternatives (thresholds, SAM2, U-Net), subpixel edges, calibration, auto-exposure |
| 7 | [methods/time_series_forecasting.md](methods/time_series_forecasting.md) | Forecasting models for short/physical series, rolling-origin / LOTO / LOPO validation, metrics |
| 9 | [methods/spatial_calibration.md](methods/spatial_calibration.md) | **mm/px calibration** from the duct ruler: global fixed-FOV scale 0.2094 mm/px ± 0.6 %, method and assumptions |
| 8 | [methods/evaluation_protocol.md](methods/evaluation_protocol.md) | **Scalar objective `val_score`**, gold set, anti-overfitting, figure catalog G1–G17 |
| — | [dataset/raw_text/](dataset/raw_text/) | Plain text extracted from ReadMe, Ops, SRD, Summary Report (NASA/TM-20210011385) and engineering requirements — for `grep` |

## Facts every agent must remember

- Main video: 720×480, 29.97 fps, **SAR 10:11** (multiply horizontal distances by 10/11).
- OSD: `FUEL AIR FAN RAD` + clock. AIR = cm/s, lagging the fan by ≈ 15–25 s (NASA docs say ~1 min; measured on BASS-II telemetry, see reports/physics_review.md §2.3); FAN = 10×V; RAD uncalibrated; **date +1 day**.
- Spatial scale: **0.2094 mm per physical px** (duct ruler, fixed field of view, see methods/spatial_calibration.md).
  **Never** calibrate with the published V_f (circular).
- B14 and B18 main videos are truncated on the NASA server (no MP4 moov atom); use their 2ND_VIEW or original zips.
- V_f references: `data/reference/published_rates.csv` — only the evaluation harness reads them.
- B1 (end-to-end validation, 2026-11-12): V_f = 8.96 phys_px/s, linear spread 15.6–35.6 s,
  direction +x; SDSU publishes 1.878 mm/s (side) ⇒ implied scale ~0.21 mm/px (only as a check).
- O2: the Summary Report gives calibrated (MCA) and raw (CSA-CP) O2 with 0.9–1.6 points of difference; fix one before comparing across PIs.
