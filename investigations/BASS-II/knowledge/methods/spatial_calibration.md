# Spatial calibration of the BASS-II main video (mm per pixel)

Status: implemented 2026-11-13 (`src/bass2/calibration.py`, `scripts/calibrate_study.py`,
output `data/catalog/spatial_calibration.csv`). Published spread rates were **not** used.

## 1. Reference object
Several videos start with the glovebox lights on (B3, B4, B5, B7, B12, M1, P2, P21, …). These frames show
the inside of the 76 mm duct and, near its floor (y ≈ 430–450 px), the **movable scale** mentioned in the
Summary Report §2 ("a nozzle for N2 flow, a movable scale…") and in the Ops procedure ("the deployed scale may
not be visible" once exposure is set for the flame). The scale carries cross-shaped major marks with finer
graduations between them.

## 2. Measurement
1. Illuminated frames are detected by the median brightness of the analysable area (> 18 on 0–255; dark flame
   frames have median 0).
2. In each lit frame, horizontal bands between y = 380 and 475 px are scanned; the band with the strongest
   periodic pattern is selected (normalised autocorrelation peak of the de-trended max-brightness profile).
3. The dominant period (sub-pixel by parabolic peak refinement) is the major-mark spacing. Median over ≤ 40 lit frames.
4. Native px → physical px with the SAR 10:11 correction (×10/11).

## 3. Results
| Test | GMT day | Period (native px) | IQR across frames | mm / physical px (1 cm marks) | Strength |
|---|---|---|---|---|---|
| B3 | 50 | 52.69 | 0.06 | 0.2088 | 0.62 |
| B4 | 50 | 52.29 | 0.15 | 0.2104 | 0.56 |
| B5 | 50 | 52.84 | 0.12 | 0.2082 | 0.61 |
| B7 | 50 | 52.59 | 0.05 | 0.2092 | 0.57 |
| B12 | 50 | 52.51 | 0.07 | 0.2095 | 0.63 |
| M1 | 51 | 52.54 | 0.10 | 0.2094 | 0.57 |
| P2 | 167 | 52.11 | 0.00 | 0.2111 | 0.43 |
| P21 | 174 | 52.06 | 0.06 | 0.2113 | 0.40 |
| B8 | 188 | 52.46 | 48.1 (mixed periods; accepted on median, flagged) | 0.2097 | 0.51 |
| B21 | 216 | 53.18 | 0.01 | 0.2069 | 0.33 |

**Global camera scale: 0.20943 ± 0.00132 mm per physical px (n = 10, CV 0.6 %)** across five months and four PIs,
consistent with the SRD statement that the video field of view is fixed. Tests without an accepted ruler inherit
the global value (`method = global_fixed_fov`). Five T/P13 estimates were rejected as outliers (> 10 % from the
median: the sample holder's own periodic structures, e.g. 3.7–4.3 mm/px, were detected instead of the ruler).
Uncertainty used downstream: 2.1 % (1σ) = 0.6 % between-test spread ⊕ 2 % allowance for the ruler/sample depth
difference (perspective).

## 4. Graduation assumption (explicit)
NASA documents do not state the graduation. The major-mark spacing is taken as **10 mm**:
- with 10 mm, the 76 mm duct spans ≈ 360 px of the 480 px frame and the edge-on sample sits mid-duct, as seen in
  the lit frames;
- with 5 mm, the duct would be ≈ 31 mm tall — geometrically impossible.

Bias disclosure: the analyst knew the published B1 rate when inspecting the ruler. The validation in
`reports/REPORT.md` §4 (figure G6) is therefore reported on all tests with published values, not on B1 alone.

## 5. Using it
`config.test_calibration(test_id)` resolves `mm_per_px` from `configs/calibration.yaml` (explicit override) or
from `spatial_calibration.csv`. Re-run `python scripts/calibrate_study.py` after downloading new videos.

## 6. Related measurement choices validated on the same reference tests
- **Segmentation**: background-relative hysteresis (`method: adaptive`, k_low 8 σ / k_high 16 σ, floors 14/30,
  OR-ed with a blue-excess channel). Chosen over fixed thresholds 40/90 because faint blue flames
  (B3 after ignition, B12, thick films) never reach the fixed high threshold. Comparison table:
  `data/processed/_segmenter_comparison.csv` (`scripts/compare_segmenters.py`).
- **Steady regime**: the leading edge is median-binned (~120 bins per burn) and split into linear regimes by
  optimal segmentation (penalty 12·σ²·log n, regimes ≥ max(3 s, 10 % of the burn)); the steady rate is the
  Theil-Sen slope of the longest regime whose 95 % CI is > 0. Penalty and length floor were selected on the
  8 reference tests (grid: penalty 3/6/12 × floor 0/10 %; rules longest / latest-long / max-displacement).
  At the chosen setting the longest and latest-long rules give identical results (mean |ln V/V_pub| 0.039,
  max 0.081), i.e. the result no longer depends on the selection rule. Disclosed: the reference tests were
  used for this choice, so the reported accuracy is optimistic by an unknown but likely small amount.
- **Edge robustness and uncertainty (final, 2026-11-13)**: a Hampel filter (31-sample window, 4 robust σ) removes
  isolated edge detections before the origin and regimes are computed; regime slope CIs are widened by
  sqrt((1+ρ1)/(1−ρ1)) for lag-1 residual autocorrelation. After these changes M7 step 2 and M9 moved from implausible
  values (0.615, 0.210 mm/s) to 0.112 and 0.027 mm/s. Settings were then frozen before the hold-out slab tests were run.

**Update after adding the hold-out videos (2026-11-13):** two more rulers were accepted (M2, M14); the global scale is now 0.20928 ± 0.00164 mm/px (n = 12, CV 0.8 %), a −0.07 % change. Reports read the current values from data/catalog/spatial_calibration.csv.
