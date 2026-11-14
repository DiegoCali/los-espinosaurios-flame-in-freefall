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
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import RBF, ConstantKernel, WhiteKernel
from sklearn.linear_model import RidgeCV

warnings.filterwarnings("ignore", category=FutureWarning)

MODEL_NAME = "ridge_plus_gp_residual__betabinomial"
LN10 = np.log(10.0)
PRIOR_STRENGTH = 2.0
AGED_S = 120.0
K_COAG = 1.25e-9
N0_FLOW = 3.0e6
MATERIALS = ["Kapton", "Lampwick", "Pyrell", "Silicone", "Teflon"]


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
    A, B = _design(train_X), _design(eval_X)
    m = RidgeCV(alphas=np.logspace(-2, 2, 9), alpha_per_target=True).fit(A, direct)
    p = m.predict(B)
    resid = direct - m.predict(A)
    for j in range(direct.shape[1]):
        kern = ConstantKernel(0.1, (1e-3, 10)) * RBF(1.0, (0.1, 20)) + WhiteKernel(0.5, (1e-3, 5))
        gp = GaussianProcessRegressor(kern, normalize_y=True, n_restarts_optimizer=2, random_state=seed)
        gp.fit(A, resid[:, j])
        p[:, j] += gp.predict(B)
    log10_dm, ln_sg, log10_m0 = p[:, 0], np.clip(p[:, 1], 0.05, None), p[:, 2]
    ln_dm = log10_dm * LN10
    log10_amd = (ln_dm - ln_sg ** 2) / LN10
    log10_dg = (ln_dm - 1.5 * ln_sg ** 2) / LN10
    return np.column_stack([log10_dg, log10_dm, log10_amd, ln_sg, log10_m0])


def fit_predict_detection(train_X, train_Y, eval_X, seed):
    # Hierarchical beta-binomial shrinkage: global -> flow regime -> (flow, material) -> (flow, material, aged).
    a = PRIOR_STRENGTH
    out = np.zeros((len(eval_X["material"]), train_Y.shape[1]))
    for j in range(train_Y.shape[1]):
        y = train_Y[:, j].astype(float)
        p_glob = (y.sum() + 1.0) / (len(y) + 2.0)
        for i in range(len(eval_X["material"])):
            f = train_X["no_flow"] == eval_X["no_flow"][i]
            p_flow = (y[f].sum() + a * p_glob) / (f.sum() + a)
            c = f & (train_X["material"] == eval_X["material"][i])
            p_cell = (y[c].sum() + a * p_flow) / (c.sum() + a)
            g = c & ((train_X["aging_s"] > AGED_S) == (eval_X["aging_s"][i] > AGED_S))
            out[i, j] = (y[g].sum() + a * p_cell) / (g.sum() + a)
    return out


def describe_model():
    return {
        "model_name": MODEL_NAME,
        "num_params": 3 * 12 + 2 * 33,
        "formula": "y_j = ridge(material one-hot + ln(1 + K N0 t) + no_flow + 5(Rt/R0-1.35)), K N0 = 3.75e-3/s "
                   "(x0.1 no-flow); Dg, AMD via Hatch-Choate; detection: "
                   "P_j = beta-binomial rate in (flow, material, aged) -> (flow, material) -> flow regime -> global, a=2",
        "notes": "Ridge on log Dm, ln sigma_g, log M0 plus a GP (RBF + white noise, ML-II) on ridge residuals; Dg and AMD by Hatch-Choate.",
    }
