"""Download the main video of every test in configs/study_tests.yaml (or the YAML given as argv[1]); resumable."""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from bass2.catalog import best_video, build_inventory  # noqa: E402
from bass2.config import CONFIG_DIR, load_config, load_yaml  # noqa: E402
from bass2.download import download_file  # noqa: E402


def main() -> None:
    cfg_name = sys.argv[1] if len(sys.argv) > 1 else "study_tests.yaml"
    tests = [t for group in load_yaml(CONFIG_DIR / cfg_name)["study"].values() for t in group]
    inv = build_inventory(write=False)
    # Fallback for irregular NASA names (e.g. "TESTB6", "test T13"): archivist's best-candidate table.
    best = pd.read_csv(ROOT / "data/catalog/best_candidates_per_test.csv").set_index("test_group")["best_file"]
    raw = load_config().path("raw")
    for t in tests:
        row = best_video(inv, t)
        if row is None and t in best.index and isinstance(best[t], str):
            sel = inv[inv.file_name == best[t]]
            row = sel.iloc[0] if len(sel) else None
        if row is None:
            print(f"[{t}] no main video", flush=True)
            continue
        try:
            p = download_file(row.file_name, raw / t, row.size_bytes)
            print(f"[{t}] ok {p.name} {row.size_bytes / 1e6:.1f} MB", flush=True)
        except Exception as e:  # keep going on failures
            print(f"[{t}] FAILED {e}", flush=True)


if __name__ == "__main__":
    main()
