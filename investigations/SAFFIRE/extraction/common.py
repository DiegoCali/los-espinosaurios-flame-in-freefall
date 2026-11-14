from __future__ import annotations
import csv
import json
import math
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = Path(os.environ.get("SAFFIRE_RAW_DATA", str(ROOT / "raw_data"))).resolve()
PROCESSED = ROOT / "data" / "processed"
INVENTORY = ROOT / "data" / "inventory"
MATRIX = "part-01/PSI-99_Experimental table_SAFFIRE-2.csv"
TELEMETRY = "part-01/Saffire-II Telemetry Data.xlsx"
PSI_METADATA = "part-01/PSI-99_metadata_PSI-167_SAFFIRE-II.zip!i_Investigation.txt"

def write_csv(path, rows, columns=None):
    rows = list(rows)
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    columns = columns if columns is not None else (list(rows[0]) if rows else [])
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: "" if v is None else v for k, v in row.items()})

def read_csv(path):
    with Path(path).open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))

def write_json(path, obj):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")

def numeric(value):
    if value in (None, ""):
        return None
    number = float(value)
    return number if math.isfinite(number) else None

def source_path(path):
    return Path(path).relative_to(RAW).as_posix()
