# Saffire data plan — frozen protocol v1

This English edition preserves the data-selection and modeling decisions from the completed v1 experiment. Publication changes do not rewrite the original experimental commits.

## Observed scope

The local archive contains 218 physical files (33.810 decimal GB), nine **Saffire-II** tests and one flight. The outer part-01/02 ZIP containers duplicate files already present in the expanded directories. File types are 191 ZIP, 11 XLSX, 10 DOCX, five PDF and one CSV. Frames, duplicate files and image variants are not independent statistical samples. The nine ignition records also share a flight, cabin and contamination history; they are not nine independent flight replicates.

Local metadata declares **PSI-99**, DOI 10.60555/2chp-m469. The supplied pendulum-example path was resolved to `/home/natalia/Documents/NASA/autoresearch-pendulum-study`, whose scientific adaptation was read locally. The online example was unavailable. The Karpathy upstream pattern was reviewed, and the original files are preserved in `upstream_reference/`.

## Metric selection and purpose

[data/processed/metrics.csv](data/processed/metrics.csv) records the source file, channels, method, unit, selection reason, conclusion, uncertainty and missing-value reason for each metric and test. The detailed JSON preserves those fields. The following families cover the 35 defined test-level metrics.

| Family and objective | Sources and channels | Method and units | Assumptions and uncertainty |
|---|---|---|---|
| Material, dimensions and direction: relevance and prevention | Postflight CSV, rows 2-1 through 2-9; DoD Table 1 for grooved PMMA | Documented transcription; mm, cm, category | Empty II-6/II-9 material cells are inherited and corroborated. `037` is interpreted as 0.37 mm using the postflight table. II-7 combines 0.85 mm PMMA and 0.37 mm Nomex; the nominal model-table thickness describes its Nomex section. II-8 is 10 mm nominal, with effective thickness null. Tolerances are not published. |
| Flow, pressure, O2 and partial pressure: habitat conditions | Per-specimen XLSX, `Calibrated Data`, H/I/J/G | Pre-ignition [-30,0) s medians of one-second medians; cm/s, kPa, %, kPa. PSIA × 6.894757293168; pO2=P×O2/100 | Flow averages the two anemometers. Measured II-6 flow near 25 cm/s takes precedence over the 20/30 documentation discrepancy. MAD describes variability; absolute calibration is unknown. Table O2 is retained separately because it is CO2-derived and not an independent predictor. |
| Electrical timing and ignitor energy: quality control | B, AG, AH, AR of each XLSX; nominal power/duration from CSV | First enabled voltage/current product above numeric threshold 20; pulse span+dt; trapezoidal channel-product integral; ms, s and nominal J/W labels | This is an electrical marker, not verified optical ignition. Sampling is about 0.033 s; duration comparison tolerance is 0.15 s. Later review found the absolute electrical-energy scale inconsistent with nominal power × duration; the archived energy magnitude remains unvalidated and is not a model input. |
| **CO2 response at 180 s: predictive modeling** | F and B, referenced to the XLSX electrical event | CO2 % ×10000; median of one-second medians at [150,180) minus [-30,0); ppm | One row per test. Signed negative values are retained because drift and mixing are possible. Descriptive variability is sqrt(MAD_pre²+MAD_final²), with MAD scaled by 1.4826, without dividing by sqrt(n). This is not a calibration-accuracy claim. |
| Baseline CO2, early maximum and end change: products/detection | F in each XLSX | Baseline median, maximum one-second median in [0,180), and median of the final 30 bins minus baseline; ppm | The maximum is not an exposure dose or clinical-risk threshold. End windows occur after different record durations and are not the common-horizon modeling target. Baseline CO2 retains prior cabin history. |
| O2, pressure and inlet temperature at 180 s: instrument response | G/J/P | Difference between medians at [150,180) and [-30,0); percentage points, kPa, degrees C | These are local temporal changes without isolated causal attribution to the fire. A single O2 channel is not an inlet/outlet difference. |
| Plume temperature and relative radiation: equipment evidence | Q:V and K:N | Maximum one-second median in [0,180); degrees C and kW/m². 1 mW/cm²=0.01 kW/m²; per-radiometer baseline subtraction | Neither maximum flame temperature nor total fire power. Views change with specimen position; the ignitor may contribute radiation. Waiver SFS-W-009 gives SIBAL B thermocouple heights of 4.445/3.175 mm rather than 5.08 mm nominal. Peaks are not converted to front velocities. Geometric-transfer uncertainty is unquantified. |
| Spread, duration, damage and 1g comparison: prevention/modeling | Postflight CSV outcomes and notes | Published-value transcription only; mm/s, s, cm or text | Only II-5/II-6 have numeric spread rates, 2.1/2.6 mm/s. No sustained spread is not a measured zero velocity. PMMA II-8/9 have about 10 cm visible damage and slow 0.01–0.04 mm/s regression, which is different from propagation. II-7 consumed the 5 cm PMMA section without igniting Nomex. |
| Cabin and smoke: detection/equipment | `Saffire-II Telemetry Data.xlsx`, `CygnusData`, D/F/J/L | Mission-record statistics after removing zero fill and implausible values; degrees C, kPa, V | Alarm thresholds are unknown. Per-test alignment is unverified; V/Y alignment columns lack stored numeric values. No clock offset or spatial cabin mean is assumed. Filters 0<T<60 degrees C, 5<P<20 psi and 0.01<V<5 are plausibility filters, not alarm or exposure limits. |
| Images: visual coverage and material checks | Prefer remapped JPEG, then remapped TIFF, then unmapped images; camera 2 for II-1/2/3 and camera 1 for II-4 through II-9 | Frames near 30, 90 and 150 s; file/member and actual time in `image_frame_audit.csv` | Sampling only, without photometry or front-velocity inference from variable-exposure imagery. Timestamp mismatches are retained. |

## Target and evaluation fixed before the search

**`co2_increase_180s_ppm`** provides nine measured responses at a common horizon. It is a local avionics-sensor indicator of products and mixing, not emitted mass, toxicity, HRR or the maximum concentration experienced by crew. The 180 s horizon fits inside the shortest record and covers an early interval relevant to detection studies. Windows are fixed rather than selecting peaks over unequal burn durations.

Alternatives were rejected for data-specific reasons. Flame spread has only two published numeric rates, insufficient for validating a general predictive relationship. HRR lacks paired inlet/outlet O2 and mass flow; radiation or a single O2 channel cannot supply that missing balance. Radiometer peaks depend on viewing geometry, thermocouple maxima depend on coverage, final CO2 changes use unequal record durations, and alarm delay lacks synchronized events and thresholds.

Allowed inputs are `material`, `thickness_nominal_mm`, `flow_pre_cm_s`, `direction`, `ignition_duration_command_s`, `ignition_power_command_w` and `structured_pmma`. These are conditions available before the outcome. Constant dimensions are omitted. O2 is excluded because some published values were derived from CO2 and the absolute sensor reading is unvalidated. Pressure is retained for relevance comparisons, but its narrow range and correlation with temporal order do not support a causal pressure-response fit. Test IDs, baseline/final CO2, burn duration, burned length, outcome classes and all other outcome columns are prohibited as predictors.

`prepare.py` validates data and fixes leave-one-test-out evaluation for n≤20, or five folds with seed 164 for a future larger protocol. RMSE in ppm is primary; MAE and maximum absolute error are secondary. Final coefficients are fitted to all rows **after** held-out predictions are calculated. Repeated candidate selection on the same CV makes the selected RMSE optimistic; it is not independent prospective validation. A single flight cannot establish transfer to other missions.

## Missing results and exclusions

- HRR remains null without paired inlet/outlet O2 and mass flow, or a validated cabin volume and mixing model.
- CO/CO2 hazard indices remain null without the required channels and applicable exposure-duration limits. No arbitrary concentration is used to declare danger or safety.
- Alarm delay remains null without verified events, thresholds and clock alignment.
- Flow-cutoff effectiveness remains null without an identified suppression intervention.
- Raw tests from Saffire I, III, IV, V and VI are absent locally, even though they appear in contextual documents.
- Duplicate images, annotated TIFF/PNG variants, BIT, F1/F2 calibration/flow sets and outer containers are inventoried rather than counted as experimental replicates.

## Habitat relevance rubric, 0–100

The fixed rubric assigns:

- O2 similarity: 30 × max(0,1−|difference in percentage points|/20).
- Pressure similarity: 25 × max(0,1−|difference in kPa|/60).
- Gravity similarity: 15 × exp(−|habitat gravity−0|/0.2).
- Sample scale: 5 × min(1,area/0.04 m²).
- Behavior: 5 for propagating SIBAL, 4 for anchored PMMA flames, 3 for other outcomes.
- Quantitative data: 6 for gas/thermal data plus 4 for a published numeric spread rate.
- Ground comparison: 10 if available.

Scores are summed and ties are ordered by test ID. These scores are evidence-relevance judgments, not ignition probabilities. Differences smaller than sensor uncertainty should not be interpreted as scientifically significant.

**Illustrative analyst design assumptions, not actual NASA mission requirements:**

| Environment | O2 (%) | Pressure (kPa) | Gravity (g) |
|---|---:|---:|---:|
| ISS-like spacecraft | 21.0 | 101.3 | 0 |
| Gateway-like station | 21.0 | 101.3 | 0 |
| Lunar base | 34.0 | 56.5 | 0.165 |
| Pressurized lunar rover | 34.0 | 56.5 | 0.165 |
| Mars base | 26.5 | 70.3 | 0.38 |

Oxygen fraction and total pressure are considered separately; equal oxygen partial pressure does not establish equivalent combustion behavior. The ranking does not validate transfer of the model to another atmosphere or gravity. Predictions are restricted to the observed dataset and 180 s horizon; unsupported habitat predictions remain unavailable.

Dataset source: Urban DL, Ruff G. "Spacecraft Fire Experiment-II(SAFFIRE-II)", NASA PSI Data Repository, Version 5, [http://doi.org/10.60555/2chp-m469](http://doi.org/10.60555/2chp-m469).
