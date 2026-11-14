"""Scientific findings computed from the processed SAME-R tables and the selected model.

Every number reported in the JSON exports and Markdown reports is computed here.
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import numpy as np
import pandas as pd

from analysis import physics as ph
from extraction.common import MATERIAL_ORDER, MODULE_DIR, PROCESSED_DIR

RUN_DIR = MODULE_DIR / "runs" / "autoresearch" / "same-run-01"
ISS_THRESHOLDS_V = [0.25, 0.5, 1.0, 1.5, 2.0, 3.0]
ION_THRESHOLDS_V = [0.1, 0.25, 0.5, 0.75, 1.0, 1.5]


def load() -> dict[str, pd.DataFrame]:
    names = ["nasa_moment_table", "size_dataset", "detection_dataset", "pushes", "tests", "coagulation_reference",
             "published_table1_baseline", "tem_summary", "nasa_flow_aging_table", "thermal_precipitator_map"]
    return {n: pd.read_csv(PROCESSED_DIR / f"{n}.csv") for n in names}


def _r(x, n=3):
    return None if x is None or (isinstance(x, float) and not np.isfinite(x)) else round(float(x), n)


# --------------------------------------------------------------------------- particle size by material
def material_size_table(size: pd.DataFrame) -> pd.DataFrame:
    s = size[size.include_in_model & (size.no_flow == 0)]
    g = s.groupby(["material", "aged_state"])
    t = g.agg(n=("run", "size"), dg_um=("dg_um", "median"), amd_um=("amd_um", "median"), dm_um=("dm_um", "median"),
              sigma_g=("sigma_g", "median"), m0_per_cc=("m0_per_cc", "median"),
              aging_s=("aging_s", "median")).reset_index()
    return t


def published_comparison(size_tab: pd.DataFrame, pub: pd.DataFrame) -> pd.DataFrame:
    m = pub.merge(size_tab, on=["material", "aged_state"], how="left", suffixes=("_published", "_this_study"))
    m["dm_ratio_this_over_published"] = m["dm_um_this_study"] / m["dm_um_published"]
    return m


def lognormal_visibility(size_tab: pd.DataFrame) -> pd.DataFrame:
    """Share of number / first moment / mass above optical-sensitivity cut-offs (log-normal)."""
    rows = []
    for r in size_tab.itertuples():
        rows.append({"material": r.material, "aged_state": r.aged_state, "dg_um": r.dg_um, "sigma_g": r.sigma_g,
                     "number_fraction_above_0p3um": ph.fraction_above(0.3, r.dg_um, r.sigma_g, 0),
                     "mass_fraction_above_0p3um": ph.fraction_above(0.3, r.dg_um, r.sigma_g, 3),
                     "mass_fraction_above_1um": ph.fraction_above(1.0, r.dg_um, r.sigma_g, 3)})
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------- aging / coagulation
def aging_pairs(size: pd.DataFrame) -> pd.DataFrame:
    s = size[size.include_in_model]
    rows = []
    for run, g in s.groupby("run"):
        if set(g.aged_state) != {"aged", "unaged"}:
            continue
        u, a = g[g.aged_state == "unaged"].iloc[0], g[g.aged_state == "aged"].iloc[0]
        dt = a.aging_s - u.aging_s
        rows.append({
            "run": int(run), "material": u.material, "flow_velocity_cm_s": u.flow_velocity_cm_s, "no_flow": int(u.no_flow),
            "aging_unaged_s": u.aging_s, "aging_aged_s": a.aging_s, "delta_t_s": dt,
            "m0_unaged": u.m0_per_cc, "m0_aged": a.m0_per_cc, "m0_ratio_aged_over_unaged": a.m0_per_cc / u.m0_per_cc,
            "dm_unaged_um": u.dm_um, "dm_aged_um": a.dm_um, "dm_growth": a.dm_um / u.dm_um,
            "amd_growth": a.amd_um / u.amd_um, "dg_growth": a.dg_um / u.dg_um,
            "sigma_g_unaged": u.sigma_g, "sigma_g_aged": a.sigma_g,
            "k_coag_cm3_s": ph.coag_coefficient_from_counts(u.m0_per_cc, a.m0_per_cc, dt),
            # mass-conserving coagulation would give Dm growth = (N_u / N_a)^(1/3)
            "dm_growth_if_mass_conserved": (u.m0_per_cc / a.m0_per_cc) ** (1 / 3),
        })
    return pd.DataFrame(rows)


def flow_effect(size: pd.DataFrame) -> pd.DataFrame:
    s = size[size.include_in_model & (size.aged_state == "unaged")]
    rows = []
    for mat, g in s.groupby("material"):
        f, q = g[g.no_flow == 0], g[g.no_flow == 1]
        if len(f) and len(q):
            rows.append({"material": mat, "n_flow": len(f), "n_no_flow": len(q),
                         "dm_flow_um": f.dm_um.median(), "dm_no_flow_um": q.dm_um.median(),
                         "dm_ratio_no_flow_over_flow": q.dm_um.median() / f.dm_um.median(),
                         "m0_flow": f.m0_per_cc.median(), "m0_no_flow": q.m0_per_cc.median(),
                         "m0_ratio_no_flow_over_flow": q.m0_per_cc.median() / f.m0_per_cc.median()})
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------- detectors
def detection_rates(det: pd.DataFrame) -> pd.DataFrame:
    d = det[det.include_in_model].copy()
    d["flow_regime"] = np.where(d.no_flow == 1, "no_flow", "flow_8cm_s")
    g = d.groupby(["material", "flow_regime"])
    t = g.agg(n_pushes=("test", "size"), iss_rate=("iss_detect", "mean"), ion_rate=("ion_detect", "mean")).reset_index()
    either = g.apply(lambda x: float(np.mean((x.iss_detect == 1) | (x.ion_detect == 1))), include_groups=False)
    t["either_rate"] = either.values
    return t


def detection_overall(det: pd.DataFrame) -> dict:
    d = det[det.include_in_model]
    out = {}
    for regime, sub in [("all", d), ("flow_8cm_s", d[d.no_flow == 0]), ("no_flow", d[d.no_flow == 1])]:
        iss, ion = sub.iss_detect == 1, sub.ion_detect == 1
        out[regime] = {"n_pushes": int(len(sub)), "iss_rate": float(iss.mean()), "ion_rate": float(ion.mean()),
                       "either_rate": float((iss | ion).mean()), "both_rate": float((iss & ion).mean()),
                       "iss_only": int((iss & ~ion).sum()), "ion_only": int((ion & ~iss).sum()),
                       "neither": int((~iss & ~ion).sum())}
    return out


def threshold_sensitivity(det: pd.DataFrame) -> pd.DataFrame:
    d = det[det.include_in_model]
    rows = []
    for thr in ISS_THRESHOLDS_V:
        for regime, sub in [("flow_8cm_s", d[d.no_flow == 0]), ("no_flow", d[d.no_flow == 1])]:
            rows.append({"detector": "ISS photoelectric (scatter)", "threshold_v": thr, "flow_regime": regime,
                         "detection_rate": float((sub.iss_scatter_delta_peak_v >= thr).mean())})
    for thr in ION_THRESHOLDS_V:
        for regime, sub in [("flow_8cm_s", d[d.no_flow == 0]), ("no_flow", d[d.no_flow == 1])]:
            rows.append({"detector": "Ionization chamber (first moment)", "threshold_v": thr, "flow_regime": regime,
                         "detection_rate": float((sub.ion_b_delta_peak_v >= thr).mean())})
    return pd.DataFrame(rows)


def sts_comparison(pushes: pd.DataFrame) -> pd.DataFrame:
    p = pushes[pushes.sts_detector_powered]
    return p[["test", "material", "push_index", "aging_s", "flow_velocity_cm_s", "sts_alarm", "sts_alarm_delay_s",
              "iss_scatter_delta_peak_v", "iss_detect_proxy", "iss_scatter_delay_s", "ion_b_delta_peak_v",
              "ion_detect_proxy", "dusttrak_b_peak_mg_m3"]].reset_index(drop=True)


def response_delays(pushes: pd.DataFrame) -> dict:
    p = pushes
    return {"iss_scatter_median_s": float(p.iss_scatter_delay_s.median()),
            "ion_b_median_s": float(p.ion_b_delay_s.median()),
            "sts_alarm_median_s": float(p.sts_alarm_delay_s.median()),
            "n_iss": int(p.iss_scatter_delay_s.notna().sum()), "n_ion": int(p.ion_b_delay_s.notna().sum()),
            "n_sts": int(p.sts_alarm_delay_s.notna().sum())}


def moment_signal_physics(det: pd.DataFrame, size: pd.DataFrame) -> pd.DataFrame:
    """Join detector responses with NASA moments on (run, aged_state) for the physical explanation."""
    d = det.rename(columns={"test": "run"})
    s = size[size.include_in_model][["run", "aged_state", "dm_um", "amd_um", "m0_per_cc", "sigma_g", "dg_um"]]
    m = d.merge(s, on=["run", "aged_state"], how="inner")
    m["m1_um_per_cc"] = m.m0_per_cc * m.amd_um
    m["m3_um3_per_cc"] = m.m0_per_cc * m.dm_um ** 3
    return m


# --------------------------------------------------------------------------- QC and TEM
def qc_summary(moments: pd.DataFrame) -> dict:
    usable = moments[moments.usable_size_stats]
    rel = ((usable.sigma_g_from_ratio - usable.sigma_g_hc).abs() / usable.sigma_g_hc)
    flagged = moments[moments.qc_flags.fillna("") != ""][["run", "material", "aged_state", "qc_flags"]]
    return {"n_rows": int(len(moments)), "n_usable": int(len(usable)),
            "sigma_g_ratio_consistency_max_rel_diff": float(rel.max()),
            "flagged": flagged.to_dict(orient="records"),
            "aged_state_sources": moments.aged_state_source.value_counts().to_dict()}


def tem_vs_moments(tem: pd.DataFrame, moments: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for r in tem[tem.method.str.startswith("count")].itertuples():
        mm = moments[(moments.run == r.run)].iloc[0]
        rows.append({"run": r.run, "particle_set": r.particle_set, "n_particles": r.n_particles,
                     "tem_amd_um": r.amd_um, "moment_amd_um": mm.amd_um, "tem_dm_um": r.dm_um,
                     "moment_dm_um": mm.dm_um, "tem_sigma_g": r.sigma_g, "moment_sigma_g": mm.sigma_g_hc,
                     "tem_dg_um": r.dg_um, "moment_dg_um": mm.dg_um_from_amd})
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------- model
def load_best_model():
    spec = importlib.util.spec_from_file_location("best_train", RUN_DIR / "best_train.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def model_curves(size: pd.DataFrame, det: pd.DataFrame) -> dict:
    """Fit the selected model on all rows and predict on a grid of conditions (scenario curves)."""
    import sys

    sys.path.insert(0, str(MODULE_DIR))
    import prepare

    mod = load_best_model()
    Xs, Ys, _, dfs = prepare.load_size()
    Xd, Yd, _, dfd = prepare.load_detection()
    rt_med = dfs.groupby("material")["rt_r0"].median()
    t_range = dfs.groupby("no_flow")["aging_s"].agg(["min", "max"])
    t_grid = np.array([11, 38, 120, 300, 566, 720, 1000, 1500, 1800], float)
    curves = []
    for mat in MATERIAL_ORDER:
        for nf, vel in [(0, 8.1), (1, 0.0)]:
            n = len(t_grid)
            X = {"material": np.array([mat] * n), "aged": (t_grid > 120).astype(float), "aging_s": t_grid,
                 "flow_velocity_cm_s": np.full(n, vel), "no_flow": np.full(n, float(nf)),
                 "rt_r0": np.full(n, float(rt_med[mat]))}
            ps = mod.fit_predict_size(Xs, Ys.copy(), X, 0)
            Xd_ = {**X, "push_index": np.where(t_grid > 120, 2.0, 1.0)}
            Xd_.pop("aged")
            pdet = mod.fit_predict_detection(Xd, Yd.copy(), Xd_, 0)
            for i, t in enumerate(t_grid):
                curves.append({"material": mat, "flow_regime": "no_flow" if nf else "flow_8cm_s", "aging_s": t,
                               "dg_um": 10 ** ps[i, 0], "dm_um": 10 ** ps[i, 1], "amd_um": 10 ** ps[i, 2],
                               "sigma_g": float(np.exp(ps[i, 3])), "m0_per_cc": 10 ** ps[i, 4],
                               "p_iss_detect": pdet[i, 0], "p_ion_detect": pdet[i, 1],
                               "iss_false_negative_risk": 1 - pdet[i, 0], "ion_false_negative_risk": 1 - pdet[i, 1],
                               "extrapolated": bool(t < t_range.loc[nf, "min"] or t > t_range.loc[nf, "max"])})
    return {"curves": pd.DataFrame(curves), "rt_r0_median": rt_med.to_dict()}


def autoresearch_ledger() -> pd.DataFrame:
    return pd.read_csv(RUN_DIR / "results.tsv", sep="\t")


def best_attempt() -> dict:
    best = json.loads((RUN_DIR / "best.json").read_text())
    full = json.loads((RUN_DIR / f"attempt-{best['attempt']:02d}.json").read_text())
    base = json.loads((RUN_DIR / "attempt-01.json").read_text())
    return {"best": best, "best_full": full, "baseline": base}


def compute_all() -> dict:
    d = load()
    size_tab = material_size_table(d["size_dataset"])
    out = {
        "data": d,
        "size_by_material": size_tab,
        "published_comparison": published_comparison(size_tab, d["published_table1_baseline"]),
        "visibility": lognormal_visibility(size_tab),
        "aging_pairs": aging_pairs(d["size_dataset"]),
        "flow_effect": flow_effect(d["size_dataset"]),
        "detection_rates": detection_rates(d["detection_dataset"]),
        "detection_overall": detection_overall(d["detection_dataset"]),
        "threshold_sensitivity": threshold_sensitivity(d["detection_dataset"]),
        "sts": sts_comparison(d["pushes"]),
        "delays": response_delays(d["pushes"]),
        "moment_signal": moment_signal_physics(d["detection_dataset"], d["size_dataset"]),
        "qc": qc_summary(d["nasa_moment_table"]),
        "tem_vs_moments": tem_vs_moments(d["tem_summary"], d["nasa_moment_table"]),
        "ledger": autoresearch_ledger(),
        "attempts": best_attempt(),
    }
    out.update(model_curves(d["size_dataset"], d["detection_dataset"]))
    coag = d["coagulation_reference"]
    out["coagulation"] = {
        "nasa_note_k_cm3_s": coag.k_coag_cm3_s.tolist(),
        "brownian_monodisperse_k_cm3_s_at_0p2um": float(ph.brownian_kernel_monodisperse(0.2)),
        "pairs_k_median_flow_cm3_s": float(out["aging_pairs"].query("no_flow == 0").k_coag_cm3_s.median()),
        "pairs_k_iqr_flow_cm3_s": out["aging_pairs"].query("no_flow == 0").k_coag_cm3_s.quantile([0.25, 0.75]).tolist(),
    }
    return out


if __name__ == "__main__":
    pd.set_option("display.width", 220)
    r = compute_all()
    for k in ["size_by_material", "published_comparison", "visibility", "aging_pairs", "flow_effect", "detection_rates",
              "sts", "tem_vs_moments"]:
        print(f"== {k}")
        print(r[k].round(3).to_string())
    for k in ["detection_overall", "delays", "coagulation", "rt_r0_median"]:
        print(f"== {k}", json.dumps(r[k], indent=1, default=float))
    print(r["curves"].query("aging_s in [38, 566, 1800]").round(3).to_string())
