"""Geometric calibration (duct ruler) for every downloaded test -> data/catalog/spatial_calibration.csv.

Per test: ruler period from illuminated frames (src/bass2/calibration.py). Tests without lit frames
inherit the median of their camera session (same PI and GMT day), flagged method=session_median.
Published spread rates are NOT used here.
"""
from __future__ import annotations

import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))


def _cal(test_id: str) -> dict:
    from bass2.calibration import calibrate_video
    vids = sorted([*(ROOT / "data/raw" / test_id).glob("*.mp4"), *(ROOT / "data/raw" / test_id).glob("*.ts")])
    if not vids:
        return {"test_id": test_id}
    try:
        return {"test_id": test_id, **calibrate_video(vids[0])}
    except Exception as e:
        return {"test_id": test_id, "error": str(e)}


def main() -> None:
    tests = sorted(d.name for d in (ROOT / "data/raw").iterdir() if d.is_dir())
    with ProcessPoolExecutor(6) as ex:
        rows = list(ex.map(_cal, tests))
    d = pd.DataFrame(rows)
    meta = pd.read_csv(ROOT / "data/catalog/best_candidates_per_test.csv")[["test_group", "pi", "gmt_day"]]
    d = d.merge(meta, left_on="test_id", right_on="test_group", how="left").drop(columns="test_group")
    # A ruler estimate is a candidate if it is strong; it is accepted if it also agrees (±10 %) with the
    # robust median of all candidates. The SRD states the video field of view is fixed, so tests without an
    # accepted ruler inherit the global camera scale (method=global_fixed_fov).
    cand = d["mm_per_phys_px"].notna() & (d["strength"].fillna(0) > 0.3)
    med = float(d.loc[cand, "mm_per_phys_px"].median())
    good = cand & ((d["mm_per_phys_px"] / med - 1).abs() < 0.10)
    glob = d.loc[good, "mm_per_phys_px"]
    g_med, g_std, g_n = float(glob.median()), float(glob.std()), int(good.sum())
    d["method"] = np.where(good, "ruler", np.where(cand, "global_fixed_fov (ruler outlier rejected)", "global_fixed_fov"))
    d["mm_per_px_final"] = np.where(good, d["mm_per_phys_px"], g_med)
    d["global_mm_per_px"], d["global_std"], d["global_n"] = g_med, g_std, g_n
    # relative 1-sigma uncertainty: spread of accepted rulers + 2 % allowance for ruler/sample depth (perspective)
    d["mm_per_px_rel_sigma"] = float(np.hypot(g_std / g_med, 0.02))
    out = ROOT / "data/catalog/spatial_calibration.csv"
    d.drop(columns=["video"], errors="ignore").to_csv(out, index=False)
    print(f"global camera scale: {g_med:.5f} ± {g_std:.5f} mm/phys-px (n={g_n} accepted rulers)")
    print(d[["test_id", "pi", "gmt_day", "method", "mm_per_phys_px", "mm_per_px_final", "strength"]].to_string())


if __name__ == "__main__":
    main()
