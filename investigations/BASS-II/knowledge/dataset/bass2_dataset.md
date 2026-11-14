# BASS-II (PSI-25) — Dataset technical sheet for video processing

> Dataset archivist. Sources: `data/docs/*` (ReadMe/FAQ, SRD, Ops, Engineering Requirements, Summary Report NASA/TM-20210011385, Test Matrices, Fan calibration, Experimental table) and the API inventory `data/catalog/psi25_investigation.json`.
> Plain text of the documents for grep: `knowledge/dataset/raw_text/` (ReadMe, Ops, SRD, Summary_Report, Engineering_Requirements).
> Convention: **[doc]** = literal fact from an official document (with reference); **[inferred]** = archivist's deduction that should be verified when opening the files.

---

## 1. Executive summary (the minimum to get started)

| Item | Value | Source |
|---|---|---|
| Main video | Panasonic **WV-CP654** color camera (CCD 760 × 480), **30 fps** (NTSC 29.97), **side/edge-on** view through the front window via a mirror; **overlay** `FUEL AIR FAN RAD` + date/time. mp4 file (probed on B1): **H.264 720×480, 29.97 fps progressive, SAR 10:11** (non-square pixel) | Summary Report §1.2, §6.1.3, §7.1.3 [doc]; `video_format_probe.md` [measured] |
| Still camera | **Nikon D300s** 12.3 MP, 60 mm lens, report: 4320 × 2968 px; actual NEF: **4288 × 2848**; **top-down** view through the top window; ~**1 fps** (CL mode; T'ien ~1 image/1.2 s); exposure 1/10–1/4 s, f/2, ISO 1000 | Summary Report §1.2, §6.1.3, §7.1.3; Ops §4.4 [doc]; probe [measured] |
| Tunnel | Black anodized duct **7.6 × 7.6 cm** (cross-section), test section **17 cm**, rounded corners | Summary Report §1.2 [doc] |
| Maximum flow | ~**55 cm/s** without restrictors; ~**35 cm/s** with 2 restrictors | Summary Report §1.2 [doc] |
| Flow calibration | `U[cm/s] = 1.0066 × AIR_display` (duct centerline). Pot→display: `fan_display ≈ 38.2 + 8.38·pot`; `V = fan_display/10`. Pooled linear fit: 0 restr. `U ≈ 5.76·V − 15.6`; 1 restr. `U ≈ 3.96·V − 14.5`; 2 restr. `U ≈ 3.72·V − 13.7` (RMSE ≈ 3 cm/s; use the calibration **of the day**) | Fan calibration xlsx + own fit |
| Spatial scale | No published mm/px. Use known dimensions in the frame: rod diameter (6.35 / 9.525 / 12.7 mm), flat sample width (1 or 2 cm; T'ien: 1.2 / 2.2 cm exposed), exposed length ~10 cm (flat samples), sphere Ø 4 cm, duct 76 mm | see §5 |
| Tests | 126 runs (vs 103 planned); 129 rows in the experimental table; 115 test groups with files | Summary Report §1.1; inventory |
| Volume | **274.63 GB** in 694 files (main mp4 videos: 7.86 GB; 2ND_VIEW: 8.91 GB; Nikon image zips: 231 GB) | `files_inventory.csv` |

---

## 2. Hardware

### 2.1 Facility and wind tunnel
- Experiment inside the **Microgravity Science Glovebox (MSG)**, Destiny module, ISS. Free working volume (WV) **≈ 250 L** (Miller cites 255 L). [doc]
- Hardware inherited from **SPICE** (Smoke Point In Co-flow Experiment, STS-126) and from BASS-I. Components: flow duct, video camera, still camera, video/power boxes, **external control box** (fan, GN2, ignitor and GN2 enable, radiometer gain), plumbing and mounts. [doc]
- **Duct**: black anodized (low-reflection background), **7.6 × 7.6 × 17 cm**, rounded internal corners (Appendix D uses H = W = 7.5 cm). Front window (hinged; access to sample and ignitor; ignitor and N2 interlocks) and top window (replaced by a sample **mounting rail**; the Nikon looks through it). [doc]
- **Flow**: variable-speed fan upstream → (optional restrictors at the fan inlet) → **honeycomb flow straightener** → **TSI 8475 omnidirectional spherical anemometer** → inlet screen → test section → outlet with perforated copper plate + brass screen (heat rejection, soot deposition) → the flow turns 90° on exit. [doc]
- Inside the test section: N2 nozzle, **movable scale** ("movable scale"/"deployed scale"), **Oriel 71768** thermopile radiometer with CaF2 window (0.13–11 µm) in the upper rear downstream corner, looking upstream. [doc]
- **Restrictors** ("Fan Flow Constrictor"): perforated plates attached to the fan inlet screen to increase pressure drop and reduce the flow range. **0 = maximum flow** (≈55 cm/s), **2 = minimum** (≈35 cm/s max.); 1 restrictor ≈ 33–40 cm/s max. depending on the day. [doc + cal.]
- The fan shuts off at a finite voltage (**~3.8 V**, display 38); the control box was modified so that the pot minimum stops the fan (extinction method by flow cutoff). [doc]

### 2.2 Ignition
- Hot-wire ignitor **Kanthal A-1, 29 gauge**, coil/hook, nominal resistance **0.8–1 Ω**, **3.5–3.8 A** (Olson: 1 Ω, 4 A circuit). Deployed by the astronaut pulling the **IGNITOR** lever; placed **≤ 1 mm** from the sample edge without touching. Flat samples with **integral ignitor** ("Integral" in the tables). [doc]
- Ignition times: typically < 40 s at high O2; up to 230 s (and > 500 s without success) at low O2. The crew can turn the ignitor off/on several times ("ignition attempts"). The ignitor **glows** (saturation/glare) in the video during ignition. [doc]

### 2.3 Gas / O2 vitiation
- ISS GN2 via hose from the MSG rear wall; **MKS 179A** flow meter (< 0.5 LPM; 0–500 SCCM); enters through a nozzle just downstream of the fan. During dilution the fan runs at maximum (> 100 LPM) to mix. **CSTR** model to set N2 time/flow rate (V = 0.25 m³, r ≤ 0.0005 m³/min). Fill 25–225 min (Ops) / 1–3 h (Report). Initial O2 from **~13.6 % to 22.2 %**. [doc]
- MSG Air Circ **OFF** during fill and test; 3 min purge after every 10 burns and between days. [doc]

### 2.4 Gas sensors (spot readings before/after each test, not time series)
- **CSA-CP** (Compound Specific Analyzer-Combustion Products): O2 (0.1 % resolution; **no on-orbit calibration** → corrected with a daily offset using the **MCA**, the ISS mass spectrometer), CO (0–1000 ppm, 1 ppm; "OR" = over range > 1000 ppm), also HCN and HCl. [doc]
- **CDM** (Carbon Dioxide Monitor): CO2 0–5 %, 0.1 % resolution. [doc]
- Matrix columns "Calibrated initial/final O2" = CSA-CP reading + MCA offset. [doc]

### 2.5 Radiometer
- Uncalibrated thermopile; **relative only** (flame intensity, dynamics, pre-extinction oscillations ~1.1 Hz on Olson rods). Adjustable gain (**1000 / 250 / 50 / 10**); the crew adjusts it so RAD ≤ 1.0 without saturating. Shown in the overlay; display rate **5 Hz** (ReadMe) — the SRD states SPICE acquisition at **4 Hz**. **Gain changes mid-test** ("250>50>250") break signal continuity. [doc]

### 2.6 Acceleration
- Nearby SAMS; tests scheduled to avoid thrusters/docking. [doc]

---

## 3. Cameras and file types

### 3.1 Main video (`..._TEST_<id>.mp4`) — Panasonic camera with overlay
- Panasonic **WV-CP654** (color CCD, NTSC), 760 × 480 px array; **30 fps** (29.97) according to Olson and T'ien. Looks at the front window via a turning mirror → **side view**: for flat samples it is **edge-on**, for rods it is a side view of the axis. The forced flow goes **upward** in the report figures (may be rotated in the files; verify). [doc]
- Recorded on digital tapes by **MSG Video Recorder 1** and shown on **MSG Video Monitor 1** (the monitor that shows AIR and FAN in the overlay, Ops §11, Fig. 18). [doc]
- **Overlay** (top strip, rows ≈ 25–85 px, white text; labels `FUEL  AIR  FAN  RAD` + `MM/DD/YY HH:MM:SS`): according to the report it shows N2 flow rate (cm³/min) → **`FUEL`** (the GN2 switch is called FUEL in Ops), **anemometer** reading (cm/s, integer, ~1 min response) → **`AIR`** (not the restrictor), **fan voltage ×10** (max. 122 = 12.2 V) → **`FAN`**, radiometer signal → **`RAD`**. **Overlay date = actual date + 1 day** (leap-year bug). Mask before segmenting; can be read by OCR for FAN/AIR/RAD time series. [doc + probe]
- Measured format (`video_format_probe.md`, B1): H.264 High, **720×480, 29.97 fps, progressive**, yuv420p, ~1 Mb/s, AAC audio; **SAR 10:11** → multiply horizontal pixel distances by 10/11 (or rescale to 654×480) before converting to mm. B1 = 1343 frames (44.8 s).
- Gain/exposure: the report does not document AGC; the WV-CP654 has automatic AGC/ELC **[inferred: treat pixel intensity as non-radiometric and not comparable across tests]**. The flame core **saturates** (V = 255; magenta/pink flame on thin PMMA). Faint blue flames at low flow/O2 are hard to see in this video (T'ien). [doc + measured + inferred]

### 3.2 `..._2ND_VIEW.mp4` — second view
- The documents do not define it. Tapes were recorded on **two** recorders (MSG Video Recorder 1 and 2, Ops §12); the main video with overlay corresponds to Monitor/Recorder 1. Ops (§4 NOTE) states that **the Nikon is shown on MSG Video Monitor 2**; however, empirical probing shows that this Nikon review screen is what the `Still_Sequence` files contain (§3.3). Therefore 2ND_VIEW is **[unverified]** the other signal recorded in parallel — probably a video camera of the MSG itself/another angle, or the Nikon live output. 2ND_VIEW files are usually somewhat larger than the main one (same duration). **Open one before using it**; meanwhile treat it as an auxiliary view with no guaranteed overlay.
- Summary: **calibratable side view with telemetry = main video**; **high-resolution top-down view = Nikon NEF** (zips); 2ND_VIEW = auxiliary, pending identification.

### 3.3 `..._Still_Sequence.mp4`
- **Measured**: it is a **recording of the Nikon D300s review screen** (thumbnail + histogram + EXIF, e.g. `M 1/10 F2 ISO1000`, `4288x2848 RAW`, counter `192/208`) → not usable for measuring the flame, but useful to know **shot timestamps and exposure parameters**. The Nikon shoots in **CL mode at 1 fps** while the control box SHUTTER is locked (max. 100 images per lock; in practice ~1 image/1–1.2 s), and includes **post-burn** photos with a Mini-Maglite. [doc + measured]
- Typical Nikon configuration (Appendix A): Release **CL**, exposure mode **A** (aperture priority) with **−3 to −4 EV** compensation, no bracketing, "F stop" noted as **F2**, **ISO 1000**, shutter hold **Cont**, no filter (N). T'ien: exposures 1/8–1/4 s (faint flames well exposed but with motion blur). Before the first test of the day a **dark frame calibration** was done with the cap on (9-frame bracket). [doc]

### 3.4 `GMT2014_<ddd>_BASS_S<sample><M|L>_TP<test>.zip` (and `iss0XXeNNNNNN.zip`)
- Large zips (0.1–3.3 GB) with the full-resolution **Nikon D300s RAW `.NEF` images** (**4288 × 2848**, measured on TPO5b; the report says 4320 × 2968) of that test point (TP = test point). Inside, the NEFs are named with the ISS ID (`iss040e071087.NEF`). Decodable with `rawpy` (`half_size=True` → 2160×1434). At 1/10 s, f/2, ISO 1000 they are noisy. The repeated prefix `..._BASS_D300sGMT2014_...` is a folder-name artifact (camera model). [measured]
- `iss038e0NNNNN.zip` / `iss040e0NNNNN.zip`: same Nikon images, but named with the **ISS photo archive ID** (expedition 38 or 40 + frame no.). Used mainly in B tests (Bhattacharjee) and some P/T. The test is identified only by the inventory subcategory.

### 3.5 `..._ProofSheet.pdf`
- **Contact sheet** (thumbnails) of the Nikon images of the test point; 0.1–1.6 MB. Useful for previewing without downloading the zip. [inferred from name/size]

### 3.6 `... original videos.zip` (also "orginal", "orignial", "originla", "vidoes")
- Contains the **original video segments** (before conversion/concatenation to mp4, e.g. `.ts` captures from downlink or tape) from which the main mp4 and 2ND_VIEW were derived. Size ~2–4× the mp4. **[inferred; unverified]**. Only needed if the mp4 has artifacts.

### 3.7 LOS (`..._LOS_Portion_HHMM-HHMM.mp4`, `..._LOS_Portion_HHhMMmSSs_to_end_of_test.mp4`, `M3-rack-video-during-LOS.mp4`, etc.)
- **LOS = Loss Of Signal** (loss of the ISS–ground Ku-band link). During LOS there was no live video; those segments were recovered later from the onboard tapes (the numbers are the GMT time window of the segment) or recorded with alternative cameras: **rack video**, **over-the-shoulder view**, **lab camera**, `experimentvideo-LOS` (Miller M3, M10). **[inferred: LOS is standard ISS operations terminology; the documents do not define it]**. Some tests (P18, M3) **only** have LOS material.

### 3.8 Other
- `O5a-all.mp4` (Part-1+Part-2 concatenation of O5a), `..._Part-1/2` (split test), `..._First/Second_Ignition_Attempt(s)` (separate ignition attempts), `T16-shifted-video` (time-shifted version), `vlc-record-...T21.ts-.mp4` (short clips recorded with VLC), `T##-post-burn-picture*.mp4`, `Flame-Blowoff-BASS-GMT177-Test-O7.mp4` (highlighted blowoff clip). The ReadMe mentions a *Misc video* folder with backup recordings and crew operations recordings.

---

## 4. Fan calibration (fan display → velocity)

Source: `Reference Data_Fan calibration data.xlsx` (exported to `data/catalog/fan_calibration_Fan_Calibration_data.csv`; tidy version `data/catalog/fan_calibration_tidy.csv`; fits `fan_calibration_fits_by_day.csv` and `fan_calibration_fits_pooled.csv`).

- At the end of each operations day the crew set the pot to 10, 8, 6, 4, 2, (1, 0.5), 0 and recorded the stabilized (~1 min) **Fan display** and **Air display**, for that day's restrictor configuration (Ops §11).
- Variables: **Pot** (control box dial, 0–10), **Fan display** = 10 × fan voltage (38 → 122), **Air display** = TSI anemometer (cm/s, integer, effective resolution ±0.5 cm/s, ~1 min response).
- Formulas from the xlsx itself: `Fan V = Fan_display / 10` and **`U [cm/s] = 1.0066 × AIR`** — *"Based on SPICE fan calibration data at 56 mm downstream, 36 mm from bottom (centerline)"* → corrects the anemometer reading to the velocity on the **duct axis** in the test section.
- Pot ↔ display relation (all days, max. residual 0.5): **`fan_display ≈ 38.16 + 8.384 · pot`** (pot 10 → 122; pot 1 → 46.5; pot 0.5 → 42; pot 0.35 → ≈ 41).
- xlsx note: the fan **turns off above 3.8 V**; **do not use the (3.8 V, 0 cm/s) point** for interpolation.

### 4.1 Typical table (median across days; U = 1.0066·AIR, cm/s)

| Pot | Fan display | 0 restr. U median (min–max) | 1 restr. U median (min–max) | 2 restr. U median (min–max) |
|---|---|---|---|---|
| 10 | 122 | 54.9 (43.3–59.4) | 33.2 (27.7–40.3) | 33.7 (20.1–40.3) |
| 8 | 105–105.5 | 45.8 (42.3–49.3) | 27.2 (23.2–31.2) | 27.2 (15.1–31.2) |
| 6 | 88–88.5 | 36.2 (33.2–39.3) | 20.1 (17.6–23.2) | 20.1 (10.1–23.2) |
| 4 | 72 | 26.2 (24.2–28.2) | 13.1 (11.6–16.1) | 13.1 (7.0–16.1) |
| 2 | 55 | 16.1 (14.1–17.1) | 7.0 (6.0–9.1) | 7.0 (3.0–9.1) |
| 1 | 46.5–47 | 10.6 (10.1–11.1) | 4.0 (3.0–5.0) | 4.4 (0–5.8) |
| 0.5 | 42 | — | 2.0 | 1.0 (0–3.8) |
| 0 | 38 | 0 | 0 | 0 |

(The xlsx example column A–E, GMT "2014-043", has much lower values — 29/21/18 cm/s at pot 10 — and is excluded from the fits: it looks like a didactic example, possibly from another configuration.)

### 4.2 Pooled linear fits `U = a·V + b` (V = fan_display/10, only points with AIR > 0)

| Restrictors | a (cm/s/V) | b (cm/s) | V0 = −b/a | n | RMSE |
|---|---|---|---|---|---|
| 0 | 5.756 | −15.58 | 2.71 V | 35 | 3.1 |
| 1 | 3.959 | −14.50 | 3.66 V | 31 | 2.7 |
| 2 | 3.717 | −13.71 | 3.69 V | 134 | 3.6 |

**Recommended recipe** for converting the overlay to velocity:
1. Read `Fan display` (10×V) from the overlay (or the pot noted in the matrix → display with the pot↔display formula).
2. Look up in `fan_calibration_tidy.csv` the **same GMT day** and **same number of restrictors** as the test (matrix column Flow restrictor); interpolate U vs V **piecewise linearly** between that day's points (excluding the 3.8 V/0 point).
3. If there is no calibration for that day/configuration, use the nearest day or the pooled fit (uncertainty ±3–4 cm/s; larger at < 5 cm/s).
4. The overlay **Air display** is only reliable after ≥ 1 min at constant flow; during ramps use the fan display.
- Significant day-to-day variation with 2 restrictors (max 20–40 cm/s): GMT 45, 50, 209 and 210 give ~20–22 cm/s at pot 10 (soot on screens; there are "post soot cleaning" calibrations). The GMT 2014-210 column with "0 restrictors" exactly duplicates the 2-restrictor values → marked `suspect=1` in the tidy file.

---

## 5. Spatial scale references

There is no published mm/px calibration for any camera. The video field of view is fixed (SRD), but the sample position is adjusted per test ("sample distance"), so **calibrate per test** with objects of known size:

| Reference | Dimension | Notes |
|---|---|---|
| Duct cross-section | 76 × 76 mm (7.6 cm) | If the walls/window are visible in the side video |
| Test section length | 170 mm | |
| PMMA rods (Olson, Fernández-Pello) | Ø **6.35 / 9.525 / 12.7 mm** (1/4", 3/8", 1/2"); radius 0.318/0.476/0.635 cm | Best reference in the side video. Length **57.15 mm** (F-P) / **59 mm** (Olson, Lo = 5.9 cm); hemispherical tip |
| PMMA films (Bhattacharjee) | **20 or 10 mm** wide × ~**95 mm** long; thickness 0.1–0.4 mm | Top view (Nikon). In side view they are almost a line |
| PMMA slabs (Miller) | **10 cm** long × **1 or 2 cm** (2.2 cm per Fig. 5.4) wide; 1–5 mm thick; 1 or 2 sides | |
| SIBAL (T'ien) | exposed width **1.2 or 2.2 cm**, exposed length **10 cm**, thickness 0.32 mm | Stainless steel sample holder |
| Nomex III (Ferkul) | 2 cm wide | |
| PMMA sphere (T'ien) | sphere section **Ø 4 cm** | |
| Ignitor wire | Kanthal 29 gauge (Ø ≈ 0.29 mm) | Only as a position reference |
| Duct movable scale | "movable scale" / "deployed scale" | Ops: with exposure optimized for the flame it **may not be visible** |
| Bhattacharjee (SDSU analysis) | dots every **6 mm** overlaid in post-processing | Not a physical fiducial |

Formula: `px_per_mm = L_px / L_mm` measured on the reference in a frame with the sample visible (before ignition or with illumination). In the main video first correct the non-square pixel: `x_corr = x_px · 10/11` (SAR 10:11). In the Nikon, `L_px` on 4288×2848 (NEF).

---

## 6. Sample materials

| PI | Material / geometry | Notes |
|---|---|---|
| Bhattacharjee (B) | **Thin** PMMA films 0.1 / 0.2 / 0.3 / 0.4 mm, 2 cm (and 1 cm) wide | Opposed flow; types A–E (S1183MFA1110-1..4, 1115-1) |
| Ferkul (F) | Natural **Nomex III** (2 cm) and **Japan wax candle** (F4) | Complete BASS-I |
| Miller (M) | **Thick PMMA slabs** 1–5 mm, 1 or 2 cm wide, burning **1 side or 2 sides** | Opposed flow, 3–20 cm/s |
| Olson (O) | **PMMA rods** (mostly **clear**) 1/4", 3/8", 1/2"; 2 black | Ignition at the **upstream** end → **stagnation-point / concurrent-flow** flame |
| Fernández-Pello (P) | **PMMA rods** (mostly **black**, soot-blackened PMMA) 1/4", 3/8", 1/2" | Ignition at the **downstream** end → **opposed-flow spread** |
| T'ien (T) | **SIBAL** fabric (75 % cotton / 25 % fiberglass; 0.32 mm; 18.2 mg/cm²), 1 or 2 cm; **4 cm PMMA spherical section** (1 sample, T3/T7) | Concurrent flow; growth and quenching |

Manifest (SRD p. 4–5): 8+4+2×7 films 2 cm; 4+5 films 1 cm; 14/6/2 black rods; 12/4/2 clear rods; 5 one-sided slabs; 1 sphere; 15 SIBAL 2 cm + 4 SIBAL 1 cm; 3 Nomex; 27 ignitors (3 types), 8 flash cards of 4 GB.

---

## 7. Procedure and timeline of a test (Ops + Report)

1. Install sample in the Sample Frame (orientation per "Ignition Type": leading or trailing edge) and ignitor at ≤ 1 mm; close window. Configure Nikon (date = Monitor 1 date ±5 s; CL 1 fps; dark frame if first test of the day). Install/remove restrictors.
2. (If reduced O2) Air Circ OFF, fan at 10, GN2 ON → dilution 25–225 min; initial CSA-CP/CDM readings; GN2 OFF; fan to 0.
3. **Flame test** (with S/Ku link so the PI can direct live): set initial flow (typically **5 cm/s**, sometimes 10), IGN ENA ON, **ignitor lever** (the ignitor glows) until a flame is seen on Monitor 1 (up to 60 s or more) → **SHUTTER locked** (Nikon at 1 fps) → retract ignitor.
4. Adjust radiometer gain (RAD ≤ 1.0).
5. After ~1 min of stable burning, the PI requests **flow changes**: most tests **step the flow down** (waiting for steady state at each step, several minutes; quench tests up to **28 min**) **until quenching extinction**; others **step the flow up** every 5–10 s until **blowoff**; others alternate (e.g. P18/P20/P23/P24: pot 1,2,1,2…). Final extinction: fan to 0 or GN2.
6. IGN/GN2 OFF, fan to maximum, release SHUTTER; final CSA-CP/CDM readings; **post-burn photo** with Mini-Maglite; cool-down ≥ 9 min; purge every 10 burns.
7. End of day: **fan calibration** (§4) and video tape change (Recorders 1 and 2).

Implication for the analysis: a single video contains **several flow regimes**; the matrix "Fan display" column gives the sequence of steps (without times). Change instants must be detected in the overlay (jump in the FAN value).

---

## 8. Naming conventions

| Pattern | Meaning |
|---|---|
| `BASS_GMT<ddd>_SAMPLE_<nnn>_TEST_<X##[a|b]>.mp4` | Main video. `ddd` = GMT 2014 day of year (**actual** date, e.g. GMT50 = 19-Feb-2014); `nnn` = sample no.; `X##` = test (PI initial + initial matrix no.); `a/b` = several runs of the same sample on the same day. Variants: `TESTB15` (no underscore), `sample139_test-T16`, `GMT_100` |
| `..._2ND_VIEW.mp4`, `..._Still_Sequence.mp4`, `..._LOS_Portion_...`, `..._Part-N`, `..._First/Second_Ignition_Attempt(s)` | see §3 |
| `GMT2014_<ddd>_BASS_S<nnn><M|L>_TP<X##[a|b]>[_ProofSheet.pdf|.zip|_1.zip|-1.zip]` | Nikon images / proof sheet. TP = test point. Suffix `_1`, `_2`, `-1` = split zip |
| `iss0<EE>e<NNNNNN>.zip` | Nikon images with ISS photo archive ID (expedition EE) |
| Prefix `PSI-25_Raw Data_` | added by the PSI repository |
| Sample suffix `m`/`M`/`L` (e.g. 153m, 205M, 819L) | Meaning undocumented (Feb-2014 samples do not carry it in the table but do in the zips: S147M). Normalize to digits |
| API subcategory `Reduced Gravity/<PI>/<test>` | Groups files by test (without a/b) |

GMT: the ISS uses GMT; the overlay shows **GMT-year-day-time** but with **+1 day** (the onboard computer did not account for the leap year). File names use the actual day.

---

## 9. PIs and science objectives

| Initial | PI | Institution | Objective |
|---|---|---|---|
| B | Subrata **Bhattacharjee** | SDSU | **Opposed-flow** spread over **thin** PMMA: effect of thickness, width, flow and O2; thermal/radiative regime; **critical radiative extinction velocity** (~2.6 cm/s for 100 µm, ~4 cm/s for 200 µm). Flame-edge tracking with Flame Analyzer (MATLAB) on the top-down photos |
| F | Paul **Ferkul** (Project Scientist, NCSER/USRA) | | Complete BASS-I: Nomex III and candle |
| M | Fletcher **Miller** (+ I. Wichman, MSU) | SDSU | **Thick** PMMA in opposed flow, 1 and 2 sides; O2–velocity flammability maps; comparison with the Narrow Channel Apparatus (NCA); tracking with Spotlight-16 |
| O | Sandra **Olson** (overall PI, NASA GRC) | GRC | PMMA rods in **axial stagnation/concurrent flow**: U-shaped flammability boundary (quenching at low flow, **blowoff** at high flow), standoff, 1.1 Hz pre-extinction oscillations, ignition delay |
| P | Carlos **Fernández-Pello** (+ S. Link) | UC Berkeley | PMMA rods (black) in **opposed flow**: spread rate vs flow, O2 and diameter; comparison with 1g |
| T | James **T'ien** | CWRU | SIBAL fabric in **concurrent flow**: growth, limiting length, steady spread and **quenching**; PMMA spherical section |

General hypothesis: with adequate ventilation, materials in microgravity burn as well as or better than in 1g; variables: ambient O2, ventilation velocity, fuel type/thickness/geometry.

---

## 10. Known data caveats (ReadMe/FAQ, Report, inspection)

1. **Overlay date +1 day** relative to the actual date (leap-year bug). [ReadMe]
2. **O2**: the sensor was uncalibrated; "calibrated" values = daily offset with MCA. O2 **decreases during the test** (Miller assumes a linear profile between initial and final). [ReadMe, Report]
3. **Air display**: ~1 min response and integers only (±0.5 cm/s) → unreliable in transients and < 2 cm/s. Use fan display + calibration of the day. [ReadMe, Report]
4. **Radiometer** uncalibrated, gain changed mid-test in some tests; relative only. [ReadMe]
5. **CO**: "OR"/"over" = > 1000 ppm; values −1/−2/−3 ppm = zero offset. [ReadMe]
6. **Total frames** includes the post-burn photos; "video" in O20–O22 = no photos. [ReadMe/matrix]
7. Anomalies: GMT 51 the front window overheated/bubbled due to a leak (long thick-slab test, M5), repaired GMT 86/91; after GMT 167 the video cut out (camera cable), repaired GMT 170; GMT 205 a steam jet fouled the window (cleaned GMT 209). [Appendix C] → possible degraded images near those dates.
8. Soot: "post soot cleaning" calibrations (GMT 49, 50, 188, 212); maximum flow with 2 restrictors drops to ~20–22 cm/s on GMT 45/50/209/210.
9. Errors in the tables (see `test_matrix_notes.md`): 2018 dates in T9/T18 (should be 2014-06-24, GMT 175); O10 with GMT 213 but date 7/22 and files GMT203 → **GMT 203**; shifted columns in B2, P22a/P22b, T28a/T28b (final O2 1.6 / 0.6 / 39.1 / 0.9 / 40.4 impossible); "Air display" sometimes contains pots.
10. Naming/archive errors: **B3** video archived under subcategory B1; **B17** files (sample 175) named `TESTB15`; **O16** zip named `TPP16`; **P8**: matrix says sample 197m (same as P4) but the proof sheet says S198M. The inventory resolves test_id by arbitrating with the sample number.
11. Tests without files in the repository: **F2, O20, O21, O22** (O20–22 are from 2016-02-26). Tests without main video: M3, P18 (LOS only), O10, O17, T20 (2ND_VIEW only), P8, P10 (Nikon images only). O16 only has ignition attempts (did not burn).
12. **Reused** samples (a/b on the same day and others: 174m in B14/B21; 176m in B18/B22; 133m in T9/T23/T24; 144m in T20/T28; 197m in P4/P8…). Reused samples were re-ignited at the burnout point and often had little usable length.
13. "BASS-II data FAQ.docx" (removed from the repo) has the same resource_id and size as the ReadMe → **the ReadMe is the FAQ**.
14. During LOS, segments of the live video are missing; some were published separately (`LOS_Portion`).

---

## 11. Inventory and analysis candidates

- Full inventory: `data/catalog/files_inventory.csv` (694 rows; columns `pi, test_id, file_name, kind, ext, size_bytes, gmt_day, sample_id, subcategory`). `gmt_day`/`sample_id` are extracted from the name; if missing (`iss…` zips), they are filled from the experimental table.
- Candidate per test: `data/catalog/best_candidates_per_test.csv`.

### 11.1 Volume by type

| kind | files | GB |
|---|---|---|
| main_video | 122 | 7.86 |
| second_view | 97 | 8.91 |
| still_sequence | 53 | 0.47 |
| los_clip | 15 | 0.31 |
| original_videos_zip | 115 | 25.75 |
| raw_images_zip | 149 | 231.00 |
| proofsheet | 125 | 0.12 |
| other (docs + loose clips) | 18 | 0.22 |
| **Total** | **694** | **274.63** |

By PI (GB / files / tests): Bhattacharjee 26.15 / 118 / 22 · Ferkul 3.33 / 15 / 3 · Fernández-Pello 79.89 / 141 / 23 · Miller 74.48 / 119 / 20 · Olson 58.84 / 130 / 19 · T'ien 31.88 / 162 / 28.

**Downloading only the best video of each test ≈ 7.1 GB** (versus 274.6 GB total).

### 11.2 Best candidate per test

Criterion: main video (side view with flow/radiometer overlay) covering the complete test; ignition attempts and parts are excluded if a complete one exists; among several, the smallest. If there is no main video, 2ND_VIEW or a LOS clip is used. Column "Total test" = everything published for that test (including image zips).

| Test | PI | GMT | Sample | Best candidate (main video) | MB | 2ND_VIEW | Still_Seq | Total test (GB) |
|---|---|---|---|---|---|---|---|---|
| B1 | Bhattacharjee | 50 | 147 | `BASS_GMT50_SAMPLE_147_TEST_B1.mp4` | 5.8 | no | yes | 0.68 |
| B2 | Bhattacharjee | 50 | 155 | `BASS_GMT50_SAMPLE_155_TEST_B2.mp4` | 7.9 | no | no | 0.17 |
| B3 | Bhattacharjee | 50 | 148 | `BASS_GMT50_SAMPLE_148_TEST_B3.mp4` | 8.0 | no | yes | 0.59 |
| B4 | Bhattacharjee | 50 | 159 | `BASS_GMT50_SAMPLE_159_TEST_B4.mp4` | 12.6 | no | yes | 0.96 |
| B5 | Bhattacharjee | 50 | 156 | `BASS_GMT50_SAMPLE_156_TEST_B5.mp4` | 11.1 | no | yes | 0.75 |
| B6 | Bhattacharjee | 188 | 153 | `BASS_GMT188_SAMPLE_153_TESTB6.mp4` | 7.6 | yes | yes | 0.97 |
| B7 | Bhattacharjee | 50 | 161 | `BASS_GMT50_SAMPLE_161_TEST_B7.mp4` | 16.7 | no | yes | 1.19 |
| B8 | Bhattacharjee | 188 | 157 | `BASS_GMT188_SAMPLE_157_TESTB8.mp4` | 18.2 | yes | yes | 1.47 |
| B9 | Bhattacharjee | 188 | 154 | `BASS_GMT188_SAMPLE_154_TESTB9.mp4` | 5.0 | yes | no | 0.61 |
| B10 | Bhattacharjee | 188 | 173 | `BASS_GMT188_SAMPLE_173_TESTB10.mp4` | 17.5 | yes | yes | 1.56 |
| B11 | Bhattacharjee | 188 | 158 | `BASS_GMT188_SAMPLE_158_TESTB11.mp4` | 17.5 | yes | yes | 1.64 |
| B12 | Bhattacharjee | 50 | 160 | `BASS_GMT50_SAMPLE_160_TEST_B12.mp4` | 13.1 | no | yes | 1.02 |
| B13 | Bhattacharjee | 188 | 162 | `BASS_GMT188_SAMPLE_162_TESTB13.mp4` | 29.2 | yes | yes | 2.44 |
| B14 | Bhattacharjee | 183 | 174 | `BASS_GMT183_SAMPLE_174_TESTB14.mp4` | 3.1 | yes | no | 0.55 |
| B15 | Bhattacharjee | 188 | 149 | `BASS_GMT188_SAMPLE_149_TESTB15.mp4` | 10.7 | yes | yes | 0.93 |
| B16 | Bhattacharjee | 183 | 150 | `BASS_GMT183_SAMPLE_150_TESTB16.mp4` | 11.8 | yes | no | 1.30 |
| B17 | Bhattacharjee | 183 | 175 | `BASS_GMT183_SAMPLE_175_TESTB15.mp4` | 21.1 | yes | no | 2.55 |
| B18 | Bhattacharjee | 183 | 176 | `BASS_GMT183_SAMPLE_176_TESTB18.mp4` | 14.5 | yes | yes | 2.04 |
| B19 | Bhattacharjee | 183 | 151 | `BASS_GMT183_SAMPLE_151_TESTB19.mp4` | 10.5 | yes | yes | 1.26 |
| B20 | Bhattacharjee | 183 | 152 | `BASS_GMT183_SAMPLE_152_TESTB20.mp4` | 10.3 | yes | yes | 1.47 |
| B21 | Bhattacharjee | 216 | 174 | `BASS_GMT216_SAMPLE_174_TEST_B21.mp4` | 20.1 | yes | no | 1.12 |
| B22 | Bhattacharjee | 216 | 176 | `BASS_GMT216_SAMPLE_176_TEST_B22.mp4` | 13.1 | yes | no | 0.90 |
| F1 | Ferkul | 50 | 227 | `BASS_GMT50_SAMPLE_227_TEST_F1.mp4` | 10.8 | no | yes | 0.69 |
| F3 | Ferkul | 213 | 229 | `BASS_GMT213_SAMPLE_229_TEST_F3.mp4` | 13.1 | yes | no | 0.49 |
| F4 | Ferkul | 175 | 039,39 | `BASS_GMT175_SAMPLE_039_TEST_F4.mp4` | 44.0 | yes | no | 2.15 |
| M1 | Miller | 51 | 222 | `BASS_GMT51_SAMPLE_222_TEST_M1.mp4` | 57.9 | no | yes | 3.86 |
| M2 | Miller | 51 | 224 | `BASS_GMT51_SAMPLE_224_TEST_M2.mp4` | 212.0 | no | yes | 4.01 |
| M3 | Miller | 192 | 226 | `M3-rack-video-during-LOS.mp4` (no main video; los_clip used) | 11.5 | no | no | 2.55 |
| M4 | Miller | 212 | 171 | `BASS_GMT212_SAMPLE_171_TEST_M4.mp4` | 153.4 | yes | no | 3.94 |
| M5 | Miller | 51 | 167 | `BASS_GMT51_SAMPLE_167_TEST_M5.mp4` | 193.5 | no | yes | 5.80 |
| M6 | Miller | 212 | 163 | `BASS_GMT212_SAMPLE_163_TEST_M6.mp4` | 144.9 | yes | no | 3.82 |
| M7 | Miller | 192 | 177 | `BASS_GMT192_SAMPLE_177_TEST_M7.mp4` | 110.0 | yes | no | 4.11 |
| M8 | Miller | 192 | 178 | `BASS_GMT192_SAMPLE_178_TEST_M8.mp4` | 163.9 | yes | no | 4.47 |
| M9 | Miller | 192 | 179 | `BASS_GMT192_SAMPLE_179_TEST_M9.mp4` | 97.7 | yes | no | 2.20 |
| M10 | Miller | 204 | 180 | `BASS_GMT204_SAMPLE_180_TEST_M10.mp4` | 210.0 | yes | no | 3.53 |
| M11 | Miller | 192 | 181 | `BASS_GMT192_SAMPLE_181_TEST_M11.mp4` | 172.6 | yes | no | 3.80 |
| M12 | Miller | 212 | 165 | `BASS_GMT212_SAMPLE_165_TEST_M12.mp4` | 125.7 | yes | no | 3.70 |
| M13 | Miller | 212 | 169 | `BASS_GMT212_SAMPLE_169_TEST_M13.mp4` | 142.3 | yes | no | 3.87 |
| M14 | Miller | 51 | 223 | `BASS_GMT51_SAMPLE_223_TEST_M14.mp4` | 188.0 | no | yes | 3.79 |
| M15 | Miller | 188 | 225 | `BASS_GMT188_SAMPLE_225_TESTM15.mp4` | 142.3 | yes | no | 2.68 |
| M16 | Miller | 204 | 164 | `BASS_GMT204_SAMPLE_164_TEST_M16.mp4` | 112.2 | yes | no | 4.25 |
| M17 | Miller | 196 | 166 | `BASS_GMT196_SAMPLE_166_TEST_M17.mp4` | 188.5 | yes | no | 4.97 |
| M18 | Miller | 196 | 168 | `BASS_GMT196_SAMPLE_168_TEST_M18.mp4` | 154.7 | yes | no | 2.94 |
| M19 | Miller | 204 | 170 | `BASS_GMT204_SAMPLE_170_TEST_M19.mp4` | 183.3 | yes | no | 3.35 |
| M20 | Miller | 213 | 172 | `BASS_GMT213_SAMPLE_172_TEST_M20.mp4` | 170.0 | yes | no | 2.85 |
| O1 | Olson | 49 | 207 | `BASS_GMT49_SAMPLE_207_TEST_O1.mp4` | 34.2 | no | yes | 0.74 |
| O2 | Olson | 49 | 204 | `BASS_GMT49_SAMPLE_204_TEST_O2.mp4` | 31.9 | no | yes | 3.07 |
| O3 | Olson | 164 | 205 | `BASS_GMT164_SAMPLE_205_TEST_O3a.mp4` (several runs/videos: O3a, O3b; see inventory) | 23.5 | yes | yes | 3.85 |
| O4 | Olson | 189 | 216 | `BASS_GMT189_SAMPLE_216_TEST_O4.mp4` | 146.7 | yes | no | 3.73 |
| O5 | Olson | 202 | 220 | `BASS_GMT202_SAMPLE_220_TEST_O5b.mp4` | 27.2 | yes | yes | 2.79 |
| O6 | Olson | 177 | 206 | `BASS_GMT177_SAMPLE_206_TEST_O6.mp4` | 86.8 | yes | no | 3.65 |
| O7 | Olson | 177 | 214 | `BASS_GMT177_SAMPLE_214_TEST_O7.mp4` | 87.6 | yes | no | 3.69 |
| O8 | Olson | 177 | 208 | `BASS_GMT177_SAMPLE_208_TEST_O8a.mp4` (several runs/videos: O8a, O8b; see inventory) | 51.1 | yes | no | 4.31 |
| O9 | Olson | 177 | 209 | `BASS_GMT177_SAMPLE_209_TEST_O9.mp4` | 61.1 | yes | no | 2.33 |
| O10 | Olson | 203 | 210 | `BASS_GMT203_SAMPLE_210_TEST_O10_2ND_VIEW.mp4` (no main video; second_view used) | 116.4 | yes | yes | 2.50 |
| O11 | Olson | 189 | 184 | `BASS_GMT189_SAMPLE_184_TEST_O11.mp4` | 120.8 | yes | no | 3.92 |
| O12 | Olson | 189 | 217 | `BASS_GMT189_SAMPLE_217_TEST_O12.mp4` | 58.4 | yes | no | 1.08 |
| O13 | Olson | 202 | 221 | `BASS_GMT202_SAMPLE_221_TEST_O13b.mp4` (several runs/videos: O13a, O13b; see inventory) | 29.5 | no | yes | 3.44 |
| O14 | Olson | 213 | 183 | `BASS_GMT213_SAMPLE_183_TEST_O14.mp4` | 110.4 | yes | no | 3.85 |
| O15 | Olson | 209 | 218 | `BASS_GMT209_SAMPLE_218_TEST_O15a.mp4` (several runs/videos: O15a, O15b; see inventory) | 78.3 | yes | no | 6.77 |
| O16 | Olson | 210 | 219 | `BASS_GMT210_SAMPLE_219_TEST_O16_Second_Ignition_Attempt.mp4` | 20.8 | yes | no | 0.34 |
| O17 | Olson | 203 | 211 | `BASS_GMT203_SAMPLE_211_TEST_O17_2ND_VIEW.mp4` (no main video; second_view used) | 154.1 | yes | yes | 2.41 |
| O18 | Olson | 209 | 212 | `BASS_GMT209_SAMPLE_212_TEST_O18.mp4` | 75.1 | yes | yes | 2.47 |
| O19 | Olson | 213 | 213 | `BASS_GMT213_SAMPLE_213_TEST_O19.mp4` | 109.7 | yes | no | 3.91 |
| P1 | Fernandez-Pello | 167 | 185 | `BASS_GMT167_SAMPLE_185_TEST_P1.mp4` | 53.0 | yes | yes | 3.92 |
| P2 | Fernandez-Pello | 167 | 188 | `BASS_GMT167_SAMPLE_188_TEST_P2.mp4` | 56.6 | yes | yes | 3.90 |
| P3 | Fernandez-Pello | 167 | 215 | `BASS_GMT167_SAMPLE_215_TEST_P3a.mp4` (several runs/videos: P3a, P3b; see inventory) | 60.7 | yes | yes | 8.25 |
| P4 | Fernandez-Pello | 184 | 197 | `BASS_GMT184_SAMPLE_197_TESTP4.mp4` | 156.2 | no | no | 4.02 |
| P5 | Fernandez-Pello | 195 | 202 | `BASS_GMT195_SAMPLE_202_TEST_P5.mp4` | 184.1 | yes | no | 4.76 |
| P6 | Fernandez-Pello | 184 | 186 | `BASS_GMT184_SAMPLE_186_TESTP6.mp4` | 57.6 | no | no | 2.06 |
| P8 | Fernandez-Pello | 184 | 197,198 | `— (Nikon images / ProofSheet only)` | — | no | no | 0.86 |
| P9 | Fernandez-Pello | 195 | 202 | `BASS_GMT195_SAMPLE_202_TEST_P9.mp4` | 109.3 | yes | no | 1.91 |
| P10 | Fernandez-Pello | 184 | 187 | `— (Nikon images / ProofSheet only)` | — | no | no | 2.83 |
| P12 | Fernandez-Pello | 210 | 199 | `BASS_GMT210_SAMPLE_199_TEST_P12.mp4` | 108.3 | yes | no | 3.73 |
| P13 | Fernandez-Pello | 195 | 203 | `BASS_GMT195_SAMPLE_203_TEST_P13b.mp4` (several runs/videos: P13a, P13b; see inventory) | 56.4 | yes | no | 4.89 |
| P14 | Fernandez-Pello | 174 | 189 | `BASS_GMT174_SAMPLE_189_TEST_P14.mp4` | 85.0 | yes | no | 2.33 |
| P15 | Fernandez-Pello | 174 | 190 | `BASS_GMT174_SAMPLE_190_TEST_P15.mp4` | 70.8 | yes | yes | 2.56 |
| P16 | Fernandez-Pello | 203 | 191 | `BASS_GMT203_SAMPLE_191_TEST_P16.mp4` | 87.5 | yes | no | 2.18 |
| P17 | Fernandez-Pello | 210 | 192 | `BASS_GMT210_SAMPLE_192_TEST_P17.mp4` | 104.6 | yes | no | 2.75 |
| P18 | Fernandez-Pello | 211 | 193 | `BASS_GMT211_SAMPLE_193_TEST_P18_LOS_Portion_10h52m52s_to_end_of_test.mp4` (no main video; los_clip used) | 59.5 | yes | no | 4.01 |
| P19 | Fernandez-Pello | 203 | 194 | `BASS_GMT203_SAMPLE_194_TEST_P19.mp4` | 153.4 | yes | no | 3.99 |
| P20 | Fernandez-Pello | 211 | 195 | `BASS_GMT211_SAMPLE_195_TEST_P20.mp4` | 98.2 | yes | no | 4.17 |
| P21 | Fernandez-Pello | 174 | 196 | `BASS_GMT174_SAMPLE_196_TEST_P21b.mp4` (several runs/videos: P21a, P21b; see inventory) | 35.9 | yes | no | 2.14 |
| P22 | Fernandez-Pello | 189 | 200 | `BASS_GMT189_SAMPLE_200_TEST_P22a.mp4` (several runs/videos: P22a, P22b; see inventory) | 33.0 | yes | no | 3.26 |
| P23 | Fernandez-Pello | 211 | 201 | `BASS_GMT211_SAMPLE_201_TEST_P23.mp4` | 154.0 | yes | no | 3.63 |
| P24 | Fernandez-Pello | 211 | 819 | `BASS_GMT211_SAMPLE_819_TEST_P24.mp4` | 138.3 | yes | yes | 4.31 |
| P25 | Fernandez-Pello | 189 | 217 | `BASS_GMT189_SAMPLE_217_TEST_P25.mp4` | 103.8 | yes | no | 3.44 |
| T1 | T'ien | 45 | 128 | `BASS_GMT45_SAMPLE_128_TEST_T1.mp4` | 11.7 | no | yes | 1.10 |
| T2 | T'ien | 45 | 129 | `BASS_GMT45_SAMPLE_129_TEST_T2.mp4` | 13.7 | no | yes | 1.33 |
| T3 | T'ien | 178 | 182 | `BASS_GMT178_SAMPLE_182_TEST_T3.mp4` | 37.7 | yes | yes | 4.04 |
| T4 | T'ien | 45 | 130 | `BASS_GMT45_SAMPLE_130_TEST_T4.mp4` | 8.1 | no | yes | 1.28 |
| T5 | T'ien | 100 | 131 | `BASS_GMT100_SAMPLE_131_TEST_T5.mp4` | 35.7 | no | yes | 1.46 |
| T6 | T'ien | 100 | 132 | `BASS_GMT100_SAMPLE_132_TEST_T6.mp4` | 23.6 | no | no | 1.37 |
| T7 | T'ien | 190 | 182 | `BASS_GMT190_SAMPLE_182_TEST_T7_First_Ignition_Attempts.mp4` | 4.3 | yes | yes | 3.77 |
| T9 | T'ien | 175 | 133 | `BASS_GMT175_SAMPLE_133_TEST_T9.mp4` | 10.8 | no | no | 0.66 |
| T10 | T'ien | 175 | 134 | `BASS_GMT175_SAMPLE_134_TEST_T10.mp4` | 9.7 | yes | no | 0.33 |
| T11 | T'ien | 178 | 135 | `BASS_GMT178_SAMPLE_135_TEST_T11.mp4` | 12.4 | yes | yes | 1.28 |
| T12 | T'ien | 178 | 136 | `BASS_GMT178_SAMPLE_136_TEST_T12.mp4` | 4.6 | yes | no | 0.61 |
| T13 | T'ien | 100 | 137 | `BASS_GMT_100_sample137_test T13.mp4` | 65.7 | no | no | 0.79 |
| T14 | T'ien | 178 | 140 | `BASS_GMT178_SAMPLE_140_TEST_T14.mp4` | 13.7 | yes | yes | 1.38 |
| T15 | T'ien | 45 | 138 | `BASS_GMT45_SAMPLE_138_TEST_T15.mp4` | 4.7 | no | yes | 0.74 |
| T16 | T'ien | 100 | 139 | `BASS_GMT100_SAMPLE_139_TEST_T16.mp4` | 35.0 | no | yes | 1.43 |
| T17 | T'ien | 178 | 142 | `BASS_GMT178_SAMPLE_142_TEST_T17.mp4` | 9.4 | yes | no | 1.17 |
| T18 | T'ien | 175 | 141 | `BASS_GMT175_SAMPLE_141_TEST_T18.mp4` | 10.3 | yes | no | 0.65 |
| T19 | T'ien | 190 | 143 | `BASS_GMT190_SAMPLE_143_TEST_T19.mp4` | 9.2 | yes | no | 0.82 |
| T20 | T'ien | 190 | 144 | `BASS_GMT190_SAMPLE_144_TEST_T20_2ND_VIEW.mp4` (no main video; second_view used) | 4.7 | yes | yes | 0.46 |
| T21 | T'ien | 190 | 145 | `BASS_GMT190_SAMPLE_145_TEST_T21.mp4` | 4.7 | yes | yes | 0.49 |
| T22 | T'ien | 190 | 146 | `BASS_GMT190_SAMPLE_146_TEST_T22.mp4` | 5.0 | yes | yes | 0.53 |
| T23 | T'ien | 190 | 133 | `BASS_GMT190_SAMPLE_133_TEST_T23.mp4` | 5.7 | yes | yes | 0.72 |
| T24 | T'ien | 190 | 133 | `BASS_GMT190_SAMPLE_133_TEST_T24.mp4` | 13.9 | yes | yes | 1.11 |
| T25 | T'ien | 216 | 138 | `BASS_GMT216_SAMPLE_138_TEST_T25.mp4` | 8.6 | yes | yes | 0.88 |
| T26 | T'ien | 216 | 137 | `BASS_GMT216_SAMPLE_137_TEST_T26.mp4` | 15.3 | yes | no | 1.15 |
| T27 | T'ien | 216 | 146 | `BASS_GMT216_SAMPLE_146_TEST_T27.mp4` | 14.0 | yes | no | 0.83 |
| T28 | T'ien | 216 | 144 | `BASS_GMT216_SAMPLE_144_TEST_T28b.mp4` (several runs/videos: T28a, T28b; see inventory) | 8.4 | yes | no | 0.68 |
| T29 | T'ien | 216 | 145 | `BASS_GMT216_SAMPLE_145_TEST_T29.mp4` | 19.1 | yes | no | 0.83 |
