"""Clean the 1 Hz SAME-R housekeeping telemetry and derive per-test / per-push features.

A SAME-R test proceeds as: ~53 s of sample heating while the aging-chamber piston draws air
past the sample (fill), a hold in the aging chamber (aging), then one or more piston pushes
that send aged smoke through the diagnostics duct, where the moment instruments (P-Trak,
ionization chamber, DustTrak) and the ISS and Space Shuttle (STS) smoke detectors read it.

Outputs (data/processed/):
- hkp_timeseries_clean.csv.gz  all tests, key channels, seconds since test start
- tests.csv                    one row per test: material, flow, heating, phase timing
- pushes.csv                   one row per push: aging time and every detector's response
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from extraction.common import (HKP_CHANNELS, NOMINAL_FILL_FLOW_LPM, NOMINAL_VELOCITY_CM_S, PROCESSED_DIR,
                               find_raw_dir, write_csv)

# Project-defined response thresholds (proxies, NOT flight alarm set points; see DATA_PLAN.md).
ISS_SCATTER_THRESHOLD_V = 1.0     # drop of the ISS detector forward-scatter channel
ION_B_THRESHOLD_V = 0.5           # rise of the ionization-chamber (first-moment) voltage
ISS_SCATTER_SATURATION_V = -6.2   # scatter channel floor observed in the data
PUSH_WINDOW_S = 180               # response window after each push start
AGED_MIN_S = 120                  # pushes held longer than this are "aged" grids
NOMINAL_FIRST_PUSH_AGING_S = 38.0  # median fill-end -> first push delay over all complete tests

# Tests whose material is not in any TEM file name but can be matched to a labelled MSG video
# by start time (video "1 Lampwick" started 2010-09-07 16:18:22 GMT; test 92 started 16:18:12).
# CAUTION: the heater fingerprint contradicts this label (see extraction/material_audit.py). It is kept
# unchanged because the frozen AutoResearch datasets were built with it; sensitivity is in runs/verification.
VIDEO_MATERIAL_MATCH = {92: ("Lampwick", "video_start_time_match_10s")}


def _read_hkp_csv(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, low_memory=False)
    df = df[df["TestNumber"].astype(str) != "TestNumber"]  # repeated header rows
    for c in df.columns:
        if c != "TimeString":
            df[c] = pd.to_numeric(df[c], errors="coerce")
    df["source_file"] = path.name
    return df


def _read_xls_original(path: Path) -> pd.DataFrame:
    df = pd.read_excel(path, sheet_name="Original (cut and paste)")
    df = df[pd.to_numeric(df["TestNumber"], errors="coerce").notna()]
    for c in df.columns:
        if c != "TimeString":
            df[c] = pd.to_numeric(df[c], errors="coerce")
    df["source_file"] = path.name
    return df


def load_all(raw: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return (telemetry rows for tests > 0, provenance table). CSV files take priority."""
    frames, prov, seen = [], [], set()
    sources = [(p, _read_hkp_csv) for p in sorted(raw.glob("HKPData_gmt*.csv"))]
    xls = sorted(raw.glob("2010_*.xls"), key=lambda p: ("wrong" in p.name.lower(), p.name))
    sources += [(p, _read_xls_original) for p in xls]
    for path, reader in sources:
        df = reader(path)
        for test, g in df[df["TestNumber"] > 0].groupby("TestNumber"):
            test = int(test)
            if test in seen:
                prov.append({"test": test, "file": path.name, "used": False, "rows": len(g),
                             "note": "duplicate copy of an already loaded test"})
                continue
            seen.add(test)
            gmt = str(g["TimeString"].iloc[0])
            prov.append({"test": test, "file": path.name, "used": True, "rows": len(g), "gmt_start": gmt,
                         "note": "label in file name says wrong run; content identified by TestNumber"
                         if "wrong" in path.name.lower() else ""})
            frames.append(g.assign(TestNumber=test))
    raw_df = pd.concat(frames, ignore_index=True)
    return raw_df, pd.DataFrame(prov)


def clean_timeseries(raw_df: pd.DataFrame) -> pd.DataFrame:
    keep = [c for c in HKP_CHANNELS if c in raw_df.columns]
    ts = raw_df[keep + ["TimeString", "source_file"]].rename(columns=HKP_CHANNELS)
    ts = ts.rename(columns={"TimeString": "gmt"})
    ts["t_s"] = ts["unix_time_s"] - ts.groupby("test")["unix_time_s"].transform("min")
    ts["ptrak_raw_pt_cc"] = ts["ptrak_raw_pt_cc"].where(ts["ptrak_raw_pt_cc"] >= 0)  # -999 = invalid
    # DustTrak A reads ~1e4/2e4 status-like codes in SAME-R (slot reassigned to MPASS): not a mass.
    ts["dusttrak_a_raw"] = ts["dusttrak_a_raw"].where(ts["dusttrak_a_raw"] < 1000)
    cols = ["test", "t_s", "gmt"] + [v for v in HKP_CHANNELS.values() if v not in ("test",)] + ["source_file"]
    return ts[cols].sort_values(["test", "t_s"]).reset_index(drop=True)


def _edges(x: np.ndarray, rising: bool) -> np.ndarray:
    x = np.nan_to_num(x).astype(int)
    d = np.diff(x)
    return np.where(d == (1 if rising else -1))[0] + 1


def _first_cross(t: np.ndarray, y: np.ndarray, thr: float) -> float:
    idx = np.where(y >= thr)[0]
    return float(t[idx[0]]) if len(idx) else np.nan


def segment_test(g: pd.DataFrame) -> dict:
    t = g["t_s"].to_numpy()
    heat = np.nan_to_num(g["heating"].to_numpy())
    fill = g["piston_fill"].to_numpy()
    push = g["piston_push"].to_numpy()
    hi = np.where(heat == 1)[0]
    seg = {"heat_start_s": np.nan, "heat_end_s": np.nan, "heat_duration_s": 0.0, "heater_flag": "present"}
    start_idx = 0
    if len(hi):
        seg.update(heat_start_s=t[hi[0]], heat_end_s=t[hi[-1]], heat_duration_s=float(heat.sum()))
        start_idx = hi[0]
    else:
        seg["heater_flag"] = "heating_flag_never_set"
    falls = [i for i in _edges(fill, rising=False) if i > start_idx]
    all_rises = [i for i in _edges(push, rising=True) if i > start_idx]
    # Fill end = last closing of the fill valve before the first push (robust when the
    # heating flag is missing or the valve cycles more than once).
    if falls and all_rises:
        before = [i for i in falls if i < all_rises[0]]
        fill_end = before[-1] if before else falls[0]
    else:
        fill_end = falls[0] if falls else None
    seg["fill_end_s"] = t[fill_end] if fill_end is not None else np.nan
    rises = [i for i in _edges(push, rising=True) if fill_end is None or i > fill_end]
    pushes = []
    for k, i in enumerate(rises):
        off = [j for j in _edges(push, rising=False) if j > i]
        pushes.append((i, off[0] if off else len(t) - 1))
    seg["pushes"] = pushes
    return seg


def test_features(g: pd.DataFrame, seg: dict) -> dict:
    t = g["t_s"].to_numpy()
    pre = g[t < (seg["heat_start_s"] if np.isfinite(seg["heat_start_s"]) else 30)].head(60)
    if len(pre) < 5:
        pre = g.head(30)
    heat_mask = (g["heating"] == 1).to_numpy()
    mfc_heat = float(np.nanmedian(g.loc[heat_mask, "mfc_flow_lpm"])) if heat_mask.any() else np.nan
    vel = max(mfc_heat, 0.0) * NOMINAL_VELOCITY_CM_S / NOMINAL_FILL_FLOW_LPM if np.isfinite(mfc_heat) else np.nan
    return {
        "gmt_start": g["gmt"].iloc[0],
        "duration_s": float(t[-1]),
        "source_file": g["source_file"].iloc[0],
        "heat_duration_s": seg["heat_duration_s"],
        "heater_flag": seg["heater_flag"],
        "gas_plume_temp_max_c": float(np.nanmax(g["gas_plume_temp_c"])),
        "gas_plume_temp_baseline_c": float(np.nanmedian(pre["gas_plume_temp_c"])),
        "fill_flow_during_heating_lpm": mfc_heat,
        "flow_velocity_cm_s": round(vel, 2) if np.isfinite(vel) else np.nan,
        "flow_regime_hkp": ("no_flow" if vel < 0.5 else "low_flow" if vel < 5 else "nominal_flow")
        if np.isfinite(vel) else "unknown",
        "fill_end_after_heat_s": seg["fill_end_s"] - seg["heat_end_s"],
        "n_pushes": len(seg["pushes"]),
        "sts_detector_powered": bool(np.nanmax(g["sts_power"]) > 0),
        "baseline_iss_scatter_v": float(np.nanmedian(pre["iss_scatter_v"])),
        "baseline_iss_obscuration_v": float(np.nanmedian(pre["iss_obscuration_v"])),
        "baseline_ion_b_v": float(np.nanmedian(pre["ion_b_v"])),
        "baseline_ion_a_v": float(np.nanmedian(pre["ion_a_v"])),
        "baseline_sts_v": float(np.nanmedian(pre["sts_v"])),
    }


def push_features(g: pd.DataFrame, seg: dict, tf: dict) -> list[dict]:
    t = g["t_s"].to_numpy()
    out = []
    starts = [p[0] for p in seg["pushes"]]
    for k, (i0, i1) in enumerate(seg["pushes"]):
        t0 = t[i0]
        t_end = min(t0 + PUSH_WINDOW_S, t[starts[k + 1]] - 1 if k + 1 < len(starts) else t[-1])
        w = g[(g["t_s"] >= t0) & (g["t_s"] <= t_end)]
        tw = w["t_s"].to_numpy() - t0
        sc = tf["baseline_iss_scatter_v"] - w["iss_scatter_v"].to_numpy()       # positive = more scatter
        ob = tf["baseline_iss_obscuration_v"] - w["iss_obscuration_v"].to_numpy()
        ib = w["ion_b_v"].to_numpy() - tf["baseline_ion_b_v"]
        ia = w["ion_a_v"].to_numpy() - tf["baseline_ion_a_v"]
        sts_al = np.nan_to_num(w["sts_alarm"].to_numpy())
        pt = w["ptrak_raw_pt_cc"].to_numpy()
        dtb = w["dusttrak_b_mg_m3"].to_numpy()
        if np.isfinite(seg["fill_end_s"]):
            aging, aging_src = t0 - seg["fill_end_s"], "fill_valve_close_to_push"
        else:  # log starts after the fill (test 63): anchor on the first push
            aging = t0 - t[starts[0]] + NOMINAL_FIRST_PUSH_AGING_S
            aging_src = "estimated_from_first_push_plus_nominal_38s"
        rec = {
            "push_index": k + 1,
            "push_start_s": t0,
            "push_duration_s": float(t[i1] - t0),
            "window_s": float(t_end - t0),
            "aging_s": float(aging),
            "aging_source": aging_src,
            "aged_state": "aged" if aging >= AGED_MIN_S else "unaged",
            "ptrak_peak_raw_pt_cc": float(np.nanmax(pt)) if np.isfinite(pt).any() else np.nan,
            "dusttrak_b_peak_mg_m3": float(np.nanmax(dtb)),
            "ion_b_delta_peak_v": float(np.nanmax(ib)),
            "ion_a_delta_peak_v": float(np.nanmax(ia)) if not tf["sts_detector_powered"] else np.nan,
            "iss_scatter_delta_peak_v": float(np.nanmax(sc)),
            "iss_scatter_saturated": bool(np.nanmin(w["iss_scatter_v"]) <= ISS_SCATTER_SATURATION_V),
            "iss_obscuration_drop_peak_v": float(np.nanmax(ob)),
            "iss_obscuration_drop_pct": float(100 * np.nanmax(ob) / tf["baseline_iss_obscuration_v"]),
            "sts_v_peak": float(np.nanmax(w["sts_v"])) if tf["sts_detector_powered"] else np.nan,
            "sts_alarm": bool(sts_al.max() > 0) if tf["sts_detector_powered"] else None,
            "sts_alarm_delay_s": float(tw[np.argmax(sts_al > 0)]) if tf["sts_detector_powered"] and sts_al.max() > 0 else np.nan,
            "iss_scatter_delay_s": _first_cross(tw, sc, ISS_SCATTER_THRESHOLD_V),
            "ion_b_delay_s": _first_cross(tw, ib, ION_B_THRESHOLD_V),
        }
        rec["iss_detect_proxy"] = bool(rec["iss_scatter_delta_peak_v"] >= ISS_SCATTER_THRESHOLD_V)
        rec["ion_detect_proxy"] = bool(rec["ion_b_delta_peak_v"] >= ION_B_THRESHOLD_V)
        out.append(rec)
    return out


def material_lookup(processed: Path = PROCESSED_DIR) -> dict[int, tuple[str, str]]:
    """Run -> (material, source). TEM grid documents first, then the labelled-video match."""
    lut: dict[int, tuple[str, str]] = {}
    mt = processed / "nasa_moment_table.csv"
    tp = processed / "thermal_precipitator_map.csv"
    if mt.exists():
        for r in pd.read_csv(mt).itertuples():
            lut.setdefault(int(r.run), (r.material, "nasa_moment_table"))
    if tp.exists():
        for r in pd.read_csv(tp).dropna(subset=["material"]).itertuples():
            lut.setdefault(int(r.run), (r.material, "thermal_precipitator_map"))
    inv = processed.parent / "inventory" / "files.csv"
    if inv.exists():
        d = pd.read_csv(inv).dropna(subset=["run", "material"])
        d = d[~d["label_flags"].fillna("").str.contains("sample_code_implies|source_label")]
        for r in d.itertuples():
            lut.setdefault(int(r.run), (r.material, "file_name"))
    for run, (mat, src) in VIDEO_MATERIAL_MATCH.items():
        lut.setdefault(run, (mat, src))
    # "2010_211_13_silcon_run59 wrong seems to be 60.xls" contains TestNumber 60 (silicone).
    lut.setdefault(60, ("Silicone", "run_spreadsheet_name"))
    return lut


def run(raw_dir: Path | None = None) -> dict[str, pd.DataFrame]:
    raw = find_raw_dir(raw_dir)
    raw_df, prov = load_all(raw)
    ts = clean_timeseries(raw_df)
    mats = material_lookup()
    tests, pushes = [], []
    for test, g in ts.groupby("test"):
        g = g.reset_index(drop=True)
        seg = segment_test(g)
        tf = test_features(g, seg)
        mat, msrc = mats.get(int(test), ("unknown", "not_identified"))
        tests.append({"test": int(test), "material": mat, "material_source": msrc, **tf})
        for p in push_features(g, seg, tf):
            pushes.append({"test": int(test), "material": mat, "flow_velocity_cm_s": tf["flow_velocity_cm_s"],
                           "sts_detector_powered": tf["sts_detector_powered"], **p})
    tests_df, pushes_df = pd.DataFrame(tests), pd.DataFrame(pushes)
    write_csv(ts, PROCESSED_DIR / "hkp_timeseries_clean.csv.gz", compression={"method": "gzip", "mtime": 0})
    write_csv(tests_df, PROCESSED_DIR / "tests.csv")
    write_csv(pushes_df, PROCESSED_DIR / "pushes.csv")
    write_csv(prov, PROCESSED_DIR / "hkp_provenance.csv")
    return {"timeseries": ts, "tests": tests_df, "pushes": pushes_df, "provenance": prov}


if __name__ == "__main__":
    out = run()
    print({k: v.shape for k, v in out.items()})
