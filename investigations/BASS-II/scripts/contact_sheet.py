"""Contact sheet of several videos: frames at given fractions, optionally gamma-boosted to reveal hardware.

Usage: python scripts/contact_sheet.py OUT.png TEST [TEST ...] [--fractions 0.05 0.5] [--boost 3]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from bass2.video import probe, read_frame  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("tests", nargs="+")
    ap.add_argument("--fractions", nargs="+", type=float, default=[0.02, 0.4, 0.7])
    ap.add_argument("--boost", type=float, default=1.0, help="gamma boost (>1 brightens dark hardware)")
    a = ap.parse_args()
    rows = []
    for t in a.tests:
        vids = sorted((ROOT / "data/raw" / t).glob("*.mp4"))
        if not vids:
            continue
        info = probe(vids[0])
        tiles = []
        for fr in a.fractions:
            f = read_frame(vids[0], int(fr * (info.n_frames - 1)))
            if a.boost != 1:
                f = (255 * (f / 255.0) ** (1 / a.boost)).astype(np.uint8)
            f = cv2.resize(f, (360, 240))
            cv2.putText(f, f"{t} {fr:.2f}", (5, 230), 0, 0.6, (0, 255, 0), 1)
            tiles.append(f)
        rows.append(np.hstack(tiles))
    cv2.imwrite(a.out, np.vstack(rows))


if __name__ == "__main__":
    main()
