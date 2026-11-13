# SAME-R explained in plain English

**Smoke from overheated spacecraft materials is made of very small particles, and those particles grow while the smoke travels. Detectors built on different physical principles miss different smoke: light scattering misses tiny particles, ionization misses dilute, coarse smoke. Using both would have caught almost every case.**

## 1. What was measured

In 2010, aboard the International Space Station (Expedition 24), the **SAME-R** experiment (the reflight of the *Smoke Aerosol Measurement Experiment*, investigation PSI-101) heated small samples of materials used in spacecraft until they gave off smoke, **without letting them ignite**. The materials were **Kapton** and **Teflon** (wire insulation), **Pyrell** (polyurethane foam), **silicone rubber** and a **cotton lamp wick** (cellulose). This smoke is the first sign of an electrical fire, which is exactly what a detector must catch early.

Each test has four steps (see `data/processed/figures/example_timeseries.png`):

1. **Heat** the sample for about 53 s while a piston draws air past it at 8 cm/s (or with no flow).
2. **Hold** the smoke in an aging chamber. This stands in for the time smoke needs to travel from a fire to a detector.
3. **Push** the smoke through a duct with instruments: a particle counter (P-Trak), an ionization chamber, a laser photometer (DustTrak), and the real smoke detectors of the ISS (photoelectric) and the Space Shuttle (ionization).
4. **Collect** particles on grids for electron microscopy (TEM) on the ground.

## 2. What was calculated

With the **moment method**, three instruments give three averages of the particle population: how many particles there are (M0), the sum of their diameters (M1) and the sum of their volumes (M3). From them come the mean diameter (AMD = M1/M0), the diameter of average mass (Dm) and, assuming a log-normal distribution, the typical diameter (Dg) and the width of the distribution (σg).

From the second-by-second telemetry we also calculated how long each smoke aged, the flow it was made with and how strongly each detector responded.

## 3. Main results

- **NASA's published sizes are reproduced** (Dm differs by at most 11%).
- **Wire-insulation smoke is tiny:** Kapton about 0.10 µm and Teflon about 0.19 µm (Dm, unaged), against about 0.42 µm for Pyrell and 0.48 µm for silicone.
- **Smoke grows while it travels:** in about 10 minutes 50–75% of the particles disappear because they collide and merge (Brownian coagulation), and Dm grows by a factor of 1.25 to 1.56. The measured rate (9.0e-10 cm³/s) agrees with theory and with NASA's own note.
- **With no flow (possible only in microgravity, where smoke does not rise)** the smoke stays concentrated near its source, coagulates very quickly and arrives with larger but far fewer particles.
- **The two detector types fail in opposite situations.** With flow, the ISS photoelectric detector responded to 71% of pushes, but to only 27% for Kapton, while the ionization chamber responded to 93%. Without flow it reverses: ISS 90%, ionization 10%. With **both** detectors, 95% of cases would have produced a response.
- **The Space Shuttle detector** alarmed in 6 of the 9 pushes in which it was powered.

## 4. What it means for fire safety

A detector that measures **one property** of smoke has a blind spot. Scattered light barely sees 0.1 µm particles (overheated wiring in ventilated areas), and an ionization chamber loses signal in dilute, coarse smoke (smoke trapped in avionics boxes or unventilated corners). **Measuring at least two moments**, as the MPASS sensor demonstrated on SAME-R did, or combining ionization and scattering, covers both cases.

## 5. The predictive model (autoresearch)

An *autoresearch*-style loop (adapted from karpathy/autoresearch, without git commits) tried 15 versions of `train.py` and kept the best. The selected model uses the material, the aging time (through coagulation physics), the flow and the heater temperature.

- On tests it **never saw**, it predicts Dm with a typical error factor of ×1.23 (about ±23%), comparable to the ±15% repeatability NASA reports.
- Its combined score is 0.529, against 1.043 for "always predict the average" (lower is better).
- It also estimates each detector type's **false-negative risk** by material, flow and transport time (`data/processed/figures/model_scenarios.png`).

## 6. Important limits

- Only **SAME-R (PSI-101)** data are available locally; SAME-1 (PSI-102, 2007) is not in the download.
- "Detected" means exceeding a **proxy threshold** defined in this project (ISS: scatter drop of at least 1 V; ionization: rise of at least 0.5 V), not the real alarm logic. The sensitivity figure shows the conclusion does not depend on the threshold.
- NASA chose the amount of smoke to give a measurable signal, so these are not probabilities for real fires.
- The model is the best of 15 attempts on about 50–65 rows, so its gain is somewhat optimistic and it has not been validated on another flight.
- Ten tests have no NASA material label; their materials are inferred from the heater wire and were not used in the models (see `data/processed/VALIDATION.md`).

## 7. Files

- Dashboard: `analysis-same-summary.json` (schema 1.0.0) and `analysis/output/same-summary.png`.
- Detail: `analysis-same.json`, `analysis-same.md`, `SAME_ANALYSIS_REPORT_EN.md`, `data/processed/*.csv`.
- Knowledge base: `knowledge/SAME_KNOWLEDGE_BASE.md`.
