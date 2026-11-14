# Saffire-II analysis: work performed, results, and interpretation - TECHNICAL 

This report explains the completed extraction and predictive pilot in this directory. The principal machine-readable result is [analysis-saffire.json](analysis-saffire.json). The study used the locally downloaded Saffire-II files attributed to Urban and Ruff's NASA PSI dataset, Version 5; the full dataset citation is given under **Sources**.

The principal result is a small, interpretable model of the **signed change in a local CO2 sensor reading 180 seconds after the electrical ignition marker**. Its selected leave-one-test-out RMSE is **23.451 ppm**, compared with **41.416 ppm** for the training-mean baseline. This is internal evidence from nine sequential tests in one flight. It does not establish performance in another flight, atmosphere, gravity regime, or crew exposure scenario.

## What was done and why

The work followed a reproducible sequence:

1. Inventoried all local files, read the supplied documentation, inspected spreadsheet schemas, and examined ZIP member lists without expanding the full image archive.
2. Reconciled documentary discrepancies and selected measurements that the available channels could support.
3. Extracted sensor data by streaming spreadsheet rows. Every test-level metric retains its source file, channels, method, selection reason, conclusion, and uncertainty or reason for absence.
4. Reduced the sensor data to one-second medians and derived one comparable predictive response per ignition.
5. Adapted AutoResearch to CPU-based Python/NumPy modeling. The dataset, allowed inputs, folds, evaluation metrics, and selection rules were frozen before the search; only `train.py` changed during the 15-attempt loop.
6. Compared the candidates under the same evaluation, retained the best permitted result, generated findings and habitat relevance rankings, and checked reproducibility and raw-file integrity.

This sequence supports three aims: identifying relevant fire-safety evidence, preparing defensible predictive data, and identifying what the archive can contribute to prevention, detection, and suppression equipment decisions.

### Archive scope

| Item | Result | Meaning |
|---|---:|---|
| Physical files inventoried | 218 | Includes duplicate image variants and delivery containers; file count is not experimental sample count. |
| Total physical size | 33.810 GB, decimal | Includes the redundant outer ZIP containers. |
| File types | 191 ZIP, 11 XLSX, 10 DOCX, 5 PDF, 1 CSV | The archive combines measurements, image variants, and explanatory documents. |
| Distinct ignition records | 9 | One modeling row per specimen test. |
| Flights represented by local raw tests | 1 | The nine records share a vehicle and cabin history; they are not independent flight replicates. |
| Valid sensor records extracted | 159,543 | Individual records were not treated as independent modeling samples. |
| One-second sensor bins | 5,274 | Used for comparable temporal summaries. |
| Test-level metric entries | 315: 250 populated, 65 null | Null entries preserve missingness and its reason. |
| Metric types | 35 defined; 29 populated somewhere | Six requested quantities remain entirely unavailable. |
| Image frames sampled | 27 | Three frames per test for visual quality control; maximum timestamp mismatch was 0.016 s. |

* The export identifies the observed Saffire-II data as PSI-99. Documents discussing Saffire I–VI do not add raw measurements from those missions.

The inventory found four groups of exactly duplicated files, in addition to two redundant outer delivery containers. JPEG, TIFF, PNG, remapped images, calibration grids, and pre/post-flow image sets were not counted as additional fires.

Evidence: [inventory](data/inventory/inventory.csv), [inventory interpretation](data/inventory/INVENTORY.md), and [data plan](DATA_PLAN.md).

## How the measurements were derived

### Conditions and event timing

Pre-ignition conditions use the interval from **−30 to 0 seconds**, referenced to an electrical activity marker. Flow is summarized from the two anemometers. The pipeline converts pressure from PSIA to kPa and gas concentration from percent to ppm.

The electrical marker is the first enabled voltage/current channel product above the extraction threshold. This aligns channels within a test. It is not an independently verified optical ignition time. Pulse durations agree with the documented commands within **0.059 s**, below the fixed 0.15 s comparison tolerance.

Important reconciliations were:

- **II-6 flow:** the measured pre-ignition median is 24.989 cm/s. The local CSV says 20 cm/s and preflight documentation says 30 cm/s. The measured value was used; the NASA postflight presentation also reports a 25 cm/s regime.
- **Thickness:** postflight values were preferred over differing preflight values. The CSV text `037 mm` was interpreted as 0.37 mm with documentary support. The grooved PMMA slab has 10 mm nominal thickness, while its effective grooved thickness remains undefined.
- **Composite specimen:** II-7 contains a PMMA lead-in and Nomex section. Its model-table nominal thickness refers to the 0.37 mm Nomex section, not a homogeneous composite slab.
- **O2:** sensor readings and published table values were retained separately. The table's oxygen values are CO2-derived, so they were excluded as independent predictors.
- **Thermocouple placement:** the waiver records SIBAL B-location heights of 4.445 and 3.175 mm rather than the 5.08 mm nominal height. Temperature peaks were not converted into flame-front velocities.

### A specific electrical-energy discrepancy

The existing `ignition_energy_measured_j` field integrates the voltage/current channel product and produces **25.98–111.97 kJ**. The documented commands imply only **0.736 kJ** for 80 W × 9.2 s and **2.910 kJ** for 97 W × 30 s.

The processed pulse power also reaches roughly 2.8–3.8 kW, far above the 80–97 W nominal commands. The cause of this mismatch has not been established. It could involve channel interpretation, units, scaling, or calibration. **The derived energy's physical magnitude remains unvalidated and should not be used for fire-energy estimates or equipment sizing.**  This quantity was not a model input or target.

### Predictive target

The selected response is:

```text
delta_CO2_180_ppm =
    median(one-second CO2 medians during [150,180) seconds)
  - median(one-second CO2 medians during [-30,0) seconds)
```

CO2 percent is multiplied by 10,000 to obtain ppm. A common 180 s horizon is available in all nine records. Subtracting each test's local baseline reduces confusion between its response and CO2 accumulated before that test.

Alternatives were rejected for specific reasons: only two numeric published spread rates are available; heat release rate lacks the required oxygen/mass-flow information; radiometer peaks depend on viewing geometry; end-of-record gas changes use unequal observation durations; and alarm delay lacks verified timing and alarm criteria.

The uncertainty field is:

```text
sqrt((1.4826 × MAD_pre)^2 + (1.4826 × MAD_150_to180)^2)
```

MAD is the median absolute deviation of the one-second values. This is descriptive window variability. It is not an absolute calibration uncertainty, confidence interval, or guaranteed prediction-error bound. Small negative responses were retained because the data can contain drift and mixing effects; they do not demonstrate physical consumption of CO2.

## Results for each test

The CO2 column below is newly derived from the telemetry. Material behavior and spread-rate results are transcribed from the supplied postflight table and notes.

| Test | Material | Nominal thickness (mm) | Measured pre-ignition flow (cm/s) | Direction | CO2 response at 180 s (ppm) | Documented behavior |
|---|---|---:|---:|---|---:|---|
| II-1 | Silicone | 0.27 | 20.00 | concurrent | 3.06 | No sustained spread |
| II-2 | Silicone | 0.61 | 19.99 | concurrent | 15.03 | No sustained spread |
| II-3 | Silicone | 1.03 | 19.99 | concurrent | -10.96 | No sustained spread |
| II-4 | Silicone | 0.37 | 19.99 | opposed | -16.61 | No sustained spread |
| II-5 | SIBAL (cotton/fiberglass) | 0.37 | 19.99 | concurrent | 39.65 | Complete fabric spread |
| II-6 | SIBAL (cotton/fiberglass) | 0.37 | 24.99 | concurrent | 45.65 | Complete fabric spread |
| II-7 | PMMA–Nomex composite | 0.37 | 19.99 | concurrent | 107.00 | PMMA consumed; Nomex not ignited |
| II-8 | PMMA | 10.00 | 19.99 | concurrent | 60.56 | Anchored flame; slow regression |
| II-9 | PMMA | 10.00 | 19.98 | concurrent | 45.31 | Anchored flame; slow regression |

The meaning of these results is:

- **Silicone, II-1–II-4:** none sustained propagation in the documented conditions. Their small positive or negative CO2 changes are consistent with a weak response relative to sensor variability and mixing. This result does not certify silicone under different oxygen levels, pressure, ignition, geometry, or ventilation.
- **SIBAL, II-5–II-6:** both specimens exhibited full fabric spread. The published rates are **2.1 and 2.6 mm/s**, a **23.8%** increase between the two tests. This is a descriptive comparison with n=2, not a fitted or independently verified causal flow law.
- **PMMA–Nomex, II-7:** the PMMA lead-in was consumed and Nomex did not ignite. This specimen has the largest derived early CO2 response, 107.00 ppm. That does not make it the most hazardous specimen: the metric is a local response at one time horizon, not total heat, toxic dose, or sustained spread through Nomex.
- **PMMA slabs, II-8–II-9:** anchored flames and slow regression were reported. Approximately 10 cm of visible damage is not a measured 10 cm flame-front trajectory. Published burn durations of 600 and 900 s also show why an early 180 s response cannot summarize the entire event.

A check using 290 mm divided by the published SIBAL burn durations gives 2.000 and 2.522 mm/s, differing from the published rates by 4.76% and 3.01%. Total burn duration and the interval used to estimate propagation need not be identical. Both numbers originate from the same documentation, so this is a consistency check, not independent video validation.

Evidence: [test-level measurements](data/processed/metrics.csv), [model dataset](data/processed/model_dataset.csv), and [validation details](data/processed/VALIDATION.md).

## Meaning of every exported test-level metric

Ranges below summarize the available values across tests. An availability count indicates how many of the nine records contain a value; it does not establish independent replication or measurement precision.

| Metric | Unit | Exported range or categories | What was calculated or retained, and what it means |
|---|---|---|---|
| `material` | category | Silicone; SIBAL (cotton/fiberglass); PMMA–Nomex composite; PMMA (9/9 available) | Describes the specimen composition. Groups tests for material selection; a material name alone does not establish fire safety. |
| `thickness_nominal_mm` | mm | 0.270–10.000 (9/9 available) | Records nominal thickness, including 10 mm for grooved PMMA. Geometry can affect burning. II-7 uses the Nomex section's 0.37 mm; II-8 has no validated single effective thickness. |
| `length_cm` | cm | 29.0 (9/9 available) | Records the specimen's nominal length. Establishes the experimental scale; the composite specimen contains 5 cm PMMA and 24 cm Nomex. |
| `width_cm` | cm | 5.0 (9/9 available) | Records the specimen's nominal width. All tests have the same width, so the dataset cannot estimate width effects. |
| `flow_direction` | category | concurrent; opposed (9/9 available) | Labels concurrent or opposed flow. Only II-4 is opposed; direction effects are confounded with specimen configuration. |
| `flow_pre_cm_s` | cm/s | 19.976–24.989 (9/9 available) | Averages the two anemometers, then takes the pre-ignition median. Provides a condition measured before the outcome; eight tests are near 20 cm/s and one near 25 cm/s. |
| `pressure_pre_kpa` | kPa | 102.495–102.759 (9/9 available) | Converts PSIA to kPa and takes the pre-ignition median. Supports atmosphere comparisons; the narrow near-terrestrial range cannot establish low-pressure behavior. |
| `o2_pre_sensor_pct` | % | 21.522–21.797 (9/9 available) | Takes the pre-ignition O2 sensor median. Documents the local oxidant condition; absolute calibration uncertainty is unresolved. |
| `o2_partial_pre_kpa` | kPa | 22.059–22.366 (9/9 available) | Multiplies pre-ignition pressure by the O2 percentage divided by 100. Describes oxygen partial pressure; equal partial pressure does not establish equivalent fire behavior at different total pressures and O2 fractions. |
| `o2_table_pct` | % | 21.500–22.100 (9/9 available) | Preserves the initial O2 values in the published table. Provides documentary context; table values are CO2-derived and were excluded as independent model inputs. |
| `ignition_epoch_ms` | ms since Unix epoch | 1479773207594–1479780645040 (9/9 available) | Locates the first enabled electrical-channel product above the pipeline threshold. Aligns channels within each specimen record. It is an electrical marker, not a verified optical ignition time. |
| `ignition_duration_measured_s` | s | 9.141–29.997 (9/9 available) | Measures the active pulse span plus one sample interval. Checks event timing against the commanded pulse; it does not validate the absolute electrical-channel scale. |
| `ignition_duration_command_s` | s | 9.200–30.000 (9/9 available) | Transcribes the programmed pulse duration. An input available before the test; it is not the subsequent burn duration. |
| `ignition_power_command_w` | W | 80.0–97.0 (9/9 available) | Transcribes the nominal programmed ignitor power. Provides the documented setpoint. It does not resolve the much larger power product in the extracted channels. |
| `ignition_energy_measured_j` | J | 25984.8–111969.0 (9/9 available) | Integrates the enabled voltage/current channel product over time. Unvalidated physical magnitude: 26–112 kJ conflicts with nominal power × duration. Treat as a channel-scaling review item; do not use it for fire-energy or equipment sizing. |
| `co2_pre_ppm` | ppm | 3306.781–4333.854 (9/9 available) | Takes the median CO2 reading during the preceding 30 seconds. Defines the local baseline and preserves the cabin's prior-test history. |
| `co2_increase_180s_ppm` | ppm | -16.611–107.004 (9/9 available) | Subtracts the pre-ignition median from the median at 150–180 seconds. The model target: a comparable signed local sensor response, not emitted CO2 mass, exposure dose, or total fire intensity. |
| `co2_peak_180s_ppm` | ppm | 3350.291–4397.234 (9/9 available) | Takes the maximum one-second median during the first 180 seconds. Shows the largest early reading at this sensor; it is not a spatial cabin maximum or a health threshold. |
| `co2_end_change_ppm` | ppm | -11.403–749.010 (9/9 available) | Subtracts the local baseline from the median of the last 30 one-second bins. Describes the full recorded response. Record durations differ, so this is not the common-horizon training target. |
| `o2_change_180s_percentage_points` | percentage points | -0.225–0.037 (9/9 available) | Subtracts the pre-ignition O2 median from the median at 150–180 seconds. Describes a local temporal change; it is not an inlet/outlet oxygen-consumption measurement. |
| `pressure_change_180s_kpa` | kPa | 0.002–0.038 (9/9 available) | Subtracts pre-ignition pressure from the median at 150–180 seconds. Describes a small pressure response; the fire's contribution is not isolated from other vehicle processes. |
| `inlet_temperature_change_180s_c` | °C | 0.032–0.208 (9/9 available) | Subtracts the pre-ignition inlet temperature from the median at 150–180 seconds. Measures local duct-inlet warming, not average cabin heating. |
| `plume_peak_180s_c` | °C | 22.625–85.851 (9/9 available) | Selects the largest one-second median from six plume thermocouples. Shows the hottest sampled local location; sensor placement limits coverage of flame temperature. |
| `radiation_peak_excess_180s_kw_m2` | kW/m2 | 0.051–0.562 (9/9 available) | Subtracts each radiometer's baseline and selects the largest early one-second median. A local relative radiative signal affected by viewing geometry and possibly the ignitor; it cannot be converted directly into total HRR. |
| `material_outcome` | category | No sustained spread; Complete fabric spread; PMMA consumed; Nomex not ignited; Anchored flame; slow regression (9/9 available) | Transcribes the documented microgravity behavior. Supports prevention decisions for the tested configuration; does not certify behavior under another atmosphere or gravity. |
| `spread_rate_reported_mm_s` | mm/s | 2.100–2.600 (2/9 available) | Transcribes the two published SIBAL spread rates. Quantifies propagation where available. These values were not independently measured from the images. |
| `burn_duration_reported_s` | s | 115.000–900.000 (5/9 available) | Transcribes numeric burn durations for five specimens. Describes persistence; 'insignificant' for silicone remains missing rather than becoming a measured zero. |
| `microgravity_burn_length_reported_cm` | cm | 0.0–29.0 (9/9 available) | Preserves published burned/damaged lengths and component-specific notes. Definitions differ: approximate zero for silicone, full 29 cm fabric, 5 cm PMMA in the composite, and about 10 cm visible damage in the slabs. |
| `ground_burn_length_label` | reported_text | Complete; 7.6 cm; ~ 0; ~ 0 (Nomex) (9/9 available) | Preserves the reported normal-gravity burn-length description. Provides context for screening comparisons; the ground tests are not randomized replicates under identical ventilation. |
| `hrr_peak_kw` | kW | null (0/9 available) | Reserved for oxygen-consumption heat release rate. Missing: no validated inlet/outlet O2 and mass-flow pair, or validated cabin mass balance. |
| `co_hazard_index` | ratio | null (0/9 available) | Reserved for measured CO divided by an applicable exposure limit. Missing: no CO channel or applicable exposure threshold is available. |
| `co2_hazard_index` | ratio | null (0/9 available) | Reserved for measured CO2 divided by an applicable exposure limit. Missing: no applicable mission/exposure-duration limit was established. |
| `smoke_alarm_delay_s` | s | null (0/9 available) | Reserved for elapsed time from ignition to a documented alarm. Missing: no calibrated alarm event/threshold and no verified Cygnus–Saffire clock alignment. |
| `flow_cut_extinction_delay_s` | s | null (0/9 available) | Reserved for elapsed time from controlled flow cutoff to extinction. Missing: no identified controlled cutoff intervention and extinction event. |
| `effective_grooved_thickness_mm` | mm | null (0/9 available) | Reserved for a defensible effective thickness of the grooved slab. Missing for II-8 because no single effective thickness is established; not applicable to the other specimens. |

The one-second time series additionally retain individual radiometer, plume-temperature, specimen-temperature, flow, and inlet-temperature channels. Those channels support inspection of sensor coverage and timing, rather than adding independent experimental replicates.

## AutoResearch setup and model results

The original GPU/LLM training files were preserved in [upstream_reference](upstream_reference/). The adapted [prepare.py](prepare.py) fixes data validation, allowed inputs, seed 164, evaluation folds, and metric calculation. [train.py](train.py) contains the candidate model. Each of the 15 attempts was tested, committed, evaluated with a timeout, and assigned a keep/discard decision.

The allowed inputs were material, nominal thickness, pre-ignition flow, flow direction, commanded ignition duration, commanded ignition power, and structured-PMMA status. These are conditions available before the outcome. Test IDs, burn duration, burned length, measured CO2 outcomes, and outcome classifications were not passed to the model. The selected model actually uses **material group and pre-ignition flow**.

Evaluation leaves out one test, fits on the remaining eight, predicts the omitted response, and repeats for all nine. Final coefficients are refitted on all nine rows only after held-out predictions have been calculated. A candidate adding parameters needed at least 2% relative RMSE improvement per added parameter; otherwise the minimum improvement was 0.1%.

### Prediction-error results

| Metric | Training-mean baseline | Selected model | Interpretation |
|---|---:|---:|---|
| RMSE | 41.416 ppm | 23.451 ppm | Square root of the mean squared held-out error; gives larger errors more influence. |
| MAE | 34.449 ppm | 17.828 ppm | Mean absolute held-out error; expresses the average magnitude of the prediction error. |
| Maximum absolute error | 84.293 ppm | 56.360 ppm | Largest absolute error among the nine held-out predictions; this is not a bound for future tests. |
| Fitted parameters | 1 | 2 | Baseline fits one mean; the selected model fits two material-group locations. |

RMSE fell by **43.38%** within this fixed evaluation. That comparison describes the observed search. The same cross-validation was used repeatedly to select candidates, so the best score is optimistic and is not an independent prospective test result.

### Selected formula and parameter meaning

The selected model is `group_huber20_inverse_flow`:

```text
Predicted delta_CO2_180_ppm =
    -2.3719876375                         for Silicone
    55.6116215801 × (20 / v_cm_s)          for SIBAL, PMMA, or PMMA_Nomex
```

- **−2.372 ppm:** the fitted robust silicone-group response. Its small negative sign describes the sensor-change target; it is not a prediction of negative CO2 concentration.
- **55.612 ppm:** the fitted non-silicone group response at the 20 cm/s reference flow. SIBAL, PMMA, and the PMMA–Nomex specimen are pooled to limit the number of fitted quantities.
- **20/v:** an assumed inverse-flow correction with exponent fixed at 1, not an exponent estimated from the nine observations. Only II-6 provides the substantially higher flow condition.
- **Huber transition of 20 ppm:** a fixed robust-estimation setting. Large residuals have reduced influence on the fitted group locations. This setting is not a gas-exposure limit.

### Held-out predictions

Error is **predicted minus observed**, in ppm.

| Test | Observed response | Held-out prediction | Signed error |
|---|---:|---:|---:|
| II-1 | 3.06 | -4.18 | -7.24 |
| II-2 | 15.03 | -8.17 | -23.20 |
| II-3 | -10.96 | 0.49 | 11.46 |
| II-4 | -16.61 | 2.37 | 18.99 |
| II-5 | 39.65 | 60.97 | 21.32 |
| II-6 | 45.65 | 44.13 | -1.52 |
| II-7 | 107.00 | 50.64 | -56.36 |
| II-8 | 60.56 | 54.01 | -6.55 |
| II-9 | 45.31 | 59.14 | 13.82 |

The largest miss is II-7, the only PMMA–Nomex composite: the model underpredicts its response by 56.36 ppm. Pooling materials stabilizes a small dataset but misses some specimen-specific behavior.

II-6 is the only test near 25 cm/s. When it is omitted, its held-out prediction uses a flow outside that fold's training range. II-7 also introduces a material composition absent from its fold's training data. The main JSON's `extrapolation: false` flags for these CV predictions refer to the **full dataset's domain**; they do not mean that every prediction is supported inside its individual training fold. The additional [fold-support audit](runs/verification/final_checks.json) records these distinctions.

### All 15 attempts

| Attempt | Candidate or change | RMSE (ppm) | Fitted parameters | Decision |
|---:|---|---:|---:|---|
| 1 | Baseline: training-fold mean, one parameter | 41.416 | 1 | keep |
| 2 | Two-parameter material-regime OLS: silicone versus carbonaceous specimens | 25.472 | 2 | keep |
| 3 | Ridge shrinkage alpha=1 on the same two material-regime parameters | 27.232 | 2 | discard |
| 4 | Separate material offsets; singleton composite uses training-only minimum-norm fallback | 38.848 | 4 | discard |
| 5 | Ridge alpha=1 regularizes four material-category parameters | 39.516 | 4 | discard |
| 6 | Add silicone log-thickness sensitivity constrained nonpositive; three parameters | 25.977 | 3 | discard |
| 7 | Two robust material-regime medians; reduce outlier influence without extra parameters | 25.305 | 2 | keep |
| 8 | Two material-regime Huber locations with fixed 20 ppm residual transition | 24.020 | 2 | keep |
| 9 | Two material-regime trimmed means when at least four training records exist | 24.471 | 2 | discard |
| 10 | Two-parameter inverse-flow dilution response for non-silicone specimens | 25.064 | 2 | discard |
| 11 | Two-parameter flow-proportional fuel-supply response for non-silicone specimens | 27.376 | 2 | discard |
| 12 | Material regime plus known ignition pulse duration; three coefficients | 29.438 | 3 | discard |
| 13 | Material regime plus opposed-flow offset; three coefficients | 25.559 | 3 | discard |
| 14 | Ridge material regime and logarithmic nominal thickness; three coefficients | 29.871 | 3 | discard |
| 15 | Huber material regimes with fixed inverse-flow dilution; two fitted parameters | 23.451 | 2 | keep |

Five attempts, including the baseline, were kept at their evaluation time; ten were discarded and none crashed. Separate offsets for every material, additional geometry terms, and ignition/direction terms did not improve the selected score. This is evidence for preferring a compact model in this pilot, not evidence that those physical variables are unimportant in fire behavior.

The selected experimental commit is `2af682a96609f938a023eb5bf94d62441d4e0d4d`. The retained experiment differs from `baseline-v1` only in `train.py`.

## Cabin and smoke results

The cabin statistics below come from a separate Cygnus telemetry stream. Zero-filled and implausible entries were excluded using documented plausibility filters; these filters are not alarm thresholds. Counts refer to retained records, not independent fire events.

| Channel | Recorded range | Median | Retained records | Meaning |
|---|---|---|---:|---|
| Cabin temperature | 19.776–21.333 °C | 20.084 °C | 4142 | A local mission-record temperature range; not a spatial mean or a per-fire temperature rise. |
| Cabin pressure | 99.754–100.202 kPa | 99.866 kPa | 4142 | A mission-record pressure range from a different telemetry stream; not an aligned per-test pressure increment. |
| FIZ2 obscuration | 3.925–3.965 V | 3.950 V | 389 | Detector voltage, without an established conversion to smoke concentration or alarm state. |
| FIZ2 scatter | 0.035–2.830 V | 0.040 V | 390 | An optical detector signal, without an established alarm threshold or particle-mass conversion. |

These measurements establish that cabin and smoke information exists. They do not establish the time from a particular ignition to alarm, a safe exposure interval, average cabin conditions, or the temperature/pressure change caused by an individual fire. Verified clock synchronization and sensor/alarm calibration are still required.

Evidence: [cabin metrics](data/processed/cabin_metrics.csv).

## Habitat relevance rankings

The ranking answers **which tests are useful evidence for a stated scenario**. It is not a probability of ignition, a danger ranking of materials, or a validation of the model in that habitat.

The documented 100-point rubric assigns up to 30 points for O2 similarity, 25 for pressure similarity, 15 for gravity similarity, 5 for sample scale, 5 for documented fire behavior, 10 for quantitative data availability, and 10 for a ground-test comparison. Weights and similarity scales are analyst choices.

The atmosphere and gravity values below are **illustrative analyst design assumptions, not actual NASA mission requirements**.

| Scenario | Assumed O2 (%) | Assumed pressure (kPa) | Assumed gravity (g) | Leading test(s) and relevance score |
|---|---:|---:|---:|---|
| ISS-like spacecraft | 21.0 | 101.3 | 0.000 | II-5, II-6 (95.08/100) |
| Lunar base | 34.0 | 56.5 | 0.165 | II-5 (50.88/100) |
| Pressurized lunar rover | 34.0 | 56.5 | 0.165 | II-5 (50.88/100) |
| Mars base | 26.5 | 70.3 | 0.380 | II-5 (63.55/100) |
| Gateway-like station | 21.0 | 101.3 | 0.000 | II-5, II-6 (95.08/100) |

Measured pre-ignition conditions span **102.50–102.76 kPa** and **21.52–21.80% O2**, in microgravity. This explains the higher similarity to the assumed ISS/Gateway scenarios. Lower scores for lunar, rover, and Mars scenarios reflect mismatches and missing transfer evidence; they do not prove those environments are safer or more dangerous.

II-5 and II-6 rank highly because they combine documented propagation, numeric spread rates, and ground-comparison context. Very small score differences should not drive scientific conclusions. The lunar base and rover use identical assumptions and therefore have identical rankings.

No low-pressure/enriched-O2 or partial-gravity prediction was validated. The export leaves the unsupported exploration-atmosphere prediction null.

## Interpretation for the three challenge objectives

| Objective | Supported result | Practical meaning and limit |
|---|---|---|
| Identify relevant investigations | Nine Saffire-II test records are available; SIBAL tests provide numeric spread evidence; current atmosphere similarity favors the assumed ISS/Gateway cases. | Prioritize these tests for the questions they actually measure. Additional missions are needed for enriched-O2/low-pressure environments and broader fire scales. |
| Extract predictive data | A traced nine-row fixed-horizon CO2 dataset and a two-parameter pilot were produced. | Useful for demonstrating an auditable modeling workflow and comparing local responses. It is not yet a validated predictor of another flight, atmosphere, toxic dose, or total fire intensity. |
| Inform next-generation controls and equipment | Material outcomes, local thermal/radiative signals, and mission smoke/cabin records were extracted; major information gaps were made explicit. | Supports prevention evidence and diagnostic planning. HRR, alarm-delay, exposure-risk, and controlled ventilation-cutoff results remain unavailable for equipment sizing or suppression validation. |

## Verification and deliverables

The completed scientific workflow recorded:

- **22 passing tests**, including data integrity checks, target recomputation from the extracted series, input restrictions, evaluation behavior, export consistency, and experiment-gate rules.
- **Two complete extraction/export passes** producing identical scientific JSON apart from `generated_at`, with byte-identical processed files.
- **SHA-256 verification of all 218 raw files** against the initial manifest, followed by size/mtime checks after regeneration.
- An experiment history of **15 logged candidates**, with preserved logs and commits, and a selected baseline-to-best diff containing only `train.py`.

These checks establish reproducibility and consistency. They do not resolve unknown sensor calibration, the electrical-energy discrepancy, the lack of independent flights, or the absence of external model validation.

| Deliverable | Purpose |
|---|---|
| [analysis-saffire.json](analysis-saffire.json) | Dashboard-ready tests, provenance, model evidence, findings, rankings, and limitations. |
| [DATA_PLAN.md](DATA_PLAN.md) | Metric selection, exclusions, uncertainty approach, target, and relevance rubric. |
| [metrics.csv](data/processed/metrics.csv) | Every test-level value with its source, method, reason, and interpretation. |
| [model_dataset.csv](data/processed/model_dataset.csv) | The nine modeling rows and target variability. |
| [sensor_timeseries.csv](data/processed/sensor_timeseries.csv) | One-second sensor summaries for temporal inspection. |
| [VALIDATION.md](data/processed/VALIDATION.md) | Comparisons with documentary values and retained discrepancies. |
| [Control figures](data/processed/figures/) | CO2 windows, thermal coverage, image sampling, and published SIBAL rate comparison. |
| [Experiment ledger](runs/autoresearch/saffire-run-01/results.tsv) | Candidate metrics, commits, keep/discard decisions, and descriptions. |
| [Reproducibility evidence](runs/verification/reproducibility.json) | Regeneration comparison and processed-file hashes. |
| [Final checks and fold-support audit](runs/verification/final_checks.json) | Final consistency checks and within-fold support limitations. |

The reporting precision supports exact reproduction. It should not be interpreted as the sensors' physical accuracy.

## Sources

**Primary dataset attribution, as supplied for this report:**

Urban DL, Ruff G. "Spacecraft Fire Experiment-II(SAFFIRE-II)", NASA PSI Data Repository, Version 5, [http://doi.org/10.60555/2chp-m469](http://doi.org/10.60555/2chp-m469).

The local investigation metadata, postflight experimental table, sensor spreadsheets, dataset-description document, camera nomenclature, and thermocouple waiver are listed in [the inventory](data/inventory/inventory.csv). Numerical results in this report are taken from the local processed CSV files, `analysis-saffire.json`, and the recorded verification evidence.
