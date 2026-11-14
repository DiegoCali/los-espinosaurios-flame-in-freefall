# Saffire inventory

218 physical files; 33.810 decimal GB, including two redundant delivery containers.

Only Saffire-II has local raw test data: specimens II-1 through II-9. F1/F2 are pre/post-flow sets, and BIT is an equipment check. Image variants are not experimental replicates.

The metadata ZIP declares `Study Identifier PSI-99`, DOI 10.60555/2chp-m469.

## Observed variables

CO2_pct, O2_pct, flow_cm_s, pressure_psia, radiation_mW_cm2, plume_temperature_C, sample_temperature_C, humidity_pct, inlet_temperature_C, igniter_current_A, igniter_voltage_V, fan_speed_rpm, camera_timestamp_ms, cabin_pressure_psi, cabin_temperature_C, smoke_obscuration_V, smoke_scatter_V

The `Calibrated Data` worksheets provide headers and units: gas fractions in %, pressure in PSIA, flow in cm/s, radiation in mW/cm2 and temperature in degrees C. Stored Excel values are read without executing formulas. Zero-filled Cygnus entries are excluded.

## Missing or ambiguous information

- No raw tests from Saffire I, III, IV, V or VI
- CO, acid gases, particle mass, alarm thresholds and exposure limits unavailable
- No inlet/outlet O2 pair, exhaust mass flow, or validated mixed cabin volume for HRR
- Preflight and postflight thicknesses and sample-6 flow disagree
- Published O2 is CO2-derived; sensor O2 fluctuates; no atmosphere-response fit is supported
- Grooved sample-8 effective thickness undefined
- Radiometers have different views of samples; local flux is not total power
- Repeated image variants and zero-filled cabin telemetry require filtering
- Cygnus and Saffire clocks cannot be assigned per-test reliably from cached alignment columns

## Provenance decisions

Flow and pressure use pre-ignition measurements. Material, nominal thickness and outcomes use the postflight table. Empty material cells for II-6 and II-9 are inherited and corroborated by documentation. The CSV text `037 mm` is interpreted as 0.37 mm. Measured II-6 flow is near 25 cm/s, versus 20 in the CSV and 30 in planning documents. SFS-W-009 gives SIBAL B thermocouple heights of 4.445 and 3.175 mm; their peaks are not used to infer spread rates.

`inventory.csv` lists every physical file and initial SHA-256. `archives.csv` counts ZIP members without expanding image payloads. `raw_integrity_initial.json` preserves the original size, modification time and hash for each file. The completed experiment included full SHA-256 verification; later documentation work checks that raw file sizes and modification times remain unchanged.

The derived ignitor energy has an unresolved voltage/current scaling discrepancy. Its magnitude is unvalidated and was not a model input. See `data/processed/VALIDATION.md` and the English analysis reports.

Dataset source: Urban DL, Ruff G. "Spacecraft Fire Experiment-II(SAFFIRE-II)", NASA PSI Data Repository, Version 5, [http://doi.org/10.60555/2chp-m469](http://doi.org/10.60555/2chp-m469).
