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

MODEL_NAME = "training_mean_baseline"


def fit_predict_size(train_X, train_Y, eval_X, seed):
    n = len(eval_X["material"])
    return np.tile(train_Y.mean(axis=0), (n, 1))


def fit_predict_detection(train_X, train_Y, eval_X, seed):
    n = len(eval_X["material"])
    return np.tile(train_Y.mean(axis=0), (n, 1))


def describe_model():
    return {
        "model_name": MODEL_NAME,
        "num_params": 7,
        "formula": "size target_j = training mean_j (5 params); P(detect_j) = training prevalence_j (2 params)",
        "notes": "Baseline required as attempt 1.",
    }
