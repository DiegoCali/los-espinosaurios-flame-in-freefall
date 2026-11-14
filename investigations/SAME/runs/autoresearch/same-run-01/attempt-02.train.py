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
import numpy as np
from sklearn.linear_model import LogisticRegression, Ridge

MODEL_NAME = "ridge_logistic_material_logaging_noflow"
MATERIALS = ["Kapton", "Lampwick", "Pyrell", "Silicone", "Teflon"]
ALPHA = 1.0
C_LOGIT = 1.0


def _design(X):
    mat = np.stack([(X["material"] == m).astype(float) for m in MATERIALS], axis=1)
    cols = [mat, np.log1p(X["aging_s"])[:, None] / 7.0, X["no_flow"][:, None], (X["rt_r0"][:, None] - 1.35) * 5]
    return np.hstack(cols)


def fit_predict_size(train_X, train_Y, eval_X, seed):
    m = Ridge(alpha=ALPHA, fit_intercept=False).fit(_design(train_X), train_Y)
    return m.predict(_design(eval_X))


def fit_predict_detection(train_X, train_Y, eval_X, seed):
    A, B = _design(train_X), _design(eval_X)
    out = np.zeros((len(B), train_Y.shape[1]))
    for j in range(train_Y.shape[1]):
        y = train_Y[:, j]
        if y.min() == y.max():
            out[:, j] = y[0]
            continue
        clf = LogisticRegression(C=C_LOGIT, max_iter=2000).fit(A, y)
        out[:, j] = clf.predict_proba(B)[:, 1]
    return out


def describe_model():
    return {
        "model_name": MODEL_NAME,
        "num_params": 5 * 8 + 2 * 9,
        "formula": "size_j = ridge(material one-hot + log1p(aging)/7 + no_flow + 5(Rt/R0-1.35)); "
                   "logit P_j = same design, L2 logistic (C=1)",
        "notes": "Linear physics-motivated design; ridge alpha=1.",
    }
