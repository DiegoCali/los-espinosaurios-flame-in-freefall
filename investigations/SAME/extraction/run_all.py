"""Run the complete SAME-R extraction: inventory -> reduced tables -> housekeeping -> TEM -> model data.

Usage:
    .venv/bin/python -m extraction.run_all            # uses SAME_RAW_DATA, data/raw/ or ../../data/
    .venv/bin/python -m extraction.run_all --no-hash  # skip SHA-256 of raw files (faster)
"""
from __future__ import annotations

import argparse
import sys
import warnings
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from extraction import housekeeping, inventory, material_audit, model_data, reduced_tables, tem  # noqa: E402
from extraction.common import find_raw_dir  # noqa: E402


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--raw", default=None, help="Folder with the PSI-101 raw files")
    ap.add_argument("--no-hash", action="store_true")
    args = ap.parse_args(argv)
    warnings.filterwarnings("ignore", category=FutureWarning)
    warnings.filterwarnings("ignore", message=".*xlrd.*")
    raw = find_raw_dir(args.raw)
    print(f"[same] raw data: {raw}")
    inv_csv = inventory.INVENTORY_DIR / "files.csv"
    if args.no_hash and inv_csv.exists():
        print("[same] inventory: kept existing (with hashes)")
    else:
        inv = inventory.build_inventory(raw, hashes=not args.no_hash)
        inventory.write_inventory(inv, raw)
        print(f"[same] inventory: {len(inv)} files")
    for name, df in reduced_tables.run(raw).items():
        print(f"[same] {name}: {df.shape}")
    for name, df in housekeeping.run(raw).items():
        print(f"[same] {name}: {df.shape}")
    for name, df in tem.run(raw).items():
        print(f"[same] {name}: {df.shape}")
    print(f"[same] test_material_audit: {material_audit.build().shape}")
    for name, df in model_data.run().items():
        print(f"[same] {name}: {df.shape}")


if __name__ == "__main__":
    main()
