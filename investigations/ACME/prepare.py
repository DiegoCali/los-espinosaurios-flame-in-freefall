#!/usr/bin/env python3
"""NASA PSI-10 / ACME Flame Design: first-stage, reproducible data preparation.

No third-party packages required. Run from any working directory:
    python3 investigations/ACME/prepare.py

Scientific scope:
- Keep ALL source rows in a normalized audit table.
- The preliminary Tad pilot uses only steady ethylene (C2H4) experiments.
- Keep Normal and Inverse physical semantics explicit.
- Separate train/validation/holdout by experimental day, not by random row.
- Do not use end-of-test values or target-derived properties as model inputs.
- This script does NOT produce soot labels, physical measurements of flame
  temperature, or a fitted model.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import random
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RAW = ROOT / "data" / "raw"
PROCESSED = ROOT / "data" / "processed"
METADATA = ROOT / "data" / "metadata"

FILES = {
    "Normal": "PSI-10_Experimental table_Flame Design_Normal Flame.csv",
    "Inverse": "PSI-10_Experimental table_Flame Design_Inverse Flame.csv",
}
SEED = 20261113
SPECIAL = {"RAMP", "RAMPED", "LOW O2"}

# Only these fields may be used as inputs in the first regression pilot.
# Importantly, NO end-of-test conditions, Zst or Tad belong here.
MODEL_FEATURES = [
    "flame_type",
    "burner_reactant_mole_fraction",
    "ambient_reactant_fraction_initial",
    "burner_reactant_flow_mg_s",
    "nitrogen_flow_mg_s",
    "total_flow_mg_s",
    "pressure_initial_atm",
]

COLUMNS = [
    "test_id", "flame_type", "day", "group_id", "fuel",
    "burner_reactant", "ambient_reactant", "flow_status",
    "burner_reactant_mole_fraction", "ambient_reactant_fraction_initial",
    "burner_reactant_flow_mg_s", "nitrogen_flow_mg_s", "total_flow_mg_s",
    "pressure_initial_atm",
    "ambient_reactant_fraction_final", "pressure_final_atm", "pressure_mean_atm",
    "zst_calculated", "tad_calculated_k", "source_file",
]
PILOT_COLUMNS = COLUMNS + ["split"]


def numeric(value: str) -> float | None:
    """Return None for explicit operational markers, never change them to zero."""
    clean = (value or "").strip()
    if not clean or clean.upper() in SPECIAL:
        return None
    try:
        return float(clean)
    except ValueError as exc:
        raise ValueError(f"Unexpected non-numeric source value: {value!r}") from exc


def fmt(value: float | None) -> str:
    # Preserve source precision by formatting the original numeric string below;
    # here we only need to represent missing values consistently.
    return "" if value is None else str(value)


def as_number(value: str) -> str:
    return fmt(numeric(value))


def file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for part in iter(lambda: source.read(1 << 20), b""):
            digest.update(part)
    return digest.hexdigest()


def read_sources(raw_dir: Path) -> tuple[list[dict[str, str]], dict[str, str]]:
    rows: list[dict[str, str]] = []
    hashes: dict[str, str] = {}
    seen: set[str] = set()

    for expected_flame_type, file_name in FILES.items():
        path = raw_dir / file_name
        if not path.is_file():
            raise FileNotFoundError(
                f"Missing source file: {path}\n"
                "Keep the original NASA CSV names under data/raw/."
            )
        hashes[file_name] = file_hash(path)
        with path.open("r", newline="", encoding="utf-8-sig") as stream:
            for line_no, source in enumerate(csv.DictReader(stream), start=2):
                if source.get("Flame Type", "").strip() != expected_flame_type:
                    raise ValueError(f"Unexpected flame type in {file_name}:{line_no}")
                test_id = source.get("Test", "").strip()
                if not test_id or test_id in seen:
                    raise ValueError(f"Empty/duplicate test identifier: {file_name}:{line_no}: {test_id}")
                seen.add(test_id)
                day = source.get("Day", "").strip()
                if not day.isdigit():
                    raise ValueError(f"Invalid day in {file_name}:{line_no}: {day!r}")

                if expected_flame_type == "Normal":
                    fuel = source["Fuel"].strip()
                    burner = "fuel"
                    ambient = "oxygen"
                    burner_fraction = source["Xfuel"]
                    ambient_initial = source["XO2 (init)"]
                    ambient_final = source["XO2 (final)"]
                    reactant_flow = source["mfuel (mg/s)"]
                else:
                    fuel = "C2H4"  # Documented source: inverse atmosphere is ethylene.
                    burner = "oxygen"
                    ambient = "fuel"
                    burner_fraction = source["XO2"]
                    ambient_initial = source["XC2H4 initial"]
                    ambient_final = source["XC2H4 final"]
                    reactant_flow = source["mO2 (mg/s)"]

                status_markers = {
                    (val or "").strip().upper() for val in source.values()
                    if isinstance(val, str) and val.strip().upper() in SPECIAL
                }
                if "LOW O2" in status_markers:
                    status = "low_oxygen"
                elif "RAMP" in status_markers or "RAMPED" in status_markers:
                    status = "ramped"
                else:
                    status = "steady"

                row = {
                    "test_id": test_id,
                    "flame_type": expected_flame_type,
                    "day": day,
                    # 'Day' is an index within each flame-type campaign, not a
                    # globally unique day. Treat both as a composite group.
                    "group_id": f"{expected_flame_type.lower()}_day_{int(day):02d}",
                    "fuel": fuel,
                    "burner_reactant": burner,
                    "ambient_reactant": ambient,
                    "flow_status": status,
                    "burner_reactant_mole_fraction": as_number(burner_fraction),
                    "ambient_reactant_fraction_initial": as_number(ambient_initial),
                    "burner_reactant_flow_mg_s": as_number(reactant_flow),
                    "nitrogen_flow_mg_s": as_number(source["mN2 (mg/s)"]),
                    "total_flow_mg_s": as_number(source["mtot (mg/s)"]),
                    "pressure_initial_atm": as_number(source["pinit (atm)"]),
                    "ambient_reactant_fraction_final": as_number(ambient_final),
                    "pressure_final_atm": as_number(source["pfinal (atm)"]),
                    "pressure_mean_atm": as_number(source["pmean (atm)"]),
                    "zst_calculated": as_number(source["mean Zst"]),
                    "tad_calculated_k": as_number(source["Tad (K)"]),
                    "source_file": file_name,
                }
                rows.append(row)

    return rows, hashes


def eligible_for_tad(row: dict[str, str]) -> bool:
    """Lightweight pilot: steady ethylene only, complete PRE-TEST features and Tad."""
    return (
        row["fuel"] == "C2H4"
        and row["flow_status"] == "steady"
        and bool(row["tad_calculated_k"])
        and all(row[name] != "" for name in MODEL_FEATURES if name != "flame_type")
    )


def group_splits(rows: list[dict[str, str]]) -> dict[str, str]:
    """Stable day-held-out split; independently stratified by flame configuration.

    The allocation intentionally stays fixed when train.py changes.
    Groups with no eligible rows do not enter the pilot.
    """
    assignment = {}
    for flame_type in ("Normal", "Inverse"):
        groups = sorted({r["group_id"] for r in rows if r["flame_type"] == flame_type})
        if len(groups) < 6:
            raise ValueError(f"Too few independent {flame_type} day groups: {groups}")
        random.Random(f"{SEED}:{flame_type}").shuffle(groups)
        n_test = max(1, round(0.2 * len(groups)))
        n_val = max(1, round(0.2 * len(groups)))
        for group in groups[:n_test]:
            assignment[group] = "holdout"
        for group in groups[n_test:n_test + n_val]:
            assignment[group] = "validation"
        for group in groups[n_test + n_val:]:
            assignment[group] = "train"
    return assignment


def write_table(path: Path, rows: list[dict[str, str]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def prepare(root: Path = ROOT) -> dict:
    all_rows, hashes = read_sources(root / "data" / "raw")
    pilot = [r.copy() for r in all_rows if eligible_for_tad(r)]
    if not pilot:
        raise ValueError("No usable steady C2H4/Tad experiments in the NASA CSVs")
    assignments = group_splits(pilot)
    for row in pilot:
        row["split"] = assignments[row["group_id"]]

    # These remain accessible for human audit. The agent must never use holdout.
    out = root / "data" / "processed"
    write_table(out / "acme_all.csv", all_rows, COLUMNS)
    write_table(out / "acme_tad_pilot.csv", pilot, PILOT_COLUMNS)
    for split in ("train", "validation", "holdout"):
        write_table(
            out / f"acme_tad_{split}.csv",
            [r for r in pilot if r["split"] == split],
            PILOT_COLUMNS,
        )

    audit = {
        "investigation": "NASA PSI-10 / ACME Flame Design",
        "doi": "10.60555/w4zy-bt45",
        "status": "preliminary_pilot_not_soot_prediction",
        "source_sha256": hashes,
        "original_rows": len(all_rows),
        "original_by_flame": dict(sorted(Counter(r["flame_type"] for r in all_rows).items())),
        "flow_statuses": dict(sorted(Counter(r["flow_status"] for r in all_rows).items())),
        "fuel_counts": dict(sorted(Counter(r["fuel"] for r in all_rows).items())),
        "tad_numeric_rows_all_fuels": sum(bool(r["tad_calculated_k"]) for r in all_rows),
        "pilot_ethylene_steady_rows": len(pilot),
        "pilot_by_flame": dict(sorted(Counter(r["flame_type"] for r in pilot).items())),
        "pilot_split_rows": dict(sorted(Counter(r["split"] for r in pilot).items())),
        "pilot_split_groups": {
            split: sorted(g for g, s in assignments.items() if s == split)
            for split in ("train", "validation", "holdout")
        },
        "grouping": "flame_type + source Day (no row-level splitting)",
        "fixed_seed": SEED,
        "target": "tad_calculated_k (adiabatic calculated quantity, NOT measured flame temperature)",
        "permitted_input_features": MODEL_FEATURES,
        "forbidden_model_features": [
            "test_id", "day", "group_id", "source_file", "flow_status",
            "ambient_reactant_fraction_final", "pressure_final_atm", "pressure_mean_atm",
            "zst_calculated", "tad_calculated_k", "split",
        ],
        "warnings": [
            "No soot-inception labels appear in these two source tables.",
            "RAMP/RAMPED/LOW O2 rows are kept for auditing, excluded from Tad pilot.",
            "Propane (C3H8) is held outside the first ethylene-only pilot.",
            "Day heldout sets remain for a single final audit, not AutoResearch tuning.",
            "Source concentrations may be operational estimates; consult NASA final report.",
        ],
    }
    meta = root / "data" / "metadata"
    meta.mkdir(parents=True, exist_ok=True)
    with (meta / "acme_inventory.json").open("w", encoding="utf-8") as stream:
        json.dump(audit, stream, indent=2, ensure_ascii=False)
        stream.write("\n")
    return audit


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check", action="store_true",
        help="prepare output and print auditable summary (same as default)",
    )
    parser.parse_args()
    audit = prepare()
    print("NASA PSI-10 — preparación inicial completada")
    print(f"Filas originales: {audit['original_rows']} | tipo: {audit['original_by_flame']}")
    print(f"Estados de flujo: {audit['flow_statuses']}")
    print(f"Filas con Tad numérico: {audit['tad_numeric_rows_all_fuels']}")
    print(f"Piloto de etileno (C2H4): {audit['pilot_ethylene_steady_rows']}")
    print(f"Filas por partición: {audit['pilot_split_rows']}")
    print(f"Grupos por partición: {audit['pilot_split_groups']}")
    print("Datos procesados: data/processed/")
    print("Auditoría y hashes: data/metadata/acme_inventory.json")
    print("NOTA: no se ha entrenado un modelo y no hay etiquetas de hollín.")


if __name__ == "__main__":
    main()
