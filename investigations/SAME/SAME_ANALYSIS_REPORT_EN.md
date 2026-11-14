# SAME-R (PSI-101): detailed analysis report (English)

Written for: researchers and reviewers who want the methods, every metric definition, the full model search and the data-quality findings behind the dashboard summary.

_Generated from `analysis-same.json` by `analysis/build_reports.py`._

## 1. Summary

- The moment-method statistics re-derived here match the published SAME-2 Table 1: the diameter of average mass agrees within 11% for all 10 material × aging cases.
- Kapton and Teflon (wire-insulation polymers) produce the smallest smoke: Dm 0.10–0.23 µm, versus 0.29–0.56 µm for lampwick (cellulose), Pyrell foam and silicone rubber at 8 cm/s flow.
- With flow, 527–793 s of extra aging cut the particle count to 27%–50% of its initial value and grew Dm by ×1.25–1.56. The growth equals the mass-conserving coagulation prediction (N0/N)^1/3, giving a coagulation coefficient of 9.0e-10 cm³/s, consistent with NASA's note (1.2e-09–1.7e-09) and Brownian theory.
- Aging narrowed the size distribution (σg fell) in 11 of 12 flow runs, the trend expected as coagulating smoke approaches a self-preserving distribution.
- Without flow (possible only in microgravity, where there is no buoyant plume) smoke had ×1.4–3.3 larger Dm and 7–18× fewer particles, and further aging changed it little because it had already coagulated near the heater.
- The two detection principles fail in opposite regimes. With 8 cm/s flow the ISS photoelectric (scattering) detector responded to 71% of pushes and the ionization chamber to 93%; for Kapton the ISS detector responded to only 27%. Without flow the ISS detector responded to 90% and the ionization chamber to 10%. Either detector would have responded to 95% of all pushes.
- The Space Shuttle ionization smoke detector (powered in 9 pushes) alarmed in 6; it stayed silent for aged Kapton (test 70), a weak Teflon test (89) and a dilute lampwick test (92).
- The AutoResearch-selected model predicts held-out Dm within a typical factor of 1.23 and M0 within 1.35, and reduces the detection Brier score by 51% relative to the prevalence; its combined score is 0.529 versus 1.043 for the mean baseline.
- TEM image sizing of lampwick grids gives mean diameters ×1.7–2.7 the in-flight moment value: small particles and liquid droplets are under-counted on grids, so in-flight moments are the better number statistic.
- A single-moment detector is not enough for spacecraft: overheated wire insulation (Kapton, Teflon) in ventilated areas makes ~0.1 µm smoke that light scattering misses, while smoke trapped in still air (avionics boxes, stagnant corners) is dilute and coarse and weakens the ionization signal. Measuring two moments (e.g. the MPASS demonstrated on SAME-R, or combining ionization and scattering) covers both cases.

## 2. Data and scope

- 230 raw files, 5.76 GB; flight: ISS Expedition 24, Microgravity Science Glovebox, GMT day 210–252 of 2010.
- 47 tests with 1 Hz telemetry, 86 smoke pushes, 70 NASA moment measurements (docx), 5,470 TEM-sized lampwick particles.
- Material known for 37 tests from NASA tables or TEM labels; the other 10 are audited in section 8.
- Local data are **SAME-R (PSI-101)** only. SAME-1 (PSI-102, 2007) flight data are not in the download.
- All tests share one flight and one hardware set; they are not independent flights.

## 3. Methods

**Moment method**
- *M0*: Number concentration — P-Trak condensation nuclei counter (isopropanol, 0.02–1 µm, diluted with N2)
- *M1*: Diameter concentration — residential ionization chamber (alpha source); signal ∝ Σ N·d
- *M3*: Mass/volume concentration — DustTrak 90° light scattering, calibrated per material
- *relations*: AMD = D0.5 = M1/M0; Dm = D1.5 = (M3/M0)^(1/3); log-normal: D_p = Dg·exp(p·ln²σg), hence ln²σg = ln(Dm/AMD) and Dg = AMD/exp(0.5·ln²σg)

**Telemetry segmentation.** Heating = HeatingInProgress flag; fill end = last closing of the piston vacuum (fill) valve before the first push; push = rising edge of the piston GN2 valve; aging = push start − fill end; aged when aging ≥ 120 s.

**Flow velocity.** Median MFC fill flow during heating mapped linearly to the 8.1 cm/s nominal duct velocity (4.29 L/min ↔ 8.1 cm/s, NASA TEMflowvsnoflow.xls).

**Detector response.** Peak change within 180 s of each push vs the pre-heating clean-air median. ISS: drop of the forward-scatter channel; ionization: rise of Ion B voltage; STS: alarm bit. Proxy thresholds 1.0 V and 0.5 V.

**Coagulation.** Constant-kernel Smoluchowski: 1/N − 1/N0 = K·t; mass conservation gives Dm ∝ N^(−1/3).

**Model validation.** Leave-one-run-out (size) and leave-one-test-out (detection) cross-validation, fixed in prepare.py.

## 4. Metric definitions

| Metric | Unit | Definition |
|---|---|---|
| M0 (`m0_per_cc`) | #/cm³ | Particle number concentration measured by the P-Trak condensation nuclei counter (NASA-reduced). |
| M1/M0 = AMD (`amd_um`) | µm | Count mean diameter from the ionization chamber moment divided by M0. |
| Dm (`dm_um`) | µm | Diameter of average mass, (M3/M0)^(1/3), from the DustTrak mass moment. |
| σg (`sigma_g`) | – | Geometric standard deviation; exp(√ln(Dm/AMD)) under a log-normal assumption. |
| Dg (`dg_um`) | µm | Geometric mean (median) diameter, AMD / exp(½ ln²σg). |
| Rt/R0 (`rt_r0`) | – | Hot/cold resistance of the heater wire: the temperature set point of a test. |
| Aging time (`aging_s`) | s | Seconds between closing the aging-chamber fill valve and the start of a push. |
| Flow velocity (`flow_velocity_cm_s`) | cm/s | Median fill flow during heating mapped to duct velocity (4.29 L/min ↔ 8.1 cm/s); 0 = no flow. |
| ISS scatter response (`iss_scatter_delta_peak_v`) | V | Peak drop of the ISS detector forward-scatter channel within 180 s of a push (saturates ≈ 6.1). |
| ISS obscuration drop (`iss_obscuration_drop_pct`) | % | Peak relative drop of the obscuration channel; an unsaturated companion. |
| Ionization response (`ion_b_delta_peak_v`) | V | Peak rise of ionization chamber B over its clean-air baseline. |
| DustTrak peak (`dusttrak_b_peak_mg_m3`) | mg/m³ | Peak uncalibrated DustTrak B reading. |
| P-Trak peak (`ptrak_peak_raw_pt_cc`) | #/cm³ | Peak diluted P-Trak count; invalid −999 values removed. |
| STS alarm (`sts_alarm`, delay) | bool, s | Space Shuttle detector alarm bit and seconds from push start; only when the detector was powered. |
| ISS / ionization proxy detection | bool | Response ≥ 1.0 V (ISS scatter) or ≥ 0.5 V (ionization): project proxy, not flight logic. |
| Coagulation coefficient K | cm³/s | (1/N_aged − 1/N_unaged)/Δt from paired measurements. |
| val_score | – | 0.5·mean NRMSE(5 size targets) + 0.5·mean Brier ratio(2 detectors); ≈ 1 for a mean baseline. |
| NRMSE | – | Held-out RMSE divided by the standard deviation of the target. |
| Brier ratio | – | Held-out Brier score divided by the Brier score of always predicting the prevalence. |

## 5. Results

### 5.1 Particle size by material (8 cm/s flow, medians)

| Material | State | n | Dg | AMD | Dm | σg | M0 |
|---|---|---:|---:|---:|---:|---:|---:|
| Kapton | aged | 7 | 0.119 | 0.136 | 0.165 | 1.67 | 1,112,400 |
| Kapton | unaged | 4 | 0.066 | 0.076 | 0.103 | 1.76 | 2,985,285 |
| Lampwick | aged | 3 | 0.178 | 0.230 | 0.377 | 2.02 | 1,251,720 |
| Lampwick | unaged | 5 | 0.091 | 0.130 | 0.286 | 2.36 | 3,197,760 |
| Pyrell | aged | 6 | 0.309 | 0.369 | 0.536 | 1.79 | 1,524,855 |
| Pyrell | unaged | 6 | 0.167 | 0.227 | 0.416 | 2.14 | 3,792,330 |
| Silicone | aged | 2 | 0.236 | 0.315 | 0.559 | 2.14 | 1,937,980 |
| Silicone | unaged | 2 | 0.144 | 0.216 | 0.483 | 2.46 | 3,438,465 |
| Teflon | aged | 1 | 0.070 | 0.105 | 0.232 | 2.44 | 557,920 |
| Teflon | unaged | 6 | 0.113 | 0.136 | 0.189 | 1.84 | 2,714,650 |

### 5.2 Aging (paired unaged/aged measurements)

| Run | Material | Flow | Δt (s) | M0 ratio | Dm growth | Mass-conserving growth | K (cm³/s) |
|---:|---|---|---:|---:|---:|---:|---:|
| 58 | Teflon | flow | 770 | 0.27 | 1.56 | 1.56 | 0.0e+00 |
| 63 | Pyrell | flow | 793 | 0.37 | 1.38 | 1.40 | 0.0e+00 |
| 64 | Pyrell | flow | 791 | 0.37 | 1.38 | 1.40 | 0.0e+00 |
| 73 | Kapton | flow | 527 | 0.40 | 1.39 | 1.35 | 0.0e+00 |
| 74 | Pyrell | flow | 578 | 0.34 | 1.44 | 1.44 | 0.0e+00 |
| 76 | Pyrell | flow | 575 | 0.50 | 1.25 | 1.26 | 0.0e+00 |
| 77 | Kapton | flow | 528 | 0.36 | 1.54 | 1.41 | 0.0e+00 |
| 78 | Lampwick | flow | 544 | 0.39 | 1.34 | 1.37 | 0.0e+00 |
| 82 | Lampwick | flow | 544 | 0.39 | 1.33 | 1.37 | 0.0e+00 |
| 84 | Pyrell | flow | 577 | 0.45 | 1.29 | 1.30 | 0.0e+00 |
| 93 | Kapton | flow | 528 | 0.34 | 1.55 | 1.44 | 0.0e+00 |
| 94 | Kapton | flow | 529 | 0.38 | 1.52 | 1.38 | 0.0e+00 |
| 98 | Lampwick | no flow | 545 | 0.75 | 1.07 | 1.10 | 0.0e+00 |
| 101 | Kapton | no flow | 529 | 0.91 | 1.01 | 1.03 | 0.0e+00 |
| 105 | Teflon | no flow | 528 | 0.75 | 1.06 | 1.10 | 0.0e+00 |
| 107 | Pyrell | no flow | 528 | 0.94 | 1.01 | 1.02 | 0.0e+00 |
| 108 | Kapton | no flow | 528 | 0.91 | 1.02 | 1.03 | 0.0e+00 |

### 5.3 Detectors

All pushes (65): ISS 77%, ionization 68%, either 95%, both 49%, neither 3.

| Material | Flow | Pushes | ISS | Ionization | Either |
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

Space Shuttle (STS) detector pushes:

| Test | Material | Aging (s) | Alarm | Delay (s) | ISS proxy | Ionization proxy |
|---:|---|---:|---|---:|---|---|
| 67 | Silicone | 748 | True | 17 | True | True |
| 67 | Silicone | 1050 | True | 16 | True | True |
| 68 | Lampwick | 747 | True | 17 | True | True |
| 69 | Teflon | 748 | True | 24 | True | True |
| 70 | Kapton | 747 | False |  | False | True |
| 87 | Pyrell | 37 | True | 14 | True | True |
| 89 | Teflon | 37 | False |  | True | True |
| 91 | unknown | 37 | True | 15 | True | True |
| 92 | Lampwick | 36 | False |  | True | False |

## 6. AutoResearch model search

Adapted from karpathy/autoresearch @ 228791fb499afffb54b46200aca536f79142f117. prepare.py fixes data, folds and metric; train.py is the only editable file; attempts are archived as files (no git commits). Metric: val_score = 0.5·mean NRMSE(5 size targets) + 0.5·mean Brier ratio(2 detectors); ~1 = mean baseline.

| # | Model | val_score | size NRMSE | detection Brier ratio | status | Description |
|---:|---|---:|---:|---:|---|---|
| 1 | `training_mean_baseline` | 1.0426 | 1.0311 | 1.0541 | keep | Baseline: training-fold mean for each size target and training prevalence for each detector (7 params) |
| 2 | `ridge_logistic_material_logaging_noflow` | 0.9361 | 1.2581 | 0.6141 | keep | Ridge (alpha=1) on material one-hot + log1p(aging) + no_flow + Rt/R0 for size; L2 logistic on the same design for detection |
| 3 | `ridge_logistic_centered` | 0.6312 | 0.6482 | 0.6141 | keep | Same design, ridge with unpenalized intercept (fixes shrinkage of material offsets toward zero) |
| 4 | `ridge_logistic_flow_interactions` | 0.6372 | 0.6581 | 0.6163 | discard | Add flow-regime interactions: log-aging x no_flow (pre-coagulated quiescent smoke) and Kapton/Teflon x no_flow |
| 5 | `ridgecv_logisticcv_centered` | 0.5919 | 0.5955 | 0.5883 | keep | Inner-CV regularisation: RidgeCV alpha per target (GCV) and LogisticRegressionCV C by Brier, training fold only |
| 6 | `ridgecv_hatch_choate_consistent` | 0.5887 | 0.5890 | 0.5883 | keep | Hatch-Choate consistency: fit log Dm, ln sigma_g, log M0 and derive Dg and AMD from them (fewer free outputs) |
| 7 | `ridgecv_hc_smoluchowski_feature` | 0.5854 | 0.5666 | 0.6043 | keep | Replace log1p(aging) by Smoluchowski coagulation variable ln(1+K*N0*t), K=1.25e-9 cm3/s from the NASA coagulation note, N0 10x lower without flow |
| 8 | `ridgecv_hc_coag_size__logit_logaging_detection` | 0.5774 | 0.5666 | 0.5883 | keep | Task-specific designs: coagulation variable for size, log1p(aging) for detector response |
| 9 | `ridgecv_hc_coag_size__logit_small_x_noflow` | 0.5814 | 0.5666 | 0.5961 | discard | Detection only: add Kapton/Teflon x no_flow interaction (small particles become visible to ISS scatter after quiescent coagulation) |
| 10 | `ridgecv_hc_coag_size__betabinomial_flow_material` | 0.5379 | 0.5666 | 0.5093 | keep | Detection: hierarchical beta-binomial rates (global -> flow regime -> flow x material, prior strength 2) instead of logistic |
| 11 | `ridgecv_hc_coag_size__betabinomial_flow_material_aged` | 0.5289 | 0.5666 | 0.4913 | keep | Detection hierarchy adds an aged level (aging > 120 s) under flow x material; remove dead logistic code |
| 12 | `ridgecv_hc_material_coag_slopes__betabinomial` | 0.5328 | 0.5743 | 0.4913 | discard | Size: material-specific coagulation slopes (material x ln(1+K N0 t)), ridge-shrunk |
| 13 | `ridge_plus_gp_residual__betabinomial` | 0.5297 | 0.5681 | 0.4913 | discard | Size: ridge mean + Gaussian-process (RBF+white, ML-II) correction on ridge residuals |
| 14 | `ridgecv_hc_coag_size__bb_logit_ensemble` | 0.5388 | 0.5666 | 0.5111 | discard | Detection: equal-weight ensemble of the hierarchical beta-binomial rate and an inner-CV L2 logistic that uses Rt/R0 |
| 15 | `ridgecv_hc_coag_size__betabinomial_detector_specific_order` | 0.5303 | 0.5666 | 0.4940 | discard | Detection: detector-specific hierarchy order (ISS: material first; ionization: flow regime first), no new parameters |

### Selected model: attempt 11

Formula: y_j = ridge(material one-hot + ln(1 + K N0 t) + no_flow + 5(Rt/R0-1.35)), K N0 = 3.75e-3/s (x0.1 no-flow); Dg, AMD via Hatch-Choate; detection: P_j = beta-binomial rate in (flow, material, aged) -> (flow, material) -> flow regime -> global, a=2

Exact architecture: Size (Dm, sigma_g, M0): RidgeCV with an unpenalised intercept and per-target alpha chosen by GCV from 9 values in 1e-2..1e2, on 8 features: 5 material indicators, ln(1 + K*N0*t) with K = 1.25e-9 cm3/s and N0 = 3e6 /cm3 (x0.1 when no_flow = 1), the no_flow flag, and 5*(Rt/R0 - 1.35). Predicted ln sigma_g is clipped at 0.05; Dg and AMD are then derived from Dm and sigma_g by the Hatch-Choate relations. Detection (ISS and ionization): no regression; a hierarchical beta-binomial rate with prior strength 2 that shrinks global -> same flow regime -> same flow regime and material -> same flow regime, material and aging state (aging_s > 120 s). Detection ignores Rt/R0 and push_index. No logistic regression is used in this attempt. num_params = 93 is the nominal count recorded at selection time (3 x 9 ridge + 2 x 33 rate cells); the fitted model on all rows has 3 x 9 ridge terms plus 2 x 30 non-empty rate cells (1 global + 2 flow + 9 flow x material + 18 flow x material x aging).

| Target | Held-out RMSE | NRMSE | Typical factor error |
|---|---:|---:|---:|
| log10_dg_um | 0.1698 | 0.708 | ×1.48 |
| log10_dm_um | 0.0888 | 0.368 | ×1.23 |
| log10_amd_um | 0.1285 | 0.569 | ×1.34 |
| ln_sigma_g | 0.1569 | 0.873 | – |
| log10_m0_per_cc | 0.1294 | 0.315 | ×1.35 |
| iss_detect (Brier) | 0.0940 | 0.529 (ratio) | accuracy 88% |
| ion_detect (Brier) | 0.0991 | 0.453 (ratio) | accuracy 89% |

Baseline val_score 1.0426; selected 0.5289. The best of 15 attempts was chosen on the same folds, so the gain is mildly optimistic.

## 7. Interpretation

- Smoke particle size follows material chemistry and transport history: wire insulation gives ~0.1 µm smoke, foam, cellulose and silicone give 0.3–0.6 µm, and coagulation enlarges all of them over minutes.
- Light scattering weights particles by area/mass and ionization by number × diameter, so each has a blind spot: scattering for small particles (ventilated Kapton/Teflon), ionization for dilute coarse smoke (still air).
- Microgravity makes the still-air case reachable: without buoyancy, smoke lingers at the source and coagulates before it spreads, a condition that normal-gravity detector tests do not reproduce.
- Design implication: a second moment (e.g. ionization + scattering, or the MPASS two-angle sensor) removes both blind spots.

## 8. Data quality and the 10 unlabeled tests

See `data/processed/VALIDATION.md` for the full audit. Summary:

- Test 59: heated 53 s, plume up to 101 °C, fingerprint → **Silicone** (inferred, margin 2.7).
- Test 61: heated 52 s, plume up to 98 °C, fingerprint → **Kapton** (inferred, margin 14.5).
- Test 65: heated 53 s, plume up to 101 °C, fingerprint → **Silicone** (inferred, margin 2.8).
- Test 66: heated 52 s, plume up to 115 °C, fingerprint → **Silicone** (inferred, margin 4.8).
- Test 86: heated 52 s, plume up to 111 °C, fingerprint → **Silicone** (inferred, margin 3.5).
- Test 90: heated 54 s, plume up to 114 °C, fingerprint → **Kapton** (inferred, margin 42.3).
- Test 91: heated 53 s, plume up to 110 °C, fingerprint → **Silicone** (inferred_low_margin, margin 2.2).
- Test 99: heated 53 s, plume up to 75 °C, fingerprint → **Silicone** (inferred, margin 4.1).
- Test 102: heated 52 s, plume up to 92 °C, fingerprint → **Kapton** (inferred, margin 29.4).
- Test 103: heated 52 s, plume up to 61 °C, fingerprint → **Silicone** (inferred, margin 6.3).

Detection Brier ratio of the frozen model: 0.491 (as run), 0.511 with test 92 relabelled, 0.499 with all inferred tests added.

- Run 54 aging: NASA lists 56.8 s net aging; the valve-edge definition gives 38 s (279 s push). The other 11 comparable values agree within 8 s.
- Test 63 telemetry starts after the fill; its aging is estimated as first push + nominal 38 s.
- Test 85 first push: P-Trak reads 1,510 /cm³, matching NASA's note 'low ptrak on peak one'.
- DustTrak A reads ~10,000/20,000 codes in SAME-R (slot repurposed); it is discarded.
- Smoke remains in the diagnostics duct between pushes until it is purged; responses are taken within 180 s of each push.
- Test 92: material assigned as lampwick from an MSG video starting 10 s after the test record, but its heater fingerprint (0.645 ohm, Rt/R0 1.368) matches Kapton, not lampwick (0.76 ohm, 1.27).

## 9. Limitations

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

## 10. References

- Urban DL, Ruff GA, Greenberg PS, Fischer D, Meyer M, Mulholland G, Yuan Z, Bryg V, Cleary T, Yang J. Particle Morphology and Size Results from the Smoke Aerosol Measurement Experiment-2. AIAA 2012-3536, 42nd International Conference on Environmental Systems, 2012. https://ntrs.nasa.gov/citations/20130000422
- Yang J, Cleary T, Mulholland G, et al. Smoke Characterization and Feasibility of the Moment Method for Spacecraft Fire Detection. Aerosol Science and Technology 49 (2015). https://doi.org/10.1080/02786826.2015.1025124
- ZIN Technologies. SAME Verification Plan and Engineering Requirements Document (SAME-PLN-005 Rev F), January 2007 (file in the PSI download).
- NASA Glenn Research Center. Dust and Aerosol measurement Feasibility Test (DAFT), ISS Expedition 13 (2006). https://ntrs.nasa.gov/citations/20070031686
- NASA Physical Sciences Informatics (PSI) repository, investigations PSI-101 (SAME-R) and PSI-102 (SAME). https://psi.nasa.gov/physci/repo/data/investigations/PSI-101
