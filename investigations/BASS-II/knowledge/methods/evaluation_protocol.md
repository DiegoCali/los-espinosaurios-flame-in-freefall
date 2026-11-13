# Evaluation protocol (BASS-II): scalar objective, gold set, anti-overfitting and figures

> Methods knowledge base — evaluation.
> Defines the **single metric** optimized by the autonomous loop (Karpathy *autoresearch* style), how to build the hand-labeled gold set, how to avoid overfitting to the metric, and which figures the final report must include.
> Depends on `computer_vision.md` and `time_series_forecasting.md`.
> Last revised: 2026-11-12.

---

## 1. Context: the autonomous loop

In `karpathy/autoresearch` (https://github.com/karpathy/autoresearch) the agent:
1. edits **a single file** (`train.py`);
2. commits and runs with a fixed time budget;
3. reads a fixed metric (`val_bpb`, lower is better) computed by an **immutable** file (`prepare.py`);
4. **keeps** the commit if it improves and runs `git reset` if not;
5. logs every attempt in `results.tsv`.

Secondary guide: https://www.datacamp.com/tutorial/guide-to-autoresearch

**Adaptation to BASS-II** (the repo's `autoresearch/` folder is the template):

> **Note (project layout)**: the project code lives in the package `src/bass2/` and the autonomous loop lives in `research/`. `research/experiment.py` is the only file the agent edits and `research/harness.py` is the fixed evaluator. **No git is used** by the loop: keep/discard is done with snapshots in `research/runs/` and `research/best/` (a snapshot is kept or reverted by the harness), instead of the upstream commit / `git reset` mechanism.

| Template | BASS-II |
|---|---|
| `prepare.py` (immutable) | `research/harness.py` (fixed): ingestion, cache of normalized frames, calibration (human-made json), splits, gold set and **`evaluate()`**, which returns `val_score` |
| `train.py` (editable) | `research/experiment.py`: segmentation, edge extraction, `V_f` estimation and forecasting model. It is the only editable file |
| `val_bpb` | **`val_score`** (§3), lower is better |
| 5 min budget | **≤ 10 min wall-clock** per full evaluation on the dev split (consumer GPU). A maximum number of frames per test is fixed for the CV part: 1 in every 3 frames, plus all gold frames |
| `results.tsv` | `results.tsv`: run ID (snapshot), val_score, components, SE, time and description |

**Contract of `research/experiment.py`** (invoked by `evaluate()` in `research/harness.py`):
```python
def segment(frames: np.ndarray, meta: dict) -> np.ndarray            # (T,H,W) bool, rectified coords
def leading_edge(frames, masks, meta) -> np.ndarray                   # (T,) mm, NaN if none
def spread_rate(t, x_le, meta) -> tuple[float, float]                 # V_f, σ_V
def forecast(history: pd.DataFrame, horizons_s: list[float], meta) -> pd.DataFrame
    # columns: h, q05, q25, q50, q75, q95  (for Δx_LE and log A)
```
`meta` contains **only** the allowed covariates: material, thickness, width, O2, flow, configuration, view, calibration and fps. It **never** contains labels or published rates.

---

## 2. Hand-labeled gold set

### 2.1 Test selection (stratified)
- There are 129 tests in the table. **30 gold tests** are chosen, stratified by:
  - PI (Bhattacharjee, Olson+Ferkul, Fernandez-Pello, Miller and T'ien: 5–7 of each);
  - material (PMMA film, clear rod, black rod, SIBAL, Nomex and candle);
  - flow (low < 5 cm/s, medium and high);
  - O2 (near the limit vs nominal).
- **Difficult cases** must be included on purpose:
  - very dim or pure blue flame;
  - heavy soot or saturation;
  - auto-exposure events;
  - strong reflections;
  - extinction;
  - tests with 2ND_VIEW (both views are labeled).
- **Gold split**: 20 **gold-dev** tests (seen by the loop) and 10 **gold-holdout** tests (sealed; see §4).

### 2.2 Frame selection
- **10 frames per test**, about 300 in total:
  - 1 pre-ignition frame, used for the background and for checking the calibration;
  - 1 in the ignition transient, with the igniter visible;
  - 6 evenly spaced in the propagation regime;
  - 1 at a difficult event (AE, saturation or reflection);
  - 1 near extinction or the end.
- Frames are chosen by timestamp (PTS) and stored by `(test, view, pts)`, never by index, so that they are robust to re-decoding.

### 2.3 What is labeled
1. **Total flame mask**: a polygon or brush on the **enhanced** image with a fixed, documented visualization (linear + gamma 0.5 + clip at p99.5), also showing the original image.
   - **Operational definition**: "every region with visible flame luminosity above the background, including the dim blue base; excludes wall reflections, the igniter and glowing sample without flame".
2. **Blue and soot submasks** (optional in the first round; mandatory on 100 frames).
3. **Leading edge**: a point (x, y) at the most advanced position of the flame base along the sample axis. It is the most important label, because it is cheap and precise.
4. **Trailing edge** and **standoff** (in the side view): one point each.
5. **Calibration check**: two clicks on the sample edges in the pre-ignition frame.
6. **Quality labels**: `ae_event`, `saturated`, `reflection` and `igniter`.

### 2.4 Manual edge time series ("gold tracks")
- In **12 tests** (8 dev and 4 holdout) the leading edge is clicked **every 1 s** throughout propagation. This is ~30–120 clicks per test, ~5 min per test.
- This yields `x_LE,gold(t)` and a **`V_f,gold`** by OLS, which are the direct reference for the rate error and for forecasting on "truth".

### 2.5 Tools and procedure
- **Tools**:
  - **CVAT** (https://www.cvat.ai/ , with an integrated SAM assistant);
  - or **Label Studio** (https://labelstud.io/ ; `label-studio` 1.23.2 is pure-Python, but it is best installed in a separate environment because of its large dependency tree);
  - or a custom notebook with `matplotlib` + `napari` for point clicks.
- **Pre-labeling** with SAM2 (via transformers) or with pipeline v0, followed by **human correction**. Record which frames were corrected and by how much, because pre-labeling introduces a bias toward the method that generated it. To mitigate this, **30 % of the frames are labeled from scratch**, without pre-labeling.
- **Inter-annotator agreement**:
  - 20 % of the frames (60) are labeled by a second annotator, or by the same annotator ≥1 week later.
  - Inter-annotator Dice and inter-annotator edge error are computed. That is the achievable **ceiling**: if a method exceeds human agreement, the improvement is noise.
- **Estimated time**: ~3 min/frame × 300 = 15 h, plus gold tracks (~1 h) and QA (~3 h). In total, ~20 person-hours.
- **Format**:
  - `gold/masks/<test>_<view>_<pts>.png`, as index PNG: 0 background, 1 blue, 2 soot, 255 ignore;
  - `gold/points.csv`: test, view, pts, type, x_px, y_px, annotator;
  - `gold/manifest.json` with hash and version.
  - This directory is **read-only** for the agent: `research/experiment.py` may not open it, and `evaluate()` verifies that no file under `gold/` is read outside it (see §5).

### 2.6 External rate references
- `V_f,pub`: the published per-test rates, taken from the BASS-II Summary Report (`data/docs/Reports_BASS-II Summary Report.pdf`) and from the team's papers, transcribed by hand into `gold/published_rates.csv` with their source (page and figure).
  - NTRS: https://ntrs.nasa.gov/api/citations/20160000593/downloads/20160000593.pdf
  - Rods: https://www.ncbi.nlm.nih.gov/pmc/articles/PMC5760683/
  - TTU ICES: https://ttu-ir.tdl.org/items/41223c66-e96b-4a7e-b390-464e5241e88e
- If a value was read from a plot (digitized with WebPlotDigitizer), it is marked `source_type=digitized` and assigned a larger σ.

---

## 3. Scalar objective: `val_score` (lower is better)

### 3.1 Principles
1. **Anchored to external truth**:
   - segmentation is evaluated against the human gold;
   - the rate, against `V_f,gold` and `V_f,pub`;
   - forecasting, on **frozen reference** series, not on the series produced by the edited pipeline itself.
   - Otherwise, the agent can "make forecasting easier" by smoothing or flattening its own series.
2. **Normalized by a frozen baseline**: each component is divided by the value of **pipeline v0** (the classical one of `computer_vision.md` §8 with the models of `time_series_forecasting.md` §13). v0 scores ~1 on each component, so the weights are meaningful and no component dominates because of its units.
3. **Per-test aggregation**, so that long tests do not dominate, and **robust**: 10 % trimmed mean across tests.
4. **Hard gates**: an experiment that violates them is rejected regardless of its score.

### 3.2 Components (all are "error / error_v0")

| Symbol | Component | Computation | Weight |
|---|---|---|---|
| `D` | Segmentation error | `(1 − mDice) / (1 − mDice_v0)`. mDice is the per-test mean of the total-flame Dice over the gold-dev frames; pixels labeled 255 are ignored. Frames with no flame in the gold and no prediction count as Dice = 1 | 0.15 |
| `E` | Leading-edge error | `MedAE_LE / MedAE_LE,v0`. It is the per-test median of `|x_LE,pred − x_LE,gold|` in mm, over the gold points and the gold tracks. An undetected edge (NaN) where the gold has flame counts as a 5 mm error | 0.20 |
| `R` | Spread-rate error | `mean_tests |ln(V̂_f / V_f,ref)| / (same for v0)`. `V_f,ref` is `V_f,gold` if it exists, otherwise `V_f,pub`; each test is weighted by `1/(σ_ref² + 0.05²)`, normalized. The log-ratio is symmetric and scale-free | 0.20 |
| `C` | Probabilistic forecasting error | `CRPS / CRPS_linear-local`, averaged over h ∈ {1, 2, 5, 10} s and over the variables {Δx_LE (weight 0.7), log A (weight 0.3)}. Computed with rolling-origin (origins every 1 s) on the dev tests, on the **frozen reference series** `ref_series_v{N}.parquet`, with LOTO evaluation for the global models. Here the denominator is linear-local rather than v0, so that it is a physically meaningful skill score | 0.25 |
| `M` | Point forecasting error | `MAE / MAE_linear-local` under the same conditions as `C` (q50 median) | 0.10 |
| `P` | Calibration penalty | `max(0, |cov90 − 0.90| − 0.03) / 0.07`, clipped to [0, 1]. It is 0 if the 90 % interval coverage falls in [0.87, 0.93] and 1 if the deviation is 0.10 or more | 0.10 |

```
val_score = 0.15·D + 0.20·E + 0.20·R + 0.25·C + 0.10·M + 0.10·P
```
- **Reading scale**:
  - Pipeline v0 with forecasting equal to linear-local gives `val_score ≈ 0.90 + 0.10·P_v0`, because D=E=R=C=M=1.
  - A value below 0.90 indicates a net improvement.
  - Useful bounds: perfection (D=E=R=0 with a perfect forecast) gives 0; the "human ceiling" is estimated by replacing the predictions with those of the second annotator.
- **Why these weights**:
  - The leading edge and the rate (E and R, 0.40 combined) are the main scientific product.
  - Forecasting (C+M+P, 0.45) is the declared goal of the project.
  - Dice (0.15) weighs less because full masks are ambiguous at the dim periphery, whereas the edge position is better defined.

### 3.3 Hard gates (if any fails → `val_score = +inf` and the harness reverts the snapshot)
- Evaluation time is 10 min or less and VRAM does not exceed 90 % of the GPU.
- The **failure rate is 5 % or less**: a dev test fails if it produces no `V_f` or if more than 30 % of its propagation frames have a NaN edge.
- No NaN or inf in the quantiles, and the quantiles are monotonic (q05 ≤ q25 ≤ … ≤ q95).
- **Physical trends** on the dev tests, with a Spearman test in which the sign suffices:
  - `V_f` must increase with O2 at fixed material and flow;
  - in thin films, `V_f` must decrease with thickness.
  - If a trend is inverted with p < 0.05, the experiment is rejected. This prevents "winning" by fitting noise.
- `research/experiment.py` does not read `gold/`, `holdout/` or `published_rates.csv`. This is verified with a file-open audit hook (`sys.addaudithook` in `evaluate`) and with a grep for literal test IDs (e.g. `B12` or `"O7"`) in `research/experiment.py`.

### 3.4 Acceptance rule (avoid chasing noise)
- Compute the **paired SE** of `Δval_score` by a bootstrap over tests (B = 500 replicates, resampling the dev tests with replacement and recomputing both versions).
- **The snapshot is kept** (promoted to `research/best/` by the harness) if `Δ = val_new − val_best < −max(0.005, 1.5·SE_Δ)`; otherwise it is reverted.
- **Simplicity criterion**, as in autoresearch: if `|Δ| ≤ 1.5·SE_Δ` and the diff **reduces** lines or dependencies, the snapshot is also kept.
- `results.tsv` logs: `commit, val_score, D, E, R, C, M, P, cov90, SE_Δ, runtime_s, status(keep/discard/crash/gate_fail), description`. (Since no git is used, the `commit` column holds the run/snapshot ID in `research/runs/`.)

---

## 4. Preventing overfitting to the metric

1. **Sealed test holdout**:
   - **25 holdout tests** are reserved, stratified by PI and material, including the 10 gold-holdout tests and 3–4 gold tracks.
   - Their frames, labels and series are never loaded during the loop.
   - The holdout is evaluated only by a **human** (script `evaluate_holdout.py` outside the agent's repo or behind a key), every ~20 accepted snapshots and at the end.
   - The agent only sees the aggregated holdout scalar, if it is shown at all, and never per-test metrics.
2. **LOPO (leave-one-PI-out) split as a secondary metric**, reported but not optimized. If `val_score` improves and LOPO worsens, it is a warning sign: specialization on the dominant configurations.
3. **Monitor the dev–holdout gap**: if `val_holdout − val_dev` grows by more than 0.05 relative to the initial gap, stop the loop, review with a human and restore the last snapshot (in `research/runs/` / `research/best/`) with an acceptable gap.
4. **Experiment budget**: a maximum of ~200 evaluations per phase. Each evaluation consumes "degrees of freedom" of the dev set (adaptive data analysis problem, Dwork et al. 2015, https://arxiv.org/abs/1411.2664). At the end of a phase, the holdout may **rotate**: 5 new tests are relabeled.
5. **Explicit prohibitions in `program.md`**:
   - no per-test parameters (if test_id …);
   - no reading labels;
   - no using `V_f,pub` as a feature;
   - no changing the steady-window definition as a function of the evaluation;
   - no installing new packages (closed list in `pyproject.toml`).
6. **The reference series for forecasting are frozen** (`ref_series_v{N}`). The agent cannot regenerate them; only a human promotes a new version, when CV improves on the holdout, and the `C` baseline is recomputed when doing so.
7. **Reproducibility**: fixed seeds, `torch.use_deterministic_algorithms(True)` where possible, and 2 seeds for stochastic models (averaged).
8. **Mandatory visual review every N acceptances**: figures G1, G2 and G4 (§6) are generated automatically for 5 random tests. A numerical improvement with worse overlays (e.g. masks that "stick" to the gold by chance) is discarded.
9. **Human ceiling**: once E or D reach inter-annotator agreement, there is no point in optimizing them further. Those weights are frozen and the loop focuses on forecasting.

---

## 5. Segmentation and measurement metrics (detail)

| Metric | Definition | Comment |
|---|---|---|
| **IoU** | `|P∩G|/|P∪G|` | Reported together with Dice. Stricter for small objects |
| **Dice / F1** | `2|P∩G|/(|P|+|G|)` | Component `D` |
| **Boundary F-score** (BF, tolerance 0.5 mm) | Precision and recall of contour pixels within ≤ τ | Sensitive to the dim edge; secondary metric |
| **Hausdorff 95** | 95th percentile of the distance between contours (mm) | Detects reflections included by mistake |
| **Leading-edge error** | `|x_pred − x_gold|` (mm); median, p90 and bias (sign) are reported | The **bias** indicates whether the threshold is too high (lagging edge) |
| **Rate error** | `|ln(V̂/V_ref)|`, relative error in %, Bland-Altman | Component `R` |
| **Area** | `|A_pred − A_gold|/A_gold` | Secondary |
| **V_f uncertainty coverage** | Fraction of tests with `|V̂ − V_ref| ≤ 2·sqrt(σ_V² + σ_ref²)` | Checks that the uncertainty propagation (`computer_vision.md` §7.3) is honest: it should give ~95 % |

Tools: `numpy` for IoU, Dice and BF; `scipy.ndimage.distance_transform_edt` for contour distances. Refs:
- Segmentation metrics (Taha & Hanbury 2015): https://bmcmedimaging.biomedcentral.com/articles/10.1186/s12880-015-0068-x
- Metrics Reloaded (Maier-Hein et al. 2024): https://www.nature.com/articles/s41592-023-02151-z

Forecasting metrics: see `time_series_forecasting.md` §12.

---

## 6. Scientific figures

Minimum set of explanatory figures for the final report. Each is generated by a deterministic script (`figures/make_G*.py`) from the results parquet files.

**Common conventions**:
- SI units (mm, s, mm/s and cm/s for flow);
- `t = 0` at ignition;
- the leading edge is always marked with the same color;
- accessible palette and perceptual colormap (`viridis`/`cividis` for quantities and `RdBu` for residuals);
- uncertainties always visible;
- the test ID and conditions (material, O2, flow) go in the title or legend.

| # | Figure | What it shows | How to read it |
|---|---|---|---|
| **G1** | **Frame + mask overlay** (4-panel: original, enhanced, blue/soot mask in semi-transparent colors, and contour + leading-edge marker + mm scale bar) for 3–4 instants of a test | What the pipeline considers to be "flame" | The contour must cover the dim blue base and exclude reflections and the igniter. The LE marker must sit at the upstream tip (opposed flow). Nothing should appear in the background |
| **G2** | **Kymograph / x–t space-time diagram**: the x axis is the position along the sample (mm), the y axis is time (s), and the color is the intensity profile `p(x,t)` of the central band (log or gamma). `x_LE(t)` and `x_TE(t)` are overlaid | The full propagation in a single image | A tilted luminous band indicates propagation. The edge **slope** is `1/V_f`, because t is vertical; with the axes swapped it would be V_f. A straight line indicates a constant rate and curvature indicates acceleration or deceleration. If the band thins or fades, extinction is approaching. Horizontal stripes indicate AE or bad frames |
| **G3** | **Leading-edge position vs time with fit**: `x_LE(t)` points with σ_x bars, the OLS line over the steady window (shaded) with its 95 % band, the manual gold points and, in a subpanel, the residuals | The `V_f` estimate and its quality | The slope is `V_f ± σ_V` (annotated). Residuals must be structureless noise; if they curve, the linear model is inadequate and §6 of forecasting must be used. Gold points must fall on the curve |
| **G4** | **Instantaneous `V_f(t)`** (Savitzky-Golay and Kalman RTS with band) | Rate stability during the test | A plateau indicates the steady regime, which defines the fit window. Drops at the end indicate the approach to extinction |
| **G5** | **Spread rate vs flow velocity, colored by O2** (marker by material or thickness, ±σ_V error bars, published values as hollow markers) | The main physical result across the test set | `V_f` is expected to increase with O2 (warmer colors on top). Versus flow, a maximum should appear at low flow (radiative regime, in microgravity) or a monotonic increase, depending on the material. Agreement between hollow (published) and filled markers validates the pipeline |
| **G6** | **Parity `V̂_f` vs `V_f,pub` / `V_f,gold`** (log-log, 1:1 line, ±10 % and ±25 % bands) and a **Bland-Altman** | Measurement accuracy | Points on the diagonal mean agreement. A systematic offset indicates a scale or threshold error. In the Bland-Altman, the mean of the differences is the bias and the ±1.96σ lines are the limits of agreement |
| **G7** | **Area and length vs time** (A_total, A_blue and A_soot stacked; L_f and W_f in stacked panels sharing the time axis (no dual y-axis); logistic or decay fit overlaid) | The evolution of flame size and composition | Growth to a plateau indicates a stable flame. If the soot fraction grows, the flame is sootier, with more O2 or more concurrent flow. Exponential decay anticipates extinction |
| **G8** | **Standoff δ(t)** and the y-profile of the side view (only in tests with 2ND_VIEW) | Flame structure perpendicular to the surface | A δ that grows in low-flow tests indicates a more diffusive flame. Compare with theory where applicable |
| **G9** | **Forecast vs observed with intervals**: history up to t0 (black), future observation (gray), forecast median (color) and 50 % and 90 % bands for 3 origins t0 of a test, with several models in facets | Predictive ability and honesty of the uncertainty | The observation should fall within the 90 % band ~9 times out of 10. The bands must **widen** with the horizon. A model whose median flattens (mean reversion) against a linear `x_LE` is misspecified |
| **G10** | **Forecast residuals**: error vs horizon (boxplots per model) and error vs test time, plus the ACF of the residuals at h = 1 | Whether unmodeled structure remains | Bias should be ≈ 0 at all h. A significant ACF indicates unexploited information |
| **G11** | **Skill vs horizon** (MAE/MAE_linear and CRPS/CRPS_linear vs h, one line per model, with bootstrap CIs over tests) | Which model wins and at what lead time | A value below 1 means the model beats the linear baseline. There are often models that win at short lead times and lose at long ones |
| **G12** | **Calibration diagram (reliability / PIT)**: empirical vs nominal coverage for 50/80/90/95 %, and PIT histogram | Probabilistic calibration | The diagonal indicates perfect calibration. If the points lie below it, the intervals are too narrow (overconfidence). A U-shaped PIT indicates narrow intervals; a hump-shaped one, wide intervals |
| **G13** | **Test-condition map**: O2 vs flow, with markers by material, colored by outcome (sustained propagation or extinction) and with the approximate flammability boundary | Experimental coverage and the flammability limit in microgravity | Shows where there is data and where extrapolation happens. Extinction tests define the limit (compare with https://ttu-ir.tdl.org/items/1922ad9f-ef4c-4f52-96a4-980c23debe5e) |
| **G14** | **Camera and QC diagnostics**: relative gain `g(t)`, reference ROI median, σ_bg(t), saturated fraction and AE events flagged, time-aligned with `x_LE(t)` | Whether the camera altered the measurement | A jump in `g(t)` simultaneous with a jump in A(t) or x_LE(t) indicates an artifact, not physics. Justifies excluding segments |
| **G15** | **Threshold sensitivity**: `V_f` vs k (3–8 σ) and Dice vs k, for several tests | Robustness of the operational edge definition | Flat curves indicate a robust measurement. Strong dependence indicates a dim flame or diffuse edge, and therefore a larger systematic uncertainty |
| **G16** | **Autonomous loop progress** (like `autoresearch/progress.png`): `val_score` vs experiment number, with kept and discarded points, the best-value line and the holdout at checkpoints | Traceability of the optimization | Dev decreases monotonically. The holdout should follow it; if it diverges, there is overfitting (§4) |
| **G17** | **Segmenter comparison** (panel of difficult cases: classical, U-Net, SAM2 and gold) and a table of Dice, E and BF per material | Why the default segmenter was chosen | Shows the concrete failure modes (reflections, lost blue base, blooming) |

**Format recommendations**:
- PNG at 300 dpi and vector PDF;
- 1- or 2-column width;
- font size ≥ 8 pt;
- all axes with units;
- a 2–3 sentence caption stating **what is shown and what to conclude**;
- the data of each figure are saved as CSV next to the image, for reproducibility.

---

## 7. Final evaluation checklist (report)
- [ ] Dev and holdout `val_score`, with all components and the bootstrap CI.
- [ ] Inter-annotator agreement (ceiling) vs pipeline performance.
- [ ] A per-test `V_f` table with σ_V, the published reference and the error.
- [ ] A forecasting skill table per model, horizon and variable, with coverage.
- [ ] LOPO as the generalization metric.
- [ ] Figures G1–G17 (at least G1–G7, G9, G11 and G12 in the main body; the rest in the appendix).
- [ ] Limitations: relative intensity (no radiometric calibration), homography parallax, ambiguity of the dim edge and foundation-model licenses (Moirai is NC).
