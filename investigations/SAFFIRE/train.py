"""Editable NumPy-only material/regime candidate; no filesystem or result access."""
import numpy as np

MODE = "group_dilution"
TERMS = ("non_silicone",)
ALPHA = 0.0
LOCATION = "huber20"
CONSTRAIN_THICKNESS = False
FLOW_POWER = 1.0
_state = {}


def _features(X):
    material = np.asarray(X["material"])
    flow = np.asarray(X["flow_pre_cm_s"], dtype=float)
    thickness = np.asarray(X["thickness_nominal_mm"], dtype=float)
    organic = (material != "Silicone").astype(float)
    silicone = 1.0 - organic
    sibal = (material == "SIBAL").astype(float)
    pmma = (material == "PMMA").astype(float)
    composite = (material == "PMMA_Nomex").astype(float)
    return {
        "non_silicone": organic,
        "sibal": sibal,
        "pmma": pmma,
        "pmma_nomex": composite,
        "log_thickness": np.log1p(thickness),
        "silicone_log_thickness": silicone * np.log1p(thickness / 0.37),
        "organic_dilution": organic * (20.0 / flow) ** FLOW_POWER,
        "organic_flow": organic * (flow / 20.0) ** FLOW_POWER,
        "flow_excess": (flow - 20.0) / 5.0,
        "opposed": (np.asarray(X["direction"]) == "opposed").astype(float),
        "structured_pmma": np.asarray(X["structured_pmma"], dtype=float),
        "long_ignition": (np.asarray(X["ignition_duration_command_s"]) - 9.2) / 20.8,
    }


def _location(y):
    if LOCATION == "median":
        return float(np.median(y))
    if LOCATION == "trimmed_mean":
        ordered = np.sort(y)
        return float(np.mean(ordered[1:-1])) if len(y) >= 4 else float(np.mean(y))
    if LOCATION == "huber20":
        center = float(np.median(y))
        for _ in range(40):
            residual = y - center
            weight = np.minimum(1.0, 20.0 / np.maximum(np.abs(residual), 1e-12))
            center = float(np.sum(weight * y) / np.sum(weight))
        return center
    return float(np.mean(y))


def fit_predict(train_X: dict, train_y, eval_X: dict, seed) -> np.ndarray:
    y = np.asarray(train_y, dtype=float)
    if MODE in ("group_location", "group_dilution"):
        training_group = np.asarray(train_X["material"]) != "Silicone"
        evaluation_group = np.asarray(eval_X["material"]) != "Silicone"
        training_scale = np.where(training_group, (20.0 / np.asarray(train_X["flow_pre_cm_s"])) ** FLOW_POWER, 1.0) if MODE == "group_dilution" else np.ones(len(y))
        evaluation_scale = np.where(evaluation_group, (20.0 / np.asarray(eval_X["flow_pre_cm_s"])) ** FLOW_POWER, 1.0) if MODE == "group_dilution" else np.ones(len(evaluation_group))
        normalized = y / training_scale
        levels = {}
        for group, label in [(False, "silicone"), (True, "non_silicone")]:
            subset = normalized[training_group == group]
            levels[label] = _location(subset) if len(subset) else _location(normalized)
        _state.clear()
        _state.update(
            model_name="group_" + LOCATION + ("_inverse_flow" if MODE == "group_dilution" else ""),
            formula="delta_CO2_180_ppm = silicone_location if material == Silicone else non_silicone_location * (20 / flow_cm_s)^1" if MODE == "group_dilution" else "delta_CO2_180_ppm = silicone_location if material == Silicone else non_silicone_location",
            coefficients={k + "_location": v for k, v in levels.items()},
            num_params=2,
            estimator=LOCATION,
            fixed_flow_exponent=FLOW_POWER if MODE == "group_dilution" else 0.0,
        )
        return np.where(evaluation_group, levels["non_silicone"], levels["silicone"]) * evaluation_scale
    train_features = _features(train_X)
    eval_features = _features(eval_X)
    design = np.column_stack([np.ones(len(y))] + [train_features[k] for k in TERMS])
    evaluation = np.column_stack([np.ones(len(next(iter(eval_X.values()))))] + [eval_features[k] for k in TERMS])
    penalty = np.diag([0.0] + [ALPHA] * len(TERMS))
    augmented = np.vstack([design, np.sqrt(penalty)])
    response = np.concatenate([y, np.zeros(len(TERMS) + 1)])
    coefficients = np.linalg.lstsq(augmented, response, rcond=None)[0]
    if CONSTRAIN_THICKNESS and "silicone_log_thickness" in TERMS:
        index = TERMS.index("silicone_log_thickness") + 1
        if coefficients[index] > 0:
            active = [j for j in range(design.shape[1]) if j != index]
            fitted = np.linalg.lstsq(augmented[:, active], response, rcond=None)[0]
            coefficients = np.zeros(design.shape[1])
            coefficients[active] = fitted
    names = ["intercept"] + list(TERMS)
    _state.clear()
    _state.update(
        model_name=("ridge" if ALPHA else "ols") + "_" + "_".join(TERMS) + ("_sign" if CONSTRAIN_THICKNESS else ""),
        formula="delta_CO2_180_ppm = intercept" + "".join(" + b_" + term + " * " + term for term in TERMS),
        coefficients={name: float(value) for name, value in zip(names, coefficients)},
        num_params=len(coefficients),
        ridge_alpha=ALPHA,
        feature_definitions={
            "non_silicone": "1 for SIBAL, PMMA or PMMA_Nomex; 0 for Silicone",
            "sibal": "1 for SIBAL; 0 otherwise",
            "pmma": "1 for flat or grooved PMMA; 0 otherwise",
            "pmma_nomex": "1 for PMMA_Nomex composite; 0 otherwise",
            "log_thickness": "ln(1 + nominal_thickness_mm)",
            "silicone_log_thickness": "I(Silicone) * ln(1 + nominal_thickness_mm / 0.37)",
            "organic_dilution": "I(non_silicone) * (20 / flow_cm_s)^p",
            "organic_flow": "I(non_silicone) * (flow_cm_s / 20)^p",
            "flow_excess": "(flow_cm_s - 20) / 5",
            "opposed": "1 for opposed; 0 for concurrent",
            "structured_pmma": "1 for grooved PMMA; 0 otherwise",
            "long_ignition": "(command_ignition_duration_s - 9.2) / 20.8",
        },
        flow_power=FLOW_POWER,
        sign_constraint="silicone_log_thickness coefficient <= 0" if CONSTRAIN_THICKNESS else None,
    )
    return evaluation @ coefficients


def describe_model():
    return dict(_state)


if __name__ == "__main__":
    from prepare import evaluate_candidate, print_report
    print_report(evaluate_candidate())
