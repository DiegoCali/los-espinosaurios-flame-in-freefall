#!/usr/bin/env python3
"""Reproduce the frozen validation predictions without adding a research attempt.

Run with ACME's existing virtual environment. Only train/validation are loaded;
the completed holdout audit is read solely for frozen-model provenance.
"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import evaluate

ROOT = Path(__file__).resolve().parent
OUTPUT = "runs/pilot-01/validation_predictions.json"
sys.path.insert(0, str(ROOT.parent))
from export_predictions import evidence, load, verify_acme_validation  # noqa: E402


def recover() -> dict:
    report = load(ROOT, "runs/holdout-final-v1/final_holdout_metrics.json")
    selected = load(ROOT, "runs/pilot-01/latest_validation.json")
    digest = evaluate.file_hash(ROOT / "train.py")
    if digest != report["train_sha256"] or digest != selected["train_sha256"]:
        raise ValueError("train.py does not match the frozen model SHA-256")
    history = evaluate.read_ledger(ROOT / "runs/pilot-01/results.tsv")
    if (len(history) != 12 or history[-1]["attempt"] != "12"
            or history[-1]["train_sha256"] != digest
            or selected["attempt"] != 12 or selected["status"] != "keep"):
        raise ValueError("The saved selection does not match the completed pilot-01 ledger")
    for key in ("val_rmse_k", "val_mae_k", "val_max_abs_error_k"):
        if float(history[-1][key]) != selected[key]:
            raise ValueError(f"Selected validation metric differs from attempt 12: {key}")
    if selected["features"] != evaluate.FEATURE_ORDER or selected["seed"] != evaluate.SEED:
        raise ValueError("Frozen feature order or seed differs from the evaluator")

    # Import editable model code only after its frozen hash has been verified.
    import train

    if train.MODEL_NAME != report["model_name"] or train.MODEL_NAME != selected["model_name"]:
        raise ValueError("The model name differs from the frozen selection")
    x_train, y_train, x_validation, y_validation = evaluate.load_and_verify()
    if (len(y_train), len(y_validation)) != (134, 52):
        raise ValueError("Expected the original 134 training and 52 validation records")
    predicted = train.fit_predict(x_train.copy(), y_train.copy(), x_validation.copy(), evaluate.SEED)
    metrics = evaluate.errors(y_validation, predicted)
    with (ROOT / "data/processed/acme_tad_validation.csv").open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    predictions = [{
        **{key: row[key] for key in ("test_id", "flame_type", "group_id", "split")},
        "actual": {"tad_calculated_k": float(actual)},
        "predicted": {"tad_calculated_k": float(estimate)},
        "residual": {"tad_calculated_k": float(actual - estimate)},
        "source_file": "data/processed/acme_tad_validation.csv", "source_row": i + 1,
        "original_source_file": "data/raw/" + row["source_file"],
    } for i, (row, actual, estimate) in enumerate(zip(rows, y_validation, predicted, strict=True))]
    sources = ["train.py", "prepare.py", "evaluate.py", "data/metadata/acme_inventory.json",
               "data/processed/acme_tad_train.csv", "data/processed/acme_tad_validation.csv",
               "runs/pilot-01/latest_validation.json", "runs/pilot-01/results.tsv",
               "runs/holdout-final-v1/final_holdout_metrics.json"]
    result = {
        "schema_version": 2, "model": train.MODEL_NAME, "train_sha256": digest,
        "split": "validation", "seed": evaluate.SEED, "feature_order": evaluate.FEATURE_ORDER,
        "n_train": 134, "n_validation": 52, "unit": "K",
        "residual_definition": "actual_minus_predicted",
        "source_row_definition": "1-based CSV data row, excluding the header",
        "python_version": sys.version.split()[0], "numpy_version": evaluate.np.__version__,
        "source_files": [evidence(ROOT, name) for name in sources],
        "metrics": metrics, "metric_tolerance": {"absolute_k": 1e-6, "relative": 1e-10},
        "predictions": predictions,
    }
    verify_acme_validation(ROOT, result, selected, report)
    return result


def main() -> None:
    result = recover()
    text = json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
    path = ROOT / OUTPUT
    if not path.exists() or path.read_text(encoding="utf-8") != text:
        path.write_text(text, encoding="utf-8")
    for name, value in result["metrics"].items():
        print(f"{name}: {value:.12f} K")
    print(f"Saved {len(result['predictions'])} validation predictions: {path}")


if __name__ == "__main__":
    main()
