"""`bass2` CLI (or `python -m bass2.cli`).

    bass2 catalog                       # NASA JSON -> inventory + cleaned experimental table
    bass2 fetch-docs                    # documents (ReadMe, SRD, Summary Report...) into data/docs
    bass2 download B1 [--kinds main_video second_view] [--max-mb 300]
    bass2 download-pilot                # tests listed in configs/pilot_tests.yaml (main video only)
    bass2 analyze B1 [--video path.mp4] [--set segmentation.low=30] [--no-forecast]
    bass2 analyze-pilot
    bass2 aggregate                     # ensemble figures G5, G11, G12, G13
    bass2 osd-learn VIDEO FRAME "values" "clock"   # add OSD OCR templates from known text
    bass2 frame VIDEO FRAME out.png     # export one frame (for calibration / labelling)
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml


def _overrides(sets: list[str] | None) -> dict:
    out: dict = {}
    for s in sets or []:
        key, val = s.split("=", 1)
        cur = out
        parts = key.split(".")
        for p in parts[:-1]:
            cur = cur.setdefault(p, {})
        cur[parts[-1]] = yaml.safe_load(val)
    return out


def _video_for(test_id: str, view: str = "main") -> Path:
    from .catalog import best_video, build_inventory
    from .config import load_config
    from .download import download_file
    inv = build_inventory(write=False)
    row = best_video(inv, test_id, view)
    if row is None:
        raise SystemExit(f"No '{view}' video for {test_id}")
    return download_file(row.file_name, load_config().path("raw") / test_id, row.size_bytes)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="bass2", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("catalog")
    sub.add_parser("fetch-docs")
    d = sub.add_parser("download"); d.add_argument("test_id"); d.add_argument("--kinds", nargs="+", default=["main_video"]); d.add_argument("--max-mb", type=float)
    sub.add_parser("download-pilot")
    a = sub.add_parser("analyze"); a.add_argument("test_id"); a.add_argument("--video"); a.add_argument("--set", nargs="*"); a.add_argument("--no-forecast", action="store_true"); a.add_argument("--no-figures", action="store_true")
    sub.add_parser("analyze-pilot")
    sub.add_parser("aggregate")
    o = sub.add_parser("osd-learn"); o.add_argument("video"); o.add_argument("frame", type=int); o.add_argument("values"); o.add_argument("clock")
    f = sub.add_parser("frame"); f.add_argument("video"); f.add_argument("frame", type=int); f.add_argument("out")
    args = ap.parse_args(argv)

    if args.cmd == "catalog":
        from .catalog import build_inventory, fetch_investigation, load_experimental_table
        inv = build_inventory(fetch_investigation())
        tab = load_experimental_table()
        print(f"inventory: {len(inv)} files, {inv.size_bytes.sum() / 1e9:.1f} GB; table: {len(tab)} tests")
    elif args.cmd == "fetch-docs":
        from .download import fetch_docs
        for p in fetch_docs():
            print(p)
    elif args.cmd == "download":
        from .download import download_test
        mb = int(args.max_mb * 1e6) if args.max_mb else None
        for p in download_test(args.test_id, tuple(args.kinds), mb):
            print(p)
    elif args.cmd == "download-pilot":
        from .config import CONFIG_DIR, load_yaml
        for t in load_yaml(CONFIG_DIR / "pilot_tests.yaml")["pilot"]:
            print(_video_for(t))
    elif args.cmd == "analyze":
        from .pipeline import analyze_test
        video = Path(args.video) if args.video else _video_for(args.test_id)
        res = analyze_test(args.test_id, video, overrides=_overrides(args.set),
                           figures=not args.no_figures, do_forecast=not args.no_forecast)
        print(json.dumps(res, indent=2, default=float))
    elif args.cmd == "analyze-pilot":
        from .config import CONFIG_DIR, load_yaml
        from .pipeline import analyze_test
        for t in load_yaml(CONFIG_DIR / "pilot_tests.yaml")["pilot"]:
            try:
                print(json.dumps(analyze_test(t, _video_for(t)), default=float))
            except Exception as e:  # one broken test must not stop the batch
                print(f"[{t}] ERROR: {e}", file=sys.stderr)
    elif args.cmd == "aggregate":
        from .pipeline import aggregate
        print(json.dumps(aggregate(), indent=2, default=float))
    elif args.cmd == "osd-learn":
        from . import osd
        from .video import read_frame
        print(osd.learn_templates(read_frame(args.video, args.frame), {"values": args.values, "clock": args.clock}))
    elif args.cmd == "frame":
        import cv2
        from .video import read_frame
        cv2.imwrite(args.out, read_frame(args.video, args.frame))
        print(args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
