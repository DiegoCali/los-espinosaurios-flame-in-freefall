"""External validation of measured spread rates against published values (evaluation side).

This module MAY read data/reference/published_rates.csv; measurement code (pipeline, segmentation,
research/experiment.py) must not. Three complementary checks:

1. Absolute accuracy: measured steady V_f (mm/s, geometric ruler calibration) vs published V_f
   (SDSU side view for B tests, NASA TM Table 5.1 for M tests). Multi-step tests are matched to the
   published step whose flow is closest to the OSD air velocity during the measured steady window.
2. Scale-free physics: thin-film opposed-flow spread follows V_f ∝ τ^-1 (de Ris thin limit); the fitted
   log-log slope over B films does not depend on the spatial calibration.
3. Uncertainty honesty: fraction of tests whose |V̂ − V_pub| ≤ 2·sqrt(σ_V² + σ_pub²).
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

from .config import PROJECT_ROOT, load_config


def load_measurements() -> pd.DataFrame:
    proc = load_config().path("processed")
    rows = []
    for d in sorted(p for p in proc.iterdir() if p.is_dir()):
        st = d / "steady.json"
        fr = d / "frames.parquet"
        if not st.exists():
            continue
        s = json.loads(st.read_text())
        row = {k: s.get(k) for k in ("test_id", "rate", "lo", "hi", "unit", "t0", "t1", "n", "direction", "status")}
        row["steps"] = s.get("steps") or []
        vname = str((s.get("video") or {}).get("path", "")).lower()
        row["invalid_video"] = "los" in Path(vname).name  # e.g. M3: only a rack camera recorded during LOS
        if fr.exists() and s.get("t0") is not None:
            f = pd.read_parquet(fr)
            w = f[(f.time_s >= s["t0"]) & (f.time_s <= s["t1"])]
            if "osd_air_cm_s" in w:
                row["osd_air_median_cm_s"] = float(w.osd_air_cm_s.median()) if len(w) else np.nan
        cal = s.get("calibration") or {}
        row["mm_per_px_rel_sigma"] = cal.get("mm_per_px_rel_sigma", 0.021)
        rows.append(row)
    return pd.DataFrame(rows)


def match_published(meas: pd.DataFrame, view: str = "side") -> pd.DataFrame:
    pub = pd.read_csv(PROJECT_ROOT / "data/reference/published_rates.csv")
    pub = pub[pub.view == view]
    out, unmatched = [], []
    for r in meas.itertuples():
        p = pub[pub.test_id == r.test_id]
        if p.empty or r.unit != "mm/s" or getattr(r, "invalid_video", False):
            continue
        steps = [s for s in (getattr(r, "steps", None) or []) if s.get("rate") == s.get("rate")
                 and s.get("air_lagged_cm_s") == s.get("air_lagged_cm_s")]
        if len(p) > 1 and steps:
            # Multi-step published test: optimal one-to-one assignment (Hungarian) between published steps and
            # measured flow steps on |lag-corrected air velocity − published flow|; pairs further apart than
            # max(1.5 cm/s, 20 %) are left unmatched and counted in `steps_available` vs `steps_matched`.
            from scipy.optimize import linear_sum_assignment
            P = list(p.itertuples())
            cost = np.array([[abs(st["air_lagged_cm_s"] - q.flow_cm_s) for st in steps] for q in P])
            rows_i, cols_j = linear_sum_assignment(cost)
            n_match = 0
            for i, j in zip(rows_i, cols_j):
                q, st = P[i], steps[j]
                if cost[i, j] > max(1.5, 0.2 * q.flow_cm_s):
                    continue
                n_match += 1
                se = (st["hi"] - st["lo"]) / (2 * 1.96)
                sig = abs(st["rate"]) * np.hypot(se / abs(st["rate"]) if st["rate"] else 0, r.mm_per_px_rel_sigma)
                out.append({"test_id": f"{r.test_id}.{q.step}", "vf_measured_mm_s": st["rate"], "vf_lo": st["lo"],
                            "vf_hi": st["hi"], "sigma_measured": sig, "vf_published_mm_s": q.vf_mm_s,
                            "sigma_published": q.vf_mm_s * q.sigma_rel, "published_step": q.step,
                            "published_flow_cm_s": q.flow_cm_s, "osd_air_median_cm_s": st["air_lagged_cm_s"],
                            "source": q.source})
            unmatched.append({"test_id": r.test_id, "steps_available": len(P), "steps_matched": n_match})
            continue
        if r.rate != r.rate:
            continue
        if len(p) > 1 and getattr(r, "osd_air_median_cm_s", np.nan) == getattr(r, "osd_air_median_cm_s", np.nan):
            p = p.iloc[[int(np.argmin(np.abs(p.flow_cm_s - 1.0066 * r.osd_air_median_cm_s)))]]
        else:
            p = p.iloc[[0]]
        q = p.iloc[0]
        se_meas = (r.hi - r.lo) / (2 * 1.96)
        sigma = abs(r.rate) * np.hypot(se_meas / abs(r.rate) if r.rate else 0, r.mm_per_px_rel_sigma)
        out.append({"test_id": r.test_id, "vf_measured_mm_s": r.rate, "vf_lo": r.lo, "vf_hi": r.hi,
                    "sigma_measured": sigma, "vf_published_mm_s": q.vf_mm_s, "sigma_published": q.vf_mm_s * q.sigma_rel,
                    "published_step": q.step, "published_flow_cm_s": q.flow_cm_s,
                    "osd_air_median_cm_s": getattr(r, "osd_air_median_cm_s", np.nan), "source": q.source})
    v = pd.DataFrame(out)
    v.attrs["step_matching"] = unmatched
    if v.empty:
        return v
    v["log_ratio"] = np.log(v.vf_measured_mm_s / v.vf_published_mm_s)
    v["rel_error"] = v.vf_measured_mm_s / v.vf_published_mm_s - 1
    v["within_2sigma"] = (v.vf_measured_mm_s - v.vf_published_mm_s).abs() <= 2 * np.hypot(v.sigma_measured, v.sigma_published)
    return v


def summary(v: pd.DataFrame) -> dict:
    if v.empty:
        return {}
    diff = v.vf_measured_mm_s - v.vf_published_mm_s
    return {"n": int(len(v)), "median_abs_rel_error": float(v.rel_error.abs().median()),
            "mean_abs_log_ratio": float(v.log_ratio.abs().mean()),
            "mean_rel_bias": float(v.rel_error.mean()), "coverage_2sigma": float(v.within_2sigma.mean()),
            "bland_altman_bias_mm_s": float(diff.mean()), "bland_altman_loa_mm_s": float(1.96 * diff.std(ddof=1)) if len(v) > 1 else np.nan,
            "spearman_rho": float(stats.spearmanr(v.vf_measured_mm_s, v.vf_published_mm_s)[0]) if len(v) > 2 else np.nan}


def thickness_law(meas: pd.DataFrame, table: pd.DataFrame) -> dict:
    """Scale-free check: log V_f vs log thickness for thin PMMA films (B tests, ~21 % O2)."""
    d = meas.merge(table[["test_id", "material_class", "thickness_mm", "o2_initial_pct", "gmt_day"]], on="test_id")
    # Same session as the published SDSU values (GMT day 50: 22.2 % O2, 2–6.5 cm/s) so only thickness varies.
    d = d[(d.material_class == "PMMA thin film") & d.rate.notna() & (d.rate > 0) & (d.gmt_day == 50)]
    if len(d) < 3 or d.thickness_mm.nunique() < 2:
        return {"n": len(d)}
    res = stats.linregress(np.log(d.thickness_mm), np.log(d.rate))
    pub = pd.read_csv(PROJECT_ROOT / "data/reference/published_rates.csv")
    pub = pub[(pub.view == "side") & pub.test_id.str.startswith("B")].merge(table[["test_id", "thickness_mm"]], on="test_id")
    pres = stats.linregress(np.log(pub.thickness_mm), np.log(pub.vf_mm_s)) if len(pub) > 2 else None
    return {"n": int(len(d)), "slope": float(res.slope), "slope_se": float(res.stderr), "r2": float(res.rvalue ** 2),
            "published_slope": float(pres.slope) if pres else np.nan,
            "published_slope_se": float(pres.stderr) if pres else np.nan, "de_ris_slope": -1.0,
            "tests": d[["test_id", "thickness_mm", "rate", "lo", "hi", "o2_initial_pct"]].to_dict("records")}


def thickness_law_any_day(meas: pd.DataFrame, table: pd.DataFrame) -> dict:
    """Thickness law over all trusted thin films with O2 > 19.5 % (any day; includes tests never used for tuning)."""
    d = meas.merge(table[["test_id", "material_class", "thickness_mm", "o2_initial_pct"]], on="test_id")
    d = d[(d.material_class == "PMMA thin film") & d.rate.notna() & (d.rate > 0) & (d.o2_initial_pct > 19.5)]
    if len(d) < 3 or d.thickness_mm.nunique() < 2:
        return {"n": len(d)}
    r = stats.linregress(np.log(d.thickness_mm), np.log(d.rate))
    return {"n": int(len(d)), "slope": float(r.slope), "slope_se": float(r.stderr), "r2": float(r.rvalue ** 2),
            "tests": d.test_id.tolist()}


def o2_trend(meas: pd.DataFrame, table: pd.DataFrame) -> dict:
    """Sign test: at fixed material and thickness, does V_f increase with O2? (Spearman per group)."""
    d = meas.merge(table[["test_id", "material_class", "thickness_mm", "o2_initial_pct"]], on="test_id")
    d = d[d.rate.notna() & (d.rate > 0)]
    out = []
    for (m, th), g in d.groupby(["material_class", "thickness_mm"]):
        if len(g) >= 3 and g.o2_initial_pct.nunique() >= 2:
            rho, p = stats.spearmanr(g.o2_initial_pct, g.rate)
            out.append({"material": m, "thickness_mm": th, "n": len(g), "rho": float(rho), "p": float(p)})
    return {"groups": out}


def run(write: bool = True) -> dict:
    from .catalog import load_experimental_table
    table = load_experimental_table(write=False)
    meas = load_measurements()
    v = match_published(meas)
    from .config import CONFIG_DIR, load_yaml
    qc = load_yaml(CONFIG_DIR / "qc.yaml")
    hold = load_yaml(CONFIG_DIR / "holdout_tests.yaml") if (CONFIG_DIR / "holdout_tests.yaml").exists() else {}
    holdout_ids = {t for g in (hold.get("study") or {}).values() for t in g}
    if len(v):
        base = v.test_id.str.split(".").str[0]
        v["set"] = np.where(base.isin(holdout_ids), "holdout",
                            np.where(base.isin(["B1", "B2", "B3", "B4", "B5", "B7", "B12", "M1"]), "development", "other"))
        v["qc_excluded"] = base.isin(list((qc.get("excluded") or {}).keys()))
        reviewed = set((qc.get("trusted") or []) + (qc.get("trusted_null") or []) + (qc.get("trusted_steps_only") or [])
                       + (qc.get("trusted_order_of_magnitude") or []) + list((qc.get("flagged") or {}).keys())
                       + list((qc.get("excluded") or {}).keys()))
        v["qc_status"] = np.where(v.qc_excluded, "excluded", np.where(base.isin(reviewed), "passed", "not reviewed"))
    def _s(d):
        return summary(d) if len(d) else {}
    sets = {name: {"all": _s(v[v.set == name]), "qc_passed": _s(v[(v.set == name) & (v.qc_status == "passed")])}
            for name in ("development", "holdout", "other")} if len(v) else {}
    if len(v):
        h = v[v.set == "holdout"]
        first = h[(h.published_step == 1) | ~h.test_id.str.contains(r"\.")]
        sets.setdefault("holdout", {})["first_or_single_step"] = _s(first)
        sets["holdout"]["later_steps"] = _s(h.drop(first.index))
    # hold-out accounting (no survivorship): every hold-out test, whether or not it produced a comparison
    hm = meas[meas.test_id.isin(holdout_ids)]
    compared = set(v.test_id.str.split(".").str[0]) if len(v) else set()
    holdout_accounting = {"n_tests": len(holdout_ids), "n_processed": int(len(hm)),
                          "n_with_comparison": int(len(holdout_ids & compared)),
                          "no_steady_spread": sorted(hm[hm.status != "steady_spread"].test_id.tolist()),
                          "no_matched_step": sorted((set(hm.test_id) - compared) - set(hm[hm.status != "steady_spread"].test_id))}
    trusted = meas[meas.test_id.isin(qc.get("trusted") or [])]
    res = {"by_set": sets, "holdout_accounting": holdout_accounting, "absolute_all": _s(v), "step_matching": v.attrs.get("step_matching", []),
           "thickness_law": thickness_law(meas, table),
           "thickness_law_extended_trusted": thickness_law_any_day(trusted, table),
           "o2_trend_trusted": o2_trend(trusted, table),
           "note": ("development = tests used to choose segmentation and regime settings (in-sample); holdout = "
                    "slab tests processed only after all settings were frozen; qc_passed excludes tests rejected by "
                    "the physics review, which was done with published values visible (not independent).")}
    if write:
        out = PROJECT_ROOT / "reports"
        out.mkdir(exist_ok=True)
        v.to_csv(out / "validation_published.csv", index=False)
        (out / "validation_summary.json").write_text(json.dumps(res, indent=2, default=float))
    return {"table": v, **res}
