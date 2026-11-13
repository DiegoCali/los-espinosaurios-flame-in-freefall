# SAME-R (PSI-101): smoke particle size, aging and detector response — analysis report

_Generated 2026-11-13T19:45:57 UTC by `analysis/build_analysis_json.py`._

## Scope

- 230 raw files (5.76 GB): 47 tests with 1 Hz telemetry (37 with an identified material), 86 smoke pushes, 70 NASA moment measurements, TEM sizing for lampwick runs 54–55.
- Grid labels 'SAMERFLT <n><material>' and 2010 timestamps identify SAME-R (SAME-2).

## Key insights

- **K1** (high confidence) — The moment-method statistics re-derived here match the published SAME-2 Table 1: the diameter of average mass agrees within 11% for all 10 material × aging cases.
- **K2** (high confidence) — Kapton and Teflon (wire-insulation polymers) produce the smallest smoke: Dm 0.10–0.23 µm, versus 0.29–0.56 µm for lampwick (cellulose), Pyrell foam and silicone rubber at 8 cm/s flow.
- **K3** (high confidence) — With flow, 527–793 s of extra aging cut the particle count to 27%–50% of its initial value and grew Dm by ×1.25–1.56. The growth equals the mass-conserving coagulation prediction (N0/N)^1/3, giving a coagulation coefficient of 9.0e-10 cm³/s, consistent with NASA's note (1.2e-09–1.7e-09) and Brownian theory.
- **K4** (medium confidence) — Aging narrowed the size distribution (σg fell) in 11 of 12 flow runs, the trend expected as coagulating smoke approaches a self-preserving distribution.
- **K5** (medium confidence) — Without flow (possible only in microgravity, where there is no buoyant plume) smoke had ×1.4–3.3 larger Dm and 7–18× fewer particles, and further aging changed it little because it had already coagulated near the heater.
- **K6** (medium confidence) — The two detection principles fail in opposite regimes. With 8 cm/s flow the ISS photoelectric (scattering) detector responded to 71% of pushes and the ionization chamber to 93%; for Kapton the ISS detector responded to only 27%. Without flow the ISS detector responded to 90% and the ionization chamber to 10%. Either detector would have responded to 95% of all pushes.
- **K7** (medium confidence) — The Space Shuttle ionization smoke detector (powered in 9 pushes) alarmed in 6; it stayed silent for aged Kapton (test 70), a weak Teflon test (89) and a dilute lampwick test (92).
- **K8** (medium confidence) — The AutoResearch-selected model predicts held-out Dm within a typical factor of 1.23 and M0 within 1.35, and reduces the detection Brier score by 51% relative to the prevalence; its combined score is 0.529 versus 1.043 for the mean baseline.
- **K9** (medium confidence) — TEM image sizing of lampwick grids gives mean diameters ×1.7–2.7 the in-flight moment value: small particles and liquid droplets are under-counted on grids, so in-flight moments are the better number statistic.
- **K10** (medium confidence) — A single-moment detector is not enough for spacecraft: overheated wire insulation (Kapton, Teflon) in ventilated areas makes ~0.1 µm smoke that light scattering misses, while smoke trapped in still air (avionics boxes, stagnant corners) is dilute and coarse and weakens the ionization signal. Measuring two moments (e.g. the MPASS demonstrated on SAME-R, or combining ionization and scattering) covers both cases.

## Particle size by material (8 cm/s flow, medians)

| Material | State | n | Dg (µm) | AMD (µm) | Dm (µm) | σg | M0 (#/cm³) | Published Dm |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| Kapton | aged | 7 | 0.119 | 0.136 | 0.165 | 1.67 | 1,112,400 | 0.161 |
| Kapton | unaged | 4 | 0.066 | 0.076 | 0.104 | 1.76 | 2,985,285 | 0.101 |
| Lampwick | aged | 3 | 0.178 | 0.230 | 0.377 | 2.02 | 1,251,720 | 0.398 |
| Lampwick | unaged | 5 | 0.091 | 0.130 | 0.286 | 2.36 | 3,197,760 | 0.258 |
| Pyrell | aged | 6 | 0.309 | 0.369 | 0.536 | 1.79 | 1,524,855 | 0.539 |
| Pyrell | unaged | 6 | 0.167 | 0.227 | 0.416 | 2.14 | 3,792,330 | 0.384 |
| Silicone | aged | 2 | 0.236 | 0.315 | 0.559 | 2.14 | 1,937,980 | 0.619 |
| Silicone | unaged | 2 | 0.145 | 0.216 | 0.483 | 2.46 | 3,438,465 | 0.465 |
| Teflon | aged | 1 | 0.070 | 0.105 | 0.232 | 2.44 | 557,920 | 0.232 |
| Teflon | unaged | 6 | 0.113 | 0.136 | 0.189 | 1.84 | 2,714,650 | 0.17 |

## Detector comparison (proxy thresholds)

| Material | Flow | Pushes | ISS photoelectric | Ionization chamber | Either |
|---|---|---:|---:|---:|---:|
| Kapton | flow_8cm_s | 15 | 27% | 93% | 93% |
| Kapton | no_flow | 4 | 100% | 0% | 100% |
| Lampwick | flow_8cm_s | 11 | 100% | 91% | 100% |
| Lampwick | no_flow | 6 | 100% | 0% | 100% |
| Pyrell | flow_8cm_s | 7 | 100% | 100% | 100% |
| Pyrell | no_flow | 6 | 100% | 0% | 100% |
| Silicone | flow_8cm_s | 4 | 100% | 100% | 100% |
| Teflon | flow_8cm_s | 8 | 75% | 88% | 88% |
| Teflon | no_flow | 4 | 50% | 50% | 75% |

## AutoResearch ledger (`runs/autoresearch/same-run-01/results.tsv`)

| # | Model | val_score | size NRMSE | detection Brier ratio | params | status |
|---:|---|---:|---:|---:|---:|---|
| 1 | `training_mean_baseline` | 1.0426 | 1.0311 | 1.0541 | 7 | keep |
| 2 | `ridge_logistic_material_logaging_noflow` | 0.9361 | 1.2581 | 0.6141 | 58 | keep |
| 3 | `ridge_logistic_centered` | 0.6312 | 0.6482 | 0.6141 | 63 | keep |
| 4 | `ridge_logistic_flow_interactions` | 0.6372 | 0.6581 | 0.6163 | 77 | discard |
| 5 | `ridgecv_logisticcv_centered` | 0.5919 | 0.5955 | 0.5883 | 63 | keep |
| 6 | `ridgecv_hatch_choate_consistent` | 0.5887 | 0.5890 | 0.5883 | 45 | keep |
| 7 | `ridgecv_hc_smoluchowski_feature` | 0.5854 | 0.5666 | 0.6043 | 45 | keep |
| 8 | `ridgecv_hc_coag_size__logit_logaging_detection` | 0.5774 | 0.5666 | 0.5883 | 45 | keep |
| 9 | `ridgecv_hc_coag_size__logit_small_x_noflow` | 0.5814 | 0.5666 | 0.5961 | 47 | discard |
| 10 | `ridgecv_hc_coag_size__betabinomial_flow_material` | 0.5379 | 0.5666 | 0.5093 | 53 | keep |
| 11 | `ridgecv_hc_coag_size__betabinomial_flow_material_aged` | 0.5289 | 0.5666 | 0.4913 | 93 | keep |
| 12 | `ridgecv_hc_material_coag_slopes__betabinomial` | 0.5328 | 0.5743 | 0.4913 | 108 | discard |
| 13 | `ridge_plus_gp_residual__betabinomial` | 0.5297 | 0.5681 | 0.4913 | 102 | discard |
| 14 | `ridgecv_hc_coag_size__bb_logit_ensemble` | 0.5388 | 0.5666 | 0.5111 | 111 | discard |
| 15 | `ridgecv_hc_coag_size__betabinomial_detector_specific_order` | 0.5303 | 0.5666 | 0.4940 | 93 | discard |

Selected: attempt 11 — y_j = ridge(material one-hot + ln(1 + K N0 t) + no_flow + 5(Rt/R0-1.35)), K N0 = 3.75e-3/s (x0.1 no-flow); Dg, AMD via Hatch-Choate; detection: P_j = beta-binomial rate in (flow, material, aged) -> (flow, material) -> flow regime -> global, a=2

Held-out errors of the selected model:

| Target | NRMSE | typical factor error |
|---|---:|---:|
| log10_dg_um | 0.708 | ×1.48 |
| log10_dm_um | 0.368 | ×1.23 |
| log10_amd_um | 0.569 | ×1.34 |
| ln_sigma_g | 0.873 | — |
| log10_m0_per_cc | 0.315 | ×1.35 |
| iss_detect (Brier ratio) | 0.529 | accuracy 88% |
| ion_detect (Brier ratio) | 0.453 | accuracy 89% |

## Figures

- [overview](analysis/output/same-summary.png)
- [moments_by_material](data/processed/figures/moments_by_material.png)
- [aging_coagulation](data/processed/figures/aging_coagulation.png)
- [flow_effect](data/processed/figures/flow_effect.png)
- [detector_comparison](data/processed/figures/detector_comparison.png)
- [threshold_sensitivity](data/processed/figures/threshold_sensitivity.png)
- [example_timeseries](data/processed/figures/example_timeseries.png)
- [size_distributions](data/processed/figures/size_distributions.png)
- [model_cv](data/processed/figures/model_cv.png)
- [autoresearch_progress](data/processed/figures/autoresearch_progress.png)
- [model_scenarios](data/processed/figures/model_scenarios.png)

## Data quality notes

- Run 54 aging: NASA lists 56.8 s net aging; the valve-edge definition gives 38 s (279 s push). The other 11 comparable values agree within 8 s.
- Test 63 telemetry starts after the fill; its aging is estimated as first push + nominal 38 s.
- Test 85 first push: P-Trak reads 1,510 /cm³, matching NASA's note 'low ptrak on peak one'.
- DustTrak A reads ~10,000/20,000 codes in SAME-R (slot repurposed); it is discarded.
- Smoke remains in the diagnostics duct between pushes until it is purged; responses are taken within 180 s of each push.
- Test 92: material assigned as lampwick from an MSG video starting 10 s after the test record, but its heater fingerprint (0.645 ohm, Rt/R0 1.368) matches Kapton, not lampwick (0.76 ohm, 1.27).

Flagged moment rows:

- run 50 (Teflon, unaged): amd_out_of_range_likely_unit_or_typo
- run 69 (Teflon, aged): dm_zero
- run 62 (Kapton, unaged): sigma_g_out_of_range
- run 79 (Teflon, aged): dm_below_amd_not_lognormal_consistent
- run 80 (Lampwick, aged): dm_below_amd_not_lognormal_consistent
- run 81 (Teflon, aged): dm_below_amd_not_lognormal_consistent
- run 83 (Teflon, aged): dm_below_amd_not_lognormal_consistent
- run 75 (Kapton, unaged): m0_missing
- run 96 (Lampwick, unknown): m0_missing
- run 97 (Pyrell, unknown): m0_missing
- run 100 (Teflon, unknown): m0_missing

## Limitations

- Local raw data cover SAME-R (PSI-101, ISS Expedition 24, 2010) only; no SAME-1 (PSI-102, 2007) flight telemetry or moment tables are present.
- Calibrated moments (M0, M1/M0, Dm, σg) are NASA/NIST reduced values from 'Sample descriptions tables.docx'; raw P-Trak counts are diluted and raw ionization/DustTrak signals are uncalibrated, so they are used only as detector responses, not re-calibrated moments.
- Detector 'detection' is a project-defined proxy: ISS scatter drop ≥ 1.0 V and ionization-chamber rise ≥ 0.5 V over each test's clean-air baseline. These are not the flight alarm algorithms; the threshold-sensitivity figure shows the conclusions hold across a range.
- Smoke amount per test was chosen by NASA (heater temperature set for a measurable signal), so detection rates describe these test conditions, not real-fire probabilities.
- Ten tests (59, 61, 65, 66, 86, 90, 91, 99, 102, 103) have telemetry but no material label in any local file. They are real heated tests, not blanks. A heater-wire fingerprint (cold resistance and Rt/R0, 34/36 leave-one-out agreement on labelled tests) infers silicone for 59, 65, 66, 86, 91, 99, 103 (DBP cannot be excluded) and Kapton for 61, 90, 102. These inferences are reported in test_material_audit.csv but were not used in the frozen model datasets; adding them changes the detection Brier ratio from 0.491 to 0.499.
- The material of test 92 was first assigned as lampwick from the start time of a labelled MSG video; its heater fingerprint matches Kapton instead. The frozen run keeps lampwick; relabelling it changes the detection Brier ratio from 0.491 to 0.511 (runs/verification/material_audit_sensitivity.json).
- Some grids have an ambiguous aging label (docx '?' or blank); they are excluded from the models. Seven moment rows have typographical or log-normal-inconsistent values and are flagged, not corrected.
- No-flow conditions have 1–2 labelled runs per material and no labelled silicone run (tests 99 and 103 are probably silicone); low-flow (2 cm/s) runs reported in the literature are not identifiable in the local telemetry (MFC = 0 during heating).
- The ISS scatter channel saturates near 6.1 V; obscuration percentage is provided as an unsaturated companion.
- Response delays are measured from the piston push and include transport to each sensor's duct position; they do not compare intrinsic sensor speed.
- The model was selected as the best of 15 attempts on the same cross-validation folds (~50–65 rows), so its apparent gain is mildly optimistic; it has not been validated on another flight.

## References

- Urban DL, Ruff GA, Greenberg PS, Fischer D, Meyer M, Mulholland G, Yuan Z, Bryg V, Cleary T, Yang J. Particle Morphology and Size Results from the Smoke Aerosol Measurement Experiment-2. AIAA 2012-3536, 42nd International Conference on Environmental Systems, 2012. https://ntrs.nasa.gov/citations/20130000422
- Yang J, Cleary T, Mulholland G, et al. Smoke Characterization and Feasibility of the Moment Method for Spacecraft Fire Detection. Aerosol Science and Technology 49 (2015). https://doi.org/10.1080/02786826.2015.1025124
- ZIN Technologies. SAME Verification Plan and Engineering Requirements Document (SAME-PLN-005 Rev F), January 2007 (file in the PSI download).
- NASA Glenn Research Center. Dust and Aerosol measurement Feasibility Test (DAFT), ISS Expedition 13 (2006). https://ntrs.nasa.gov/citations/20070031686
- NASA Physical Sciences Informatics (PSI) repository, investigations PSI-101 (SAME-R) and PSI-102 (SAME). https://psi.nasa.gov/physci/repo/data/investigations/PSI-101
