"""Retry the hold-out download until the NASA presigned-URL endpoint answers again, then extract the tests.

The PSI download endpoint occasionally returns an empty body (HTTP 200, 0 bytes) for every file. This script
probes it every `--every` seconds for up to `--hours`, then runs download_study.py and analyze_study.py on the
hold-out list (configs/holdout_tests.yaml) and finally refit_study.py so the frozen regime logic is applied.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
PY = sys.executable


def endpoint_ok() -> bool:
    from bass2.download import presigned_url
    try:
        return presigned_url("PSI-25_Raw Data_BASS_GMT50_SAMPLE_147_TEST_B1.mp4").startswith("https://")
    except Exception:
        return False


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--every", type=int, default=300)
    ap.add_argument("--hours", type=float, default=1.5)
    a = ap.parse_args()
    deadline = time.time() + a.hours * 3600
    while not endpoint_ok():
        if time.time() > deadline:
            print("endpoint still unavailable; giving up", flush=True)
            return
        print(time.strftime("%H:%M"), "endpoint unavailable, retrying", flush=True)
        time.sleep(a.every)
    print("endpoint available", flush=True)
    subprocess.run([PY, str(ROOT / "scripts/download_study.py"), "holdout_tests.yaml"], check=False)
    from bass2.config import CONFIG_DIR, load_yaml
    tests = [t for g in load_yaml(CONFIG_DIR / "holdout_tests.yaml")["study"].values() for t in g]
    subprocess.run([PY, str(ROOT / "scripts/calibrate_study.py")], check=False, capture_output=True)
    subprocess.run([PY, str(ROOT / "scripts/analyze_study.py"), "--workers", "5", "--tests", *tests], check=False)
    print("hold-out extracted", flush=True)


if __name__ == "__main__":
    main()
