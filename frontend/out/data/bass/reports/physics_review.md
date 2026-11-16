# Physical plausibility review of the BASS-II spread-rate results

Reviewer: domain-scientist agent, 2026-11-13. Scope: the 70 tests in `reports/figures/_ensemble/steady_rates.csv`
and `data/processed/<test>/steady.json`. Nothing was reprocessed; `src/` and `configs/` were not modified.

**Sources (abbreviations used below)**
- **[PHYS §x]** `knowledge/physics/flame_spread_physics.md`. It reproduces NASA/TM-20210011385 (https://ntrs.nasa.gov/citations/20210011385).
- **[PUB §x]** `knowledge/literature/publications.md`. Per-test reference values: SDSU http://flame.sdsu.edu/bass.html, TM Tables 5.1/A.x, Link et al. 2018 Table S1, and BASS-I NTRS 20130012832.
- **[CAL §x]** `knowledge/methods/spatial_calibration.md`.
- **[TS]** Time-series evidence in `reports/figures/<test>/G7_size.csv`, `G18_telemetry.csv` and `G3_edge_fit.csv`, binned by the reviewer.

Statements marked **(inferred)** are the reviewer's interpretation. They have not been confirmed by a source or by visual frame inspection.

**Expected ranges applied** (O2 here is the ensemble's MCA-calibrated value; SDSU uses the raw CSA-CP reading, which is about 0.9–1.6 points lower [PUB §0])
- **Thin PMMA films, opposed (B):**
  - Thermal thin regime: V_f is independent of V_g and V_f ∝ 1/δ. At ~21 % the range is 0.46–2.06 mm/s, with V_f·δ ≈ 0.18–0.24 mm²/s and an upper bound of ≲ 2.5 mm/s [PHYS §2.2, §6.1, §6.3].
  - Radiative extinction at V_g,cr ≈ 1 cm/s (21 %) and 2.6–4 cm/s (16 %) [PHYS §2.4].
  - Kinetic decrease and blowoff above ~16 cm/s (16 %) or ~40 cm/s (21 %) [PHYS §2.5].
- **PMMA slabs (M):** 0.012–0.144 mm/s, bound ≲ 0.2 mm/s. V_f increases with V_g. The flame reaches a stable size after ~3 min [PHYS §6.1, §6.3; PUB §2.2, §2.6].
- **Opposed rods (P):** ~0.02–0.10 mm/s, bound ≲ 0.15 mm/s. Steps are quasi-steady after ≥ 1 min. Flames are blue and open below ~2 cm/s [PUB §1.13, §2.3; PHYS §4].
- **Stagnation/concurrent rods (O):** the tip regresses at ~0.04 mm/s (0.0385 mm/s in the lowest-O2 test). Flame length relaxes with t_s = 59–235 s [PHYS §3, §5.3; PUB §1.1].
- **SIBAL, concurrent (T):**
  - Growth to a limiting length, then decay at the sample end. "Steady" requires constant V_f for > 20 s [PUB §1.8; PHYS §3].
  - BASS-I prior at 21 %: V_F = 0.20U + 0.56 (2 cm) and 0.15U + 0.07 (1 cm), in mm/s with U in cm/s [PUB §2.6]. Bound ≲ 5 mm/s [PHYS §6.3].
  - T9, T10 and T12 did not ignite [PUB §2.5].

---

## 1. Per-test verdicts

**Verdict definitions**
- **P** = plausible: the value lies in the expected range for its regime and the window is physically meaningful.
- **S** = suspicious: the magnitude is possible, but the window, quantity or tracking is compromised.
- **I** = implausible: the value violates a physical bound or the crew notes, or a documented burn was missed.

For tests without a rate, the verdict judges the null result.

**Notation**
- "dim" = the share of frames where the radiometer is on (RAD > 5th percentile + 0.3) but the segmented area is < 5 mm² **(inferred heuristic)**.
- Flows are those in the as-run table. "FAN n" is the overlay fan reading.

### B: thin PMMA films, opposed (22 tests)

| Test | Conditions | V_f [95 % CI] mm/s | Window | Verdict | Reason |
|---|---|---|---|---|---|
| B1 | 100 µm, 2 cm, 22.2 %, 5 cm/s | 1.890 [1.886, 1.896] | 20–35 s | P | Thin 100 µm range 1.8–2.1. V_f·δ = 0.189 mm²/s. SDSU 1.878 |
| B2 | 200 µm, 2 cm, 22.2 %, 6.5 cm/s | 1.073 [1.064, 1.082] | 21–47 s | P | V_f·δ = 0.215. SDSU 1.078 |
| B3 | 100 µm, 2 cm, 22.2 %, 2.5 cm/s | 2.027 [2.003, 2.052] | 27–49 s | P | V_f·δ = 0.203. SDSU 2.056 |
| B4 | 300 µm, 2 cm, 22.2 %, 6.2 cm/s | 0.756 [0.746, 0.766] | 31–80 s | P | V_f·δ = 0.227. SDSU 0.800 |
| B5 | 200 µm, 2 cm, 22.2 %, 5.7 cm/s | 1.186 [1.173, 1.200] | 50–70 s | P | V_f·δ = 0.237 (upper end). SDSU 1.126 |
| B6 | 100 µm, 2 cm, 21.0 %, 3→5 cm/s | 2.039 [2.023, 2.053] | 23–36 s | P | Same as B1/B3. Flow-independent, as expected for the thin thermal regime |
| B7 | 400 µm, 2 cm, 22.2 %, 2.5 cm/s | 0.490 [0.469, 0.518] | 17–111 s | P | V_f·δ = 0.196. SDSU 0.472 |
| B8 | 200 µm, 2 cm, 21.0 %, 10→56 cm/s | 0.274 [0.164, 0.463] | 47–76 s | S | The window bridges a ~15 s gap in which the flame was not segmented during the FAN ramp to 122, and the edge jumps by ~35 mm. The 10 cm/s step (0.936, V_f·δ = 0.187) is plausible. The FAN-68 step (3.98) is **I**: it exceeds the 2.5 mm/s bound |
| B9 | 100 µm, 2 cm, 21.0 %, 2.6→1.8 cm/s | 1.934 [1.919, 1.950] | 11–30 s | P | Thin 100 µm range. V_g is above V_g,cr |
| B10 | 200 µm, 1 cm, 21.0 %, 7→1.7 cm/s | 0.552 [0.524, 0.580] | 8–54 s | S | The window starts during the ignition acceleration: the edge rate rises 0.14 → 0.6 → 0.97 mm/s per 10 s [TS]. The later regime gives 0.84. No published value |
| B11 | 200 µm, 2 cm, 21.0 %, 9→1.8 cm/s | 0.853 [0.843, 0.862] | 59–96 s | P | Measured at ~2 cm/s after a FAN drop. V_f·δ = 0.171, slightly below 0.18. The earlier regime at ~4–5 cm/s is 0.895. Extinction follows when AIR → 0–1 cm/s, consistent with V_g,cr ≈ 1 cm/s |
| B12 | 300 µm, 2 cm, 22.2 %, 2.5 cm/s | 0.663 [0.637, 0.696] | 34–79 s | P | V_f·δ = 0.199. SDSU 0.607 (+9 %). The flame is faint and mostly blue [PUB §2.1] |
| B13 | 400 µm, 2 cm, 21.0 %, 9.7→1.2 cm/s | 0.471 [0.468, 0.475] | 23–134 s | P | Equal to B7. V_f·δ = 0.188 |
| B14 | 200 µm, 1 cm, 15 % (raw 14.1) | none | — | P | Crew reports no sustained ignition. The only regime, in the first 8.6 s (0.11 mm/s), is the brief ignition |
| B15 | 100 µm, 2 cm, 21.0 %, 10→55 cm/s | 1.046 [1.019, 1.080] | 49–62 s | P | **Kinetic-regime value at FAN 122 (AIR ≈ 40–44 cm/s), not thermal.** Per-FAN steps are 1.94 / 2.14 / 1.98 / 1.12. The final ~20 mm before the sample end is a possible confound (inferred). Plotted at 10 cm/s in G5 by mistake |
| B16 | 100 µm, 2 cm, 17.3 %, 3→0 cm/s | none | — | I | Missed: the crew reports a "prolonged burn". RAD stays at 1.9–3.5 for ~60 s while the segmented area is ~2.5 mm², a dim, single-sided blue flame. After 120 s a 3500 mm² region with RAD at baseline is lighting or exposure, not flame |
| B17 | 200 µm, 1 cm, 17.5 %, 4.8→1 cm/s | 0.306 [0.261, 0.339] | 1–180 s | P | Low confidence: 68 % dim, sparse edges, and the window includes ignition. Edge points between 60 and 180 s give 0.34. A ~50 % reduction from 1 cm at ~21 % is consistent with lower O2 and V_g close to V_g,cr (~4 cm/s at 16 %) |
| B18 | 200 µm, 1 cm, 17.4 %, 7.5→50 cm/s | 0.437 [0.403, 0.469] | 94–141 s | P | 50 % dim, but the edge track is consistent (0.39 from binned edges). The FAN-71 step (0.94, 8 s) is a transient flare just before blowoff at ~155–160 s → S |
| B19 | 100 µm, 2 cm, 17.3 %, 7.3→30 cm/s | 1.039 [1.033, 1.047] | 11–82 s | P | About 0.53× the 21 % value. Drops to 0.89 at FAN 70 before blowoff, a kinetic effect expected above ~16 cm/s at 16 % |
| B20 | 100 µm, 2 cm, 17.4 %, 4.5→2 cm/s | 1.012 [0.990, 1.034] | 29–52 s | P | Agrees with B19 within 3 %. The crew reports the whole sample burned |
| B21 | 200 µm, 1 cm, 20.8 %, 6.2→1.8 cm/s | 0.623 [0.564, 0.693] | 35–62 s | P | 71 % dim, but the edge is tracked. About 0.55× the 2-cm value: a width effect of plausible sign (TM §5 reports narrower M slabs as slower [PUB §1.9]), but its size is unverified |
| B22 | 200 µm, 1 cm, 20.7 %, 6.5→1.9 cm/s | none | — | I | Missed: the crew reports spread until extinction at pot 0.36. The flame is visible only for 0–30 s, then dim (RAD ≈ 1). The auto-chosen direction ("left") is opposite to the other B tests. Lights artefact after 90 s |

### F: Nomex and candle (3 tests)

| Test | Conditions | V_f | Verdict | Reason |
|---|---|---|---|---|
| F1 | Nomex, 22.2 %, 9.6 cm/s | none | P | No sustained ignition [PUB §2.7] |
| F3 | Nomex, 21.7 %, 8 cm/s | none | P | No sustained ignition |
| F4 | Wax candle, 17.4 %, 3 cm/s | none | P | A candle has a stationary flame, so no spread is expected. The non-significant +2.2 mm/s regimes at 177–249 s are probably the wax droplet ejected upstream [PUB §2.7] (inferred) |

### M: PMMA slabs, opposed (5 tests)

| Test | Conditions | V_f [95 % CI] mm/s | Window | Verdict | Reason |
|---|---|---|---|---|---|
| M1 | 1 mm, 2.2 cm, 1-sided, 22.2 %, 9 cm/s | 0.0745 [0.0731, 0.0760] | 133–321 s | P | In the slab range. Flame area stays on a plateau (19–27 mm²) and the edge is detected in 100 % of frames. The 0–90 s flare (1236 mm²) is ignition. TM 0.071 |
| M3 | 5 mm, 2.2 cm, 1-sided, 20.8 % | none | S | Inconclusive: a 111 s rack-camera clip of a 20.1 min burn, with maximum area 24 mm² (ROADMAP) |
| M7 | 1 mm, 1.2 cm, 2-sided, 18.9 %, 10→3 cm/s | 0.615 [0.003, 1.479] | 7–120 s | I | 3× the 0.2 mm/s slab bound, with a CI spanning 3 decades. The fit mixes the igniter blob (−63 mm) with a static feature at +39 mm. Regime 2 (128–230 s, 0.112 [0.087, 0.132]) is physically plausible |
| M9 | 3 mm, 1.2 cm, 2-sided, 18.0 %, 14 cm/s | 0.210 [0.022, 0.346] | 264–685 s | I | Above the bound and above the thin-film ceiling for 3 mm (0.076 mm/s, §3). The segmented area is 0 from 120 s onward while RAD rises 0.15 → 1.55. Edges jump between 2–7 mm (dim flame) and 51–100 mm (static artefacts) |
| M16 | 1 mm, 2.2 cm, 2-sided, 19.2 %, 5→3→2 cm/s | 0.160 [0.151, 0.169] | 97–279 s | S | In range, but the window is the growth phase: area 104 → 330 mm². The plateau regime at FAN 48 (286–432 s) gives 0.141. At ~2 cm/s the flame is not segmented. A flare at 800 s (area 950 mm², FAN 75) is not steady spread |

### O: PMMA rods, stagnation/concurrent (7 tests)

| Test | Conditions | V_f [95 % CI] mm/s | Window | Verdict | Reason |
|---|---|---|---|---|---|
| O1 | 6.35 mm, 22.2 %, 20→1 cm/s | 0.147 [0.098, 0.207] | 129–183 s | S | Measures flame-tip motion, not spread or regression. L_f grows 14.6 → 42.9 mm (≈ 0.21 mm/s) while the edge moves ≈ 0.27 mm/s. This is flame-length relaxation (t_s ≈ 59 s for r = 0.318 cm). The expected regression is ~0.04 mm/s |
| O2 | 6.35 mm, 22.2 %, ~2 cm/s | 0.089 [0.078, 0.098] | 108–203 s | S | Same issue: L_f grows 4 → 16 mm over 60–180 s (dL/dt ≈ 0.08 ≈ rate) |
| O3 | 6.35 mm, 18.0 % (TM), concurrent | 0.231 [0.175, 0.274] | 73–102 s | S | 30 s window. Metadata not merged (suffixed run O3a/b). Probably flame growth (inferred) |
| O5 | 12.7 mm, 15.1→14.2 % (TM), concurrent | 0.068 [0.019, 0.109] | 133–179 s | S | Later regimes accelerate to 0.19–0.26, consistent with leading-edge blowoff (inferred). Metadata not merged |
| O8 | 6.35 mm, ~15.5 % (TM), stagnation | 0.143 [0.129, 0.158] | 105–410 s | I | 69 % dim. The fit bridges a static edge (−0.3 mm) and a later artefact (+52 mm). Only 15 bins |
| O13 | 12.7 mm, 15.9→14.6 % (TM), concurrent | 0.144 [0.110, 0.176] | 180–211 s | S | The edge is stationary (−6 mm) for 180 s, as expected for a stagnation flame. The fitted regime is the 30 s just before extinction (area 1025 → 9 mm² at ~220 s) |
| O16 | 9.525 mm, 14.5 % | none | P | Crew reports no sustained flame [PUB §2.4] |

### P: PMMA rods, opposed (5 tests)

| Test | Conditions | V_f [95 % CI] mm/s | Window | Verdict | Reason |
|---|---|---|---|---|---|
| P1 | 6.35 mm, 17.7 %, 5→2 cm/s | 1.616 [1.009, 1.997] | 1–68 s | I | 11× the 0.15 mm/s rod bound. The window is the igniter flash (0–30 s: area 482 mm², intensity 4600). The real flame starts at ~90 s (RAD 1.3 → 4). Late regimes give 0.053–0.061 (Link P1: 0.059 at 2.15 cm/s), identified post hoc |
| P2 | 6.35 mm, 17.4 %, 5→2 cm/s | 0.0669 [0.0640, 0.0694] | 252–366 s | P | Link P2 0.073–0.079 (−8 to −15 %). The edge jumps +17 mm at ~240 s, possibly because the flame opens at low flow (inferred) |
| P13 | 12.7 mm, ~20.6 % (Link) | none | I | Missed: Link reports 0.046–0.071. Area ~10 mm² while RAD ≈ 1.2 (dim blue flame at ≤ 2 cm/s), and the edge locks onto a static feature at 81.8 mm |
| P21 | rod (metadata not merged) | 0.079 [0.020, 0.132] | 227–311 s | S | The edge toggles between ~2 and ~17 mm. RAD and area oscillate together with a ~80–100 s period, which is not the 1.1 Hz pre-extinction oscillation; the cause is unexplained (needs frame check) |
| P22 | 9.525 mm, 20.8 % (Link) | 0.099 [0.080, 0.121] | 26–51 s | S | A 25 s window in the first minute, below Link's ≥ 1 min quasi-steady requirement, and near the upper end of the rod range. After FAN 41 the flame is dim and the edge locks at 76 mm |

### T: SIBAL fabric (concurrent) and PMMA spheres (28 tests)

| Test | Conditions | V_f [95 % CI] mm/s | Verdict | Reason |
|---|---|---|---|---|
| T1 | 2.2 cm, 18.5 %, 10 cm/s | none | S | Inconclusive: 46 % dim, regimes not significant. A burn is expected at ~2 mm/s (BASS-I prior, reduced for O2) |
| T2 | 2.2 cm, 18.5 %, 10→5 cm/s | none | S | Inconclusive: 55 % dim |
| T3 | 4 cm sphere, 17.2 % | none | P | Not sustained [PUB §2.5] |
| T4 | 2.2 cm, 18.7 %, 10→2.2 cm/s | 0.738 [0.544, 1.681] | I | The flame is never segmented (area 0, RAD 0.15–0.19). The edge jumps between 0.6 and 124 mm. The crew documents growth and quenching, which the pipeline cannot see |
| T5 | 2.2 cm, 18.8 %, 10→2.4 cm/s | none | I | Missed: a "flamelet" burned the entire sample |
| T6 | 2.2 cm, 18.8 %, 4.5→2.6 cm/s | none | I | Missed: the flame did not extinguish. Only 8 bins were usable |
| T7 | 4 cm sphere, 17.3 % | none | P | Flame grows around a sphere, so linear spread is not expected. Extinction at pot 0.28 |
| T9 | 2.2 cm, 16.4 %, 10 cm/s | 0.666 [0.096, 1.082] | I | The crew reports **no ignition**. A non-spreading glow (edge fixed at ~21 mm, 30–70 s) appears, and the rate comes from the jump at its onset |
| T10 | 2.2 cm, 16.4 %, 5 cm/s | 1.734 [0.884, 2.580] | I | The crew reports **no ignition**. The 3 s window coincides with a RAD spike at zero area (igniter) |
| T11 | 2.2 cm, 17.1 %, 4 cm/s | none | I | Missed: the sample "burned completely, steady". 76 % dim, with RAD rising to 3.3 at zero area |
| T12 | 2.2 cm, 16.8 %, 5 cm/s | none | P | No ignition |
| T13 | 2.2 cm, 17.5 %, 4→2.2 cm/s | none | S | Quenched. RAD not read by OCR. A persistent ~470 mm² area with no spread was not inspected |
| T14 | 2.2 cm, 16.9 %, 4→2.8 cm/s | none | S | Quenched below 3 cm/s. 70 % dim |
| T15 | 2.2 cm, 18.7 %, 10→29 cm/s | 3.636 [3.556, 3.740] | P | Below the 5 mm/s bound and plausible against the BASS-I trend at ~29 cm/s. The window (11–18 s) is in the **growth** phase, where tip speed = V_f + dL_f/dt (≈ +0.9 mm/s). L_f stays at its limit for only ~6 s, short of the > 20 s steady criterion |
| T16 | 2.2 cm, 17.6 %, 4→3 cm/s | none | I | Missed: the flame spread over the entire sample. RAD not read |
| T17 | 2.2 cm, 16.9 %, 6→53 cm/s | 2.776 [1.237, 4.484] | S | Wide CI, median area 1.2 mm² (mostly dim). The FAN-122 step gives 1.19 [0.01, 3.75] |
| T18 | 2.2 cm, 17.4 %, 5→2.6 cm/s | 0.264 [0.185, 0.382] | S | 43 % dim. The window spans the flow reduction toward quenching. The FAN-47 step gives 0.48 |
| T19 | 1.2 cm, 17.2 %, 11 cm/s | none | I | Missed: the crew reports a steady burn. 72 % dim. A non-significant regime of 1.52 is near the expected value (1 cm BASS-I prior at 11 cm/s: 1.72 at 21 %) |
| T20 | 1.2 cm, 17.2 %, 11→3 cm/s | none | S | 33 s video. Quenched |
| T21 | 1.2 cm, 17.2 %, 11→47 cm/s | none | S | 3 s video. Nothing can be measured |
| T22 | 1.2 cm, 17.1 %, 10.5→5 cm/s | none | S | 46 s video, 53 % dim. Quenched |
| T23 | reused, 17.2 % | none | P | Partial or failed ignition on a reused sample. Maximum area 59 mm² |
| T24 | 1.2 cm, 18.2 %, 10 cm/s, reused | 0.922 [0.313, 1.078] | S | Magnitude possible (below the 1 cm BASS-I prior of 1.57 at 21 %). Measured L_f of 35–58 mm is inconsistent with ~16 mm expected for 1 cm SIBAL at 10 cm/s. Probably smouldering or char glow is included (inferred) |
| T25 | 2.2 cm, 20.8 %, 5→2.5 cm/s, reused | 0.745 [0.716, 0.829] | S | 58 % dim, sparse edges. Value 30–50 % below the BASS-I prior (1.06–1.56) |
| T26 | 2.2 cm, 20.8 %, reused | none | S | 56 % dim. Inconclusive |
| T27 | 1.2 cm, 20.7 %, 5→2 cm/s, reused | 0.238 [0.075, 0.277] | S | The window (91 s) spans the flow step. Agrees with T29 within the CI. BASS-I prior is 0.37–0.82 |
| T28 | reused (metadata not merged) | 0.734 [0.513, 1.056] | S | 5.4 s window, well short of the > 20 s steady criterion |
| T29 | 1.2 cm, 20.7 %, 5→2 cm/s, reused | 0.312 [0.027, 0.370] | S | Only 12 bins over 82 s. The FAN-122 step (4.80) is near the bound and comes from noisy edges |

**Counts: P = 29, S = 26, I = 15 (70 tests).**

| Series | P | S | I |
|---|---|---|---|
| B | 18 | 2 | 2 |
| F | 3 | 0 | 0 |
| M | 1 | 2 | 2 |
| O | 1 | 5 | 1 |
| P | 1 | 2 | 2 |
| T | 5 | 15 | 8 |

---

## 2. Trend checks

### 2.1 V_f against film thickness (B, opposed, thin)
- **Validated set.** For the 7 SDSU-validated films, slope = −0.97 ± 0.07 and R² = 0.98 (`validation_summary.json`).
- **Extended set (reviewer).** Adding the GMT 188 films (B6, B9, B11, B13) and the thermal per-FAN steps of B15 (1.945) and B8 (0.936) gives **slope −0.99 ± 0.05, R² 0.975, n = 13**.
- **Theory.** The de Ris thin limit predicts −1 [PHYS §2.2].
- **Products.** V_f·δ falls between 0.171 (B11) and 0.237 (B5), against the expected 0.18–0.24 mm²/s [PHYS §6.3.5].
- **Absolute level.** The 100 µm mean is 1.967 mm/s (CV 3.2 %, n = 5). This is 0.86× the thermal prediction with F_adb (2.29, 1.14, 0.76 and 0.57 mm/s for 100, 200, 300 and 400 µm). The ratio holds at all four thicknesses, which is consistent with a constant effective F ≈ 4.2 (inferred).
- **Conclusion.** This is the most robust physical result of the study.

### 2.2 V_f against O2 at fixed material
- **100 µm, 2 cm.** About 21–22 % calibrated O2 gives 1.89–2.04 mm/s (B1, B3, B6, B9, B15 at 10 cm/s). About 17.3–17.4 % gives 1.01–1.04 (B19, B20): **−48 % for −4.5 O2 points.**
  - A pure thermal-regime F reduction would give only about −20 % (inferred, from T_f falling ~300 K).
  - The rest is consistent with being near the radiative and kinetic limits at 16 % [PHYS §2.4–2.5].
  - B19 (16.35 % raw) and B20 (17.4 % raw) do not differ (they also differ in flow), so no monotonic trend can be resolved within 16–17.5 %.
- **200 µm, 1 cm.** About 20.8–21 % gives 0.55–0.62 (B10 selected, B21), or 0.84 using the B10 late regime. About 17.4–17.5 % gives 0.31–0.44 (B17, B18): **−30 to −50 %**.
- **Thin films at 20–22 %.** GMT 050 (22.2 % calibrated) and GMT 188 (21.0 %) 100 µm films agree within 5 %, and so do 400 µm films (B7/B13). V_f is insensitive to O2 in this range, as expected.
  - The 200 µm, 2 cm films on GMT 188 (B8 thermal step, B11) are 12–25 % below GMT 050 (B2, B5).
  - That gap is larger than the O2 difference explains (inferred). B11 was also measured at ~2 cm/s.
- **Artefactual correlations in `validation_summary.json → o2_trend`.**
  - The "1 mm slab ρ = −1.0" is driven by M7's implausible 0.615. The 1 mm slabs also differ in sides, width and flow, so no O2 conclusion is possible.
  - The "SIBAL ρ = −0.28" is driven by T9 and T10, which are no-ignition tests at 16.4 % that were given non-zero rates.
  - Both statistics should be removed or recomputed on the trusted set.

### 2.3 V_f against flow
- **Thin thermal plateau.** 100 µm films give 1.93–2.04 mm/s at 2, 2.5, 3–5, 5 and 10 cm/s (B9, B3, B6, B1, B15 step). That is **flat within ±3 %**, as theory predicts [PHYS §2.2].
  - For 300 µm, B12 at 2.5 cm/s is 12 % below B4 at 6.2 cm/s (SDSU: −24 %). This is the radiative branch starting to show [PHYS §2.6] (inferred).
- **Kinetic branch.**
  - B15 (100 µm, ~21 %): 1.94 → 2.14 → 1.98 → 1.12 mm/s as FAN rises 50 → 67 → 93 → 122 (AIR ≈ 40–44 cm/s). That is −45 % near the 40 cm/s blowoff onset [PHYS §2.5]. The crew reported no blowoff; the flame reached the sample end.
  - B19 (16.4 %): 1.03 → 0.89 before blowoff.
- **Radiative branch.**
  - B11 holds 0.89 → 0.85 between 4–5 and ~2 cm/s, then extinguishes when the flow is brought to ~0–1 cm/s, matching V_g,cr ≈ 1 cm/s.
  - B18 (16.4 %) rises 0.44 → 0.94 in the 8 s before blowoff. The sign is consistent with leaving the radiative branch (V_g,cr ≈ 4 cm/s at 16 %), but the duration is too short to call it steady.
- **Slabs (thick-fuel regime, V_f grows with V_g).** M16 gives 0.160 (5 cm/s, growth phase) → 0.141 (3 cm/s) → 0.13 (toward 2 cm/s), so V_f falls with V_g as in TM §5 [PUB §1.9].
- **Telemetry timing (FAN leads, AIR lags).**
  - B15: V_f halves within ~4 s of FAN reaching ≥ 109 (t ≈ 48–52 s), while AIR reads only 18–23 cm/s at that moment and 41–44 cm/s at 68–76 s, a lag of ~15–25 s.
  - T15: the FAN step at 7–9 s coincides with the edge acceleration at 7.5 s, while AIR climbs 15 → 29 cm/s over 9–39 s.
  - B18: the FAN step at 140 s → area flare → blowoff at ~155–160 s (RAD 2.05 → 0.75) → AIR reaches 26 at 160 s.
  - This confirms the "flame response very rapid" note [PHYS §6.1] and the anemometer lag [PHYS §4.1].
- **The `air_lagged_cm_s` field in `steps` is unreliable.** Examples: B15 and B8 at FAN 50 are labelled 41.3 cm/s (as-run 10). B11 is labelled 0.0 (AIR read ~2). B10 is labelled 1.0 (AIR read 5). When the FAN changes less than a minute after a plateau, looking up AIR at t + 60 s reads the next plateau. Use the FAN → velocity calibration instead [PHYS §4.1].
- **Figure G5 plots `flow_initial_cm_s`.** B15 and B8 (measured at ≥ 40 cm/s) and M16 (measured during the 5 cm/s growth phase) are therefore placed at the wrong flow.

### 2.4 RAD and luminous area
- **Bright tests co-vary as expected.** Spearman ρ(RAD, area) is 0.60–0.87 for the bright GMT 050 films (B1 0.87, B2 0.82, B7 0.78, B4 0.75, B5 0.63, B3 0.60) and 0.74 for M16.
- **Dim tests decouple.** ρ is ≤ 0.1 or negative where the flame is blue or dim, with dim fractions of 0.68–0.78 in M7, M9, B17, B21, T11, T14, T19 and O8. This decoupling is the clearest signature of dim, low-soot flames [PHYS §2.4, §4] that the side camera cannot segment.
- **Caveat (inferred).** The thermopile also sees the hot sample, so part of the "dim" time after extinction is the sample cooling down.
- **Post-test lighting or exposure artefact.** Area is ≈ 3400–3500 mm² with RAD at baseline and FAN raised in B16 (t ≥ 120 s), B22 (≥ 90 s), B17 (≥ 240 s) and B10 (≥ 160 s). These spans are not flame and must be masked.

### 2.5 Concurrent SIBAL (T)
- **T15 shows the expected sequence** [PHYS §3]: L_f grows 3 → 22 mm in ~18 s, stays at its limiting length for ~6 s, then shrinks 22 → 4 mm as the tip reaches the sample end (92.7 mm) at ~36 s.
  - The total of ~40 s matches the 10 cm/s reference [PUB §1.8].
  - At ~29 cm/s the plateau is shorter than 20 s, as anticipated for a 10 cm sample at high flow (TM §7.1.2).
  - Overall tip advance is 2.8 mm/s. The reported 3.64 mm/s is the growth-phase tip speed and overestimates V_f by about dL_f/dt (inferred).
- **Most other T tests are too dim in the side video.** They are at 16.4–18.8 % O2, and T'ien used the top camera for dim flames [PUB §1.8].
  - 8 documented burns were missed or misread: T4, T5, T6, T11, T16, T19, plus T9/T10, which were given rates despite no ignition.
  - The two repeat tests at the same conditions (T27, T29) agree with each other (0.24 and 0.31) but lie below the BASS-I 1 cm prior.
- **Conclusion.** No quantitative SIBAL trend (U, O2, width) can be supported with the current measurements.

### 2.6 Rods
- **O tests: the pipeline does not measure regression.**
  - The tracked "leading edge" is the flame tip. Its motion equals the flame-length relaxation after flow steps: O1 dL_f/dt ≈ 0.21 mm/s against an edge rate of 0.27; O2 0.08 against 0.089.
  - The time constants are consistent with t_s ≈ 59 s for r = 0.318 cm [PHYS §5.3].
  - The reference regression rate (~0.04 mm/s) [PUB §1.1] would correspond to ~19 px per 100 s at 0.209 mm/px [CAL §3]. It is measurable in principle by tracking the rod tip, but that is not implemented.
  - O16 (no flame) is correctly null.
- **P tests (opposed spread).**
  - P2 agrees with Link within 15 %.
  - P1's selected value is the igniter flash.
  - P13 and P22 are lost below ~2 cm/s, where opposed rod flames turn blue and open [PHYS §4]. These are quenching-branch flames that the side camera barely sees.

---

## 3. M slabs: why the automatic selection fails, and a physics-based proposal

**How the selection works now** (`src/bass2/pipeline.py: steady_regime`). It picks the **longest** piecewise-linear regime whose slope CI is > 0 and whose advance is ≥ 2 mm. The rule contains no physics, so in thick-fuel tests the longest "significant" regime is usually not the steady one.

### 3.1 Why the selection is misled

1. **Igniter flash and ignition growth.**
   - The heated Kanthal wire and the first flame produce the brightest and largest blob of the test: M1 1236 mm², M9 868 mm², M7 138 mm² with RAD barely above baseline, P1 482 mm².
   - The leading edge first sits on the wire, then jumps to the true flame edge. A regime that contains the jump has a huge, "significant" slope: M7 0.615, P1 1.62, T10 1.73.
   - After ignition, a thick fuel's flame needs its solid thermal layer to develop before it reaches a stable size: "slow initial growth, stable size at ~3 min" [PHYS §6.1; PUB §2.6].
     - The solid diffusion time τ²/α_s is ≈ 8 s for 1 mm and ≈ 75 s for 3 mm (α_s = 1.2×10⁻³ cm²/s [PHYS §5.3]; inferred).
     - In O2-limited, low-flow μg conditions the full flame takes minutes to stabilise.
   - While the flame grows upstream, dx_LE/dt = V_f + dL_up/dt > V_f. M16's selected window shows this: area 104 → 330 mm², rate 0.160, against 0.141 on the subsequent area plateau.
2. **Dim late phases.**
   - O2 falls during each slab burn: 0.5–2 points [PUB §2.2], because the MSG is a closed volume [PUB §0]. The crew also steps the flow down.
   - Both effects push the flame toward the radiative, low-soot regime, where it turns blue and luminosity drops [PHYS §2.4, §4].
   - RAD shows the flame (or the hot slab) is still there (M7 RAD 2.5–3.2, M9 0.6–1.5), but the segmented area falls to the noise floor: 78 % and 73 % of the record.
   - The edge detector then locks onto **static features** (M7 at 39 mm, M9 at 100 mm, M16 at 30 mm). A regime that bridges dim flame edges and a static feature yields a long, "significant", meaningless slope: M9 0.21 mm/s over 421 s, which is longer, and therefore preferred, than the physically sensible 0.027/0.019 phase.
3. **"Longest" favours the wrong phase.**
   - In thin films, steady spread dominates the record. In slabs, the steady phase is a short part of a 15–30 min record that also contains ignition, growth, flow steps and dim tails.
   - The bright, densely sampled growth phase also produces the tightest CIs.
   - M7 shows how fragile the rule is: the igniter-contaminated regime (113 s) beat the plausible one (102 s) by 11 s.

### 3.2 Proposed physics-based selection rule for thick fuels

**Status:** a proposal, not validated. It does not use any published per-test rate. It uses only material properties, the de Ris theory and the telemetry. It must be validated on **independent data**, for example the M tests with TM Table 5.1 values that formed the hold-out (M2, M4, M5, M8, M10, M11, M13–M15, M17–M20; processed after this review with frozen settings, see reports/REPORT.md §4), with no tuning on M1, M7, M9 or M16.

A candidate window [t0, t1] is accepted only if **all** of the following hold:

1. **Post-ignition.** t0 ≥ t_ig + max(60 s, 3·τ_s²/α_s), where τ_s is the burning half-thickness (two-sided) or full thickness (one-sided) and α_s = 1.2×10⁻³ cm²/s [PHYS §5.3].
   - t_ig is the end of the igniter phase: the time after the first area/intensity peak when the intensity-to-RAD ratio falls back below its median. A hot wire is bright in the camera but weak on the thermopile (inferred).
2. **Constant flame size.** Opposed steady spread means a flame of fixed size [PHYS §1].
   - Require |d ln A/dt| and |d ln L_f/dt| < 0.1 min⁻¹ over the window, from a Theil-Sen fit on the area and length series in G7.
   - This rejects growth (M16 97–279 s) and decay windows.
3. **Visibility and consistency.**
   - The leading edge is detected in ≥ 80 % of frames.
   - The fraction of frames with RAD on but area at the noise floor is < 20 %.
   - No single edge jump exceeds 5× the expected advance between frames.
   - No edge is stationary to within 1 px for longer than 60 s while RAD > baseline (a static artefact).
   - Dim windows are reported as "not measurable", **not** as zero or as a rate.
4. **Single flow plateau.** The window lies within one FAN plateau (FAN, not AIR, because the anemometer lags [PHYS §4.1]). It starts ≥ 60 s after the FAN step, or after the criterion-2 plateau has been re-established, whichever is later.
5. **Physical ceiling (theory only).**
   - Compute V_ceiling = min(V_thin, V_thick), with V_thin = 2.34×10⁻⁸ F_adb/τ_s and V_thick = 9.72×10⁻⁵ V_g F_adb² (F_adb = 4.89 at 21 %) [PHYS §2.2].
   - Use the thin value alone when 2τ < 2τ_cr(V_g) ≈ 5.19 mm × (1.9 cm/s / V_g) [PHYS §2.3].
   - Reject any window with V_f > V_ceiling, and also any V_f > 0.2 mm/s [PHYS §6.3].
   - Example ceilings: M7 (1 mm, two-sided, 10 cm/s) ≈ 0.23 mm/s, which rejects 0.615. M9 (3 mm, two-sided, 14 cm/s, thick) gives V_thin = 0.076 mm/s, which rejects 0.21.
   - The ceiling is conservative at lower O2 because F decreases.
6. **Ranking.** Among accepted windows, report one rate **per FAN plateau**, taken from the longest accepted window in that plateau. Then check thick-fuel physics across plateaus: V_f should not increase when V_g decreases [PHYS §2.2; PUB §1.9]. A violation flags the test instead of being fixed silently.

**Illustration only (inferred, not validation).** On the regimes already computed, the rule would:
- keep M1 (133–321 s);
- choose the area plateau for M16 (286–432 s, 0.141);
- find no acceptable window for M9 ("not measurable from side video"), because the area is 0 throughout the post-ignition phase;
- for M7, keep only regime 2 (128–230 s, 0.112), flagged as quasi-steady because the area is still growing 40 → 63 mm².

The same criteria would also fix the selections for P1 (igniter), T9/T10 (no ignition: criteria 1 and 3), B8 (gap bridging) and O8.

---

## 4. Trusted set and exclusions

### Trusted for quantitative scientific conclusions (17 rates)
B1, B2, B3, B4, B5, B6, B7, B9, B11, B12, B13, B19, B20, B15 (**per-FAN-step values only**, not the summary rate), M1, P2, and T15 (flame-growth/limiting-length sequence and order of magnitude only, not as a steady V_f).

These have the following properties:
- bright, continuously tracked flames (RAD–area ρ ≥ 0.3 where RAD is available);
- windows inside one flow plateau and after ignition;
- values inside the knowledge-base ranges;
- where published values exist, agreement within 15 %.

**Trusted null results** (consistent with the crew notes): B14, F1, F3, F4, O16, T3, T12.

### Usable with a flag (trend or illustration only, low confidence)
- B17, B18, B21: dim, but the edge track is consistent.
- B10: use the late regime (0.84), not the summary value.
- B8: 10 cm/s step (0.936) only.
- M16: plateau regime 0.141 rather than the selected 0.160.
- M7 regime 2 (0.112) and P1 late regimes (0.053–0.061): these were identified **post hoc**, after the published values were known, so they are not independent validation.

### Exclude from figures, or show with a distinct "artefact/missed" marker
- **Implausible rates:** M7 (0.615), M9 (0.210), P1 (1.616), O8, T4, T9, T10, and the B8 FAN-68 step (3.98).
- **Missed documented burns:** B16, B22, P13, T5, T6, T11, T16, T19.
- **Wrong quantity:** O1, O2, O3, O5, O13. These measure flame-tip or flame-length dynamics, not spread or regression. Relabel them, or exclude them from the V_f figures.
- **Insufficient footage or windows:** M3, T20, T21, T22, and T28 (5 s window).
- **Reused or dim SIBAL with wide CIs:** T1, T2, T13, T14, T17, T18, T24, T25, T26, T27, T29.

### Cross-cutting fixes for figures (recommendations, not applied)
1. **G5:** plot each rate at the flow of its own FAN plateau (from the FAN calibration), not at `flow_initial_cm_s`. Mark B15 and B8 as kinetic-regime points.
2. **Ensemble merge:** suffixed runs (O3, O5, O8, O13, P13, P21, P22, T28) have no material, O2 or flow, so they cannot appear in condition plots.
3. **O2 convention:** state on every O2 axis that it is MCA-calibrated (22.2 % for GMT 050), whereas SDSU uses raw CSA-CP (20.6 %) [PUB §0].
4. **`o2_trend` in `validation_summary.json`:** recompute on the trusted set only (§2.2).
5. **Disclosure:** the B-film accuracy is partly in-sample, because the regime penalty and length floor were chosen on the reference tests [CAL §6]. The extended n = 13 thickness law above includes six films (B6, B8, B9, B11, B13, B15) that have no published values and were not used for tuning.


## Addendum (2026-11-13, after the final measurement changes)
After this review, a Hampel outlier filter on the leading edge and an autocorrelation-aware CI were added
(src/bass2/spread.py). Re-measured values: M7 step 2 = 0.112 mm/s (was 0.615) and M9 = 0.027 mm/s (was 0.210), both
inside the thick-slab range; their "implausible" verdicts are obsolete and they are now *flagged* in configs/qc.yaml
(diagnosed post hoc, not independent evidence). Note also that the slab "expected range" in §1 (0.012–0.144 mm/s) is the
span of NASA TM Table 5.1, i.e. it comes from the validation reference itself; slab plausibility verdicts are therefore
not independent of the validation.
