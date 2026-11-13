"""Structured FLEX baseline for autoresearch.

The experiment target is multi-output prediction of burning rate and burn time.
The model uses source CSV conditions plus features extracted from droplet
diameter histories. Missing target values are masked per task.
"""

from __future__ import annotations

import csv
import json
import math
import re
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler


DATA_DIR = Path(__file__).resolve().parent / "data"
CSV_PATH = DATA_DIR / "PSI-69_Experimental table_FLEX.csv"
RESULTS_PATH = Path(__file__).resolve().parent / "predictions.json"

# Experimental knobs for autoresearch. Keep the split and targets fixed.
N_ESTIMATORS = 500
MAX_DEPTH = None
MIN_SAMPLES_LEAF = 2
RANDOM_STATE = 42

TARGETS = {
    "burning_rate_m2_s": "burning_rate_m2_s",
    "burn_time_s": "Burn time; s",
}

# Summary files identify these detailed histories by FLEX identifier.
HISTORY_FILES = {
    "20CAL13": DATA_DIR / "Heptane_FLEX-007_DropletData.txt",
    "20CAL08": DATA_DIR / "MeOH_Air_FLEX-001_DropletData.txt",
    "256F002": DATA_DIR / "MeOH_FLEX-010_DropletData.txt",
}


def _numeric(value: str) -> float:
    value = value.strip().replace("\ufffd", "")
    return float(value) if value else math.nan


def _history_features(path: Path) -> dict[str, float]:
    rows = []
    with path.open(newline="", encoding="utf-8-sig") as source:
        for row in csv.DictReader(source, delimiter="\t"):
            time_s = _numeric(row["DropletTime_sec"])
            diameter_mm = _numeric(row["DropletDiameter_mm"])
            if np.isfinite(time_s) and np.isfinite(diameter_mm):
                rows.append((time_s, diameter_mm))

    if not rows:
        return {}
    values = np.asarray(rows, dtype=float)
    time_s, diameter_mm = values[:, 0], values[:, 1]
    duration = float(time_s.max() - time_s.min())
    d_squared = diameter_mm**2
    slope_d = np.polyfit(time_s, diameter_mm, 1)[0] if len(rows) > 1 else math.nan
    slope_d_squared = (
        np.polyfit(time_s, d_squared, 1)[0] if len(rows) > 1 else math.nan
    )
    return {
        "history_points": float(len(rows)),
        "history_duration_s": duration,
        "history_initial_diameter_mm": float(diameter_mm[0]),
        "history_final_diameter_mm": float(diameter_mm[-1]),
        "history_min_diameter_mm": float(diameter_mm.min()),
        "history_max_diameter_mm": float(diameter_mm.max()),
        "history_diameter_std_mm": float(diameter_mm.std()),
        "history_diameter_slope_mm_s": float(slope_d),
        "history_d_squared_slope_mm2_s": float(slope_d_squared),
    }


def _history_feature_table() -> pd.DataFrame:
    records = []
    for identifier, path in HISTORY_FILES.items():
        if not path.exists():
            raise FileNotFoundError(f"Missing droplet history: {path}")
        records.append({"FLEX Identifier": identifier, **_history_features(path)})
    return pd.DataFrame(records)


def load_dataset() -> tuple[pd.DataFrame, pd.DataFrame]:
    frame = pd.read_csv(CSV_PATH, encoding="cp1252")
    frame["Test Date"] = pd.to_datetime(frame["Test Date"], errors="coerce")
    frame["campaign"] = frame["Test Date"].dt.to_period("M").astype(str)
    frame = frame.merge(_history_feature_table(), on="FLEX Identifier", how="left")

    numeric_columns = [
        "Ambient pressure; mmHg",
        "O initial ambient composition; mole fraction",
        "N initial ambient composition; mole fraction",
        "CO initial ambient composition; mole fraction",
        "He initial ambient composition; mole fraction",
        "Droplet initial diameter; mm",
        "Visible flame extinction diameter; mm",
        *[column for column in frame if column.startswith("history_")],
    ]
    for column in numeric_columns:
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
    frame["pressure_pa"] = frame["Ambient pressure; mmHg"] * 133.322368
    frame["droplet_initial_diameter_m"] = (
        frame["Droplet initial diameter; mm"] / 1000
    )
    frame["visible_extinction_diameter_m"] = (
        frame["Visible flame extinction diameter; mm"] / 1000
    )
    frame["burning_rate_m2_s"] = frame["Burning rate; mm"] / 1000**2
    frame["burn_time_s"] = frame["Burn time; s"]
    numeric_columns.extend(
        ["pressure_pa", "droplet_initial_diameter_m", "visible_extinction_diameter_m"]
    )
    features = frame[numeric_columns].apply(pd.to_numeric, errors="coerce")
    features["fuel_methanol"] = (frame["Fuel"] == "Methanol").astype(float)
    features["fuel_heptane"] = (frame["Fuel"] == "Heptane").astype(float)
    features["campaign"] = frame["campaign"]
    targets = frame[list(TARGETS.values())].apply(pd.to_numeric, errors="coerce")
    targets.columns = list(TARGETS)
    return features, targets


def _split_by_campaign(features: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    campaigns = features["campaign"].dropna().unique()
    if len(campaigns) < 2:
        raise ValueError("At least two dated campaigns are required for validation.")
    validation_campaign = sorted(campaigns)[-1]
    validation = features["campaign"].to_numpy() == validation_campaign
    return np.flatnonzero(~validation), np.flatnonzero(validation)


def main() -> None:
    features, targets = load_dataset()
    train_idx, validation_idx = _split_by_campaign(features)
    feature_columns = [column for column in features if column != "campaign"]
    x = features[feature_columns]

    metrics = {}
    predictions = pd.DataFrame(index=validation_idx)
    for target_name in TARGETS:
        valid_target = targets[target_name].notna().to_numpy()
        fit_idx = train_idx[valid_target[train_idx]]
        score_idx = validation_idx[valid_target[validation_idx]]
        if len(fit_idx) == 0 or len(score_idx) == 0:
            metrics[target_name] = {"status": "insufficient_target_data"}
            continue

        model = make_pipeline(
            SimpleImputer(strategy="median", add_indicator=True),
            StandardScaler(),
            RandomForestRegressor(
                n_estimators=N_ESTIMATORS,
                max_depth=MAX_DEPTH,
                max_features=0.7,
                min_samples_leaf=MIN_SAMPLES_LEAF,
                random_state=RANDOM_STATE,
                n_jobs=-1,
            ),
        )
        model.fit(x.iloc[fit_idx], targets[target_name].iloc[fit_idx])
        predicted = model.predict(x.iloc[score_idx])
        actual = targets[target_name].iloc[score_idx].to_numpy()
        predictions.loc[score_idx, target_name] = predicted
        metrics[target_name] = {
            "n_train": int(len(fit_idx)),
            "n_validation": int(len(score_idx)),
            "mae": float(mean_absolute_error(actual, predicted)),
            "rmse": float(np.sqrt(mean_squared_error(actual, predicted))),
            "r2": float(r2_score(actual, predicted)) if len(actual) > 1 else None,
        }

    valid_rmses = [item["rmse"] for item in metrics.values() if "rmse" in item]
    metrics["objective"] = float(np.mean(valid_rmses)) if valid_rmses else math.inf
    output = {
        "schema_version": 1,
        "model": "random_forest_multi_task_masked",
        "validation_campaign": sorted(features["campaign"].dropna().unique())[-1],
        "metrics": metrics,
        "predictions": predictions.reset_index().rename(columns={"index": "row_index"}).to_dict("records"),
    }
    RESULTS_PATH.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    print(f"objective_rmse: {metrics['objective']:.6f}")
    for target_name, target_metrics in metrics.items():
        if target_name != "objective" and "rmse" in target_metrics:
            print(f"{target_name}_rmse: {target_metrics['rmse']:.6f}")
    print(f"predictions: {RESULTS_PATH}")


if __name__ == "__main__":
    main()
