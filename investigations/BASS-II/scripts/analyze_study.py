"""Analyse every downloaded test of the study set in parallel (skips tests already processed).

Usage: python scripts/analyze_study.py [--workers 4] [--force] [--tests B1 B3 ...]
Writes data/processed/_batch_log.csv with one row per test (status, steady rate, runtime).
"""
from __future__ import annotations

import argparse
import json
import sys
import time
import traceback
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))


def _one(test_id: str, force: bool) -> dict:
    from bass2.config import load_config
    from bass2.pipeline import analyze_test
    cfg = load_config()
    out = cfg.path("processed") / test_id / "steady.json"
    if out.exists() and not force:
        s = json.loads(out.read_text())
        if s.get("unit") == "mm/s":  # results from uncalibrated (px) runs are recomputed
            return {"test_id": test_id, "status": "cached", "rate": s.get("rate"), "unit": s.get("unit")}
    vids = sorted([*(cfg.path("raw") / test_id).glob("*.mp4"), *(cfg.path("raw") / test_id).glob("*.ts")])
    if not vids:
        return {"test_id": test_id, "status": "no_video"}
    t0 = time.time()
    try:
        r = analyze_test(test_id, vids[0])
        return {"test_id": test_id, "status": "ok", "rate": r.get("steady_rate"), "lo": r.get("steady_lo"),
                "hi": r.get("steady_hi"), "unit": r.get("steady_unit"), "n_frames": r.get("n_frames"),
                "runtime_s": round(time.time() - t0, 1)}
    except Exception as e:
        return {"test_id": test_id, "status": f"error: {e}", "trace": traceback.format_exc()[-800:]}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--tests", nargs="*")
    a = ap.parse_args()
    from bass2.config import load_config
    raw = load_config().path("raw")
    tests = a.tests or sorted(d.name for d in raw.iterdir() if d.is_dir() and (any(d.glob("*.mp4")) or any(d.glob("*.ts"))))
    rows = []
    with ProcessPoolExecutor(a.workers) as ex:
        futs = {ex.submit(_one, t, a.force): t for t in tests}
        for f in as_completed(futs):
            r = f.result()
            rows.append(r)
            print(f"[{r['test_id']}] {r['status']} rate={r.get('rate')}", flush=True)
    log = ROOT / "data/processed/_batch_log.csv"
    old = pd.read_csv(log) if log.exists() else pd.DataFrame()
    new = pd.DataFrame(rows)
    pd.concat([old[~old.test_id.isin(new.test_id)] if len(old) else old, new]).sort_values("test_id").to_csv(log, index=False)


if __name__ == "__main__":
    main()
