# Flame time-series forecasting (BASS-II)

> Methods knowledge base — forecasting of flame evolution.
> **Input**: the per-test series produced by the vision pipeline (`computer_vision.md` §8):
> - `x_LE(t)` (leading edge, mm), `V_f(t)` (mm/s), `A(t)` (mm²), `L_f(t)`, `W_f(t)`, `δ(t)` and `I_sum(t)`;
> - static test covariates: material, thickness, width, O2 %, flow (cm/s), PI, opposed or concurrent;
> - the `qc_flags`.
>
> Last revised: 2026-11-12.

---

## 0. Problem formulation

**Nature of the series**:
- There are ~130 tests, each lasting from tens of seconds to a few minutes.
- After resampling to 2–5 Hz, there are between ~100 and ~2000 points per series.
- The series are noisy (segmentation, AE, H.264), **non-stationary** (ignition → steady regime → extinction or end of sample) and governed by fairly simple physics: approximately linear propagation in the steady regime, growth toward a plateau in flame size, and decay toward extinction near the flammability limit.

**Forecasting tasks** (define them explicitly; each has its own baseline):
- **T1 — Within-test forecasting (rolling)**: given the history `y(t ≤ t0)` of a test, predict `y(t0 + h)` for h ∈ {1, 2, 5, 10} s. The primary variable is `x_LE`; secondary ones are `A` and `L_f`.
- **T2 — Forecasting full behavior from conditions (cold-start)**: given material, O2, flow and thickness, with no history or only the first 2–5 s, predict the steady-regime `V_f` and the `A(t)` curve. This is a cross-test regression problem.
- **T3 — Event classification or forecasting**: probability of extinction before `t0 + H`, and time to extinction. This is survival or hazard modeling.

**Formulation recommendations**:
- Forecast `x_LE(t0+h) − x_LE(t0)` (the **displacement**) instead of the absolute level, to remove the arbitrary offset. For `A`, work in `log A`.
- Resample to a uniform grid of **Δt = 0.2 s (5 Hz)** with the per-bin median. Keep `n_valid` and `σ` per bin, mask bins with bad QC, and do not interpolate if the gap lasts more than 1 s.
- **Minimum forecast origin**: t0 ≥ t_ign + 3 s, to have enough history.

---

## 1. Baselines (mandatory; every method must beat them)

| Baseline | Definition | Why |
|---|---|---|
| **Persistence (naive)** | `ŷ(t0+h) = y(t0)` | The MASE reference. Poor for `x_LE`, because it ignores propagation |
| **Random walk with drift** | `ŷ(t0+h) = y(t0) + h·(y(t0) − y(t0−w))/w` | The drift comes from the recent window (w = 2 s) |
| **Linear local (OLS)** | Line over the last window w ∈ {2, 5, 10} s, extrapolated | Matches the physics (constant V_f) and is usually **very hard to beat** for `x_LE` |
| **Theil-Sen local** | Same as above, but robust | For outliers |
| **Seasonal naive** | Not applicable (no seasonality) | — |
| **Conditional climatology** (T2) | Mean `V_f` of tests with the same material and O2 and flow bin | Cross-test baseline |

**Rule**: the official metric uses the **linear-local w=5 s** as denominator (skill score), not persistence. This prevents a method from "winning" by beating a trivially bad baseline.

---

## 2. ARIMA / ETS (statsmodels, statsforecast)

- **ARIMA(p,1,q)** with drift on `x_LE`: equivalent to a stochastic linear trend.
  - `statsmodels.tsa.arima.model.ARIMA(y, order=(1,1,1), trend="t")`.
  - With `auto_arima` (statsforecast `AutoARIMA`), bound p,q ≤ 2 for short series.
- **ETS with damped additive trend** (`ExponentialSmoothing(trend="add", damped_trend=True)` or `ETSModel`): captures both the "linear spread" and the deceleration toward extinction. Prediction intervals come from the innovations model (`ETSModel.get_prediction().summary_frame(alpha=0.1)`).
- **Pros**: analytic intervals, speed, interpretability. **Cons**: they assume a stable process and do not see the regime change; a per-test fit with few points is unstable.
- **Use**: fit them per test over the window from the end of the transient to t0, and refit at each origin.
- Docs:
  - https://www.statsmodels.org/stable/generated/statsmodels.tsa.arima.model.ARIMA.html
  - https://www.statsmodels.org/stable/generated/statsmodels.tsa.exponential_smoothing.ets.ETSModel.html
  - https://nixtlaverse.nixtla.io/statsforecast/
  - Reference book: Hyndman & Athanasopoulos, *Forecasting: Principles and Practice* (3rd ed.) https://otexts.com/fpp3/

---

## 3. Why physics matters: reference model

For thin films in opposed flow, de Ris theory and Bhattacharjee's extensions give an approximately constant `V_f` in the steady regime.

In microgravity, at very low flow, the **radiative regime** appears: `V_f` drops as flow decreases and extinction may occur. That is why `x_LE(t)` is nearly linear and `A(t)` tends to a plateau, or decays toward extinction.

Models that incorporate this structure win with little data. References:
- https://ttu-ir.tdl.org/items/41223c66-e96b-4a7e-b390-464e5241e88e
- https://www.ncbi.nlm.nih.gov/pmc/articles/PMC5760683/

---

## 4. State-space / Kalman filters

### 4.1 Constant-velocity (CV) model — recommended for `x_LE`
```
state s = [x, v]ᵀ ;  s_{k+1} = F s_k + w_k ;  F = [[1, Δt],[0, 1]]
Q = q · [[Δt³/3, Δt²/2],[Δt²/2, Δt]]   (white-noise acceleration, q in mm²/s³)
z_k = H s_k + ε_k ;  H = [1, 0] ;  R = σ_x²  (from the subpixel edge uncertainty, per frame)
```
- **h-step forecast**:
  - `ŝ_{k+h} = F^h ŝ_k` and `P_{k+h} = F^h P F^hᵀ + Σ F^i Q F^iᵀ`.
  - The Gaussian interval is `x̂ ± z_{α/2} √P_xx`.
- **Hyperparameters**:
  - `q` is fitted by maximum likelihood (MLE) on the training tests, shared per material, or replaced by a per-test `q`.
  - `R` comes from σ_x or from MLE.
- **With covariates**: the prior initial velocity `v0` and its variance are taken from a cross-test model (T2), a hierarchical prior: `v0 ~ N(f(O2, flow, material, thickness), σ²)`. This helps a lot at the start of each test (cold-start).
- **Variants**:
  - **Constant acceleration (CA)**: state `[x, v, a]`, for deceleration.
  - **IMM** (Interacting Multiple Models, CV + CA + "stopped"): useful for detecting the transition to extinction.
  - **RTS smoother**: for offline analysis, because it gives a smoothed `V_f(t)` with an uncertainty band.
- **Implementation**:
  - `statsmodels.tsa.statespace` (`UnobservedComponents(level="local linear trend")` is equivalent to CV, with MLE included and `get_forecast()` with intervals);
  - or `filterpy` 2.0.0, or `pykalman` 0.11.2, or a custom 30-line numpy Kalman filter (recommended for transparency).
- Docs:
  - https://www.statsmodels.org/stable/generated/statsmodels.tsa.statespace.structural.UnobservedComponents.html
  - https://filterpy.readthedocs.io/
  - Labbe, *Kalman and Bayesian Filters in Python*: https://github.com/rlabbe/Kalman-and-Bayesian-Filters-in-Python

### 4.2 For `A(t)` and `log A(t)`
- **Local level + AR(1)** or damped local linear trend on `log A`.
- Alternatively, a nonlinear Kalman filter (EKF/UKF) on the logistic model of §6.

---

## 5. Gaussian processes

- **Kernel**: `ConstantKernel · (DotProduct + RBF(ℓ ∈ [1, 20] s)) + WhiteKernel`. The linear part (propagation trend) is added to a smooth deviation plus noise.
  - Alternatively, Matern-3/2 + Linear.
  - For extrapolation, the **linear kernel** dominates beyond ℓ. The prediction thus returns to the linear trend with growing variance, which gives reasonable intervals.
- **Scale**: with N ≤ 2000 points per test, an exact GP with `sklearn.gaussian_process.GaussianProcessRegressor` is feasible (O(N³), ~1 s). If needed, downsample to 2 Hz.
- **Multi-task or hierarchical cross-test GP**: with `gpytorch` (variational/multitask), hyperparameters are shared across tests of the same material.
- **Pros**: well-calibrated intervals if the kernel is reasonable. **Cons**: with purely stationary kernels (RBF) the prediction reverts to the mean outside the window, which is inappropriate for `x_LE`. That is why the linear term is always included.
- Docs:
  - https://scikit-learn.org/stable/modules/gaussian_process.html
  - https://gpytorch.ai/
  - Rasmussen & Williams, *GPML*: https://gaussianprocess.org/gpml/

---

## 6. Physics-informed parametric fits

| Model | Equation | Variable | When |
|---|---|---|---|
| **Linear spread** | `x(t) = x0 − V (t − t_s)` | `x_LE` | Steady regime (the default) |
| **Linear + exponential transient** | `x(t) = x0 − V t − D(1 − e^{−t/τ})` | `x_LE` | Initial acceleration or deceleration after ignition |
| **Growth-to-plateau (logistic)** | `A(t) = A∞ / (1 + e^{−r(t − t_m)})` | `A`, `L_f` | Growth toward a stable size |
| **Exponential saturation** | `A(t) = A∞ (1 − e^{−(t−t_i)/τ})` | `A` | 2-parameter alternative |
| **Decay to extinction** | `A(t) = A_p e^{−(t − t_d)/τ_d}` (for t > t_d), extinction when `A < A_min` | `A`, `I_sum` | Tests near the O2 or flow limit |
| **Decaying velocity** | `V(t) = V∞ + (V0 − V∞) e^{−t/τ}` | `V_f` | Integrates to `x(t)` |
| **Piecewise / change-point** | Piecewise linear with k segments (BIC) | `x_LE` | Regime changes |

- **Fitting**: `scipy.optimize.curve_fit` (with `sigma=σ_x` and `absolute_sigma=True`) or `least_squares(loss="soft_l1")` (robust). For probabilistic forecasting there are three routes:
  - the parameter covariance, propagated by the delta method or Monte Carlo;
  - a **block bootstrap of residuals**;
  - **Bayesian**: `emcee` or PyMC, with hierarchical priors `V ~ f(O2, flow, ...)`. The cp314 wheel of PyMC must be verified; emcee is pure.
- **Per-test model selection**: by AICc or BIC on the history (up to t0). Another option is an **ensemble weighted** by Akaike weights.
- **Strength**: they extrapolate with physical sense (they do not predict negative areas or absurd accelerations) and their parameters are interpretable (`V`, `A∞`, `τ`), which is what is of interest to report.

---

## 7. Gradient boosting with lag features (global cross-test model)

- **Global dataset**: for each (test, origin t0), a feature vector is formed and the target is `Δx(h) = x(t0+h) − x(t0)`, with one model per horizon (direct strategy) or h as a feature.
- **Features**:
  - `Δx` lags at {0.2, 0.5, 1, 2, 5} s;
  - local slopes (OLS over windows of 1, 2 and 5 s) with their SE;
  - curvature (quadratic coefficient);
  - `log A`, `L_f`, `W_f` and their slopes;
  - soot fraction `A_soot/A`;
  - time since ignition;
  - QC flags;
  - **static covariates**: material (categorical), thickness, width, O2, flow, opposed/concurrent and PI. PI is risky, because it can leak information (leakage); see §10.
- **Models**:
  - `lightgbm` 4.7.0 or `xgboost` 3.4.1 (py3 win_amd64 wheels OK), or `sklearn.ensemble.HistGradientBoostingRegressor`, which adds no dependencies.
  - **Quantiles** for the intervals: `objective="quantile"`, α ∈ {0.05, 0.5, 0.95}, or `HistGradientBoostingRegressor(loss="quantile")`.
- **Recommendation**: predict the **residual over the linear baseline** (`Δx − V_local·h`). The GBM then learns corrections (deceleration, O2 effect) and does not have to relearn the physics. This greatly reduces overfitting with little data.
- **Conservative hyperparameters**: `num_leaves` 15, `min_data_in_leaf` 50, `learning_rate` 0.05, 300–500 trees with early stopping **by group** (GroupKFold by test).
- Docs: https://lightgbm.readthedocs.io/ , https://scikit-learn.org/stable/modules/ensemble.html#histogram-based-gradient-boosting

---

## 8. Small neural models (LSTM / TCN)

- With ~130 tests (the effective number is lower, because several are near-duplicates or extinguish quickly), a neural model **rarely** beats Kalman or GBM-on-residual. It is only worth it as a bounded experiment.
- **Design, if attempted**:
  - Input: 10 s window at 5 Hz (50 steps) with channels `Δx`, `log A` and `L_f` plus static covariates (embedded and concatenated).
  - Output: quantiles for h = 1..50 steps (MQ-loss).
  - Architecture: 1-layer LSTM with 32–64 units, or 4-block TCN with dilations 1, 2, 4, 8 and 32 channels.
  - Regularization: dropout 0.2, weight decay, **early stopping on validation tests**.
- **Libraries**:
  - plain PyTorch (torch 2.15.0 cp314);
  - `neuralforecast` 3.3.1 (pure, requires lightning; verify that all its dependencies resolve on 3.14);
  - `darts` 0.48.1 (pure).
- **Data augmentation**: velocity scaling, noise, random window crops and mild time-warping.
- Refs:
  - TCN (Bai et al. 2018): https://arxiv.org/abs/1803.01271
  - DeepAR: https://arxiv.org/abs/1704.04110
  - neuralforecast: https://nixtlaverse.nixtla.io/neuralforecast/

---

## 9. Foundation time-series models (zero-shot)

| Model | PyPI package (version) | Py 3.14 | Weights license | Notes |
|---|---|---|---|---|
| **Chronos / Chronos-Bolt / Chronos-2** (Amazon) | `chronos-forecasting` 2.3.2 (pure; torch, transformers<6, accelerate) | **Yes** (dependencies with cp314 or pure wheels) | Apache-2.0 | Chronos-2 supports covariates and multivariate input. It is probabilistic (quantiles). Bolt-small or tiny runs on CPU |
| **TimesFM** (Google) | `timesfm` 3.0.2 (pure; numpy, huggingface_hub, safetensors and torch or jax backend as an extra) | Probable (verify the torch backend) | **TimesFM 2.5: Apache-2.0. TimesFM 3.0: non-commercial weights** (per secondary sources; confirm on the HF model card) | Gives quantiles. Use 2.5 to avoid restrictions |
| **Moirai / Moirai 2.0** (Salesforce) | `uni2ts` 2.0.0 | **No**: pins `numpy~=1.26`, `scipy~=1.11` and `gluonts~=0.14`, which have no wheels for 3.14 | **CC BY-NC 4.0** (research only) | If it is to be used, a separate environment with Python 3.11 (uv) is needed, isolated from the pipeline |
| Others (TiRex, Toto, Sundial) | various | verify | mostly Apache-2.0 | Consult the fev-bench or GIFT-Eval benchmark |

- **Recommended use**:
  - As a **zero-shot baseline**: give each model the normalized `Δx` or `log A` series up to t0 and ask for quantiles at h.
  - On short, smooth, nearly linear series, these models are usually **comparable to or worse** than linear-local or Kalman, because they tend toward mean reversion, seasonal patterns or "flattening".
  - They serve to demonstrate that physics adds value, and as ensemble members.
- **Fine-tuning**: not recommended with 130 tests, except for a minimal LoRA with group validation.
- **Legal use**: Chronos and TimesFM 2.5 allow any use; Moirai is non-commercial research only. If results are published, the license must be cited.
- Refs:
  - Chronos-2: https://arxiv.org/abs/2510.15821 ; repo https://github.com/amazon-science/chronos-forecasting
  - TimesFM: https://github.com/google-research/timesfm ; TimesFM licenses: https://www.mindstudio.ai/blog/timesfm-licensing-commercial-use
  - License comparison (secondary): https://www.beri.net/article/timesfm-vs-chronos-vs-moirai-time-series-foundation-model-licence-bigquery-sagemaker-cost-2026
  - Moirai / uni2ts: https://github.com/SalesforceAIResearch/uni2ts
  - fev-bench leaderboard: https://huggingface.co/spaces/autogluon/fev-bench

---

## 10. Probabilistic forecasting and intervals

### 10.1 Sources of intervals
- **Analytic**: ARIMA/ETS and Kalman (Gaussian).
- **Quantile-based**: GBM with quantile loss, networks with MQ-loss, Chronos or TimesFM.
- **Bootstrap**: block residuals on the parametric fits.
- **Bayesian**: posteriors of the physical parameters.

### 10.2 Conformal prediction (recommended as the final calibration layer)
- **Group split conformal**:
  1. Reserve calibration tests (not frames).
  2. Compute the scores `s = |y − ŷ|`, or better, normalized: `s = |y − ŷ|/σ̂`, to obtain adaptive intervals.
  3. The quantile `q̂ = Quantile_{⌈(n+1)(1−α)⌉/n}(s)` gives the interval `ŷ ± q̂·σ̂`.
- **CQR (Conformalized Quantile Regression)**: corrects the GBM or Chronos quantiles. It is the best option when quantiles are already available.
- **Temporal dependence problem**: scores within a test are autocorrelated, so calibrate with **one score per (test, h)** subsampled (e.g. one origin every 5 s) or use conformal with *groups* (exchangeability across tests, not across frames).
- **Adaptive Conformal Inference (ACI)** for online mode within a test: `α_{t+1} = α_t + γ(α − err_t)`, with γ = 0.005–0.05. It maintains coverage under regime change.
- **Libraries**:
  - `mapie` 1.6.0 (pure), with regression, CQR and time series (EnbPI/ACI);
  - `crepes` 0.9.1 (pure);
  - a custom implementation, which is ~20 lines and guarantees correct grouping.
- Refs:
  - Angelopoulos & Bates, *A Gentle Introduction to Conformal Prediction*: https://arxiv.org/abs/2107.07511
  - CQR (Romano et al. 2019): https://arxiv.org/abs/1905.03222
  - ACI (Gibbs & Candès 2021): https://arxiv.org/abs/2106.00170
  - EnbPI (Xu & Xie 2021): https://arxiv.org/abs/2010.09107
  - MAPIE: https://mapie.readthedocs.io/

---

## 11. Cross-validation without leakage

### 11.1 Levels
1. **Rolling-origin within each test** (T1 evaluation):
   - Origins `t0 ∈ {t_ign+3 s, +1 s, …}` up to `t_end − h_max`.
   - At each origin only data with `t ≤ t0` are used, and features, normalization and the steady window are also recomputed with data ≤ t0.
   - **Common mistake**: computing the "steady window" or the normalization `V_f` with the full series. That is *look-ahead leakage*.
   - Ref: Hyndman, *Time series cross-validation*: https://otexts.com/fpp3/tscv.html
2. **Leave-one-test-out (LOTO) / GroupKFold by test** (for the global GBM and NN models, the hierarchical prior and conformal calibration):
   - No frame of the evaluation test may be in training.
   - `sklearn.model_selection.GroupKFold(n_splits=5)` or `LeaveOneGroupOut` with `groups = test_id`.
3. **Leave-one-PI-out (LOPO)**:
   - There are 129 tests in `Experimental table_BASS-II.csv`, distributed as follows: T'ien 29, Olson 27, Fernandez-Pello 27, Bhattacharjee 22, Miller 20 and Ferkul 4. Ferkul is grouped with Olson.
   - Each PI uses a different material or configuration: PMMA films (Bhattacharjee), clear and black rods, SIBAL, Nomex, candles or spherical sections, and probably a different camera or settings.
   - LOPO measures **generalization to new configurations** and is the most honest evaluation for T2.
   - If a PI has very few tests, it is grouped with another of similar material.
4. **The two views of the same test** (front and 2ND_VIEW) **always go in the same fold**. The same applies to repetitions of the same sample or re-ignitions.

### 11.2 Nested scheme
- For hyperparameter selection: an outer LOTO or LOPO loop and an inner GroupKFold loop.
- The **final holdout** set (see `evaluation_protocol.md` §4) does **not** take part in any selection step.

---

## 12. Forecasting metrics

Notation: `y` is the actual value, `ŷ` the predicted median or mean, h the horizon and N the evaluated origins.

| Metric | Formula | Use |
|---|---|---|
| **MAE** | `mean|y − ŷ|` | In mm: interpretable for `x_LE` |
| **RMSE** | `sqrt(mean(y − ŷ)²)` | Penalizes large errors |
| **MASE** | `MAE_model / MAE_naive,in-sample` (Hyndman & Koehler 2006) | Scale-free, comparable across tests. Here a **per-test** denominator is used, computed with the one-step naive on its training history. Preferred variant: **skill relative to linear-local**, `MAE_model/MAE_linear` |
| **sMAPE** | `mean(2|y−ŷ|/(|y|+|ŷ|))` | **Not advisable** for `Δx` near 0 (it blows up); only for `A` or `L_f` > 0 |
| **CRPS** | `∫ (F(z) − 1{z ≥ y})² dz` | Probabilistic. With quantiles it is approximated by the mean pinball loss over quantiles 0.05..0.95. Libs: `scoringrules` 0.12.0, `properscoring` |
| **Interval coverage** | `mean(1{y ∈ [l, u]})` for a nominal 90 % PI | Must be 0.9 ± 0.03 |
| **Interval width / Winkler score** | `(u − l) + (2/α)(l − y)1{y<l} + (2/α)(y − u)1{y>u}` | Balances coverage and width |
| **Forecast `V_f` error** | `|V̂_f − V_f,obs|/V_f,obs` | For T2 |
| **Brier / AUROC** | on `P(extinction before t0+H)` | For T3 |

**Aggregation**:
1. First average per test (so each test carries the same weight, regardless of its duration).
2. Then average across tests, with the median and IQR as additional information.
3. Report per horizon h and aggregated (mean over h ∈ {1, 2, 5, 10} s).

Refs:
- Hyndman & Koehler 2006 (MASE): https://robjhyndman.com/papers/mase.pdf
- Gneiting & Raftery 2007 (scoring rules, CRPS): https://sites.stat.washington.edu/raftery/Research/PDF/Gneiting2007jasa.pdf
- scoringrules: https://frazane.github.io/scoringrules/

---

## 13. Default recommendation

1. **Primary model for `x_LE` (T1)**: constant-velocity Kalman. `q` and `R` are fitted by MLE on the training folds, and the `v0` prior comes from a cross-test regression (Huber on O2, flow, material and thickness). This is followed by **grouped conformal calibration** of the intervals.
2. **For `A` and `L_f`**: AICc ensemble of the parametric models of §6 (linear, logistic, decay) on `log A`, plus block bootstrap and conformal.
3. **Challenger**: `HistGradientBoostingRegressor(loss="quantile")` on the **linear-local residual**, with lag features and covariates, and GroupKFold.
4. **Zero-shot comparators**: Chronos-Bolt-small or Chronos-2 and TimesFM 2.5.
5. **Baselines** always present: persistence, drift and linear-local w = 5 s.
6. **Evaluation**: rolling-origin with origins every 1 s within the tests of a LOTO fold, with h ∈ {1, 2, 5, 10} s. Metrics: MAE (mm), skill vs linear-local, CRPS and 90 % coverage.

### Libraries (Python 3.14, verified on PyPI 2026-11-12)
| Package | Version | Status on 3.14 |
|---|---|---|
| statsmodels | 0.15.0 | cp314 ✔ |
| statsforecast | 2.1.1 | cp314 ✔ |
| scikit-learn | 1.9.1 | cp314 ✔ |
| lightgbm | 4.7.0 | py3-win_amd64 ✔ |
| xgboost | 3.4.1 | py3-win_amd64 ✔ |
| sktime | 1.3.0 | pure (<3.16) ✔ |
| filterpy | 2.0.0 | pure ✔ |
| pykalman | 0.11.2 | pure (<3.15) ✔ |
| GPy | 1.15.0 | cp314 ✔ |
| gpytorch | 1.15.2 | pure ✔ |
| mapie | 1.6.0 | pure ✔ |
| crepes | 0.9.1 | pure ✔ |
| scoringrules | 0.12.0 | pure ✔ |
| torch | 2.15.0 | cp314 ✔ |
| chronos-forecasting | 2.3.2 | pure ✔ (with torch and transformers 5.x) |
| timesfm | 3.0.2 | pure ✔ (verify the backend extra) |
| neuralforecast | 3.3.1 / darts 0.48.1 | pure; verify the dependency tree |
| uni2ts (Moirai) | 2.0.0 | ✘ (numpy~=1.26): separate environment |
| gluonts | 0.17.0 | pure (<3.15) ✔ |
