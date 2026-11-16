"""Structured FLEX baseline for autoresearch.

The experiment target is multi-output prediction of burning rate and burn time.
The model uses source CSV conditions plus features extracted from droplet
diameter histories. Missing target values are masked per task.
"""

from __future__ import annotations

import csv
import hashlib
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
TARGET_METADATA = {
    "burning_rate_m2_s": {
        "unit": "m^2/s",
        "source_column": TARGETS["burning_rate_m2_s"],
    },
    "burn_time_s": {
        "unit": "s",
        "source_column": TARGETS["burn_time_s"],
    },
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


def _json_float(value) -> float | None:
    """Convert numeric values to strict-JSON numbers, mapping missing/non-finite to null."""
    if value is None or pd.isna(value):
        return None
    number = float(value)
    return number if math.isfinite(number) else None


_SOURCE_HASHES = {}


def _source_reference(filename: str) -> dict:
    source_path = DATA_DIR / filename
    reference = {
        "file": f"data/{filename}",
        "reference": f"@data/{filename}",
    }
    if source_path.is_file():
        if filename not in _SOURCE_HASHES:
            _SOURCE_HASHES[filename] = hashlib.sha256(source_path.read_bytes()).hexdigest()
        reference["sha256"] = _SOURCE_HASHES[filename]
    return reference


def _numeric_summary(values: pd.Series, scale: float = 1.0) -> dict:
    numeric = pd.to_numeric(values, errors="coerce") * scale
    numeric = numeric[np.isfinite(numeric)]
    return {
        "n_observed": int(numeric.count()),
        "n_missing_or_unparseable": int(len(values) - numeric.count()),
        "min": _json_float(numeric.min()) if len(numeric) else None,
        "median": _json_float(numeric.median()) if len(numeric) else None,
        "max": _json_float(numeric.max()) if len(numeric) else None,
    }


def _build_discovery_dashboard(
    metrics: dict, validation_campaign: str, validation_idx: np.ndarray
) -> dict:
    """Build evidence-linked discovery content from the local PSI-69 files."""
    frame = pd.read_csv(CSV_PATH, encoding="cp1252")
    parsed_dates = pd.to_datetime(frame["Test Date"], errors="coerce")
    pressure_column = "Ambient pressure; mmHg"
    gas_columns = {
        "oxygen_mole_fraction": "O initial ambient composition; mole fraction",
        "nitrogen_mole_fraction": "N initial ambient composition; mole fraction",
        "co_source_column_mole_fraction": "CO initial ambient composition; mole fraction",
        "helium_mole_fraction": "He initial ambient composition; mole fraction",
    }
    gas_data = frame[list(gas_columns.values())].apply(pd.to_numeric, errors="coerce")
    burn_rate = pd.to_numeric(frame["Burning rate; mm"], errors="coerce") / 1000**2
    burn_time = pd.to_numeric(frame["Burn time; s"], errors="coerce")
    source_ref = _source_reference

    fuel_counts = {
        str(name): int(count)
        for name, count in frame["Fuel"].fillna("Missing").value_counts().items()
    }
    outcome_counts = {
        str(name): int(count)
        for name, count in frame["Test end"].fillna("Missing").value_counts().items()
    }
    outcomes_by_fuel = {}
    target_statistics_by_fuel = {}
    for fuel, group in frame.groupby("Fuel", dropna=False):
        fuel_name = str(fuel) if pd.notna(fuel) else "Missing"
        outcomes_by_fuel[fuel_name] = {
            str(name): int(count)
            for name, count in group["Test end"].fillna("Missing").value_counts().items()
        }
        indices = group.index
        target_statistics_by_fuel[fuel_name] = {
            "n_records": int(len(group)),
            "burning_rate_m2_s": _numeric_summary(burn_rate.loc[indices]),
            "burn_time_s": _numeric_summary(burn_time.loc[indices]),
        }

    pressure = pd.to_numeric(frame[pressure_column], errors="coerce")
    positive_pressure = pressure[pressure > 0]
    distinct_atmospheres = int(gas_data.drop_duplicates().shape[0])
    common_atmospheres = gas_data.groupby(
        list(gas_data.columns), dropna=False
    ).size().sort_values(ascending=False).head(5)
    atmosphere_rows = []
    for values, count in common_atmospheres.items():
        values = values if isinstance(values, tuple) else (values,)
        atmosphere_rows.append({
            "composition": {
                name: _json_float(value)
                for name, value in zip(gas_columns, values)
            },
            "n_records": int(count),
        })

    duplicate_identifiers = []
    identifier_counts = frame["FLEX Identifier"].dropna().value_counts()
    for identifier, count in identifier_counts[identifier_counts > 1].items():
        matching = frame.loc[frame["FLEX Identifier"] == identifier, "FLEX Test #"]
        duplicate_identifiers.append({
            "flex_identifier": str(identifier),
            "test_numbers": [int(value) for value in matching],
            "n_records": int(count),
        })

    unparseable_targets = {}
    for column, numeric_values in (
        ("Burning rate; mm", burn_rate),
        ("Burn time; s", burn_time),
    ):
        invalid = frame[column].notna() & numeric_values.isna()
        tokens = frame.loc[invalid, column].astype(str).value_counts()
        if len(tokens):
            unparseable_targets[column] = {
                str(value): int(count) for value, count in tokens.items()
            }

    zero_pressure_records = frame.loc[pressure == 0, ["FLEX Test #", "FLEX Identifier"]]
    date_missing_count = int(parsed_dates.isna().sum())
    target_coverage = {
        "burning_rate_m2_s": {
            "unit": TARGET_METADATA["burning_rate_m2_s"]["unit"],
            **_numeric_summary(burn_rate),
        },
        "burn_time_s": {
            "unit": TARGET_METADATA["burn_time_s"]["unit"],
            **_numeric_summary(burn_time),
        },
    }

    data_quality_flags = []
    if date_missing_count:
        data_quality_flags.append({
            "id": "missing_test_dates",
            "severity": "review",
            "n_records": date_missing_count,
            "message": "Test Date is absent or unparsable; these rows form the current NaT validation campaign.",
            "evidence": [source_ref(CSV_PATH.name)],
        })
    if unparseable_targets:
        data_quality_flags.append({
            "id": "non_numeric_target_values",
            "severity": "review",
            "raw_values": unparseable_targets,
            "message": "Non-numeric target strings are counted as unavailable, not silently imputed.",
            "evidence": [source_ref(CSV_PATH.name)],
        })
    if duplicate_identifiers:
        data_quality_flags.append({
            "id": "reused_flex_identifiers",
            "severity": "review",
            "records": duplicate_identifiers,
            "message": "Rows with a repeated identifier remain separate test records.",
            "evidence": [source_ref(CSV_PATH.name)],
        })
    if len(zero_pressure_records):
        data_quality_flags.append({
            "id": "zero_ambient_pressure",
            "severity": "review",
            "records": [
                {
                    "test_number": int(row["FLEX Test #"]),
                    "flex_identifier": str(row["FLEX Identifier"]),
                    "value_mmhg": 0.0,
                }
                for _, row in zero_pressure_records.iterrows()
            ],
            "message": "Displayed as recorded; confirm whether zero is a measurement or a missing-value code before physical interpretation.",
            "evidence": [source_ref(CSV_PATH.name)],
        })
    data_quality_flags.append({
        "id": "gas_column_label_mismatch",
        "severity": "review",
        "test_number": 10,
        "csv_label": gas_columns["co_source_column_mole_fraction"],
        "summary_document_label": "YCO2",
        "message": "The CSV field is labelled CO while the FLEX-010 summary text labels the corresponding fraction YCO2; no automatic reconciliation is applied.",
        "evidence": [
            source_ref(CSV_PATH.name),
            source_ref("MeOH_FLEX_001_Summary.pdf"),
        ],
    })

    summary = {
        "investigation_id": "PSI-69",
        "title": "Flame Extinguishment Experiment (FLEX)",
        "citation": {
            "source": source_ref("PSI-69.bib"),
            "bibtex_reference": "@data/PSI-69.bib",
            "doi": "10.60555/mbq8-0451",
            "repository": "NASA Physical Sciences Informatics",
        },
        "dataset": {
            "source": source_ref(CSV_PATH.name),
            "n_test_records": int(len(frame)),
            "n_unique_flex_identifiers": int(frame["FLEX Identifier"].nunique()),
            "date_range": {
                "start": parsed_dates.min().date().isoformat() if parsed_dates.notna().any() else None,
                "end": parsed_dates.max().date().isoformat() if parsed_dates.notna().any() else None,
                "n_missing_or_unparseable": date_missing_count,
            },
            "fuel_counts": fuel_counts,
            "test_end_counts": outcome_counts,
            "test_end_counts_by_fuel": outcomes_by_fuel,
            "target_coverage": target_coverage,
            "target_statistics_by_fuel": target_statistics_by_fuel,
            "conditions": {
                "pressure_mmhg": {
                    "n_positive_observations": int(positive_pressure.count()),
                    "min_positive": _json_float(positive_pressure.min()),
                    "median_positive": _json_float(positive_pressure.median()),
                    "max": _json_float(pressure.max()),
                    "n_zero_records": int((pressure == 0).sum()),
                    "n_missing_or_unparseable": int(pressure.isna().sum()),
                },
                "n_distinct_gas_compositions": distinct_atmospheres,
                "gas_composition_fields": gas_columns,
                "five_most_common_gas_compositions": atmosphere_rows,
            },
        },
    }

    investigation_ranking = [{
        "rank": 1,
        "rank_out_of": 1,
        "investigation_id": "PSI-69",
        "title": "Flame Extinguishment Experiment (FLEX)",
        "priority_basis": "Direct topical match: the local record identifies a flame-extinguishment investigation and the table contains droplet fuel, atmosphere, pressure, burn-rate, and burn-time fields.",
        "rating_scope": "Discovery relevance only; not a hazard, flammability, or operational-safety rating.",
        "evidence": [
            source_ref("PSI-69.bib"),
            source_ref(CSV_PATH.name),
            source_ref("FLEX Overall Ext File-2.pdf"),
        ],
    }]

    case_review_specs = [
        {
            "identifier": "256F002",
            "rank": 1,
            "role": "atmosphere_pressure_contrast",
            "reason": "Review first for condition coverage: this Methanol record has the highest pressure among the three detailed-history cases and a distinct gas-composition vector; the CSV/PDF gas label mismatch is flagged above.",
            "summary_file": "MeOH_FLEX_001_Summary.pdf",
        },
        {
            "identifier": "20CAL13",
            "rank": 2,
            "role": "fuel_contrast",
            "reason": "Review next for a Heptane record under the air-like O/N composition also represented by the Methanol reference case.",
            "summary_file": "Heptane_FLEX-007_Summary.pdf",
        },
        {
            "identifier": "20CAL08",
            "rank": 3,
            "role": "methanol_reference",
            "reason": "Use as the Methanol reference case in the detailed-history set; its summary reports an O/N air-like mixture and the table contains burn outcomes.",
            "summary_file": "MeOH_Air_FLEX_001_Summary.pdf",
        },
    ]
    ranked_cases = []
    for spec in case_review_specs:
        matching = frame.loc[frame["FLEX Identifier"] == spec["identifier"]]
        if matching.empty:
            continue
        record = matching.iloc[0]
        test_number = int(record["FLEX Test #"])
        history_path = HISTORY_FILES.get(spec["identifier"])
        history_features = _history_features(history_path) if history_path and history_path.exists() else {}
        case_fields = {
            "flex_identifier": spec["identifier"],
            "test_number": test_number,
            "test_date": (
                pd.to_datetime(record["Test Date"], errors="coerce").date().isoformat()
                if pd.notna(pd.to_datetime(record["Test Date"], errors="coerce"))
                else None
            ),
            "fuel": str(record["Fuel"]) if pd.notna(record["Fuel"]) else None,
            "pressure_mmhg": _json_float(pd.to_numeric(record[pressure_column], errors="coerce")),
            "gas_composition": {
                name: _json_float(pd.to_numeric(record[column], errors="coerce"))
                for name, column in gas_columns.items()
            },
            "droplet_initial_diameter_mm": _json_float(
                pd.to_numeric(record["Droplet initial diameter; mm"], errors="coerce")
            ),
            "visible_flame_extinction_diameter_mm": _json_float(
                pd.to_numeric(record["Visible flame extinction diameter; mm"], errors="coerce")
            ),
            "burning_rate_m2_s": _json_float(
                pd.to_numeric(record["Burning rate; mm"], errors="coerce") / 1000**2
            ),
            "burn_time_s": _json_float(pd.to_numeric(record["Burn time; s"], errors="coerce")),
            "test_end": str(record["Test end"]) if pd.notna(record["Test end"]) else None,
        }
        ranked_cases.append({
            "rank": spec["rank"],
            "rank_basis": "Qualitative review order for condition coverage, not a hazard or safety ranking.",
            "review_role": spec["role"],
            "review_reason": spec["reason"],
            "record": case_fields,
            "droplet_history_summary": history_features,
            "evidence": [
                {**source_ref(CSV_PATH.name), "record_key": f"FLEX Test #{test_number}"},
                source_ref(spec["summary_file"]),
                source_ref(history_path.name) if history_path else {},
            ],
        })

    insights = [
        {
            "id": "fuel_and_outcome_coverage",
            "type": "descriptive_coverage",
            "summary": f"The local table contains {len(frame)} test records: {fuel_counts.get('Methanol', 0)} Methanol and {fuel_counts.get('Heptane', 0)} Heptane; recorded end labels are {outcome_counts}.",
            "values": {"fuel_counts": fuel_counts, "test_end_counts": outcome_counts},
            "evidence": [source_ref(CSV_PATH.name)],
        },
        {
            "id": "condition_coverage",
            "type": "descriptive_coverage",
            "summary": f"The table contains {distinct_atmospheres} distinct recorded gas-composition vectors and positive pressure observations from {_json_float(positive_pressure.min())} to {_json_float(positive_pressure.max())} mmHg.",
            "values": summary["dataset"]["conditions"],
            "evidence": [source_ref(CSV_PATH.name)],
        },
        {
            "id": "fuel_group_descriptives",
            "type": "descriptive_comparison",
            "summary": "Burn-time and burning-rate summaries by fuel are descriptive only; pressure and gas-composition mixtures differ across records, so these comparisons do not isolate a fuel effect.",
            "values": target_statistics_by_fuel,
            "evidence": [source_ref(CSV_PATH.name)],
        },
        {
            "id": "data_quality_review",
            "type": "data_quality",
            "summary": f"Review date coverage ({date_missing_count} missing/unparseable dates), target coverage, repeated identifiers, zero pressure, and the CSV/PDF gas-label mismatch before interpreting comparisons.",
            "values": {"flags": data_quality_flags},
            "evidence": [source_ref(CSV_PATH.name)],
        },
    ]
    if validation_campaign == "NaT":
        insights.append({
            "id": "validation_campaign_missing_dates",
            "type": "model_validation_limit",
            "summary": "The current fixed split selected the NaT label: all validation rows lack a parsed test date. The metric therefore does not measure a held-out dated campaign.",
            "values": {
                "validation_rows": int(len(validation_idx)),
                "burning_rate_n_validation": metrics.get("burning_rate_m2_s", {}).get("n_validation"),
                "burn_time_n_validation": metrics.get("burn_time_s", {}).get("n_validation"),
                "validation_campaign": validation_campaign,
            },
            "evidence": [source_ref(CSV_PATH.name)],
        })

    application_recommendations = [
        {
            "id": "low_gravity_droplet_model_inputs",
            "category": "research_application",
            "recommendation": "Prioritize PSI-69 as a candidate source of droplet-scale combustion observations for low-gravity fire-scenario model research; keep model outputs as screening estimates and validate against independent experiments before application.",
            "evidence": [
                {**source_ref(CSV_PATH.name), "fields": [
                    "Fuel", pressure_column, *gas_columns.values(),
                    "Droplet initial diameter; mm", "Burning rate; mm", "Burn time; s",
                ]},
                source_ref("FLEX Overall Ext File-2.pdf"),
                source_ref("PSI-69.bib"),
            ],
            "limitations": [
                "This is one droplet-combustion investigation, not a complete spacecraft or habitat fire test.",
                "The local table contains Methanol and Heptane; lunar/Martian habitats and pressurized-rover conditions are not identified as tested environments.",
                "The records do not directly evaluate suppression hardware, solid materials, smoke sensors, or enclosure-scale fire behavior.",
            ],
        },
        {
            "id": "follow_up_test_review",
            "category": "research_planning",
            "recommendation": "For literature and data review, compare the high-pressure/composition-contrast case first, then the Heptane/air-like and Methanol/air-like detailed histories; use the ranking only to organize condition coverage, not to rank hazards.",
            "evidence": [source_ref(CSV_PATH.name)] + [
                source_ref(spec["summary_file"]) for spec in case_review_specs
            ],
            "limitations": ["The qualitative ordering is a navigation aid; it is not a model score, safety assessment, or operating recommendation."],
        },
        {
            "id": "terrestrial_transfer_context",
            "category": "challenge_context_only",
            "recommendation": "Treat fine-water-mist extinguishers, smoke detection, protective clothing, and air tanks as separate technology-transfer leads from the challenge brief; the local FLEX records do not provide evidence to recommend or design those technologies.",
            "evidence": [{"source": "challenge_brief", "source_type": "user-provided context"}],
            "limitations": ["No effectiveness or design data for those technologies are present in the local PSI-69 FLEX files."],
        },
    ]

    return {
        "study_summary": summary,
        "ranked_investigations": investigation_ranking,
        "ranked_cases": ranked_cases,
        "ranking_note": "The local files contain one PSI investigation; case ordering is a qualitative condition-coverage review aid, not a safety ranking.",
        "insights": insights,
        "application_recommendations": application_recommendations,
        "data_quality_flags": data_quality_flags,
        "interpretation_limits": [
            "Descriptive differences and model predictions do not establish causality.",
            "The validation set is the undated NaT group under the unchanged split and is small.",
            "The scalar objective averages RMSE values with different physical units; burn_time_s dominates its magnitude.",
            "Earth technology-transfer examples in the challenge brief are not findings of the local FLEX dataset.",
        ],
    }


def main() -> None:
    features, targets = load_dataset()
    train_idx, validation_idx = _split_by_campaign(features)
    feature_columns = [column for column in features if column != "campaign"]
    x = features[feature_columns]

    metrics = {}
    predictions_by_target: dict[str, dict[int, float]] = {}
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
                max_features=0.4,
                min_samples_leaf=MIN_SAMPLES_LEAF,
                random_state=RANDOM_STATE,
                n_jobs=-1,
            ),
        )
        model.fit(x.iloc[fit_idx], np.log1p(targets[target_name].iloc[fit_idx]))
        predicted = np.expm1(model.predict(x.iloc[score_idx]))
        all_validation_predictions = np.expm1(model.predict(x.iloc[validation_idx]))
        predictions_by_target[target_name] = {
            int(row_index): float(value)
            for row_index, value in zip(validation_idx, all_validation_predictions)
        }
        actual = targets[target_name].iloc[score_idx].to_numpy()
        metrics[target_name] = {
            "n_train": int(len(fit_idx)),
            "n_validation": int(len(score_idx)),
            "mae": float(mean_absolute_error(actual, predicted)),
            "rmse": float(np.sqrt(mean_squared_error(actual, predicted))),
            "r2": float(r2_score(actual, predicted)) if len(actual) > 1 else None,
        }

    valid_rmses = [item["rmse"] for item in metrics.values() if "rmse" in item]
    metrics["objective"] = _json_float(np.mean(valid_rmses)) if valid_rmses else None
    validation_campaign = str(sorted(features["campaign"].dropna().unique())[-1])
    validation_campaigns = features["campaign"].iloc[validation_idx]
    prediction_rows = []
    for row_index in validation_idx:
        actual_values = {}
        predicted_values = {}
        residual_values = {}
        for target_name in TARGETS:
            actual_value = _json_float(targets.iloc[row_index][target_name])
            predicted_value = _json_float(
                predictions_by_target.get(target_name, {}).get(int(row_index))
            )
            actual_values[target_name] = actual_value
            predicted_values[target_name] = predicted_value
            residual_values[target_name] = (
                actual_value - predicted_value
                if actual_value is not None and predicted_value is not None
                else None
            )
        prediction_rows.append({
            "row_index": int(row_index),
            "actual": actual_values,
            "predicted": predicted_values,
            "residual": residual_values,
        })
    discovery = _build_discovery_dashboard(
        metrics, validation_campaign, validation_idx
    )

    output = {
        "schema_version": 2,
        "model": "random_forest_multi_task_masked",
        "data_source": _source_reference(CSV_PATH.name),
        "references": {
            "@data/PSI-69.bib": {
                "file": "data/PSI-69.bib",
                "sha256": _source_reference("PSI-69.bib").get("sha256"),
                "bibtex": (DATA_DIR / "PSI-69.bib").read_text(encoding="utf-8").strip(),
            },
            "source_files": [
                _source_reference(filename)
                for filename in [
                    "PSI-69_Experimental table_FLEX.csv",
                    "FLEX Overall Ext File-2.pdf",
                    "MeOH_FLEX_001_Summary.pdf",
                    "Heptane_FLEX-007_Summary.pdf",
                    "MeOH_Air_FLEX_001_Summary.pdf",
                    "MeOH_FLEX-010_DropletData.txt",
                    "Heptane_FLEX-007_DropletData.txt",
                    "MeOH_Air_FLEX-001_DropletData.txt",
                ]
            ],
        },
        "target_metadata": TARGET_METADATA,
        "validation_campaign": validation_campaign,
        "validation": {
            "split_rule": "last_lexicographically_sorted_campaign_label",
            "campaign_label": validation_campaign,
            "n_rows": int(len(validation_idx)),
            "missing_date_rows": int(validation_campaigns.eq("NaT").sum()),
            "is_missing_date_campaign": validation_campaign == "NaT",
        },
        "metrics": metrics,
        "residual_definition": "actual_minus_predicted",
        "predictions": prediction_rows,
        "discovery": discovery,
    }
    RESULTS_PATH.write_text(
        json.dumps(output, indent=2, allow_nan=False) + "\n", encoding="utf-8"
    )
    if metrics["objective"] is None:
        print("objective_rmse: unavailable")
    else:
        print(f"objective_rmse: {metrics['objective']:.6f}")
    for target_name, target_metrics in metrics.items():
        if target_name != "objective" and "rmse" in target_metrics:
            print(f"{target_name}_rmse: {target_metrics['rmse']:.6f}")
    print(f"predictions: {RESULTS_PATH}")


if __name__ == "__main__":
    main()
