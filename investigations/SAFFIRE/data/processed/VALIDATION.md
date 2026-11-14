# Validation and discrepancies

## Electrical events versus the postflight table

This comparison uses AG x AH and AR electrical channels rather than outcome labels. The fixed 0.15 s tolerance covers sampling and pulse-threshold definitions; it is not a flame-duration accuracy claim.

| Test | Measured (s) | Published (s) | Absolute difference (s) | Status |
|---|---:|---:|---:|---|
| II-1 | 9.174 | 9.2 | 0.026 | pass |
| II-2 | 9.24 | 9.2 | 0.04 | pass |
| II-3 | 9.207 | 9.2 | 0.007 | pass |
| II-4 | 9.207 | 9.2 | 0.007 | pass |
| II-5 | 9.141 | 9.2 | 0.059 | pass |
| II-6 | 9.174 | 9.2 | 0.026 | pass |
| II-7 | 9.174 | 9.2 | 0.026 | pass |
| II-8 | 29.964 | 30.0 | 0.036 | pass |
| II-9 | 29.997 | 30.0 | 0.003 | pass |

## Consistency of published propagation values

No independent optical front trajectory was extracted. Variable exposure, dark flames and different views prevent certifying a calibrated trajectory. The rates are labeled as published values, not new image measurements.

| Test | Published length/duration (mm/s) | Published spread rate (mm/s) | Relative difference |
|---|---:|---:|---:|
| II-5 | 2.000000 | 2.100000 | 4.76% |
| II-6 | 2.521739 | 2.600000 | 3.01% |

The roughly 3-5% differences compare quantities with different definitions and time intervals. Both numbers come from the same published table. This is an accounting check, not independent validation of the video.

## Retained or reconciled discrepancies

- II-6 pre-ignition flow measures 24.988703 cm/s. The CSV says 20 and planning documents say 30. The measurement is used; the NASA NTRS 20180005168 postflight table (PDF page 30) also reports 25 cm/s.
- Preflight thicknesses 0.25/1.02/0.36/0.33 mm differ from postflight 0.27/1.03/0.37 mm. Postflight values take precedence. CSV `037` is interpreted as 0.37 with postflight support. Grooved PMMA is 10 mm nominal; its effective thickness remains null.
- The II-1 CSV O2 cell says about 21.5%, whereas the postflight presentation summarizes about 22.1%. Other table oxygen values are CO2-derived (note 1) and are not independent model inputs. Sensor readings are retained with unknown absolute calibration uncertainty.
- SFS-W-009 documents SIBAL B thermocouples at 0.175 and 0.125 inches (4.445 and 3.175 mm), rather than 0.20 inches nominal. Their peaks are not converted into spread velocities.
- Radiometers have negative offsets and different views. Only excess above each instrument's baseline is reported; readings are not summed or converted into total fire power.
- The local SaffireIIStitchedCO2V7 plot uses an approximate 0.30-0.50% CO2 scale. Extracted readings have the same order of magnitude, with the final record slightly above 0.50%. This is a scale check, not independent calibration.
- CygnusData contains zero-filled records, which are filtered. Its V/Y alignment columns lack stored numeric values. No clock offset is guessed to calculate per-test alarm delays.

## Ignitor energy requires validation

The archived voltage/current-product integral gives 25.98-111.97 kJ. Nominal commanded energy is only 0.736 kJ (80 W x 9.2 s) or 2.910 kJ (97 W x 30 s). Channel units, scaling and interpretation need review. Agreement in pulse duration does not validate the absolute energy scale. The calculated energy was not an input or target of the model and should not be used for fire-energy or equipment-sizing conclusions.

## Uncertainty

The CO2 target compares medians of one-second medians in two 30-second windows. Its descriptive variability is sqrt((1.4826 MAD_pre)^2+(1.4826 MAD_final)^2). It is not divided by sqrt(n), because autocorrelation is unknown. This quantity is not a confidence interval or absolute calibration accuracy. Small negative CO2 changes are retained and do not demonstrate physical CO2 consumption.

No published table provides exactly the same 180 s response for independent validation. Leave-one-test-out evaluation checks internal predictive consistency, not transfer to another mission or atmosphere.
