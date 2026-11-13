# SAME / SAME-R knowledge base

Reference notes for the `investigations/SAME/` module (NASA PSI-101 SAME-R and PSI-102 SAME).
Sources are listed at the end; statements marked _(this study)_ come from the local analysis.

## 1. Why the experiment exists

Spacecraft smoke detectors were designed from terrestrial fire data. In microgravity there is no buoyant
plume, so smoke lingers near its source, residence and transport times grow, and particles have more
time to coagulate. Spacecraft fires are also expected to begin as **overheated, non-flaming** materials
(wire insulation, electronics), whose smoke is condensed pyrolysis products rather than soot. Earlier
experiments (Comparative Soot Diagnostics, CSD, on STS-75) suggested low-gravity smoke can be larger
than in 1 g, but could not size liquid smoke well enough to guide detector design. SAME was built to
measure the particle-size statistics of such smoke **on orbit** with minimal sample return.

| | SAME (SAME-1) | SAME-R (SAME-2, "reflight") |
|---|---|---|
| PSI ID | PSI-102 | PSI-101 |
| Flight | ISS Expedition 15, 2007 (MSG) | ISS Expedition 24, July–Sept 2010 (MSG) |
| Local data | none | **all files in the team download** (`SAMERFLT` grid labels, 2010 timestamps) |
| Light-scattering | 2 DustTraks (1 µm and 10 µm impactors) | 1 DustTrak + **MPASS** two-angle sensor (tech demo) |
| TEM grids | contaminated, unusable | 72 grids, good images |
| Test matrix | baseline flow/temperature | + higher temperatures, **no-flow** runs, longer aging |

Principal investigator: David L. Urban (NASA Glenn); co-investigators include G. Ruff, P. Greenberg,
M. Meyer (GRC), G. Mulholland (U. Maryland), T. Cleary and J. Yang (NIST), Z.-G. Yuan and V. Bryg (NCSER).

## 2. Hardware and test sequence

Installed in the Microgravity Science Glovebox (MSG). From the VPRED (SAME-PLN-005 Rev F, 2007) and
Urban et al. (2012):

- **Sample carousel + heater**: each sample is wrapped around a resistance-wire heater coil. Wire
  resistance is linear with temperature, so the hot/cold ratio **Rt/R0** is the temperature set point
  (design range 50–500 °C). The baseline temperature was chosen per material to give 1–2 mg of mass loss
  in ~60 s; "mid"/"high" runs use larger Rt/R0. A plume thermocouple records gas temperature.
- **Smoke generation duct → aging chamber**: a piston (~6 L) driven by vacuum draws air past the hot
  sample (baseline 8 cm/s duct velocity) for ~60 s, filling the chamber; a mixing fan homogenises it.
- **Aging**: the smoke is held for a programmed time (11–1800 s in SAME-2) to emulate transport time from
  a fire to a detector. Several pushes can be taken from one fill (pre-age and post-age).
- **Diagnostics duct**: GN2 drives the piston, pushing smoke through the instruments. A dynamic diluter
  feeds the P-Trak; a static diluter (~4:1) is available for the optical instruments.
- **Thermal precipitators** (6 modules, A/B sides, 6 slots): a heated wire drives particles onto TEM grids
  by thermophoresis — one grid for the first (pre-age) push and one for the post-age push.
- **No-flow runs** (11 tests in SAME-2): valves re-sequenced so the sample is heated in still air and the
  chamber is filled afterwards. Pyrolysis products stay ~4 cm around the sample (~64 cm³ instead of the
  6000 cm³ chamber), so the initial concentration is ~50× higher; about half the smoke diffuses out of the
  inlet, so counts are lower. This condition only exists in microgravity.

_(this study)_ Telemetry segmentation: heating ≈ 52–56 s; first push 36–40 s after the fill valve closes;
second push 211–1913 s. Fill flow during heating is ~4.3 L/min (↔ 8.1 cm/s) or 0 (no-flow).

## 3. Materials

| Code | Material | Spacecraft use | Smoke character (SAME-2) |
|---|---|---|---|
| K | Kapton (polyimide) | wire insulation, flexible circuits | smallest particles, liquid-like spheres and chains |
| T | Teflon (PTFE) | wire insulation | small fractal aggregates, beam-sensitive in TEM |
| L | Lampwick (cotton cellulose) | paper, cloth, cellulose stand-in | larger liquid droplets (200–1400 nm in TEM) |
| P | Pyrell (polyurethane foam) | packing foam | aggregates with flow, spheres without flow |
| S | Silicone rubber | seals, cable jackets | large, partly liquid (evaporates under TEM) |
| D | Dibutyl phthalate (DBP) on a wick | reference aerosol | liquid; not identified in the local files |

Run ↔ sample numbering: the grid label `SAMERFLT nX` corresponds to run `n + 47` (e.g. `53T` = run 100).

## 4. The moment method

Three instruments measure three moments of the number size distribution f_N(D):

| Moment | Physical meaning | SAME instrument | Notes |
|---|---|---|---|
| M0 = ∫ f_N dD | number concentration (#/cm³) | **P-Trak** (TSI) condensation nuclei counter | isopropanol condensation, 0.02–1 µm, 0–10⁵ /cm³ → needs N2 dilution (smoke is 0.5–5×10⁶ /cm³); condenser grooved for microgravity |
| M1 = ∫ D f_N dD | "diameter concentration" | **ionization chamber** from a residential (First Alert) detector | ion current reduction ∝ Σ N·D; nearly size-independent calibration; no dilution |
| M3 = ∫ D³ f_N dD | volume / mass concentration | **DustTrak** (TSI) 90° photometer | 0.001–100 mg/m³; calibrated per material against a TEOM microbalance |

Derived quantities (no shape assumption): count mean diameter **AMD = D0.5 = M1/M0**; diameter of
average mass **Dm = D1.5 = (M3/M0)^(1/3)**.

Assuming a **log-normal** distribution with geometric mean Dg and geometric standard deviation σg
(Hatch–Choate): D_p = Dg · exp(p · ln²σg). Hence

    ln²σg = ln(Dm / AMD)        Dg = AMD / exp(½ ln²σg) = Dm / exp(1.5 ln²σg)
    M_k   = M0 · Dg^k · exp(k² ln²σg / 2)

Dm > AMD is a necessary condition for a log-normal; σg between 1 and ~3.5 is physically reasonable.
_(this study)_ NASA's tabulated σg equals exp(√ln(Dm/AMD)) to within 2% for every usable row; seven rows
violate a condition (e.g. AMD = 65.14 µm, σg = 20.66, Dm < AMD) and are flagged.

Calibration (Urban 2012): monodisperse DOP droplets and polystyrene spheres vs TSI 3022A (count), TSI EAD
(first moment) and TEOM (mass). Repeatability of the diameters ≈ ±15%.

**MPASS** (Multi-Parameter Aerosol Scattering Sensor, SAME-2 only): two scattering angles approximating the
2nd and 3rd moments; with a single correlation it halves the response variance across materials — the
technology demonstration of a two-moment smoke detector.

## 5. Coagulation (aging)

Brownian collisions merge particles. With a constant kernel (Smoluchowski):

    1/N(t) − 1/N0 = K · t       N(t) = N0 / (1 + K N0 t)

Mass is conserved, so Dm ∝ N^(−1/3). For 0.1–0.3 µm particles the continuum kernel with slip correction
gives K ≈ 4kT·Cc/(3µ) ≈ 5–6×10⁻¹⁰ cm³/s for equal spheres; polydispersity raises it. NASA's coagulation
note (`ISS Coagulation.doc`) lists lampwick 2.83×10⁶ → 1.96×10⁶ /cm³ in 126 s (K ≈ 1.25×10⁻⁹ cm³/s) and
Teflon 2.63×10⁶ → 2.28×10⁶ in 35 s (K ≈ 1.67×10⁻⁹).
Coagulation preferentially removes the smallest (most mobile) particles: AMD grows more than Dm, and σg
narrows toward a self-preserving value (≈1.32 in the continuum limit).

_(this study)_ Paired unaged/aged moments with flow give K ≈ 9.0×10⁻¹⁰ cm³/s (IQR 5.7–10.3×10⁻¹⁰),
M0 falling to 27–50% in 9–13 min, Dm growth ×1.25–1.56 matching (N0/N)^(1/3), and σg narrowing in 11 of 12 runs.

## 6. Spacecraft smoke detectors in SAME

| Detector | Principle | Most sensitive to | SAME-R channels |
|---|---|---|---|
| **ISS smoke detector** | near-IR forward light scattering (+ obscuration) | particles ≳ 1 µm (mass/area-weighted) | `ISSDetectorScatterMeasurement`, `ISSDetectorObscurationMeasurement` (V) |
| **Space Shuttle (STS) detector** | ionization chamber behind an inertial separator that removes > 1–2 µm | number × diameter of sub-micron particles | `STSDetectorMeasurement`, `STSDetectorAlarm` (installed in tests 67–70, 87, 89, 91, 92) |
| Ionization chamber (M1 instrument) | residential ionization sensor | number × diameter | `IonDetectorB` (V, rises with smoke); `IonDetectorA` when the STS unit is absent |

Implication (Urban 2012; confirmed here): Kapton/Teflon smoke (Dm 0.1–0.2 µm) gives weak scattering
signals; a detector with enough gain for them would false-alarm on dust. Measuring two moments lets a
detector correct for size and separate smoke from large dust.

_(this study, proxy thresholds)_ With flow: ISS 71% vs ionization 93% of pushes (Kapton: ISS 27%).
Without flow: ISS 90% vs ionization 10%. Either: 95%. STS alarm: 6 of 9 powered pushes.

## 7. Relation to DAFT / DAFT-2

- **DAFT (Dust and Aerosol measurement Feasibility Test)** was a NASA Glenn/ZIN risk-reduction experiment
  **for SAME**. It flew on the ISS in 2006 (Expedition 13, operated by J. Williams) to prove that the
  commercial **P-Trak** condensation nuclei counter works in long-duration microgravity (isopropanol wick
  wetting) and gave the first measurement of ISS background particulate. The grooved condenser used by SAME
  came out of that work. So the P-Trak was qualified by DAFT **before** SAME, not adopted after it.
- **DAFT-2**: the team brief refers to a follow-on; this knowledge base could not confirm its flight dates
  or data from public sources, so no DAFT-2 numbers are used.
- Relevance for the dashboard: DAFT's ISS background particle levels are the "noise floor" against which
  the SAME smoke numbers (10⁵–10⁶ /cm³) must be detected; a detector threshold must sit above cabin dust
  and below small-particle smoke — the core design tension SAME quantifies.

## 8. Housekeeping data dictionary (SAME-R `HKPData_gmtDDD_n.csv`, 98 columns, 1 Hz)

| Column | Meaning | Use here |
|---|---|---|
| `TimeString`, `Time` | GMT `YYYY/DDD/hh:mm:ss`, Unix seconds | time base |
| `TestNumber`, `RunMode`, `EventCode` | test id (= run), mode, event | test split |
| `HeatingInProgress`, `GasPlumeTemperature(DegC)` | heater on, plume thermocouple | heating phase, temperature |
| `MFCMassFlowRate(LPM)` | aging-chamber fill flow | flow velocity (4.29 L/min ↔ 8.1 cm/s) |
| `PistonVacuumSolenoid[BN16]` / `PistonGN2Solenoid[BN18]` | fill / push valves | fill end, pushes, aging |
| `PTrakMeasurement(PtPerCC)` | P-Trak count (diluted; −999 = invalid) | M0 response |
| `IonDetectorA/B Measurement(Volts)` | ionization chambers | M1 response |
| `DustTrakBMeasurement(MgPerM3)` | DustTrak mass | M3 response |
| `DustTrakAMeasurement(MgPerM3)` | reads ~10⁴/2×10⁴ codes in SAME-R | discarded |
| `ISSDetector{Scatter,Obscuration}Measurement(Volts)` | ISS detector channels | photoelectric response |
| `STSDetectorMeasurement(Volts)`, `STSDetectorAlarm`, `STSDetectorPower` | Shuttle detector | alarm behaviour |
| `ThermalPrecipitatorPre/PostAge*` | TEM sampling | grid timing |

## 9. Reduced NASA/NIST tables in the download

- `Sample descriptions tables.docx`: 70 grid rows — precipitator, run, material, aged?, description
  (temperature/flow regime), Rt/R0, TEM morphology, **M0, M1/M0 (AMD), Dm, Hatch–Choate σg**.
- `TEMflowvsnoflow.xls`: 15 rows — inlet velocity, Rt/R0, net aging, M0, M1, DustTrak (dilution-corrected),
  AMD, Dm, MPASS 3/2, σg, Dg, TEM max/background diameters, shape.
- `thermal precipitator map updated.xlsx`: grid map and viewing notes.
- `54 lampwick binneddatacorr from GWM.xlsx`, `55 Lampwick.xlsx`: per-particle TEM sizes and binned
  distributions (G. W. Mulholland); `SPV of 54-7L_21 all quarters`: quarter statistics of grid 54-7L.

## 10. References

1. Urban DL et al. Particle Morphology and Size Results from the Smoke Aerosol Measurement Experiment-2.
   AIAA 2012-3536, 42nd ICES (2012). NTRS 20130000422.
2. Yang J, Cleary T, Mulholland G, et al. Smoke Characterization and Feasibility of the Moment Method for
   Spacecraft Fire Detection. Aerosol Sci. Technol. 49 (2015). doi:10.1080/02786826.2015.1025124.
3. ZIN Technologies. SAME Verification Plan and Engineering Requirements Document, SAME-PLN-005 Rev F (2007).
4. Cleary T, Weinert D, Mulholland G. Moment method for obtaining particle size measures of test smokes.
   NIST interagency report (2004), cited as ref. 7 in Urban et al. (2012).
5. NASA GRC. DAFT — Dust and Aerosol measurement Feasibility Test (Expedition 13, 2006). NTRS 20070031686.
6. Friedlander SK. Smoke, Dust, and Haze (2000) — coagulation and self-preserving distributions.
