# BASS-II (PSI-25): publications, measurement methods and per-test reference values

> Primary and most complete source: **Olson, Ferkul, Bhattacharjee, Miller, Fernandez-Pello, Link, T'ien, Wichman, "Burning and Suppression of Solids–II (BASS-II) Summary Report", NASA/TM-20210011385, Oct. 2021.** NTRS: https://ntrs.nasa.gov/citations/20210011385 · PDF: https://ntrs.nasa.gov/api/citations/20210011385/downloads/TM-20210011385.pdf
> Hereafter **[TM]**. It collects the reports of the 5 PIs, the as-run test matrices (Appendix A, Tables A.1–A.6) and the publication list (Appendix E). When I cite "[TM §x]" it refers to a section of that PDF.
>
> Convention: **"NR"** = not reported numerically in what I could read (usually only in a figure). **"(inferred)"** = deduced by me and must be verified. I did not invent any number: all come from the cited sources.

---

## 0. Hardware and imaging: what the CV pipeline needs

| Item | Value | Source |
|---|---|---|
| Flow duct | 7.6 × 7.6 × 17 cm, black anodized aluminum, rounded corners; 17 cm test section | [TM §1.2] |
| Flow velocity | 0 to ~55 cm/s without restrictors; max. ~35 cm/s with 2 restrictors. TSI 8475 anemometer with ~1 min response and integer display (±0.5 cm/s). Fan calibrated on each operations day | [TM §1.2, §6.1.3] |
| **Video camera** | Panasonic WV-CP654, **760×480 px**, color, side/edge view through a mirror and front window; **30 fps** ("29.97 fps" per T'ien). **Overlay**: N2 flow (cm³/min), fan voltage (×10 V), anemometer (cm/s) and radiometer signal | [TM §1.2, §6.1.3, §7.1.3] |
| **Still camera** | Nikon D300s 12.3 MP, 60 mm lens, top view (normal to the sample); 4320×2968 px images according to [TM]. The SDSU site says the NEF files are **2848×4288 px** and the scale is **32.95 px/mm** (3295 px per 100 mm). Rate **~1 frame/s** (≈1.125–1.25 s between photos, 1/8–1/4 s exposure for fabric); some thick-slab tests every ~5–8 s | [TM §1.2, §2.2.3, §7.1.3]; http://flame.sdsu.edu/bass.html; Ferkul 2012 (NTRS 20130012832) |
| Scale in SDSU reprocessed video | Top view downscaled to 1360×2048 (factor 0.4776) → **15.7373 px/mm** | http://flame.sdsu.edu/bass.html |
| Scale reported by Link et al. | "34 pixels/mm in sample" (Nikon) | Link et al. 2018, Sci. Rep. 8:120, https://doi.org/10.1038/s41598-017-18398-4 |
| Panasonic video scale | **NR**. Must be calibrated with a known dimension: movable scale inside the duct [TM §1.2], sample width (1/1.2 or 2/2.2 cm), film length (~95 mm), SIBAL (10 cm exposed), rod (57.15 mm) | — |
| Radiometer | Oriel 71768 thermopile with CaF2 window (0.13–11 µm) in the upper rear downstream corner. **Not calibrated** (relative only), 5 Hz | [TM §1.2, §6.1.3] |
| Gas sensors | CSA-CP (O2 with 0.1 % resolution, CO 0–1000 ppm) and CDM (CO2 0–5 %, 0.1 % resolution), **only before and after** each test | [TM §1.2] |
| Ignition | 29-gauge Kanthal A-1 wire of 0.8–1 Ω at 3.5–4 A. Ignition time can reach 230 s (rods at low O2) | [TM §1.2, §6.1.4.1] |
| MSG volume | 250 L free. O2 drops during each burn, so **O2 is not constant within a test** (Miller assumes linear decay) | [TM §1.3, §5.4] |

**On O2 in the Appendix A tables.** There are two pairs of columns. The first pair is the value **calibrated against the MCA** (e.g. 22.2 % for all of GMT 050). The second pair is the **raw CSA-CP reading** (e.g. 20.6 %). The difference ranges from ~0.9 to 1.6 points. Bhattacharjee (SDSU) reports B1/B3 at 20.6–20.7 %, i.e. uses the raw reading. Olson reports his range as 13.6–22.2 %, i.e. uses the calibrated one. Before comparing across PIs **one must fix which O2 is used** (inferred by cross-checking [TM] Table A.1 with http://flame.sdsu.edu/bass.html and with http://flame.sdsu.edu/projects/BASS/asRunMatrix.html).

**Test ID prefixes** (from [TM] Appendix A):
- **B#** = Bhattacharjee: thin PMMA films of 100–400 µm, opposed.
- **F#** = Ferkul: Nomex and a candle.
- **P#** = Fernandez-Pello/Link: PMMA rods in opposed flow.
- **M#** = Miller/Wichman: PMMA slabs of 1–5 mm, opposed.
- **O#** = Olson: PMMA rods in concurrent/stagnation flow.
- **T#** = T'ien: SIBAL fabric in concurrent flow, plus sphere tests T3/T7.

In total there were **126 tests** [TM §1.1].

---

## 1. Publications (those requested plus those listed in [TM] Appendix E)

> I could not extract the exact list of the "17 publications" from NASA's PSI/SSRE page because the page renders with JS. Below are the ones you requested and others verified in [TM] Appendix E. **Marked with ★** are those containing quantitative BASS-II data that I used.

### 1.1 ★ Olson & Ferkul 2017, Combust. Flame 180:217–229
"Microgravity flammability boundary for PMMA rods in axial stagnation flow: Experimental results and energy balance analyses." DOI: https://doi.org/10.1016/j.combustflame.2017.03.001. The full text is reproduced in [TM §6.1].
- **Tests:** O1–O19 (clear and black PMMA rods with r = 0.318, 0.476 and 0.635 cm, hemispherical tip, concurrent/stagnation flow of 0–55 cm/s, O2 of 13.6–22.2 %).
- **Video method:** 30 fps video plus Nikon photos at ~1 fps. Measures flame length, width, **standoff** (measured to the outer edge of the bright cyan zone), aspect ratio, rod tip position (regression) and radiometer. Blowoff is defined as "the instant the stagnation region forms a hole". Standoff taken from the high-resolution photos.
- **Key numbers:**
  - Flammability boundary: $X_{O_2} = 6e^{-0.5a} + 0.0167a + 13.4$ (in %), with $a=\tfrac32 (U/r)(r/r_0)^{1/2}$ in s⁻¹ and $r_0=0.318$ cm. Minimum of **~13.5 % O2 at a ≈ 8–12 s⁻¹**. Linear extrapolation of blowoff to a=0 gives 13.3–13.4 %. The lowest tested was **13.6 %**.
  - **Sustained ignition** limit **≈ 14.5 % O2**. Ignition in ≤ ~40 s at high O2 and up to 230 s at low O2.
  - Lowest-O2 quenching test (r = 0.476 cm, 14.8 → 13.6 % O2): flame length stops growing at the change from 2 → 1.5 cm/s. **Stable rod regression = 0.0385 mm/s.** At extinction L/W → **0.5** (hemispherical). Quenching more than 100 s after the last flow change (≈ t_s). **1.1 Hz oscillations** before quenching. Duration up to 28 min.
  - Blowoff hole of 9 mm (re-closed in 7 s) and of 10 mm (did not re-close; persisted more than 1 min and then total blowoff). Thermal length δ = 2 mm. Final X_O2 = 14.5 %.
  - **Standoff ∝ a^(1/3)**, with a 7× increase when a drops by two orders of magnitude.
  - CO of ~600 ppm per 1 vol % of CO2. Minimum heat flux of 1.57 W/cm². Vaporization ≈ 70 % of heat on the blowoff branch and ~20 % on the quenching branch.
  - Diffusion U_D = 2 cm/s; the blowoff→quenching transition occurs at U/U_D ≈ 1.
  - Opposed flow over rods: no spread below **16.4 % O2** at any flow.

### 1.2 Olson & Ferkul 2015, 9th US Natl. Combust. Mtg. (Cincinnati)
"Microgravity Flammability of PMMA Rods in Concurrent Flow". NTRS: https://ntrs.nasa.gov/citations/20150008961
- 24 concurrent tests. A preliminary version of 1.1.
- The time to develop the solid thermal profile is estimated with Fo = αt/R² ≈ 0.3, giving **25 to 100 s** depending on radius.
- Blowoff extrapolation to 13.3 % O2 (vs a minimum tested of 13.6 %). In opposed rods there was no spread below 16.4 %.

### 1.3 Marcum, Olson & Ferkul 2016, Central States CI Spring Mtg. (Knoxville)
"Correlation of normal gravity mixed convection blowoff limits with microgravity forced flow blowoff limits". NTRS: https://ntrs.nasa.gov/citations/20160012691
- 1g tests with PMMA rods of 0.635–3.81 cm diameter and 14–18 % O2, in a 7.6 cm quartz tube; maximum 60.3 cm/s. The video includes a scale imaged on the grid.
- The blowoff boundary is **linear (O2 ∝ flow)**.
- An **empirical buoyant stretch of a_b = 78 s⁻¹** aligns the 1g data with BASS-II. For the baseline rod it is equivalent to a forced flow of **16.5 cm/s** (the estimated buoyant flow is ~20 cm/s).
- Extrapolating to zero stretch gives **13.4 % O2** (vs the BASS-II minimum of 13.6 %).
- Related versions: Marcum, Ferkul & Olson, PCI 37 (2019) 4001–4008; ICES-2017-370 (NTRS 20170006615); Marcum et al., C&F 216 (2020) 385–397 (low pressure).

### 1.4 ★ Bhattacharjee, Simsek, Olson & Ferkul 2016, Combust. Flame 163:472–477
"The critical flow velocity for radiative extinction in opposed-flow flame spread in a microgravity environment: A comparison of experimental, computational, and theoretical results." DOI: https://doi.org/10.1016/j.combustflame.2015.10.023. Reproduced in [TM §2.2].
- **Tests:** B# (PMMA films of 100–400 µm, 20 mm wide, ~95 mm long, opposed, 0–50 cm/s).
- **Method (important for our pipeline):** the **SDSU MATLAB app** ("Flame Analyzer") works on the **top-view photo sequence at 1 fps**.
  1. Crops a central ~14 mm strip to remove edge effects.
  2. Converts RGB to intensity.
  3. Averages across the width, giving a 1D profile I(x).
  4. **Leading edge = first x where I crosses a fixed threshold of 30** (on a 0–255 scale; "worked for almost all tests").
  5. Defines the "bright edge" as the maximum of I(x).
  6. **Vf = slope of a linear regression over 5 consecutive positions**.
  - Reproducible within ±5 % using either the leading edge or the bright edge. In Fig. 2.7 of [TM] the leading edge falls at x = 887 px. Overlaid points every 6 mm.
- **Numbers:**
  - 100 µm: stable spread of **2.2 mm/s**. With an abrupt flow cut-off it extinguishes in **<2 s**. In the ramp from 3 cm/s it extinguishes ~30 s after ignition at Vg ≈ **1.1 cm/s**.
  - Critical extinction velocity **≈1 cm/s for 100/200/300 µm and ≈1.5 cm/s for 400 µm (21 %)**. At **~16 % O2: 2.6 cm/s (100 µm) and ~4 cm/s (200 µm)**.
  - Table 2.1, Vg,cr in mm/s:

    | O2 | Exp. | Computation | Theory (eq. 2.5) |
    |---|---|---|---|
    | 21 % | 10 ± 5 | 15 | 7.5 |
    | 16 % | 30 ± 5 | 35 | 10 |

  - 2D computation: Vg,cr = 1.5 cm/s for all thicknesses (21 %) and 3.5 cm/s (16 %). At 16 % the kinetic effect appears for **Vg > 16 cm/s**.
  - In 1g downward (model): **2.8, 1.6, 1.2 and 0.9 mm/s for 100, 200, 300 and 400 µm**.
  - Linearized T_f = 2199 K, T_v = 673 K.
  - Radiative extinction sequence: t = 27 s → Vg = 3.0; t = 28 → 1.5; t = 29 → 1.1; t = 30 s → no visible flame. The orange is lost and the flame turns entirely blue.

### 1.5 ★ Bhattacharjee, Laue, Carmignani, Ferkul & Olson 2016, Fire Safety J. 79:111–118
"Opposed-flow flame spread: A comparison of microgravity and normal gravity experiments to establish the thermal regime." DOI: https://doi.org/10.1016/j.firesaf.2015.11.011. Reproduced in [TM §2.3]. (In the request it appears as "FSJ 2015, 10.1016/j.firesaf.2015.11.011".)
- **Method:** the same Flame Analyzer. The photos are converted into video (published at http://flame.sdsu.edu). Threshold = 70 in the 1g tests. 5 s spread average with reproducibility ≤ 5 %, except near ignition.
- **Numbers:**
  - In μg the maximum for 100 µm is **2.2 mm/s**, with Vg between ~40 and ~1 cm/s. In 1g downward, 100 µm gives **2.0 mm/s**.
  - Kinetic blowoff at high Vg (~40 cm/s) and radiative extinction at ~1 cm/s.
  - Experimental de Ris coefficient **F_expt = 4.76**. Other values: F_deRis(lin) = 5.54, F_adb = 4.89, F_eql = 4.41.
  - Formulas (τ = half-thickness, SI): $V_{f,thin}=2.34\times10^{-8}F/\tau$ and $V_{f,thick}=9.72\times10^{-5}V_gF^2$.
  - Thick downward limit: **0.044 mm/s** (0.042 mm/s for 10 cm width).
  - Buoyant $V_{g,eff}$ = **1.9 cm/s**. Thin/thick transition thickness for downward spread in air: **2τ = 5.19 mm**.
  - Figures with IDs: **B03 = 100 µm, B11 = 200 µm, B4 = 300 µm and B13 = 400 µm**, all at 20.7 % O2.

### 1.6 Bhattacharjee, Simsek, Miller, Olson & Ferkul 2017, Proc. Combust. Inst. 36:2963–2969
"Radiative, thermal, and kinetic regimes of opposed-flow flame spread: A comparison between experiment and theory." DOI: https://doi.org/10.1016/j.proci.2016.06.025 (the request cites it as "PCI 2016").
- **I could not access the abstract or the text** (Elsevier, closed). From the title and [TM §2], it compares BASS-II data (μg, radiative and thermal regimes) with tunnel data (kinetic regime) and with scaling theory. **Numerical values: NR (pending).**

### 1.7 Bhattacharjee et al. 2015, Proc. Combust. Inst. 35 (2014 papers)
- **10.1016/j.proci.2014.06.125**: Bhattacharjee, Tran, Laue, Paolini & Nakamura, "Experimental validation of a correlation capturing the boundary layer effect on spread rate in the kinetic regime of opposed-flow flame spread", PCI 35(3):2631–2638. https://doi.org/10.1016/j.proci.2014.06.125
- **10.1016/j.proci.2014.05.093**: Bhattacharjee, Paolini, Tran, Villaraza & Takahashi, "Temperature and CO2 fields of a downward spreading flame over thin cellulose: A comparison of experimental and computational results", PCI 35(3):2665–2672. https://doi.org/10.1016/j.proci.2014.05.093
- Titles and authors verified via Semantic Scholar. **They appear to be 1g works** (tunnel or downward), supporting material. I did not verify that they contain BASS-II data. Useful as context for the kinetic regime and the boundary-layer effect.

### 1.8 ★ Zhao, Liao, Johnston, T'ien, Ferkul & Olson 2017, Proc. Combust. Inst. 36:2971–2978
"Concurrent flame growth, spread, and quenching over composite fabric samples in low speed purely forced flow in microgravity." DOI: https://doi.org/10.1016/j.proci.2016.06.028. The conference version (USNCM 2015) is at NTRS 20150008962: https://ntrs.nasa.gov/citations/20150008962. Reproduced in [TM §7.1].
- **Tests:** T1–T29 (SIBAL: 75 % cotton and 25 % fiberglass, 0.32 mm, 18.2 mg/cm², 1.2 and 2.2 cm wide, 10 cm exposed). Flow of 40 → 1 cm/s, O2 of 21 → 16 %.
- **Method:** **tracking of flame tip, flame base and flame length** in the side video at 29.97 fps. For dim flames (low flow and low O2) the top camera is used (~1 image every 1.2 s, 1/8–1/4 s exposure). "Steady spread" is defined as constant velocity for more than 20 s.
- **Numbers:**
  - 2.2 cm, 10 cm/s, 21 %: the flame reaches a **constant limiting length at ~19 s**, the steady state lasts **~9 s** and the whole process ~40 s.
  - 2.2 cm, 5 cm/s, 21 %: more than 60 s in total, steady state **~21 s**, shorter and slower flame.
  - **Quenching velocities of 1–5 cm/s** (higher the lower the O2).
  - Quenching sequence (T4: 2.2 cm, 18.7 %, 10 → 2.2 cm/s): the flame shrinks in length and width until it becomes circular and blue.
  - **Vf values are only in Fig. 7.4 → numerically NR.**

### 1.9 ★ Shah, Miller, Olson & Wichman: intermediate-thickness PMMA slabs in opposed flow
- Shah, T.J., et al., "Modeling and Analysis of Intermediate Thickness PMMA Sheets Burning in Microgravity Opposed Flow", WSSCI Fall 2015, paper 134HC-0056. Also at the 31st ASGSR 2015, and Shah's MS thesis (SDSU, 2016). Cited in [TM §5.9 and Appendix E]. **I have no public URL.**
- **Data** in [TM §5] Table 5.1 (below, M# tests).
- **Method:** **Spotlight-16** (NASA image-tracking software; Klimek & Wright, NASA/TM-2006-214084) on photos and video, then Excel for Vf (slope of position vs t). O2 linearly interpolated between start and end.
- Findings: Vf decreases with thickness and with decreasing Vg. Two-sided samples are faster than one-sided. There is a width effect (2 cm samples are faster than 1 cm at 1 mm). Near ~19 % O2 the two-sided sample is consumed from the trailing edge instead of spreading. The FDS (DNS) model overestimates Vf. Max. model HRR = 225 kW/m².

### 1.10 Hariharan / Wichman, Olson, Miller & Hariharan 2016, American Scientist 104(1):44–51
"Fire in Microgravity". Authors: I.S. Wichman, S.L. Olson, F.J. Miller and A. Hariharan. https://www.americanscientist.org/author/fletcher_j._miller
- Popular-science article on **flamelets**, which persist at very low O2 and can revive. **No verified quantitative data (full text not accessible).**

### 1.11 ★ Olson et al. 2015, ICES-2015-196
"Results from On-Board CSA-CP and CDM Sensor Readings During the BASS-II Experiment in the MSG". NTRS: https://ntrs.nasa.gov/citations/20150019858
- CSTR dilution model: $c(t)=C_0e^{-rt/V}$ with V = 0.25 m³ and r ≤ 0.0005 m³/min. Calibration gave r = 493 cm³/min, CSA-CP = 20.9 % vs MCA = 21.48 %.
- O2 consumed / CO2 produced matches the 6:5 stoichiometry. HRR ≪ 100 W (Huggett, 13.1 kJ/g O2). φ_global ≈ 1.3. Concurrent rods: ~550 ppm CO per 1 % CO2. Opposed slabs: ~370 ppm/1 %.
- One thick-slab test released ~100 W and damaged the window (M5, GMT 051). One concurrent rod test reached ~110 W without damage.

### 1.12 Olson et al. 2019, ICES-2019-101
"Flammability Limits from BASS-II Testing in Microgravity Compared to Normal Gravity Limits". Listed in [TM] Appendix E. TTU repository: https://ttu-ir.tdl.org/items/1922ad9f-ef4c-4f52-96a4-980c23debe5e (returned 403). **Content not verified.**

### 1.13 ★ Link, Huang, Fernandez-Pello, Olson & Ferkul 2018, Sci. Rep. 8:120 (open access)
"The Effect of Gravity on Flame Spread over PMMA Cylinders". https://doi.org/10.1038/s41598-017-18398-4 · PMC5760683.
- **Tests:** P# (black/clear rods of 0.64, 0.95 and 1.27 cm, opposed, 0.4–8 cm/s, 15–21 % O2).
- **Method:** **leading edge** tracking in the high-resolution photos (~1 every 1 s) with an "imaging tracking code", at 34 px/mm. Linearity of x(t) is used to confirm the quasi-steady state, with flow steps of ≥ 1 min. They then perform a multivariate linear regression of Vf against (O2, Vg, d).
- **Numbers:**
  - Vf **first increases and then decreases** with Vg (the first experimental observation of this).
  - No spread at **Vg < 0.6 cm/s**.
  - In μg it spreads at **17 %** O2, vs 18 % as the 1g limit.
  - Above 19 % spread is faster in 1g; below 19 %, faster in μg.
  - Per-test values are in Table S1 (see §2.3).
- ⚠️ **Link's "Sample B##" are not Bhattacharjee's B## tests.** B = black and C = clear, and the number matches the **P#** of Appendix A.3 (inferred by cross-checking diameter and O2; see §2.3).

### 1.14 Other BASS-II papers with data (from [TM] Appendix E)
- Carmignani, Celniker, Rhoades & Bhattacharjee, "Measurement of instantaneous flame spread rate over solid fuels using image analysis", **Fire Saf. J. 91 (2017) 123–129**, https://doi.org/10.1016/j.firesaf.2017.03.039. Describes the Flame Analyzer method (**direct CV precedent**). Text not accessible.
- Carmignani et al., "Boundary Layer Effect on Opposed-Flow Flame Spread and Flame Length Over Thin PMMA in Microgravity", **Combust. Sci. Technol. 190(3) (2018) 535–549**. Uses ISS data on thin films. Flame size changes strongly along the developing boundary layer, but the predicted Vf increase was not fully confirmed (abstract via AMiner: https://www.aminer.cn/pub/5c757263f56def979880a7a7). Values NR.
- Olson, Ferkul & Marcum, "High-speed video analysis of flame oscillations along a PMMA rod after stagnation region blowoff", PCI 37(2) (2019) 1555–1562. Values NR.
- Huang et al., "Transition from opposed flame spread to fuel regression and blow off: Effect of flow, atmosphere, and microgravity", PCI 37(3) (2019) 4117–4126. Values NR.
- Endo et al., "Flame growth around a spherical solid fuel in low speed forced flow in microgravity", Fire Technol. 56 (2020) 5–32 (sphere: tests T3/T7). Values NR.
- Carmignani, Dong & Bhattacharjee, "Radiation from flames in a microgravity environment", Fire Technol. 56 (2020) 33–47.
- Ferkul et al. 2014, ASGSR poster, "Combustion of Solids in Microgravity: Results from the BASS-II Experiment", NTRS https://ntrs.nasa.gov/citations/20160000593. Summary by PI: 22 B tests, 54 unique Vf for P# rods, 20 M tests, 24 O rods and 29 T tests.
- **BASS-I** (precursor, same duct): Ferkul, Olson, Johnston & T'ien 2012, ASGSR poster, "Flammability Aspects of a Cotton-Fiberglass Fabric in Opposed and Concurrent Airflow in Microgravity", NTRS https://ntrs.nasa.gov/citations/20130012832 (numbers in §2.6).

---

## 2. Table of reference values by test ID (ground truth for validating the CV pipeline)

### 2.1 B# tests: thin PMMA films, opposed (Bhattacharjee)
Sources:
- **Vf "side" and "top"**: SDSU repository, http://flame.sdsu.edu/bass.html. These are two methods, side view (video) and top view (photos).
- Conditions: [TM] Table A.1 and http://flame.sdsu.edu/projects/BASS/asRunMatrix.html.

O2 is the value reported by SDSU, mostly the CSA-CP reading. The arrow ↓ means decreasing flow and ↑ increasing.

| Test | GMT 2014 | Width (cm) | Thickness (µm) | O2 (%) SDSU | Vg (cm/s) | **Vf side (mm/s)** | **Vf top (mm/s)** | Result / notes ([TM] A.1) |
|---|---|---|---|---|---|---|---|---|
| B1 | 050 | 2 | 100 | 20.6 | 5 ↓ (cut-off) | **1.8783** | **1.7662** | Flow cut off mid-sample; extinguishes very quickly (<2 s). Sooty flame with blue leading edge. 57 frames |
| B3 | 050 | 2 | 100 | 20.7 ± 0.2 | 2.5 ↓ | **2.0562** | **1.9688** | Bluer flame at low flow. 253 frames. Appears in FSJ as "B03" |
| B6 | 188 | 2 | 100 | 20.05 ± 0.05 | 4, 5, 8, 10 ↑ | NR | NR | Steady at 3 and 5 cm/s; did not reach 10 before the end |
| B9 | 188 | 2 | 100 | 20.05 ± 0.05 | 2.6, 1.8 ↓ | NR | NR | Steady at 2 cm/s; extinguishes at pot 0.35 (<1 cm/s) |
| B15 | 188 | 2 | 100 | 20.00 ± 0.05 | 10 ↑ 55 | NR | NR | Spreads at 10 cm/s; **no blowoff** at maximum |
| B5 | 050 | 2 | 200 | 20.7 ± 0.2 | 5.67, 0 ↓ | **1.1262** | **1.0531** | Repeat of B2 with top view |
| B2 | 050 | 2 | 200 | 20.6 | 6.47, 0 ↓ | **1.0784** | N/A | No photos (loose cable) |
| B8 | 188 | 2 | 200 | 19.8 ± 0.25 | 10, 56 ↑ | NR | NR | No blowoff |
| B11 | 188 | 2 | 200 | 19.95 ± 0.15 | 9, 1.8 ↓ (slow) | NR | NR | Extinction at pot 0.35. "B11" in FSJ |
| B10 | 188 | 1 | 200 | 20 ± 0.1 | 7, 1.7 ↓ (steps) | NR | NR | Extinction at pot 0.35 |
| B21 | 216 | 1 | 200 | 19.7 ± 0.1 | 6.2, 1.8 ↓ | NR | NR | Extinguishes at pot 0.355 |
| B22 | 216 | 1 | 200 | 19.7 ± 0.1 | 6.5, 1.9 ↓ | NR | NR | Extinguishes at pot 0.36 |
| B4 | 050 | 2 | 300 | 20.6 | 6.2, 0 ↓ | **0.8004** | **0.7205** | Thicker bubble layer. "B4" in FSJ |
| B12 | 050 | 2 | 300 | 20.5 ± 0.1 | 2.52, 0 ↓ | **0.6073** | **0.5842** | Mostly blue; soot only at the bottom |
| B7 | 050 | 2 | 400 | 20.55 ± 0.05 | 2.47, 0 ↓ | **0.4715** | **0.4577** | Very long bubble layer |
| B13 | 188 | 2 | 400 | 19.85 ± 0.15 | 9.7, 1.2 ↓ | NR | NR | Extinction at pot 0.35. "B13" in FSJ |
| B20 | 183 | 2 | 100 | 17.4 | 4.5, 3.5, 2 | ? | ? | Consumed the entire sample |
| B16 | 183 | 2 | 100 | 17.3 | 3, 2.1, 0 | ? | ? | Quench after a prolonged burn at pot 0.4; single-sided flame |
| B19 | 183 | 2 | 100 | 16.35 ± 0.2 | 7.31, 30 ↑ | ? | ? | **Blowoff** at fan pot 6.0 |
| B18 | 183 | 1 | 200 | 16.4 | 7.5, 50 ↑ | ? | ? | **Blowoff** at fan pot 7.0 |
| B17 | 183 | 1 | 200 | 16.55 ± 0.05 | 4.8, 1 ↓ | ? | ? | Extinguishes on reaching pot 0.4 |
| B14 | 183 | 1 | 200 | 14.1 | — | — | — | **No sustained ignition** (only a brief ignition) |

**Critical extinction velocities** ([TM §2.2.5]):

| O2 | 100 µm | 200 µm | 300 µm | 400 µm |
|---|---|---|---|---|
| ~21 % | ≈ 1 cm/s | ≈ 1 cm/s | ≈ 1 cm/s | ≈ 1.5 cm/s |
| ~16 % | ≈ 2.6 cm/s (20 mm wide) | ≈ 4 cm/s (10 mm wide) | — | — |

Check against de Ris (inferred). With $V_{f,thin}=2.34\times10^{-8}F_{adb}/\tau$ and $F_{adb}=4.89$, the prediction is 2.29, 1.14, 0.76 and 0.57 mm/s for 100, 200, 300 and 400 µm. The SDSU measurements of 1.77–2.06, 1.05–1.13, 0.58–0.80 and 0.46–0.47 mm/s scale as 1/τ. **Use it as a consistency test for the pipeline.**

### 2.2 M# tests: PMMA slabs of 1–5 mm, opposed (Miller/Wichman/Shah), [TM] Table 5.1
Method: Spotlight-16. Vf in **mm/s**, as it appears in the table. ⚠️ The values are very low (0.012–0.144 mm/s). They are consistent with thick fuel in μg (see BASS-I slab of 0.037 mm/s), but should be verified with the pipeline.

| Test | Thick. (mm) | Width (cm) | Sides | Vg (cm/s) | **Vf (mm/s)** | Burn (min) | O2 init → final (%) |
|---|---|---|---|---|---|---|---|
| M1 | 1 | 2.2 | 1 | 9 | 0.071 | 6.4 | 22.2 → 21.9 |
| M2 | 3 | 2.2 | 1 | 20; 15 | 0.052; 0.033 | 22.9 | 22.2 → 21.2 |
| M3 | 5 | 2.2 | 1 | 10; 20 | 0.029; 0.024 | 20.1 | 20.8 → 19.7 |
| M4 | 5 | 2.2 | 2 | 5; 3 | 0.045; 0.033 | 19.8 | 21.8 → 19.8 |
| M5 | 3 | 2.2 | 2 | 10 | 0.071 | 27.2 | 22.2 → 19 |
| M6 | 1 | 2.2 | 2 | 10; 8 | not tracked | 16.8 | 21.8 → 20.7 |
| M7 | 1 | 1.2 | 2 | 10; 6; 5; 3 | 0.106; 0.099; 0.083; 0.07 | 18.4 | 18.9 → 18.4 |
| M8 | 2 | 1.2 | 2 | 10; 6; 5 | 0.057; 0.056; 0.04 | 25.2 | 19.1 → 18.2 |
| M9 | 3 | 1.2 | 2 | 14 | 0.025 | 16.8 | 18 → 17.6 |
| M10 | 4 | 1.2 | 2 | 15; 10 | 0.0373; 0.03 | 30.5 | 20.1 → 18.6 |
| M11 | 5 | 1.2 | 2 | 21; 15; 13 | 0.048; 0.028; 0.022 | 28.5 | 20 → 18.5 |
| M12 | 2 | 2.2 | 2 | 12; 10 | not tracked | 16.2 | 21.7 → 20.4 |
| M13 | 4 | 2.2 | 2 | 6; 5; 4 | 0.047; 0.035; 0.033 | 20.5 | 20.8 → 19 |
| M14 | 2 | 2.2 | 1 | 15; 14; 10 | 0.0624; 0.055; 0.0353 | 15.4 | 22.2 → 21.6 |
| M15 | 4 | 2.2 | 1 | 20 | 0.045 | 22.0 | 21 → 20 |
| M16 | 1 | 2.2 | 2 | 5; 3; 2 | 0.144; 0.1309; 0.1062 | 8.4 | 19.2 → 18.7 |
| M17 | 2 | 2.2 | 2 | 5; 4; 3 | 0.053; 0.042; 0.026 | 30.7 | 18.8 → 17.1 |
| M18 | 3 | 2.2 | 2 | 10; 8 | 0.026; 0.013 | 25.5 | 17.9 → 16.8 |
| M19 | 4 | 2.2 | 2 | 10; 6 | 0.027; 0.0159 | 25.7 | 19 → 17.4 |
| M20 | 5 | 2.2 | 2 | 10 | 0.012 | 16.5 | 18 → 17.4 |

Extinctions according to the notes in Table A.4 of [TM]:
- M10: self-extinction at 8 cm/s after ~10 min.
- M11: extinction at 12 cm/s (29 min burn).
- M13: extinguishes at 9 cm/s.
- M18: extinguishes at 8 cm/s (26 min).
- M19: extinguishes at 5 cm/s.
- M20: extinguishes at 18 cm/s.
- M2: self-extinction at 13–14 cm/s.
- M5: extinguishes at 5 cm/s, ~100 W and window damage.

There are minor O2 discrepancies between Table 5.1 and A.4 (for example, M1 appears as 22.2/21.9 and as 22.2/21.9/20.6/20.3).

### 2.3 P# tests: PMMA rods in opposed flow (Fernandez-Pello/Link)
Source: **Link et al. 2018, Sci. Rep., Table S1** (supplement PMC5760683). Vf is in **×10⁻³ cm/s**: divide by 100 to get mm/s. The right-hand column of the table says "(mm/s)", but its magnitudes are the same as the left-hand ones, so I assume it is the same unit (inferred). Δt is the step duration in s.

**ID mapping (inferred, high confidence):** Link's sample "B n" (black) or "C n" (clear) corresponds to **P n** in [TM] A.3. Diameter and O2 match: P13a/b are 12.7 mm at 20.7/20.6 %, P22 is 9.525 mm at 20.8 %, P6 is 6.35 mm at 18.9 %, etc. ⚠️ [TM] A.3 lists P16 and P19 as "Concurrent", but Link describes them as opposed.

| Link sample → test (inferred) | d (cm) | O2 (%) | Pairs (Vg cm/s → Vf ×10⁻³ cm/s) | Vf (mm/s) |
|---|---|---|---|---|
| B13a → P13a | 1.27 | 20.7 | 1.64→5.23; 1.54→5.27; 1.43→4.63; 1.38→4.69 | 0.046–0.053 |
| B13b → P13b | 1.27 | 20.6 | 1.64→7.09; 1.54→4.91 | 0.049–0.071 |
| B5 → P5 | 1.27 | 19.3 | 1.64→3.76; 1.54→3.74 | ~0.037 |
| B9 → P9 | 1.27 | 17.6 | (1.64→4.57)*; 1.54→3.34; 1.43→2.67; 1.38→2.03 | 0.020–0.046 |
| C25 → P25 | 0.95 | 20.9 | 1.58→6.09; 1.52→5.50; 1.48→5.59 | 0.055–0.061 |
| B22 → P22 | 0.95 | 20.8 | 1.58→6.45; 1.58→8.31; 1.52→5.89; 1.48→4.10 | 0.041–0.083 |
| B4 → P4 | 0.95 | 18.5 | 2.00→3.25; 1.87→3.10; 1.73→2.69; (1.01→3.08)* | 0.027–0.033 |
| B12 → P12 | 0.95 | 17.5 | 0.82→3.45; 0.60→3.65; 0.48→2.37 | 0.024–0.037 |
| B6 → P6 | 0.64 | 18.9 | 2.00→10.00; 1.87→9.74; 1.73→8.32 | 0.083–0.100 |
| B15 → P15 | 0.64 | 18.4 | 2.14→7.16 | 0.072 |
| B14 → P14 | 0.64 | 18.4* | 1.98→6.38 | 0.064 |
| **B16 → P16** | 0.64 | 18.2 | 7.55→6.78; 1.67→7.62; 0.83→6.99; 0.72→5.68 | 0.057–0.076 (peak at 1.67 cm/s) |
| B1 → P1 | 0.64 | 17.7 | 4.00→7.15 (Δt = 794 s); 2.15→5.91 | 0.059–0.072 |
| C3a → P3a | 0.64 | 17.7* | 2.50→8.37; 2.00→6.42 | 0.064–0.084 |
| **B19 → P19** | 0.64 | 17.5 | 7.55→4.69; 1.67→6.52; 0.83→6.25; 0.72→5.44 | 0.047–0.065 (peak at 1.67 cm/s) |
| B2 → P2 | 0.64 | 17.4 | 2.50→7.25; 2.00→7.87 | 0.073–0.079 |
| C3b → P3b | 0.64 | 17.4* | 1.85→6.00; 2.00→5.41 | 0.054–0.060 |
| B10 → P10 | 0.64 | 17.0 | 1.87→5.15; 1.73→4.22 | 0.042–0.052 |
| P17 → P17 | 0.64 | 16.8 | 1.01→4.12; 0.82→4.78; 0.41→2.26 | 0.023–0.048 |

\* = the assignment of a row to a sample, or the O2, is ambiguous because the PDF table has merged cells.

Other data from this group:
- Range of conditions ([TM] Table 4.2): 6.35 mm → 16.8–18.9 % O2, 0.41–7.5 cm/s; 9.525 mm → 17.5–20.9 %; 12.7 mm → 17.6–20.7 %.
- No sustained spread with Vg < ~4 mm/s (0.4 cm/s) at 6.35 and 9.525 mm ([TM §4.1.2]); Link gives 0.6 cm/s.
- Small, blue flames open at the rear at low Vg. Yellow, luminous and with closed tip from ~2 cm/s.
- 1g comparison values (Link Table S2, ×10⁻³ cm/s, at 25 / 2 cm/s): 1.27 cm at 20.9 % = 7.81 / 9.07; 0.64 cm at 20.9 % = 11.17 / 13.63; 0.32 cm at 20.9 % = 18.40 / 23.57. In 1g there is no spread below ~18–18.5 % (depending on diameter).

### 2.4 O# tests: PMMA rods in concurrent/stagnation flow (Olson), [TM] Table A.5 + §6.1
O2 = calibrated initial → final. Spread Vf: NR. The main measurements are **tip regression** and **flame length and standoff**.

| Test | Rod | Mode | O2 calib. (%) | Result |
|---|---|---|---|---|
| O1 | 6.35 clear | ? (bracket) | 22.2 → 21.7 | Flows 20, 10, 5, 2, 1; very sooty and long flame at high flow; vapor jetting |
| O2 | 6.35 clear | — | 22.2 → 21.9 | Ignition at 2 cm/s; dim, sooty flame |
| O3a/O3b | 6.35 clear | Concurrent | 18.0 → 17.7 | Sooty even at low flow; blue only with air ≈ 0 |
| O4 | 9.525 clear | Stagnation | 14.8 → 13.6 (inferred) | Extinction at pot 0.36. **Probably the lowest-O2 test of §6.1.4.2** (r = 0.476, 14.8 → 13.6 %, regression 0.0385 mm/s, 1.1 Hz). Inferred |
| O5a | 12.7 clear | Concurrent | 15.1 → 14.2 | 9 min, then blowoff at pot 4.0 |
| O6 | 6.35 clear | Stagnation | 16.7 → 16.0 | Flow lowered until extinction (out) |
| O7 / O8b / O9 | 6.35 clear | Stagnation | 16.0→15.5 / 15.5→15.2 / 15.0→14.8 | **Blowoff** at fan 97 / 78 / 68 |
| O8a | 6.35 clear | Stagnation | 15.7 → 15.3 | Quench at pot 0.31 |
| O10 | 6.35 clear | Concurrent | 16.7 → 16.1 | Leading-edge blowoff at fan 81; rest of the flame within 25 s |
| O11 | 6.35 black | Stagnation | 15.4 → 14.8 | Blowoff at pot 6.0 |
| O12 | 9.525 clear | Stagnation | 13.6 → 13.5 | **No sustained flame** |
| O13a | 12.7 clear | Concurrent | 15.9 → 14.6 | Self-extinction after more than 3 min at pot 0.31 |
| O14 / O19 | 6.35 black / clear | Concurrent | 16.3→15.3 / 15.3→14.6 | Quench at pot 0.28 / 0.288 |
| O15a / O15b | 9.525 clear | Stagnation | 17.1→16.7 / 16.7→15.6 | Quench at pot 0.32 / 0.27. Steps of 1–5 min documented (O15b: 5 → 0.27 pot in ~25 min) |
| O16 | 9.525 clear | Stagnation | 14.5 | No sustained flame |
| O17 | 6.35 clear | Concurrent | 15.1 → 14.3 | Leading-edge blowoff at fan 72; does not recover |
| O18 | 6.35 clear | Stagnation | 15.2 → 14.5 | Blowoff hole re-closed once; the second time it did not (see 1.1: holes of 9 and 10 mm) |

### 2.5 T# tests: SIBAL fabric in concurrent flow (T'ien), [TM] Table 7.1

| Test | Width (cm) | Flow (cm/s) | O2 (%) | Result |
|---|---|---|---|---|
| T1 | 2.2 | 10 | 18.5 (doubtful) | — |
| T2 | 2.2 | 10 → 5 | 18.5 (doubtful) | — |
| T4 | 2.2 | 10 → 2.2 | 18.7 | **Quenched** (sequence in Fig. 7.5: t = 6.7 s at 8 cm/s … t = 54 s at 2.2 cm/s) |
| T15 | 2.2 | 10 → 29 | 18.7 | No blowoff |
| T5 | 2.2 | 10 → 2.4 | 18.8 | "Flamelet", burned the entire sample |
| T6 | 2.2 | 4.5 → 2.6 | 18.8 | Did not extinguish |
| T13 | 2.2 | 4 → 2.2 | 17.5 | Quenched |
| T16 | 2.2 | 4 → 3 | 17.6 | Spread over the entire sample |
| T9, T10, T12 | 2.2 | 10 / 5 / 5 | 16.4 / 16.4 / 16.8 | No ignition |
| T18 | 2.2 | 5 → 2.6 | 17.4 | Quenched |
| T11 | 2.2 | 4 | 17.1 | Burned completely, steady |
| T14 | 2.2 | 4 → 2.8 | 16.9 | Quenched (below 3 cm/s) |
| T17 | 2.2 | 6 → 53 | 16.9 | No blowoff |
| T19 | 1.2 | 11 | 17.2 | Steady burn |
| T20 | 1.2 | 11 → 3 | 17.2 | Quenched |
| T21 | 1.2 | 11 → 47 | 17.2 | **Blowoff** |
| T22 | 1.2 | 10.5 → 5 | 17.1 | Quenched |
| T23–T29 | 2.2 / 1.2 | 5–10 | 17.2–20.8 | Reused (partial or failed ignition) |
| BASS-I GMT96-T8 / T7 | 2.2 | 5 / 10 | 21 | References for Figs. 7.2–7.3: steady ~21 s / ~9 s, limiting length at ~19 s (10 cm/s) |
| BASS-I GMT131-T10 / GMT222-T11 | 1.2 | 11 / 19 | 21 | — |
| T3, T7 (4 cm sphere) | — | 10 → 1 | 17.2–17.3 | T7: extinction at pot 0.28 after a series of reductions. T3: not sustained |

### 2.6 BASS-I SIBAL (same duct, 21 % O2), useful as a prior
Source: Ferkul et al. 2012, NTRS https://ntrs.nasa.gov/citations/20130012832.
- **Concurrent 2 cm: $V_F = 0.20|U| + 0.56$ mm/s. Concurrent 1 cm: $V_F = 0.15|U| + 0.07$ mm/s** (U in cm/s). The linear fits are taken from the figure.
- At ~10 cm/s: **2.55 mm/s concurrent vs 1.21 mm/s opposed** (2 cm).
- Tracking 1 cm at 10 cm/s: $x_{tip}=1.71t+2.25$ and $x_{base}=1.68t-13.81$ (mm, s). Steady at ~10 s and **flame length ≈ 16 mm** (inferred from the difference).
- Opposed: the Vf maximum is at an intermediate flow. Quenching at ~1 cm/s. Photos every 1.125–1.25 s.
- One-sided PMMA slab 1 cm wide at low flow ([TM] App. D.7): **Vf = 0.037 mm/s**, 15 mm flame, stable size at ~3 min, ignition of more than 1 min.
- 1 cm PMMA sphere: 617.5 mg consumed in 325 s (1.9 mg/s, mean regression of ~0.3 mm/min).

### 2.7 F#: Nomex and candle (Ferkul)
- F1–F3 (Nomex III): **no sustained ignition**.
- F4 (Japan Wax candle, 17.4 → 16.2 % O2): blue flame at 3 cm/s. Pots 0.6, 0.4, 0.35, 0.32, 0.31 and 0.305 until extinction. Ejects a wax droplet upstream ([TM §3]).

---

## 3. Prior art: automated image processing and ML on microgravity flame videos
1. **SDSU Flame Analyzer (MATLAB)**, on BASS-II top-view photos. Fixed intensity threshold (30 in μg, 70 in 1g), width-averaged 1D profile and 5-point linear regression. ±5 %. [TM §2.2.4, §2.3.6]; Bhattacharjee et al., FSJ 91 (2017) 123–129, https://doi.org/10.1016/j.firesaf.2017.03.039. Per-test data and NEF images/videos at http://flame.sdsu.edu/bass.html.
2. **NASA Spotlight-16 / Spotlight-8**, semi-manual tracking used for the M# tests ([TM §5.3]). Klimek & Wright, NASA/TM-2006-214084.
3. **Link et al. 2018**: "imaging tracking code" on the leading edge, plus multivariate regression (Sci. Rep.).
4. **Olson et al., PCI 37 (2019)**: high-speed video analysis of oscillations (1g/drop). Values NR.
5. **Liao (CWRU), NASA Task Book "Predicting Material Flammability in Partial Gravity Using Microgravity and Ground Data"** (2023–2026). MATLAB code on images and videos from the **NASA PSI database** for BASS and BASS-II:
   - flame-edge tracing with a per-experiment adjusted threshold;
   - position vs t tracking;
   - **OCR of the video overlay to extract real-time air velocity**.

   According to the FY2026 report, they obtained flame position vs t and flow for most BASS and BASS-II tests. They do not publish numbers. https://taskbook.nasaprs.com/tbp/index.cfm?action=public_query_taskbook_content&TASKID=31FF2895CF11A3D63C9B8986DB12A22A
6. **Saffire**: base and pyrolysis position from video. Jomaas et al., 10th USNCM 2017, https://www.pure.ed.ac.uk/ws/files/31828517/The_Saffire_Experiment_2017_US_National_Meeting_Final.pdf. SIBAL at 20 cm/s: **concurrent 1.8 mm/s with a plateau flame of ~40 mm; opposed 1.3 mm/s with ~24 mm**.
7. **MicroFire Atlas (GitHub, NASA Space Apps 2026 "Flame in Freefall")** is a team in the **same challenge**. It uses classical OpenCV segmentation **not validated** against human masks and a logistic regression over 41 BASS-II tests to predict "established flame" (AUC 0.80). https://github.com/A-K-M-Asifuzzaman/MicroFire-Atlas
8. **Published, peer-reviewed ML or deep learning on BASS, BASS-II, SoFIE or Saffire: I found none.** There is a clear gap. Our pipeline (automated CV + forecasting) would be novel if validated against tables 2.1–2.3.
