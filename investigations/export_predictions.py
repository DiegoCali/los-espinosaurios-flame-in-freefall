#!/usr/bin/env python3
"""Export saved research results using FLEX's schema; never run a model.

Run from any directory. --check verifies all five exports without writing files.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent
NAMES = ("ACME", "BASS-II", "SAFFIRE", "SAME", "flex")
MAIN_KEYS = ("schema_version", "model", "data_source", "references",
             "target_metadata", "validation", "metrics", "predictions", "discovery")
READING_GUIDE = {
    "measured": "Recorded by an instrument; retain its calibration and uncertainty limits.",
    "published": "A value reported in the original NASA or published reduction.",
    "calculated": "Derived from recorded conditions or measurements, not a model prediction.",
    "predicted": "A saved model estimate; validation and scenario predictions are separate.",
    "null": "Unavailable or not applicable; never interpret as zero.",
}


def load(root, name):
    return json.loads((root / name).read_text(encoding="utf-8"))


def evidence(root, name):
    return {"file": name, "reference": "@" + name,
            "sha256": hashlib.sha256((root / name).read_bytes()).hexdigest()}


def cell(value):
    if value == "":
        return None
    if value in ("True", "False"):
        return value == "True"
    try:
        number = float(value)
    except ValueError:
        return value
    if not math.isfinite(number):
        return None
    return int(value) if value.lstrip("-+").isdigit() else number


def table(root, name):
    with (root / name).open(encoding="utf-8-sig", newline="") as handle:
        return [{k: v if k in ("test_id", "sample_id") else cell(v)
                 for k, v in row.items()}
                for row in csv.DictReader(handle, delimiter="\t" if name.endswith(".tsv") else ",")]


def pointer(document, path):
    for part in path.lstrip("/").split("/") if path else ():
        key = part.replace("~1", "/").replace("~0", "~")
        document = document[int(key)] if isinstance(document, list) else document[key]
    return document


def saved_prediction(source, path, row, targets, identifiers):
    actual = {k: row[m["observed_column"]] for k, m in targets.items()}
    predicted = {k: row[m["predicted_column"]] for k, m in targets.items()}
    return {**{k: row[k] for k in identifiers}, "source_file": source,
            "source_pointer": path, "actual": actual, "predicted": predicted,
            "residual": {k: None if actual[k] is None or predicted[k] is None
                         else actual[k] - predicted[k] for k in targets}}


def discovery(investigation_id, title, dataset):
    return {
        "study_summary": {"investigation_id": investigation_id, "title": title, "dataset": dataset},
        "ranked_investigations": [], "ranked_cases": [],
        "ranking_note": "No new ranking was computed for this export.",
        "insights": [], "application_recommendations": [],
        "data_quality_flags": [], "interpretation_limits": [],
        "reading_guide": READING_GUIDE, "experimental_data": {}, "charts": [],
    }


def envelope(root, model, source, targets, validation, metrics, content, sources, citations):
    return {"schema_version": 2, "model": model, "data_source": evidence(root, source),
            "references": {"source_files": [evidence(root, f) for f in sources], "citations": citations},
            "target_metadata": targets, "validation": validation, "metrics": metrics,
            "residual_definition": "actual_minus_predicted", "predictions": [], "discovery": content}


def acme(root):
    source = "runs/holdout-final-v1/final_holdout_metrics.json"
    report = load(root, source)
    validation = load(root, "runs/pilot-01/latest_validation.json")
    inventory = load(root, "data/metadata/acme_inventory.json")
    content = discovery("PSI-10", report["investigation"], inventory)
    content["experimental_data"] = {"records": table(root, "data/processed/acme_all.csv"),
                                    "pilot": table(root, "data/processed/acme_tad_pilot.csv")}
    content["model_details"] = {"holdout_audit": report, "selected_validation": validation,
                                "attempts": table(root, "runs/pilot-01/results.tsv")}
    content["insights"] = [{"id": "final_holdout_audit", "type": "existing_validation_result",
        "summary": "The completed frozen-model audit evaluates calculated Tad on 50 reserved records.",
        "values": report["global"], "evidence": [evidence(root, source)]}]
    content["interpretation_limits"] = report["limitations"] + [
        "Individual predictions were not saved; aggregate metrics cannot reconstruct them.",
        "Tad is a calculated thermodynamic quantity, not measured flame temperature, soot or extinction.",
    ]
    content["data_quality_flags"] = [{"id": "inventory_warnings", "values": inventory["warnings"]}]
    content["charts"] = [
        {"id": "errors", "type": "metric_comparison", "data_pointer": "/metrics/tad_calculated_k",
         "title": "Validation and final holdout errors (K)",
         "interpretation_note": "Different partitions; preserve their separate counts and precision."},
        {"id": "search", "type": "line", "data_pointer": "/discovery/model_details/attempts",
         "x": "attempt", "y": "val_rmse_k", "title": "Recorded validation search"},
    ]
    targets = {"tad_calculated_k": {"unit": "K", "source_column": "tad_calculated_k",
                                    "actual_kind": "calculated", "definition": report["objective"]}}
    metrics = {"tad_calculated_k": {"validation": {
        "n_train": validation["n_train"], "n_validation": validation["n_validation"],
        "rmse": validation["val_rmse_k"], "mae": validation["val_mae_k"],
        "max_abs_error": validation["val_max_abs_error_k"]},
        "holdout": {"n_train": report["n_train"], "n_holdout": report["n_holdout"],
                    "rmse": report["global"]["rmse_k"], "mae": report["global"]["mae_k"],
                    "max_abs_error": report["global"]["max_abs_error_k"],
                    "by_flame_type": report["by_flame_type"], "by_day_group": report["by_day_group"]}}}
    sources = [source, "runs/pilot-01/latest_validation.json", "runs/pilot-01/results.tsv",
               "data/metadata/acme_inventory.json", "data/processed/acme_all.csv",
               "data/processed/acme_tad_pilot.csv", "analysis/FINAL_TAD_PILOT.md"]
    citations = [{"doi": inventory["doi"], "url": "https://psi.nasa.gov/physci/repo/data/investigations/PSI-10"}]
    for name, digest in report["source_sha256"].items():
        path = "data/raw/" + name
        if evidence(root, path)["sha256"] != digest:
            raise ValueError(f"ACME original hash mismatch: {path}")
        sources.append(path)
    return envelope(root, report["model_name"], source, targets,
                    {"split_rule": inventory["grouping"], "partitions": inventory["pilot_split_rows"],
                     "groups": inventory["pilot_split_groups"], "status": report["status"],
                     "frozen_model_commit": report["frozen_model_commit"]}, metrics, content, sources, citations)


def bass(root):
    source = "reports/validation_summary.json"
    summary = load(root, source)
    catalog = load(root, "data/catalog/psi25_investigation.json")
    ensemble = "reports/figures/_ensemble/"
    files = {"steady_rates": ensemble + "steady_rates.csv",
             "published_comparisons": "reports/validation_published.csv",
             "forecast_qc_trusted": ensemble + "forecast_summary.csv",
             "forecast_all_tests": ensemble + "forecast_summary_all_tests.csv"}
    tables = {k: table(root, f) for k, f in files.items()}
    content = discovery("PSI-25", catalog["title"], {
        "n_processed_tests": len(tables["steady_rates"]),
        "n_published_comparisons": len(tables["published_comparisons"]),
        "holdout_accounting": summary["holdout_accounting"]})
    content["experimental_data"] = {k: v for k, v in tables.items() if not k.startswith("forecast")}
    content["experimental_data"]["conditions"] = table(root, "data/catalog/experimental_table_clean.csv")
    content["model_details"] = {"selected_research_result": load(root, "research/best/result.json"),
                                "baseline": load(root, "research/baseline.json"),
                                "attempts": table(root, "research/results.tsv")}
    content["interpretation_limits"] = [summary["note"],
        "Individual rolling-origin forecasts were not saved locally; predictions is empty.",
        "Extracted video rates and published rates are measurements/calculations, not model predictions.",
        "Segmentation error in the research harness uses synthetic flames, not hand-labelled flight frames.",
        "Steady windows were selected with hindsight; forecasts describe behavior within those windows.",
        "Preserve area_phys_px (aspect-corrected px^2) separately from area_mm2 (mm^2).",
        "Faint-flame segmentation and thick-slab flow transients limit interpretation; see physics_review.md.",
    ]
    content["insights"] = [{"id": "thickness_law", "type": "existing_calculation",
        "summary": "Recorded thickness-law fits; no refitting in this export.",
        "values": {k: summary[k] for k in ("thickness_law", "thickness_law_extended_trusted", "o2_trend_trusted")},
        "evidence": [evidence(root, source)]}]
    for image in sorted(set(load(root, "reports/site/files.json").values())):
        caption = (root / image).with_suffix(".md")
        content["charts"].append({"id": Path(image).stem + "_" + Path(image).parent.name,
            "type": "existing_figure", "path": image,
            "description": caption.read_text(encoding="utf-8").strip() if caption.is_file() else None})
    content["charts"].append({"id": "forecast_metrics", "type": "metric_comparison",
        "title": "Saved forecast metrics by target, model and horizon",
        "data_pointer": "/metrics/forecast_qc_trusted"})
    targets = {
        "leading_edge_mm": {"unit": "mm", "actual_kind": "calculated_from_video",
                            "metric_target_aliases": ["leading_edge"]},
        "area_mm2": {"unit": "mm^2", "actual_kind": "calculated_from_video",
                     "metric_target_aliases": ["area"]},
        "area_phys_px": {"unit": "px^2", "actual_kind": "calculated_from_video",
                         "definition": "Pixel area corrected for pixel aspect ratio; no mm conversion."},
        "spread_rate_mm_s": {"unit": "mm/s", "actual_kind": "calculated_from_video",
                             "source_column": "vf_measured_mm_s", "prediction_available": False},
    }
    sources = [source, "data/catalog/psi25_investigation.json", "data/catalog/experimental_table_clean.csv",
               "research/best/result.json", "research/baseline.json", "research/results.tsv",
               "reports/site/files.json", "reports/REPORT.md", "reports/physics_review.md", *files.values()]
    return envelope(root, "multiple_existing_forecasters", source, targets,
        {"split_rule": summary["note"], "by_set": summary["by_set"],
         "holdout_accounting": summary["holdout_accounting"],
         "forecast_protocol": "Saved rolling-origin backtests; horizons and models retained per metric row."},
        {"published_rate_comparison": summary, **{k: v for k, v in tables.items() if k.startswith("forecast")},
         "research": content["model_details"]["selected_research_result"]}, content, sources,
        [{"doi": catalog["doi"], "title": catalog["title"]},
         {"citation": "SDSU BASS repository; NASA/TM-20210011385 Table 5.1",
          "source_file": "reports/REPORT.md"}])


def flight(root):
    name = root.name.lower()
    source = f"analysis-{name}.json"
    a = load(root, source)
    brief = load(root, f"analysis-{name}-summary.json")
    best, baseline = a["autoresearch"]["best"], a["autoresearch"]["baseline"]
    content = discovery(a["psi_investigation"], a["experiment"], a["data_inventory_summary"])
    content["study_summary"]["citation"] = brief["source"]
    content["insights"] = [{"id": i["id"], "type": "existing_finding", "summary": i["title"],
                            "values": i, "evidence": i["evidence_refs"]} for i in brief["insights"]]
    content["data_quality_flags"] = [{"id": "existing_quality_review", "values": a["data_quality"]}]
    content["interpretation_limits"] = a["limitations"]
    content["charts"] = brief["charts"] + [{"id": "prediction_parity", "type": "observed_vs_predicted",
        "title": "Saved cross-validation predictions", "data_pointer": "/predictions",
        "interpretation_note": "Separate targets, scales and validation groups."}]
    content["model_details"] = {"autoresearch": a["autoresearch"], "predictive_model": a["predictive_model"]}
    content["unavailable_results"] = brief["unavailable_results"]
    if name == "saffire":
        target = a["autoresearch"]["target"]
        targets = {target: {"unit": "ppm", "source_column": target, "actual_kind": "calculated_from_sensors",
            "definition": a["autoresearch"]["target_definition"],
            "observed_column": "observed", "predicted_column": "predicted"}}
        validation = {"split_rule": best["validation"], "n_rows": best["n_rows"], "n_flights": 1,
                      "selection_limitation": a["autoresearch"]["selection_limitation"]}
        metrics = {target: {"n_validation": best["n_rows"], "rmse": best["val_rmse"],
                           "mae": best["val_mae"], "max_abs_error": best["val_max_abs_err"],
                           "baseline": {k: baseline[k] for k in ("val_rmse", "val_mae", "val_max_abs_err")}}}
        predictions = [saved_prediction(source, f"/predictive_model/cv_predictions/{i}", row, targets, ("test_id",))
                       | {"original_error": row["error"], "original_error_definition": "predicted_minus_actual"}
                       for i, row in enumerate(a["predictive_model"]["cv_predictions"])]
        content["experimental_data"] = {k: a[k] for k in ("tests", "data_plan", "findings", "relevance_ranking")}
        data_files = ["data/processed/metrics.csv", "data/processed/model_dataset.csv", "data/processed/cabin_metrics.csv"]
        series = "data/processed/sensor_timeseries.csv"
        model = best["model_name"]
    else:
        size_units = {"log10_dg_um": "um", "log10_dm_um": "um", "log10_amd_um": "um",
                      "ln_sigma_g": "1", "log10_m0_per_cc": "cm^-3"}
        targets = {k: {"unit": "1", "source_unit": unit, "source_column": k,
            "transform": "natural_log" if k.startswith("ln_") else "log10",
            "actual_kind": "transformed_published_reduction", "observed_column": k + "_observed",
            "predicted_column": k + "_predicted"} for k, unit in size_units.items()}
        targets.update({k: {"unit": "1", "source_column": k, "actual_kind": "calculated_proxy_detection",
            "prediction_kind": "probability", "observed_column": k + "_observed",
            "predicted_column": k + "_probability"} for k in ("iss_detect", "ion_detect")})
        predictions = []
        for group, rows in a["predictive_model"]["cv_predictions"].items():
            group_targets = {k: m for k, m in targets.items() if m["observed_column"] in rows[0]}
            identifiers = ("run", "source_row", "material", "aged_state") if group == "size" else (
                "test", "push_index", "material", "flow_velocity_cm_s", "aging_s")
            predictions.extend(saved_prediction(source, f"/predictive_model/cv_predictions/{group}/{i}",
                row, group_targets, identifiers) | {"task": group} for i, row in enumerate(rows))
        metrics = {k: {"rmse": best["size_rmse"][k], "nrmse": best["size_nrmse_by_target"][k],
            "factor_error": best["size_factor_error"].get(k), "n_validation": best["n_size_rows"]}
                   for k in size_units}
        metrics.update({k: {"brier": best["detection_brier"][k],
            "brier_ratio": best["detection_brier_ratio_by_target"][k],
            "accuracy_at_0p5": best["detection_accuracy_at_0p5"][k], "n_validation": best["n_detection_rows"]}
                        for k in ("iss_detect", "ion_detect")})
        metrics["objective"] = best["val_score"]
        metrics["aggregate"] = {"size_nrmse": best["size_nrmse"],
                                "detection_brier_ratio": best["detection_brier_ratio"]}
        validation = {"split_rule": a["methods"]["model_validation"],
            **{k: best[k] for k in ("n_size_rows", "n_size_groups", "n_detection_rows", "n_detection_groups")}}
        content["experimental_data"] = {k: a[k] for k in ("tests", "size", "aging", "flow_effect", "detectors", "methods")}
        data_files = ["data/processed/size_dataset.csv", "data/processed/detection_dataset.csv",
                      "data/processed/nasa_moment_table.csv", "data/processed/pushes.csv"]
        series = "data/processed/hkp_timeseries_clean.csv.gz"
        model = best["model"]["model_name"]
    content["charts"].append({"id": "sensor_timeseries", "type": "time_series", "file": series,
        "title": "Existing processed sensor series", "interpretation_note": "Units are retained in channel names and source analysis."})
    inventory_file = "data/inventory/inventory.csv" if name == "saffire" else "data/inventory/files.csv"
    result = envelope(root, model, source, targets, validation, metrics, content,
        [source, f"analysis-{name}-summary.json", *data_files, series, inventory_file], a["references"])
    result["predictions"] = predictions
    return result


def normalize(root, document):
    """Keep historical source names, but expose only resolvable links to consumers."""
    missing = {}
    non_finite = 0
    links = {"file", "path", "source_file", "detail_ref", "source_analysis", "summary_file",
             "insights_file", "overview_figure", "ledger_file", "inventory_file", "run_dir"}

    def resolve(value):
        filename, sep, fragment = value.partition("#") if "#/" in value else (value, "", "")
        for base in (root, root / "data/raw", root / "raw_data"):
            path = base / filename
            if not path.is_absolute() or not path.is_relative_to(ROOT.parent):
                continue
            if path.exists():
                relative = path.relative_to(root).as_posix()
                if fragment.startswith("/"):
                    pointer(load(root, relative), fragment)
                return relative + (sep + fragment if sep else "")
        missing[value] = {"original_source": value, "file": None, "status": "unavailable_locally"}
        return None

    def walk(value):
        nonlocal non_finite
        if isinstance(value, float) and not math.isfinite(value):
            non_finite += 1
            return None
        if value == "":
            return None
        if isinstance(value, list):
            return [walk(v) for v in value]
        if not isinstance(value, dict):
            return value
        out = {}
        for key, item in value.items():
            if key in links and isinstance(item, str):
                resolved = resolve(item) if ";" not in item else None
                if resolved != item:
                    out["original_" + key] = item
                    if ";" in item:
                        for part in item.split(";"):
                            resolve(part)
                out[key] = resolved
            elif key in ("source_files", "evidence_refs", "evidence") and isinstance(item, list):
                if any(isinstance(v, str) for v in item):
                    out["original_" + key] = item
                out[key] = [resolve(v) if isinstance(v, str) and not v.startswith("/")
                            and ("/" in v or "." in v) else walk(v) for v in item]
            else:
                out[key] = walk(item)
        return out

    result = walk(document)
    inventory_file = {"SAFFIRE": "data/inventory/inventory.csv", "SAME": "data/inventory/files.csv"}.get(root.name)
    if inventory_file:
        inventory = {r.get("path", r.get("file")): r for r in table(root, inventory_file)}
        for name, item in missing.items():
            if name in inventory and inventory[name].get("sha256"):
                row = inventory[name]
                item.update(sha256=row["sha256"], hash_kind=row.get("hash_kind", "full"),
                            hash_status="recorded_not_reverified", inventory_file=inventory_file)
    result["discovery"]["provenance"] = {
        "path_base": "investigation_root", "historical_sources": list(missing.values()),
        "note": "original_* fields preserve historical labels. Null links are unavailable locally; source JSONs retain the original metadata."}
    if missing:
        result["discovery"]["data_quality_flags"].append({"id": "unavailable_original_sources",
            "n_sources": len(missing), "message": "Some historical originals are absent. Local derived files and recorded provenance remain available."})
    if non_finite:
        result["discovery"]["data_quality_flags"].append({"id": "non_finite_values_as_null",
            "n_values": non_finite, "message": "Historical non-finite numbers are exported as null; originals are unchanged."})
    return result


def check(root, document):
    for key in MAIN_KEYS:
        if key not in document:
            raise ValueError(f"{root.name}: missing {key}")
    if document["schema_version"] != 2 or not isinstance(document["model"], str):
        raise ValueError(f"{root.name}: incompatible version/model")
    for key in ("data_source", "references", "target_metadata", "validation", "metrics", "discovery"):
        if not isinstance(document[key], dict):
            raise ValueError(f"{root.name}: {key} must be an object")
    expected = {"ACME": 0, "BASS-II": 0, "SAFFIRE": 9, "SAME": 117, "flex": 50}
    if not isinstance(document["predictions"], list) or len(document["predictions"]) != expected[root.name]:
        raise ValueError(f"{root.name}: incorrect prediction count")
    if document["residual_definition"] != "actual_minus_predicted":
        raise ValueError(f"{root.name}: incorrect residual definition")
    if any(not m.get("unit") for m in document["target_metadata"].values()):
        raise ValueError("Each target needs an explicit unit")
    source_positions = [(r["source_file"], r["source_pointer"]) for r in document["predictions"] if "source_pointer" in r]
    if len(set(source_positions)) != len(source_positions):
        raise ValueError("Duplicate prediction source rows")
    for row in document["predictions"]:
        if not row["actual"].keys() == row["predicted"].keys() == row["residual"].keys():
            raise ValueError("Prediction target keys differ")
        original = pointer(load(root, row["source_file"]), row["source_pointer"]) if "source_pointer" in row else None
        for target, actual in row["actual"].items():
            metadata = document["target_metadata"][target]
            predicted, residual = row["predicted"][target], row["residual"][target]
            if actual is None or predicted is None:
                if residual is not None:
                    raise ValueError("Missing input must have null residual")
            elif not math.isclose(residual, actual - predicted, rel_tol=1e-12, abs_tol=1e-15):
                raise ValueError("Residual differs from actual minus predicted")
            if original is not None and (actual != original[metadata["observed_column"]]
                                         or predicted != original[metadata["predicted_column"]]):
                raise ValueError("Saved prediction was altered")
        if "original_error" in row and row["original_error"] != original["error"]:
            raise ValueError("Original signed error was altered")
    if root.name == "ACME":
        splits = document["validation"]["partitions"]
        if sum(splits.values()) != len(document["discovery"]["experimental_data"]["pilot"]):
            raise ValueError("ACME partition counts differ from the saved pilot")
        holdout = document["metrics"]["tad_calculated_k"]["holdout"]
        for group in ("by_flame_type", "by_day_group"):
            if sum(v["n"] for v in holdout[group].values()) != holdout["n_holdout"]:
                raise ValueError("ACME holdout group counts differ")
    if root.name == "BASS-II":
        data = document["discovery"]["experimental_data"]
        if len(data["steady_rates"]) != 83 or len(data["published_comparisons"]) != 25:
            raise ValueError("BASS-II measurement/comparison counts differ")
        if any(r["unit"] != "mm/s" for r in data["steady_rates"] if r["qc"] == "trusted"):
            raise ValueError("BASS-II forecast aliases require rechecking physical units")
    if root.name == "SAME":
        for task, count_key in (("size", "n_size_rows"), ("detection", "n_detection_rows")):
            if sum(r["task"] == task for r in document["predictions"]) != document["validation"][count_key]:
                raise ValueError("SAME task counts differ")
    if root.name == "flex":
        with (root / document["data_source"]["file"]).open(encoding="cp1252", newline="") as handle:
            records = list(csv.DictReader(handle))
        for row in document["predictions"]:
            source = records[row["row_index"]]
            for target, column, divisor in (("burning_rate_m2_s", "Burning rate; mm", 1000**2),
                                             ("burn_time_s", "Burn time; s", 1)):
                try:
                    observed = float(source[column]) / divisor
                    observed = observed if math.isfinite(observed) else None
                except ValueError:
                    observed = None
                actual = row["actual"][target]
                if observed is None or actual is None:
                    if observed is not actual:
                        raise ValueError("FLEX missing target differs from source")
                elif not math.isclose(observed, actual, rel_tol=1e-12, abs_tol=1e-15):
                    raise ValueError("FLEX observed value/unit conversion differs from source")
        for target in document["target_metadata"]:
            if sum(r["actual"][target] is not None for r in document["predictions"]) != document["metrics"][target]["n_validation"]:
                raise ValueError("FLEX observed target counts differ")
    def walk(value):
        if isinstance(value, dict):
            if value.get("file") is not None and "sha256" in value:
                if evidence(root, value["file"])["sha256"] != value["sha256"]:
                    raise ValueError(f"Source hash mismatch: {value['file']}")
            for key, item in value.items():
                if key in ("file", "path", "source_file", "detail_ref") and isinstance(item, str):
                    filename, _, fragment = item.partition("#") if "#/" in item else (item, "", "")
                    if not (root / filename).exists():
                        raise ValueError(f"Broken local link: {root.name}/{item}")
                    if fragment.startswith("/"):
                        pointer(load(root, filename), fragment)
                if key == "data_pointer":
                    pointer(document, item)
                walk(item)
        elif isinstance(value, list):
            for item in value:
                walk(item)
    walk(document)
    json.dumps(document, allow_nan=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Verify all five saved JSONs without writing")
    args = parser.parse_args()
    builders = {"ACME": acme, "BASS-II": bass, "SAFFIRE": flight, "SAME": flight}
    for name in NAMES:
        root = ROOT / name
        path = root / "predictions.json"
        expected = normalize(root, builders[name](root)) if name in builders else load(root, "predictions.json")
        if args.check:
            actual = load(root, "predictions.json")
            if actual != expected:
                raise ValueError(f"{name}: export differs from existing source results")
        else:
            actual = expected
        check(root, actual)
        if not args.check and name != "flex":
            path.write_text(json.dumps(actual, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
        print(f"{name}: OK; {len(actual['predictions'])} predictions; {len(actual['target_metadata'])} targets")


if __name__ == "__main__":
    main()
