"""SAME AutoResearch candidate model. THE ONLY FILE EDITED DURING THE SEARCH.

Contract (see program.md):
    fit_predict_size(train_X, train_Y, eval_X, seed) -> (n_eval, 5) array
        targets: log10 Dg, log10 Dm, log10 AMD, ln sigma_g, log10 M0
    fit_predict_detection(train_X, train_Y, eval_X, seed) -> (n_eval, 2) probabilities
        targets: ISS photoelectric proxy alarm, ionization-chamber proxy alarm
    describe_model() -> dict with model_name, num_params, formula/notes

X dicts hold numpy arrays: material (str), aged, aging_s, flow_velocity_cm_s, no_flow, rt_r0
(+ push_index for detection). Do not read files or use run/test identifiers.
"""
import warnings

import numpy as np
from sklearn.linear_model import LogisticRegressionCV, RidgeCV

warnings.filterwarnings("ignore", category=FutureWarning)

MODEL_NAME = "ridgecv_hc_coag_size__logit_logaging_detection"
LN10 = np.log(10.0)
K_COAG = 1.25e-9
N0_FLOW = 3.0e6
MATERIALS = ["Kapton", "Lampwick", "Pyrell", "Silicone", "Teflon"]
ALPHA = 1.0
C_LOGIT = 1.0


def _design_detection(X):
    mat = np.stack([(X["material"] == m).astype(float) for m in MATERIALS], axis=1)
    cols = [mat, np.log1p(X["aging_s"])[:, None] / 7.0, X["no_flow"][:, None], (X["rt_r0"][:, None] - 1.35) * 5]
    return np.hstack(cols)


def _design(X):
    mat = np.stack([(X["material"] == m).astype(float) for m in MATERIALS], axis=1)
    # Smoluchowski constant-kernel coagulation: N0/N = 1 + K N0 t, K = 1.25e-9 cm3/s (NASA
    # "ISS Coagulation" note), N0 ~ 3e6 /cm3 with flow, ~10x lower for quiescent (no-flow) smoke.
    kn0 = K_COAG * N0_FLOW * (1.0 - 0.9 * X["no_flow"])
    coag = np.log1p(kn0 * X["aging_s"])[:, None]
    cols = [mat, coag, X["no_flow"][:, None], (X["rt_r0"][:, None] - 1.35) * 5]
    return np.hstack(cols)


def fit_predict_size(train_X, train_Y, eval_X, seed):
    # Fit the three best-determined quantities, derive Dg and AMD with Hatch-Choate:
    # ln AMD = ln Dm - ln^2 sg ; ln Dg = ln Dm - 1.5 ln^2 sg
    direct = train_Y[:, [1, 3, 4]]  # log10 Dm, ln sigma_g, log10 M0
    m = RidgeCV(alphas=np.logspace(-2, 2, 9), alpha_per_target=True).fit(_design(train_X), direct)
    p = m.predict(_design(eval_X))
    log10_dm, ln_sg, log10_m0 = p[:, 0], np.clip(p[:, 1], 0.05, None), p[:, 2]
    ln_dm = log10_dm * LN10
    log10_amd = (ln_dm - ln_sg ** 2) / LN10
    log10_dg = (ln_dm - 1.5 * ln_sg ** 2) / LN10
    return np.column_stack([log10_dg, log10_dm, log10_amd, ln_sg, log10_m0])


def fit_predict_detection(train_X, train_Y, eval_X, seed):
    A, B = _design_detection(train_X), _design_detection(eval_X)
    out = np.zeros((len(B), train_Y.shape[1]))
    for j in range(train_Y.shape[1]):
        y = train_Y[:, j]
        if y.min() == y.max():
            out[:, j] = y[0]
            continue
        clf = LogisticRegressionCV(Cs=np.logspace(-2, 2, 9), cv=5, scoring="neg_brier_score",
                                   max_iter=4000).fit(A, y)
        out[:, j] = clf.predict_proba(B)[:, 1]
    return out


def describe_model():
    return {
        "model_name": MODEL_NAME,
        "num_params": 3 * 9 + 2 * 9,
        "formula": "y_j = ridge(material one-hot + ln(1 + K N0 t) + no_flow + 5(Rt/R0-1.35)), K N0 = 3.75e-3/s "
                   "(x0.1 no-flow); Dg, AMD via Hatch-Choate; detection: "
                   "logit P_j = material + log1p(aging)/7 + no_flow + 5(Rt/R0-1.35), L2 logistic (inner-CV C)",
        "notes": "Ridge on log Dm, ln sigma_g, log M0; Dg and AMD derived by Hatch-Choate. Per-target alpha by GCV; logistic C by inner 5-fold Brier.",
    }
