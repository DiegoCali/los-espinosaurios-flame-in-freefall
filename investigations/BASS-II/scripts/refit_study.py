"""Refit spread regimes / flow steps / backtests / figures for every processed test (no video decoding)."""
from __future__ import annotations

import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))


def _one(test_id: str):
    import warnings
    warnings.filterwarnings("ignore")
    from bass2.pipeline import refit_test
    try:
        r = refit_test(test_id)
        return test_id, r.get("steady_rate"), "ok"
    except Exception as e:
        return test_id, None, f"error: {e}"


def main() -> None:
    proc = ROOT / "data/processed"
    tests = sorted(d.name for d in proc.iterdir() if (d / "frames.parquet").exists())
    with ProcessPoolExecutor(6) as ex:
        for t, rate, status in ex.map(_one, tests):
            print(f"[{t}] {status} rate={rate}", flush=True)


if __name__ == "__main__":
    main()
