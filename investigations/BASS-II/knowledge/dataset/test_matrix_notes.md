# BASS-II — Notes on the test matrix and the experimental table

Source files (do not modify): `data/docs/Science Documents_BASS-II_Test.Matrices.xlsx`, `data/docs/Experimental table_BASS-II.csv`.
Exports: `data/catalog/test_matrix_<PI>.csv` (one per sheet, cells as-is; dates in ISO `YYYY-MM-DD`).
Most complete version of the matrix (with overlay start/end time, ignitor, sample distance, GN2 pot, Nikon settings, SD card no. and text observations): **Summary Report Appendix A** (Tables A.1–A.6), text in `knowledge/dataset/raw_text/BASS-II_Summary_Report.txt` (search for `TABLE A.`). It is not tabulated. `catalog.parse_summary_report_appendix_a()` extracts the regime, restrictor, Fan + Air text, calibrated and raw O2 and the observations (see §5.2).

---

## 1. Test.Matrices.xlsx

6 sheets, one per PI, 16 identical columns, no formulas or charts:

| Sheet | Data rows | Tests | Exported |
|---|---|---|---|
| Bhattacharjee | 22 | B1–B22 | `test_matrix_Bhattacharjee.csv` |
| Ferkul | 4 | F1–F4 | `test_matrix_Ferkul.csv` |
| Miller | 20 | M1–M20 | `test_matrix_Miller.csv` |
| Olson | 27 | O1–O22 (with a/b) | `test_matrix_Olson.csv` |
| Fernandez-Pello | 27 | P1–P25 (P7, P11 missing; with a/b) | `test_matrix_Fernandez_Pello.csv` |
| T'ien | 29 | T1–T29 (T8 missing; with a/b) | `test_matrix_T_ien.csv` |

Total 129 rows (= runs; 126 tests per the report + a/b duplicates counted separately).

### Columns (literal header → meaning, per ReadMe/FAQ)

| # | xlsx header | Meaning |
|---|---|---|
| 1 | `Actual Date (for Video Display Date, add 1 for Leap Year)` | Actual test date (Excel datetime). The video overlay date is **+1 day**. |
| 2 | `GMT 2014-` (Olson: `GMT 2014- (except last 3 tests from 2016)`) | GMT day of year (1–366). O20–O22 are from **2016** (GMT 57 = 26-Feb-2016). |
| 3 | `Test no.` | PI initial + initial matrix no.; suffix a/b = several runs of the same sample on the same day. |
| 4 | `Sample no.` | Sample no.; suffix `m`/`M`/`L` with no documented meaning. Samples reused in several tests. |
| 5 | `Material` | Free text (thickness, width, color, 1/2 sides). |
| 6 | `Flow restrictor` | 0, 1 or 2 perforated plates at the fan inlet (0 = max. flow ~55 cm/s; 2 = min. ~35 cm/s max.). |
| 7 | `Fan display` | Overlay reading = **10 × fan voltage** (max. 122 = 12.2 V). Often the control box dial **pot** (0–10) is noted instead. List of successive steps. |
| 8 | `Air display` | Anemometer velocity (cm/s) in the overlay; ~1 min response → only reliable on long plateaus. List of steps. |
| 9 | `Radiometer gain (1000, 250, 50, 10)` | Radiometer (uncalibrated) gain; may change during the test. |
| 10 | `total frames shot` | No. of Nikon photos taken (includes post-burn). |
| 11 | `calibrated initial O2 % by vol` | Initial CSA-CP O2 corrected with the day's MCA offset. |
| 12 | `calibrated final O2 % by vol` | Final O2, same. |
| 13–14 | `Initial/Final CO2 % by vol` | CDM. |
| 15–16 | `Initial/Final CO (ppm)` | CSA-CP; `OR` = over range (> 1000 ppm). |

---

## 2. Experimental table_BASS-II.csv

- UTF-8 **with BOM**, comma separator, 129 rows × 17 columns. It is the same information as the xlsx, concatenated, with an extra `PI` column (first) and these differences:
  - `Date` in `M/D/YYYY` format (text).
  - **Commas inside cells were replaced by spaces** (usually 3) → `"5, 3, 1, <1"` in the xlsx appears as `5   3   1   <1`. That is why steps are separated by multiple spaces (sometimes 1–2). **Prefer the xlsx** (or `test_matrix_*.csv`) to parse lists, because it preserves commas and semicolons.
  - Headers with double and trailing spaces: `'Calibrated  initial O2 % by vol '`, `'Radiometer gain   (1000   250   50   10)'` → normalize with `strip()` and collapse spaces.

Columns: `PI, Test #, Date, GMT, Sample #, Fuel Sample Material, Flow restrictor, Fan display, Air display, Radiometer gain (...), Total Frames Shot, Calibrated initial O2 % by vol, Calibrated final O2 % by vol, Initial CO2 % by vol, Final CO2 % by vol, Initial CO (ppm), Final CO (ppm)`.

---

## 3. Dirty formats (observed catalog)

### 3.1 `Fan display`
| Example | Interpretation |
|---|---|
| `62` | single display (6.2 V) |
| `58, 54` / `58   54` | successive display steps |
| `0.9, 1.3, 2.75` | **pot** steps (values ≤ 10 with decimals → pot) |
| `1.7 (52), 1.25, 0.9…` | pot 1.7 with display 52 in parentheses, then pots |
| `44 (pot 0.68)` / `47 (pot 1.05), incr to pot 6.0` | display with pot in parentheses; upward ramp to pot 6 (blowoff) |
| `pot 0.9, 0.5 and down` / `53, and down` | continuous/undetailed decrease until extinction |
| `1.4 , incr to 10.0` | upward ramp to pot 10 |
| `73,57,59,48 (4.2,2.2,2.4,1.2…)` | list of displays + parallel list of pots in parentheses |
| `2.6, 1.3…; 60, 49, 45…` | list of pots `;` parallel list of displays |
| `94/91, 72/69` | display drifting from 94 to 91 within the step |
| `3/0/2.7` | typo for `3.0/2.7` |
| `5, .36, .32, .31, .305, out .275` (Olson O6–O9, O11, P22, P25) | first value **5 = 5 cm/s at ignition** (not pot), then pots; `out`/`ext` = extinction |
| `… blowoff fan max 10` / `blowoff pt 4.0` / `blowoff 6.0` | blowoff at the indicated pot |
| `Fan pot 1.5 (5cm/s), 0.9…, 0 ext` | pot with velocity in parentheses |
| `80122` (T15) | typo: `80, 122` |
| `60,52,48,233,48,41 (…,10,…)` (P17) | `233` is a typo for `122` (pot 10) |
| `55,47,etc (pot 1,2,1,2, etc)` (P18, P20, P23, P24) | periodic alternation between pot 1 and 2 |
| `ignited 10, adjusted down then up to 20…` / `see notes` | free text; see Appendix A |
| empty | not recorded (use Air display or Appendix A) |

### 3.2 `Air display`
Lists of cm/s (`10, 5, 4, 3, 2, 1`), with tokens: `<1`, `~8`, `max`, `approaching 10`, `ext`/`0ext`/`extinction`, `blowoff`, `low`, `down to ext`, `5>7` (change from 5 to 7), `(brief)`, `?`, `pot 0.4` (a pot slipped into the column), `(49, 62, 49, 44, 42)` (displays slipped in), `3 ign` (3 cm/s at ignition), `see fan`, `no ign at any flow`, `incr to max 38.5`.

### 3.3 Other columns
- `Radiometer gain`: `250>50>250` (sequence of changes), `50, 250`, `10, 250`, `1000, 250`.
- `total frames shot`: `none`, `300+ +102` (two cards: ≥ 300 + 102), `10 postburn only`, `video` (no photos; O20–O22).
- O2/CO2/CO: `none` (not measured), `OR`/`over` (> 1000 ppm CO), `>500`, negative CO values (−1…−3 = zero offset, treat as 0 ± 3).
- `Sample no.`: `153m`, `205M`, `39M`, `819L`.

### 3.4 Detected errors
| Test | Problem | Proposed correction |
|---|---|---|
| T9, T18 | Date `2018-06-24` | 2014-06-24 (GMT 175 matches) |
| O10 | GMT 213 with date 2014-07-22 | GMT **203** (files `GMT203`, GMT 203 = 22-Jul) |
| B2 | Final O2 = 1.6; final CO2 empty; initial CO 6 | shifted row: probably final CO2 ≈ ?, values unreliable → set `qc_flag` |
| P22a / P22b | Final O2 0.6 / 39.1; CO2 `none` | columns shifted between the two runs → do not use final O2 |
| T28a / T28b | Final O2 0.9 / 40.4 | same |
| B14 | Final O2 `none`; initial CO2 0 | partial |
| P8 | sample 197m (same as P4) | proof sheet indicates S198M |
| B17 | files named `TESTB15` | B17 = sample 175 |
| M5 | `Fan display` empty; final CO `>500`; frames `300+ +102` | long test that damaged the window (GMT 51) |
| F2, O20–O22 | no files in the repository | — |

---

## 4. Proposed clean schema

### 4.1 `tests` table (one row per run)

| Column | dtype | Unit | Parsing rule |
|---|---|---|---|
| `test_id` | string | — | `Test #` without spaces; pattern `^[BFMOPT]\d+[ab]?$` |
| `test_group` | string | — | `test_id` without a/b suffix (links to PSI subcategory) |
| `run_suffix` | category | — | `a`, `b` or empty |
| `pi` | category | — | initial → {B: Bhattacharjee, F: Ferkul, M: Miller, O: Olson, P: Fernandez-Pello, T: T'ien} |
| `date_actual` | date | — | `Date` (CSV `M/D/YYYY`) or xlsx; correct 2018→2014; validate with `gmt_day` |
| `year` | int | — | 2014 (2016 for O20–O22) |
| `gmt_day` | int | day of year | `GMT`; correct O10→203; check `date_actual.dayofyear == gmt_day` |
| `video_overlay_date` | date | — | `date_actual + 1 day` |
| `sample_raw` | string | — | `Sample #` as-is |
| `sample_num` | int | — | digits of `sample_raw` |
| `sample_suffix` | category | — | trailing letter (`m`/`M`/`L`) or empty |
| `material_raw` | string | — | original text |
| `fuel` | category | — | regex: `pmma` → PMMA; `sibal` → SIBAL; `nomex` → Nomex III; `candle` → candle |
| `geometry` | category | — | `film` (≤ 0.4 mm), `slab` (≥ 1 mm), `rod`, `sphere`, `fabric`, `candle` |
| `thickness_mm` | float | mm | `(\d+) micron` → /1000; `([\d.]+) ?mm thick` / `([\d.]+) mm` ; SIBAL 0.32 |
| `width_cm` | float | cm | `([\d.]+) cm( wide)?` (careful: "2 cm thick" in M5 is the width) |
| `rod_diameter_mm` | float | mm | `1/4"`→6.35; `3/8"`→9.525; `1/2"`/`0.5"`→12.7 |
| `rod_color` | category | — | `clear` / `black` |
| `sides_burned` | int | — | `1 sided`→1, `2 sided`→2; Miller without indication → null (see Appendix A) |
| `flow_config` | category | — | **implemented as `regime`** — see §5.4 (per-test label from Appendix A; P16/P19 are concurrent, Olson rods split concurrent/stagnation) |
| `flow_restrictors` | int8 | — | `Flow restrictor` ∈ {0,1,2} |
| `fan_display_raw` | string | — | original text (from the xlsx, with commas) |
| `air_display_raw` | string | — | original text |
| `n_flow_steps` | int | — | no. of parsed steps (`flow_steps` table) |
| `end_event` | category | — | `quench` if `ext`/`out`/`extinguished`/`down to ext` appears; `blowoff` if `blowoff`; `no_ignition` if `no ign`; `flow_off`; otherwise null |
| `radiometer_gain_raw` | string | — | original text |
| `radiometer_gains` | list[int] | — | split on `[,> ]+`, values ∈ {1000,250,50,10} |
| `radiometer_gain_changed` | bool | — | `len(set(radiometer_gains)) > 1` |
| `nikon_frames` | Int (nullable) | frames | leading number; `300+ +102`→402 (with flag); `none`/`video`→NA; `10 postburn only`→10 |
| `o2_initial_pct` | float | % vol | numeric; `none`→NA |
| `o2_final_pct` | float | % vol | numeric; NA if < 10 or > 25 (shifts) |
| `co2_initial_pct`, `co2_final_pct` | float | % vol | numeric; `none`→NA |
| `co_initial_ppm`, `co_final_ppm` | float | ppm | numeric; negatives → 0 (flag); `OR`/`over`/`>500` → NA + `co_censored = '>1000'`/`'>500'` |
| `co_censored` | category | — | `>1000`, `>500` or empty |
| `qc_flags` | list[str] | — | e.g. `date_typo`, `gmt_typo`, `o2_final_shifted`, `files_misnamed`, `no_files` |

### 4.2 `flow_steps` table (one row per flow step)

| Column | dtype | Unit | Rule |
|---|---|---|---|
| `test_id` | string | — | FK |
| `step_idx` | int | — | order of appearance |
| `pot` | float | 0–10 | number ≤ 10 in `Fan display` (or in parentheses `pot x`) |
| `fan_display` | float | 10×V | number 38–122 (or in parentheses after a pot) |
| `fan_display_est` | float | 10×V | if only pot is present: `38.16 + 8.384·pot` |
| `fan_volts` | float | V | `fan_display/10` |
| `air_display_cm_s` | float | cm/s | i-th number of `Air display` (if the lists have equal length; otherwise NA) |
| `air_qualifier` | category | — | `<`, `~`, `max`, `approaching` |
| `u_cal_cm_s` | float | cm/s | piecewise linear interpolation of `fan_calibration_tidy.csv` for (`gmt_day`, `flow_restrictors`) excluding the 3.8 V point; fallback: pooled fit `fan_calibration_fits_pooled.csv` |
| `event` | category | — | `ignition` (first step / `ign`), `ramp_up` (`incr to`), `ramp_down` (`and down`, `decr`), `extinction` (`ext`, `out`), `blowoff`, `off` |
| `token_raw` | string | — | original token |

Tokenization rules for `Fan display` (apply to the xlsx text):
1. Split parallel lists on `;` or on a trailing parenthesized block (`… (4.2, 2.2, …)`); if there are two lists of equal length, one of pots (all ≤ 10) and one of displays (all ≥ 38), pair them.
2. Split on `,` (CSV: on `\s{2,}`); clean `pot`, `Fan pot`, `p.36`→`.36`, `..305`→`.305`.
3. Number `x`: if `x ≤ 10` → pot; if `38 ≤ x ≤ 122` → display; other (`233`, `80122`) → typo (flag).
4. Olson/Pello exception: first token `5` followed by pots < 1 → ignition velocity 5 cm/s (not pot).
5. `a/b` (e.g. `94/91`) → initial and final display of the step; store the first and the drift.
6. Keywords → `event` (see above); `etc` → `n_flow_steps` incomplete (flag).

### 4.3 Join keys
- `tests.test_id` ↔ `files_inventory.test_id` (files with a/b) and `test_group` ↔ PSI subcategory (`Reduced Gravity/<PI>/<test_group>`).
- `tests.gmt_day` + `flow_restrictors` ↔ `fan_calibration_tidy.(gmt_day, n_restrictors)` (some days have 2 calibrations: "post soot cleaning" and "end"; use the one after the test if the time is known).

---

## 5. Implemented clean table (`catalog.load_experimental_table()`, ROADMAP Phase 1 #1)

Outputs (regenerate with `.venv/Scripts/bass2 catalog`):
- `data/catalog/experimental_table_clean.parquet` / `.csv`: one row per run (129). List columns are lists in parquet and `;`-joined strings in the CSV (`fan_steps`, `fan_paren`, `air_steps`, `air_paren` are parquet-only, as before).
- `data/catalog/experimental_table_validation.csv`: one row per run with the parsed flow vs the as-run matrices, the O2 cross-check, the regime and disagreement flags.

Tests: `tests/test_catalog.py` has one test per rule below, plus O13a, O5a, B10, M10, P5, T15 and the geometry cases.

### 5.1 Flow velocity (`parse_air_display`)

The `Air display` cell is tokenised into numbers (with qualifiers `<`, `~` and a trailing `?`), words, parenthesised groups and `,`/`;` separators. Normalisation: `p.36`→`.36`, `..305`→`.305`, trailing dots `0.45.`→`0.45`, `0ext`→`0 ext`.

Constants:
- Plausible imposed air velocity is **0–55 cm/s**. The limit per restrictor is min(55, fan-calibration maximum): **55 with 0 restrictors and 41 with 1 or 2 restrictors** (the calibration maxima are 59 / 40 / 40 cm/s).
- The fan display never goes below **38** (pot 0 ≈ 38.2). Pot→display: `38.16 + 8.384·pot`.

Number classification:
- `pot` binds **backward** to the previous number when that number is fractional (`0.5 pot`) or when `pot` closes an item (`5 pot,` in the report). Otherwise it binds **forward** (`pot 0.4`). `pots` always binds forward. Pots are never velocities.
- A number followed by `cm/s` is an explicit velocity.
- Parenthesised groups:
  - containing `pot` → pots;
  - no numbers → annotation (`(brief)`; `(?)` marks the previous value uncertain);
  - a single number right after `max` → the velocity reached at max (`max(47)`);
  - all values ≥ 38 → **fan display**;
  - all values ≤ 10 with a fractional value → pots;
  - otherwise → **cm/s group**.
- Words are **events, not numbers**:
  - `ext`/`extinction`/`extinguished`/`out` → extinction;
  - `blowoff`;
  - `max`/`maximum` → max;
  - `low`/`lower`/`very low` → lower_unrecorded;
  - `decr`/`down` → decrease;
  - `incr` → ramp_up (the next number is the ramp target);
  - `ign` → ignition (`no ign` → no_ignition);
  - `off` → flow_off;
  - `etc` → periodic_etc;
  - `would not stay lit` → not_sustained;
  - `see fan`.

Rules (`flow_parse_rule`), in priority order:

| Rule | Condition | Steps taken | Confidence | Examples |
|---|---|---|---|---|
| `explicit_cm_s_unit` | some number tagged `cm/s` | only the tagged numbers; the others are dropped as fan display | medium | O5b (`49 5 cm/s` → 5) |
| `swap_paren_cm_s_outside_fan_display` | all outside numbers ≥ 38 and a cm/s group in parentheses | the parenthesised group | medium if the outside values match the display predicted from the Fan-column pots (mean abs. error ≤ 3), else low | O13a (`49 44 42 41 41 40.5 (5 2 0)` → 5, 2, 0) |
| `only_fan_display_values` | all outside numbers ≥ 38 and above the limit, no cm/s group | none | low | (none in the table) |
| `dropped_implausible_values` | some outside numbers above the restrictor limit | the plausible ones | medium | (none in the table; guards against typos) |
| `outside_cm_s_paren_fan_display` | cm/s outside, fan displays in parentheses | the outside numbers | high (medium if qualified) | O5a, O13b |
| `cm_s_then_pots` | cm/s values followed by pots in the same cell | the cm/s values; `flow_min_is_upper_bound = True` | high | B16, B17, B20, P4, P6, P10 |
| `plain_list` | anything else with numbers | the outside numbers (+ `max(…)` values, in order) | high; medium for qualifiers (`<1`, `~8`, `4?`, `2(?)`, `approaching 10`) or values in the 38–55 overlap zone (T17 53, T21 47, O20 38.5) | most tests |
| `ramp_target_only` | the first number is a ramp target (`incr to 28`) | the target; **`flow_initial_cm_s` = NaN** | low | O21 |
| `fan_column_explicit_cm_s` | no velocity in Air display; Fan display has `(N cm/s)` | N | medium | (would apply to P5/P9/P13 if Air were empty) |
| `fan_column_ignition_velocity` | no velocity in Air display; Fan display starts with an integer 1–10 followed by pots < 1 (`5, .36, .32 …`) | that integer (ignition velocity, Olson/Pello convention §3.1) | low (medium when the Air cell says `see fan`) | O6 (medium), O7, O8a, O8b, O9 |
| `no_numeric_flow` | nothing usable | none | low | O12 (`no ign at any flow`) |

Derived columns:
- `flow_steps_air_display`: the AIR display values (cm/s, as read on the anemometer overlay).
- `flow_steps_cm_s`: **`U = 1.0066 × AIR`** for every step. This is the anemometer → duct-centreline correction from the fan calibration xlsx (bass2_dataset.md §4). `flow_initial_cm_s`, `flow_max_cm_s` and `flow_min_cm_s` use the same convention. `<1` is stored as 1 (an upper bound).
- `flow_max_is_lower_bound`: a `max` event without a recorded value (B8, B15, O10, P19).
- `flow_min_is_upper_bound`: the flow was lowered further without a recorded value (`low`, `decr`, `down to ext`, `off`, pots after cm/s, or the minimum is `<x`).
- `flow_events`, `flow_parse_rule`, `flow_parse_confidence` (high/medium/low) and `flow_parse_notes`.

Confidence levels:
- **high**: values read directly as unambiguous cm/s.
- **medium**: a disambiguation rule was needed, or a value is approximate or in the overlap zone.
- **low**: no cm/s in the Air display (inferred from the Fan display or ramp text), or the rule could not be confirmed.

Legacy columns are kept unchanged: `fan_steps`, `air_steps` (numbers outside parentheses; **not** reliable as cm/s, e.g. O13a), `fan_paren`, `air_paren`, `extinction`, `blowoff`, `no_ignition` and the raw text columns.

Counts (129 runs): **high 109, medium 14, low 6**.
- Medium: B6, B9, B11, M12, M14, O5b, O6, O13a, O13b, O20, T6, T17, T21, T29.
- Low: O7, O8a, O8b, O9, O12, O21.

### 5.2 As-run cross-check

Sources:
1. `data/catalog/test_matrix_<PI>.csv` (Test.Matrices.xlsx, commas preserved). The same rules are applied to its `Air display` cell.
2. Summary Report Appendix A, read from the raw PDF text by `parse_summary_report_appendix_a`. O20–O22 (2016) are not in the report.

How the Appendix A rows are read:
- **Row location:** each row is found by its `<as-run no> <test> <sample>` pattern.
- **Restrictor and regime:** the restrictor and the regime label follow the igniter (`… 2 Opposed …`).
- **Flow text:** the Fan + Air text runs up to the radiometer gain (`250`, `250 > 50`, `1,000 and 250` …). The gain is followed by the radiometer display (`---`, `Saturated`, `0.97 maximum`, `NA` …).
- **Air part:** split off in the first way that works:

  | Split method | Runs |
  |---|---|
  | xlsx Air text matched as a suffix | 113 |
  | blank Fan column | 6 |
  | trailing `------` (blank Air) | 4 |
  | xlsx Fan text matched as a prefix | 1 |
  | whole segment parsed (B16, M2) | 2 |

- **Gas block:** the 8 numbers (calibrated O2 i/f, raw O2 i/f, CO2 i/f, CO i/f) are located by matching the calibrated O2 values of the experimental table. 125 runs match on initial + final, 1 on initial only. The text after the block is kept as `report_observations`.

Columns added to the clean table:
- `flow_asrun_cm_s`: 1.0066 × the first as-run AIR value (from the report if parsed, else the xlsx; NaN for O12 and O21).
- `o2_asrun_pct`: calibrated initial O2 (from the report, else the xlsx).
- `asrun_source`: `flow:<source>;o2:<source>`, with source ∈ {`summary_report_appA`, `test_matrix_xlsx`, `none`}.
- `o2_raw_csa_cp_pct`, `o2_raw_csa_cp_final_pct`: uncalibrated CSA-CP readings from the report (NaN where the report shows `----`, e.g. P22b initial, T28b initial).
- `o2_convention` = `calibrated_mca`: **all O2 analysis uses the calibrated value** (CSA-CP + daily MCA offset) from the experimental table (`o2_initial_pct`, `o2_final_pct`). Raw CSA-CP is typically 0.9–2.1 points lower.
- `report_observations`: the free-text observations from Appendix A.

Flags in the validation CSV (AIR units with tolerance 0.5 cm/s; O2 tolerance 0.05):
- `flow_initial_disagree`, `flow_steps_disagree`, `o2_disagree`, `restrictor_disagree`;
- `disagreement`: any of the four above;
- `obs_ignition_mismatch` (soft flag): the ignition velocity quoted in the observations ("Ignition at 5 cm/s", "ignited at 10") differs from the parsed initial value. Without a unit, only integers are accepted (decimals are pots).

Results: no initial-flow, O2 or restrictor disagreement. Disagreements found:
- **M2:** the table steps are `20, 15, 13, 14`; the report has `20, 15, 13`. The report row lacks the Fan display and the final 14; its observations confirm "increased flow to 14 cm/s".
- Observation mismatches (for human review; not used to override the table):
  - **M4** and **M13:** the observations say "Mild ignition at 10 cm/s"; the Air display starts at 5 / 6. The two observation texts are identical, probably copied in the report; the Air display lists the plateaus after ignition.
  - **O2:** "Ignited at 2 cm/s"; the Air display is `0`.
  - **T22:** "Ignited at 11"; the Air display is `10, 5`.

### 5.3 Geometry (`_material`)
- Typos are fixed before parsing and logged in `material_parse_flags`: `2ide`→`wide` (M19), `blac`→`black` (P14).
- Rod diameter: `1/4` → 6.35, `3/8` → 9.525, `1/2` or `0.5"` → 12.7 mm. The inch mark is optional; `3/8"clear` without a space works.
- Thickness: `N micron` → N/1000 mm, else the first `N mm`. This fixes `2 cm 4 mm 1 sided PMMA slab` → 4 mm. SIBAL → 0.32 mm (bass2_dataset.md; flagged `thickness_from_dataset_doc`).
- Width: `N cm` (not for rods or spheres). `2 cm thick` in M5 is the width.
- Spherical section: `4 cm spherical section` → `sphere_diameter_mm` = 40; `width_mm` stays empty.
- `sides_burned` comes from `N sided`.
- `geometry` ∈ {film (PMMA ≤ 0.4 mm), slab, rod, sphere, fabric, candle}.

### 5.4 Regime (`regime`, `regime_source`)
Values: `opposed`, `concurrent`, `stagnation`, `mixed`.

1. **Per test from Summary Report Appendix A**, where the column after the flow restrictor reads Opposed / Concurrent / Stagnation. `regime_source = summary_report_appA` (120 runs). Notable cases:
   - **P16 and P19 are concurrent**; the rest of P is opposed.
   - Olson rods split into concurrent (O3a/b, O5a/b, O10, O13a/b, O14, O17, O19) and stagnation (O4, O6–O9, O11, O12, O15a/b, O16, O18).
   - F1–F3 are concurrent; F4 (candle) and T3/T7 (sphere) are stagnation.
2. Otherwise the **PI default** (`regime_source = pi_default`, 9 runs), from bass2_dataset.md (PI table) and flame_spread_physics.md §1:
   - B, M, P → opposed;
   - T, F → concurrent (for T1, T2, T4 and T15 the report column holds the sample distance `1`);
   - O → `mixed` (stagnation-point tip + concurrent sides): O1 and O2 are marked `?` in the report, and O20–O22 are absent.

Counts: opposed 67, concurrent 42, stagnation 15, mixed 5.
