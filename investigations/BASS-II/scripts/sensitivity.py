"""Threshold sensitivity of the steady spread rate (figure G15) -> data/processed/_sensitivity.csv.

Re-measures selected tests with the adaptive segmenter's noise multiplier k_low around the default (8σ;
k_high = 2·k_low, absolute floors scaled proportionally).
"""
from __future__ import annotations

import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

TESTS = ["B1", "B3", "B4", "B7", "B12", "M1", "T10", "O16"]
KS = [4, 6, 8, 11, 14]


def _job(args):
    test_id, k = args
    from bass2.pipeline import measure_rate
    vids = sorted([*(ROOT / "data/raw" / test_id).glob("*.mp4"), *(ROOT / "data/raw" / test_id).glob("*.ts")])
    if not vids:
        return None
    seg = {"method": "adaptive", "k_low": k, "k_high": 2 * k, "min_low": 14 * k / 8, "min_high": 30 * k / 8}
    r = measure_rate(test_id, vids[0], {"segmentation": seg, "video": {"max_processed_frames": 1500}})
    return {"test_id": test_id, "k_low": k, "rate": r.get("rate"), "lo": r.get("lo"), "hi": r.get("hi"), "unit": r.get("unit")}


def main() -> None:
    jobs = [(t, k) for t in TESTS for k in KS]
    with ProcessPoolExecutor(5) as ex:
        rows = [r for r in ex.map(_job, jobs) if r]
    out = ROOT / "data/processed/_sensitivity.csv"
    pd.DataFrame(rows).to_csv(out, index=False)
    print(pd.DataFrame(rows).pivot(index="test_id", columns="k_low", values="rate").round(4).to_string())


if __name__ == "__main__":
    main()
