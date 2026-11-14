"""Compare segmentation settings on the tests with published spread rates (evaluation-side script).

Usage: python scripts/compare_segmenters.py [--frames 1500]
Writes data/processed/_segmenter_comparison.csv and prints |ln(V/V_pub)| per variant.
"""
from __future__ import annotations

import argparse
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

TESTS = ["B1", "B2", "B3", "B4", "B5", "B7", "B12", "M1"]
VARIANTS = {
    "hysteresis_40_90 (v0)": {"method": "hysteresis", "low": 40, "high": 90},
    "hysteresis_15_30": {"method": "hysteresis", "low": 15, "high": 30},
    "adaptive_k6_12": {"method": "adaptive", "k_low": 6, "k_high": 12, "min_low": 10, "min_high": 22, "use_blue": False},
    "adaptive_k6_12_blue": {"method": "adaptive", "k_low": 6, "k_high": 12, "min_low": 10, "min_high": 22, "use_blue": True},
    "adaptive_k8_16_blue": {"method": "adaptive", "k_low": 8, "k_high": 16, "min_low": 14, "min_high": 30, "use_blue": True},
}


def _job(args):
    test, name, seg, frames = args
    from bass2.pipeline import measure_rate
    vids = sorted([*(ROOT / "data/raw" / test).glob("*.mp4"), *(ROOT / "data/raw" / test).glob("*.ts")])
    r = measure_rate(test, vids[0], {"segmentation": seg, "video": {"max_processed_frames": frames}})
    return {"test_id": test, "variant": name, "rate": r.get("rate"), "lo": r.get("lo"), "hi": r.get("hi"),
            "t0": r.get("t0"), "t1": r.get("t1"), "unit": r.get("unit")}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--frames", type=int, default=1500)
    ap.add_argument("--workers", type=int, default=4)
    a = ap.parse_args()
    jobs = [(t, n, s, a.frames) for t in TESTS for n, s in VARIANTS.items()]
    with ProcessPoolExecutor(a.workers) as ex:
        d = pd.DataFrame(list(ex.map(_job, jobs)))
    pub = pd.read_csv(ROOT / "data/reference/published_rates.csv")
    pub = pub[(pub.view == "side") & (pub.step == 1)].set_index("test_id").vf_mm_s
    d["published"] = d.test_id.map(pub)
    d["abs_log_ratio"] = np.abs(np.log(d.rate.where(d.rate > 0) / d.published))
    d.to_csv(ROOT / "data/processed/_segmenter_comparison.csv", index=False)
    print(d.pivot(index="test_id", columns="variant", values="rate").round(4).assign(published=pub).to_string())
    print(d.groupby("variant").abs_log_ratio.agg(["mean", "median", "count"]).round(4).to_string())


if __name__ == "__main__":
    main()
