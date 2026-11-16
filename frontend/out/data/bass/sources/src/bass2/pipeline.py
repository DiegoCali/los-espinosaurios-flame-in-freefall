"""Per-test orchestration: video -> per-frame series -> spread -> forecast -> figures.

Per-test outputs (data/processed/<test_id>/):
    frames.parquet     one row per frame: metrics, OSD telemetry, edges, spread rates
    kymograph.npy      horizontal intensity profile per frame (t × x)
    steady.json        steady Theil-Sen spread rate + CI and the steady window
    backtest.parquet   rolling-origin evaluation of the forecasting models
    reports/figures/<test_id>/G*.png|md|csv
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from tqdm import tqdm

from . import forecast, metrics, osd, segmentation, spread, viz
from .config import Config, load_config, test_calibration
from .video import iter_frames, probe, valid_mask


def _conditions(test_id: str) -> dict | None:
    p = load_config().path("catalog") / "experimental_table_clean.parquet"
    if not p.exists():
        return None
    t = pd.read_parquet(p)
    row = t[t.test_id == test_id]
    if row.empty:
        row = t[t.test_base == test_id.rstrip("ab")]
    return row.iloc[0].to_dict() if len(row) else None


def extract(video_path: str | Path, test_id: str, cfg: Config | None = None,
            read_osd: bool = True, keep_examples: int = 4,
            segment_fn=None) -> tuple[pd.DataFrame, np.ndarray, dict]:
    """Walk the video and compute per-frame metrics + the kymograph.

    segment_fn(frame, valid) -> mask overrides the configured segmenter (used by research/harness.py).
    """
    cfg = cfg or load_config()
    cal = test_calibration(test_id)
    vcfg, scfg, mcfg = cfg["video"], cfg["segmentation"], cfg["metrics"]
    info = probe(video_path)
    roi = cal.get("roi") or vcfg.get("roi")
    valid = valid_mask((info.height, info.width), vcfg.get("osd_mask"), roi)
    templates = osd.load_templates() if read_osd else {}
    rows, kymo = [], []
    examples = {}
    layout = None
    if segment_fn is None and vcfg.get("static_mask", True):
        valid = valid & ~static_artifacts(video_path, valid, scfg, vcfg, info)
    step = vcfg.get("frame_step", 1)
    if step == "auto":
        step = max(1, int(np.ceil(info.n_frames / vcfg.get("max_processed_frames", 4000))))
    step = max(int(step), 1)
    n_total = info.n_frames // step
    pick = set(np.linspace(0, max(n_total - 1, 0), keep_examples + 2, dtype=int)[1:-1].tolist())
    for k, (idx, t, frame) in enumerate(tqdm(iter_frames(video_path, step,
                                                         max_frames=vcfg.get("max_frames")),
                                             total=n_total, desc=f"{test_id} frames", leave=False)):
        # Lights-on / illuminated frames (crew lights before ignition, e.g. B4, B7): the whole scene is
        # bright, so they cannot be segmented as flame. They are flagged and measured as "no flame".
        bg_level = float(np.median(frame.max(axis=2)[valid]))
        lights_on = bg_level > vcfg.get("lights_on_median", 18)
        if lights_on:
            mask = np.zeros(valid.shape, bool)
        elif segment_fn is not None:
            mask = segment_fn(frame, valid)
        else:
            mask = segmentation.segment(frame, valid, scfg)
        r = {"frame": idx, "time_s": t, "bg_median": bg_level, "lights_on": lights_on,
             **metrics.frame_metrics(frame, mask, pixel_aspect=vcfg["pixel_aspect"],
                                     mm_per_px=cal.get("mm_per_px"), edge_frac=mcfg["edge_threshold_frac"],
                                     gamma=mcfg["intensity_gamma"])}
        bg = frame.max(axis=2)[valid & ~mask]
        r["n_px_valid_bg"] = float(bg.mean()) if bg.size else np.nan
        # Telemetry changes slowly: OCR it every ~osd_every_s seconds (forward-filled later).
        # The OSD layout shifts by a few px between videos: detect it once on a dark frame.
        if templates and layout is None and not lights_on:
            layout = osd.detect_layout(frame)
        if templates and layout and k % max(1, int(round(vcfg.get("osd_every_s", 0.5) * info.fps / step))) == 0:
            try:
                r.update({k2: v for k2, v in osd.read_telemetry(frame, templates, layout).items()
                          if not k2.endswith("_raw")})
            except Exception:
                pass
        rows.append(r)
        lin = metrics.linearize(frame.max(axis=2).astype(np.float32), mcfg["intensity_gamma"])
        kymo.append(np.where(mask, lin, 0).sum(axis=0))
        if k in pick:
            examples[k] = (frame.copy(), mask.copy())
    df = pd.DataFrame(rows)
    osd_cols = [c for c in df.columns if c.startswith("osd_")]
    if osd_cols:
        df[osd_cols] = df[osd_cols].ffill()
    return df, np.asarray(kymo, np.float32), {"info": info.__dict__ | {"path": str(info.path), "frame_step": step},
                                              "examples": examples, "calibration": cal}


def static_artifacts(video_path, valid: np.ndarray, scfg: dict, vcfg: dict, info, n: int = 60,
                     frac: float = 0.6, max_area: int = 300) -> np.ndarray:
    """Pixels that are 'flame' in most sampled frames but form small blobs: LEDs, hot pixels, fixed
    reflections. A real flame moves and is larger, so it is not removed. Returns a dilated boolean mask."""
    import cv2
    acc, used = np.zeros(valid.shape, np.float32), 0
    thr = vcfg.get("lights_on_median", 18)
    for _, _, f in iter_frames(video_path, step=max(1, info.n_frames // n)):  # ~n frames spread over the video
        if np.median(f.max(axis=2)[valid]) > thr:
            continue
        acc += segmentation.segment(f, valid, scfg)
        used += 1
        if used >= n:
            break
    if used < 10:
        return np.zeros(valid.shape, bool)
    cand = (acc / used) > frac
    num, lab, stats, _ = cv2.connectedComponentsWithStats(cand.astype(np.uint8), connectivity=8)
    keep = np.zeros(valid.shape, bool)
    for k in range(1, num):
        if stats[k, cv2.CC_STAT_AREA] <= max_area:
            keep |= lab == k
    return cv2.dilate(keep.astype(np.uint8), np.ones((7, 7), np.uint8)).astype(bool)


def flame_window(df: pd.DataFrame, min_area_px: int = 50, trim_frac: float = 0.1) -> tuple[float, float]:
    """Interval with a flame present, trimmed at both ends (ignition / extinction)."""
    on = df[df.area_px >= min_area_px]
    if on.empty:
        return np.nan, np.nan
    t0, t1 = on.time_s.min(), on.time_s.max()
    pad = (t1 - t0) * trim_frac
    return t0 + pad, t1 - pad


def steady_regime(df: pd.DataFrame, min_len_s: float = 3.0) -> dict:
    """Steady spread = the longest significantly-advancing linear regime of the leading edge.

    The leading edge is median-binned (robust to flicker of faint flames) and partitioned into linear
    regimes by optimal segmentation (spread.regimes): ignition flash, spread under flow, spread after a
    flow change, approach to extinction, ... The longest regime whose 95 % CI of the slope is > 0 is the
    steady regime. Returns rate/lo/hi/t0/t1 (NaN rate + status when no regime advances significantly).
    """
    unit = df["unit"].iloc[0]
    reg = spread.regimes(df, min_len_s=min_len_s)
    out = {"rate": np.nan, "lo": np.nan, "hi": np.nan, "unit": f"{unit}/s", "n": 0,
           "regimes": reg.to_dict("records") if len(reg) else []}
    if reg.empty:
        return out
    min_disp = 2.0 if unit == "mm" else 10.0  # a spread regime must advance ≥ 2 mm (≈10 px)
    cand = reg[reg.significant & (reg.duration_s >= min_len_s) & (reg.rate * reg.duration_s >= min_disp)]
    if cand.empty:
        return out
    # Longest significantly advancing regime. With the regime length floor (10 % of the burn) and penalty
    # used in spread.regimes, the 'longest' and 'latest long' rules agree on all reference tests
    # (knowledge/methods/spatial_calibration.md §6).
    best = cand.loc[cand.duration_s.idxmax()]
    out.update({k: float(best[k]) for k in ("rate", "lo", "hi", "intercept", "t0", "t1")})
    out["n"] = int(best["n_bins"])
    return out


def steady_window(df: pd.DataFrame, min_len_s: float = 3.0) -> tuple[float, float]:
    """(t0, t1) of the steady regime, or (nan, nan)."""
    st = steady_regime(df, min_len_s)
    return st.get("t0", np.nan), st.get("t1", np.nan)


def flow_steps(df: pd.DataFrame, min_len_s: float = 8.0, jump: float = 3.0, air_lag_s: float = 20.0) -> list[dict]:
    """Per-flow-step spread rates for tests where the crew stepped the fan during the burn.

    Steps are plateaus of the OSD FAN reading (10× fan voltage, changes immediately) separated by
    jumps > `jump`. The flow of a step is the OSD AIR velocity read `air_lag_s` later (the anemometer
    lags the fan by 15–25 s, physics review §2.3). Within each step the Theil-Sen rate of the leading edge is computed over frames
    with a flame present.
    """
    if "osd_fan" not in df or df.osd_fan.isna().all():
        return []
    unit = df["unit"].iloc[0]
    col = f"leading_edge_{unit}"
    fan = df.osd_fan.rolling(15, center=True, min_periods=1).median()
    brk = np.r_[0, np.where(np.abs(np.diff(fan.to_numpy())) > jump)[0] + 1, len(df)]
    # merge breakpoints that are closer than min_len_s (ramps are a sequence of small jumps)
    steps, start = [], 0
    for b in brk[1:]:
        if df.time_s.iloc[b - 1] - df.time_s.iloc[start] >= min_len_s:
            steps.append((start, b))
            start = b
    out = []
    for a, b in steps:
        seg = df.iloc[a:b]
        seg = seg[(seg.area_px >= 50) & seg[col].notna()]
        if len(seg) < 10 or seg.time_s.iloc[-1] - seg.time_s.iloc[0] < min_len_s:
            continue
        st = steady_regime(seg.assign(unit=unit), min_len_s=min(3.0, min_len_s / 2))
        if st["rate"] != st["rate"]:
            continue
        ta, tb = seg.time_s.iloc[0] + air_lag_s, seg.time_s.iloc[-1] + air_lag_s
        air = df[(df.time_s >= ta) & (df.time_s <= tb)].get("osd_air_cm_s")
        out.append({"t0": float(st["t0"]), "t1": float(st["t1"]),
                    "fan_median": float(seg.osd_fan.median()),
                    "air_lagged_cm_s": float(1.0066 * air.median()) if air is not None and len(air) else np.nan,
                    "rate": st["rate"], "lo": st["lo"], "hi": st["hi"], "n": st["n"]})
    return out


def measure_rate(test_id: str, video_path: str | Path, overrides: dict | None = None,
                 segment_fn=None) -> dict:
    """Steady spread rate only (no files written): used for sensitivity studies and the research harness."""
    cfg = load_config().with_overrides(overrides)
    df, _, meta = extract(video_path, test_id, cfg, read_osd=False, keep_examples=0, segment_fn=segment_fn)
    df.loc[df.area_px < 50, [c for c in df.columns if c.startswith(("x_", "y_", "cx", "cy"))]] = np.nan
    df = spread.edge_series(df, meta["calibration"].get("spread_direction", "auto"), cfg["video"]["pixel_aspect"])
    df = spread.spread_rates(df, cfg["spread"])
    st = steady_regime(df)
    st.pop("regimes", None)
    return {"test_id": test_id, **st}


def analyze_test(test_id: str, video_path: str | Path, cfg: Config | None = None,
                 overrides: dict | None = None, figures: bool = True, do_forecast: bool = True) -> dict:
    cfg = (cfg or load_config()).with_overrides(overrides)
    out_dir = cfg.path("processed") / test_id
    out_dir.mkdir(parents=True, exist_ok=True)
    fig_dir = cfg.path("figures") / test_id
    cond = _conditions(test_id)

    df, kymo, meta = extract(video_path, test_id, cfg)
    df.loc[df.area_px < 50, [c for c in df.columns if c.startswith(("x_", "y_", "cx", "cy"))]] = np.nan
    df = spread.edge_series(df, meta["calibration"].get("spread_direction", "auto"), cfg["video"]["pixel_aspect"])
    df = spread.spread_rates(df, cfg["spread"])
    steady = steady_regime(df)
    regimes_list = steady.pop("regimes", [])
    t0, t1 = steady.get("t0", np.nan), steady.get("t1", np.nan)
    unit = df["unit"].iloc[0]

    df.to_parquet(out_dir / "frames.parquet", index=False)
    np.save(out_dir / "kymograph.npy", kymo)
    (out_dir / "steady.json").write_text(json.dumps({"test_id": test_id, **steady,
                                                     "direction": df.direction.iloc[0],
                                                     "status": "steady_spread" if steady.get("rate") == steady.get("rate")
                                                               else "no_steady_spread",
                                                     "frame_step": meta["info"].get("frame_step"),
                                                     "steps": flow_steps(df),
                                                     "regimes": regimes_list,
                                                     "calibration": {k: v for k, v in meta["calibration"].items()
                                                                     if k.startswith(("mm_per_px", "spread"))},
                                                     "video": meta["info"]}, indent=2, default=float))

    bt = pd.DataFrame()
    fcfg = cfg["forecast"]
    if do_forecast:
        parts = []
        for target in (f"leading_edge_{unit}", "area_mm2" if unit == "mm" else "area_phys_px"):
            d = df[(df.time_s >= t0) & (df.time_s <= t1)] if t0 == t0 else df
            s = forecast.resample(d, target, fcfg["resample_hz"])
            b = forecast.rolling_origin(s, target, fcfg["models"], fcfg["horizons_s"],
                                        fcfg["min_history_s"], fcfg["n_origins"], fcfg["interval"])
            if not b.empty:
                parts.append(b.assign(test_id=test_id, target=target))
        if parts:
            bt = pd.concat(parts, ignore_index=True)
            bt.to_parquet(out_dir / "backtest.parquet", index=False)

    if figures:
        _test_figures(test_id, df, kymo, meta, steady, bt, cond, fig_dir, cfg)
    return {"test_id": test_id, "n_frames": len(df), "unit": unit, **{f"steady_{k}": v for k, v in steady.items()}}


def refit_test(test_id: str, cfg: Config | None = None, figures: bool = True) -> dict:
    """Recompute spread regimes, flow steps, backtests and figures from saved frames.parquet
    (no video decoding). Use after changing spread/forecast logic; segmentation changes need analyze_test."""
    cfg = cfg or load_config()
    out_dir = cfg.path("processed") / test_id
    df = pd.read_parquet(out_dir / "frames.parquet")
    kymo = np.load(out_dir / "kymograph.npy")
    old = json.loads((out_dir / "steady.json").read_text())
    cal = test_calibration(test_id)
    steady = steady_regime(df)
    regimes_list = steady.pop("regimes", [])
    t0, t1 = steady.get("t0", np.nan), steady.get("t1", np.nan)
    unit = df["unit"].iloc[0]
    (out_dir / "steady.json").write_text(json.dumps({
        "test_id": test_id, **steady, "direction": df.direction.iloc[0],
        "status": "steady_spread" if steady.get("rate") == steady.get("rate") else "no_steady_spread",
        "frame_step": old.get("frame_step"), "steps": flow_steps(df), "regimes": regimes_list,
        "calibration": {k: v for k, v in cal.items() if k.startswith(("mm_per_px", "spread"))},
        "video": old.get("video")}, indent=2, default=float))
    fcfg = cfg["forecast"]
    parts = []
    for target in (f"leading_edge_{unit}", "area_mm2" if unit == "mm" else "area_phys_px"):
        d = df[(df.time_s >= t0) & (df.time_s <= t1)] if t0 == t0 else df
        sres = forecast.resample(d, target, fcfg["resample_hz"])
        b = forecast.rolling_origin(sres, target, fcfg["models"], fcfg["horizons_s"],
                                    fcfg["min_history_s"], fcfg["n_origins"], fcfg["interval"])
        if not b.empty:
            parts.append(b.assign(test_id=test_id, target=target))
    bt = pd.concat(parts, ignore_index=True) if parts else pd.DataFrame()
    if len(bt):
        bt.to_parquet(out_dir / "backtest.parquet", index=False)
    elif (out_dir / "backtest.parquet").exists():
        (out_dir / "backtest.parquet").unlink()
    if figures:
        meta = {"examples": {}, "calibration": cal, "info": old.get("video") or {}}
        _test_figures(test_id, df, kymo, meta, steady, bt, _conditions(test_id), cfg.path("figures") / test_id, cfg)
    return {"test_id": test_id, **{f"steady_{k}": v for k, v in steady.items()}}


def _test_figures(test_id, df, kymo, meta, steady, bt, cond, fig_dir, cfg):
    unit = df["unit"].iloc[0]
    ex = meta["examples"]
    if ex:
        ks = sorted(ex)
        rows = []
        for k in ks:
            r = df.iloc[k].to_dict()
            lead = "x_left_sub_px" if df.direction.iloc[0] == "left" else "x_right_sub_px"
            r["le_x_px"] = r.get(lead)
            rows.append(r)
        fig, cap = viz.fig_overlay([ex[k][0] for k in ks], [ex[k][1] for k in ks], rows, test_id, cond)
        viz.save(fig, cap, fig_dir, "G1_overlay")
    pa = cfg["video"]["pixel_aspect"]
    mm = meta["calibration"].get("mm_per_px")
    x_axis = np.arange(kymo.shape[1]) * pa * (mm or 1)
    edges = df.assign(le_x_axis=df["x_left_sub_px"] * pa * (mm or 1), te_x_axis=df["x_right_sub_px"] * pa * (mm or 1))
    if df.direction.iloc[0] == "right":
        edges = edges.assign(le_x_axis=edges.te_x_axis, te_x_axis=edges.le_x_axis)
    fig, cap = viz.fig_kymograph(kymo, df.time_s.to_numpy(), x_axis, edges, test_id, unit, cond)
    viz.save(fig, cap, fig_dir, "G2_kymograph")
    fig, cap, data = viz.fig_edge_fit(df, steady, test_id, cond)
    viz.save(fig, cap, fig_dir, "G3_edge_fit", data)
    fig, cap, data = viz.fig_rate(df, test_id, cond)
    viz.save(fig, cap, fig_dir, "G4_rate", data)
    fig, cap, data = viz.fig_size(df, test_id, cond)
    viz.save(fig, cap, fig_dir, "G7_size", data)
    fig, cap = viz.fig_qc(df, test_id, cond)
    viz.save(fig, cap, fig_dir, "G14_qc")
    if "osd_fan" in df:
        fig, cap, data = fig_telemetry(df, test_id, cond)
        viz.save(fig, cap, fig_dir, "G18_telemetry", data)
    if not bt.empty:
        target = f"leading_edge_{unit}"
        t0, t1 = steady_window(df)
        d = df[(df.time_s >= t0) & (df.time_s <= t1)]
        s = forecast.resample(d, target, cfg["forecast"]["resample_hz"])
        if len(s) > 10:
            cuts = np.linspace(s.time_s.iloc[0] + cfg["forecast"]["min_history_s"],
                               s.time_s.iloc[-1] - max(cfg["forecast"]["horizons_s"]), 3)
            paths = [forecast.forecast_path(s, target, m, c, max(cfg["forecast"]["horizons_s"]))
                     for m in cfg["forecast"]["models"] for c in cuts if c > s.time_s.iloc[0]]
            if paths:
                fig, cap = viz.fig_forecast(s, target, paths, test_id, f"front position ({unit})", cond)
                viz.save(fig, cap, fig_dir, "G9_forecast")


def fig_telemetry(df, test_id, cond):
    """G18: OSD telemetry aligned with the flame area — stacked panels, no dual axis."""
    import matplotlib.pyplot as plt
    panels = [("osd_air_cm_s", "AIR (cm/s)"), ("osd_fan", "FAN (10×V)"), ("osd_rad", "RAD (a.u.)"),
              ("area_phys_px", "flame area (px²)")]
    fig, axes = plt.subplots(len(panels), 1, figsize=(6.4, 6.4), sharex=True)
    for ax, (c, lab), color in zip(axes, panels, viz.SERIES):
        ax.plot(df.time_s, df[c], color=color, lw=1.2)
        ax.set_ylabel(lab)
    axes[-1].set_xlabel("time t (s)")
    axes[0].set_title(f"G18 · OSD telemetry vs. flame — {viz._title(test_id, cond)}")
    cap = (f"**G18 — {test_id}.** Telemetry read by OCR from the video (AIR = air velocity, lagging the fan by "
           "≈15–25 s; FAN = 10× fan voltage; RAD = uncalibrated radiometer) aligned with the luminous area measured by "
           "computer vision. RAD and area should co-vary (independent cross-check). FAN steps are the crew's flow "
           "manoeuvres and explain changes in V_f.")
    return fig, cap, df[["time_s"] + [c for c, _ in panels]]


def aggregate(test_ids: list[str] | None = None, cfg: Config | None = None) -> dict:
    """Ensemble figures and tables (G5, G11, G12, G13) from already-processed tests."""
    from . import evaluation
    from .catalog import load_experimental_table
    cfg = cfg or load_config()
    proc = cfg.path("processed")
    fig_dir = cfg.path("figures") / "_ensemble"
    table = load_experimental_table()
    fig, cap, data = viz.fig_conditions(table)
    viz.save(fig, cap, fig_dir, "G13_conditions", data)
    dirs = [d for d in proc.iterdir() if d.is_dir() and (not test_ids or d.name in test_ids)]
    steadies = [json.loads((d / "steady.json").read_text()) for d in dirs if (d / "steady.json").exists()]
    bts = [pd.read_parquet(d / "backtest.parquet") for d in dirs if (d / "backtest.parquet").exists()]
    out = {}
    if steadies:
        from .config import CONFIG_DIR, load_yaml
        qc = load_yaml(CONFIG_DIR / "qc.yaml")
        st = pd.DataFrame(steadies).drop(columns=["video", "regimes", "steps", "calibration"], errors="ignore")
        # suffixed runs (O13a/O13b ...) are processed under their base id: fall back to the first run's conditions
        base = table.drop_duplicates("test_base").set_index("test_base")
        exact = table.set_index("test_id")
        rows = [exact.loc[t] if t in exact.index else base.loc[t] if t in base.index else pd.Series(dtype=object)
                for t in st.test_id]
        s = pd.concat([st.reset_index(drop=True), pd.DataFrame(rows).reset_index(drop=True)
                       .drop(columns=[c for c in st.columns if c != "test_id"], errors="ignore")], axis=1)
        s = s.loc[:, ~s.columns.duplicated()]
        # flow during the steady window: OSD AIR, lag-corrected
        lag = float(qc.get("anemometer_lag_s", 20))
        flows = []
        for t, t0, t1 in zip(s.test_id, s.get("t0"), s.get("t1")):
            f = proc / t / "frames.parquet"
            v = np.nan
            if f.exists() and t0 == t0 and t0 is not None:
                fr = pd.read_parquet(f, columns=["time_s", "osd_air_cm_s"])
                # lag-corrected window, clipped to the recorded footage; fall back to the unlagged window
                w = fr[(fr.time_s >= t0 + lag) & (fr.time_s <= min(t1 + lag, fr.time_s.max()))].osd_air_cm_s.dropna()
                if len(w) < 3:
                    w = fr[(fr.time_s >= t0) & (fr.time_s <= t1)].osd_air_cm_s.dropna()
                v = 1.0066 * float(w.median()) if len(w) else np.nan
            flows.append(v)
        s["flow_steady_cm_s"] = flows
        def verdict(t):
            if t in (qc.get("trusted") or []): return "trusted"
            if t in (qc.get("trusted_steps_only") or []): return "trusted_steps_only"
            if t in (qc.get("trusted_order_of_magnitude") or []): return "order_of_magnitude"
            if t in (qc.get("trusted_null") or []): return "trusted_null"
            if t in (qc.get("flagged") or {}): return "flagged"
            if t in (qc.get("excluded") or {}): return "excluded"
            return "unreviewed"
        s["qc"] = s.test_id.map(verdict)
        s["qc_note"] = s.test_id.map(lambda t: (qc.get("flagged") or {}).get(t) or (qc.get("excluded") or {}).get(t) or "")
        s.to_csv(fig_dir / "steady_rates.csv", index=False)
        out["qc_counts"] = s.qc.value_counts().to_dict()
        unit = "mm" if (s.loc[s.qc == "trusted", "unit"] == "mm/s").all() else "px"
        fig, cap, data = viz.fig_spread_vs_flow(s[s.qc == "trusted"].assign(
            flow_initial_cm_s=lambda d: d.flow_steady_cm_s.fillna(d.flow_initial_cm_s)), unit)
        viz.save(fig, cap, fig_dir, "G5_spread_vs_flow",
                 data[["test_id", "flow_initial_cm_s", "o2_initial_pct", "rate", "lo", "hi"]])
        out["n_steady"] = len(s)
    if bts:
        from .config import CONFIG_DIR, load_yaml
        trusted = set((load_yaml(CONFIG_DIR / "qc.yaml").get("trusted")) or [])
        bt_all = evaluation.add_crps(pd.concat(bts, ignore_index=True))
        bt_all.groupby(["target", "model", "horizon_s"]).agg(MASE=("scaled_err", "mean"), coverage=("covered", "mean"),
                                                              n=("abs_err", "size")).reset_index().to_csv(
            fig_dir / "forecast_summary_all_tests.csv", index=False)
        # Ensemble forecasting statistics: QC-trusted tests only, one target at a time (no mixing of mm and mm²).
        bt = bt_all[bt_all.test_id.isin(trusted)] if trusted else bt_all
        bt = bt.assign(target=bt.target.str.replace("_mm$|_px$", "", regex=True).str.replace("area_mm2|area_phys_px", "area", regex=True))
        summ = evaluation.forecast_summary(bt, by=("target", "model", "horizon_s"))
        summ.to_csv(fig_dir / "forecast_summary.csv", index=False)
        bt = bt[bt.target == "leading_edge"]
        fig, cap = viz.fig_skill(summ[summ.target == "leading_edge"], "MASE",
                                 "(leading edge, QC-trusted tests)")
        viz.save(fig, cap, fig_dir, "G11_skill")
        fig, cap = viz.fig_calibration(bt)
        viz.save(fig, cap, fig_dir, "G12_calibration")
        fig, cap = viz.fig_residuals(bt)
        viz.save(fig, cap, fig_dir, "G10_residuals")
        out["forecast"] = {m: evaluation.forecast_components(bt, m) for m in bt.model.unique()}
    # External validation (evaluation side: reads published rates, never feeds back into measurement)
    from . import validation
    val = validation.run()
    v = val.pop("table")
    out["validation"] = val
    if len(v) >= 2:
        from .config import CONFIG_DIR, load_yaml
        qc = load_yaml(CONFIG_DIR / "qc.yaml")
        v["qc_excluded"] = v.test_id.str.split(".").str[0].isin(list((qc.get("excluded") or {}).keys()))
        fig, cap = viz.fig_parity(v)
        viz.save(fig, cap, fig_dir, "G6_parity_published", v)
    if val["thickness_law"].get("slope") is not None:
        fig, cap, data = viz.fig_thickness_law(val["thickness_law"])
        viz.save(fig, cap, fig_dir, "G19_thickness_law", data)
    sens = cfg.path("processed") / "_sensitivity.csv"
    if sens.exists():
        fig, cap = viz.fig_sensitivity(pd.read_csv(sens))
        viz.save(fig, cap, fig_dir, "G15_threshold_sensitivity", pd.read_csv(sens))
    res = Path(__file__).resolve().parents[2] / "research/results.tsv"
    if res.exists():
        r = pd.read_csv(res, sep="\t")
        if len(r) > 1:
            fig, cap = viz.fig_loop_progress(r)
            viz.save(fig, cap, fig_dir, "G16_loop_progress", r)
    return out
