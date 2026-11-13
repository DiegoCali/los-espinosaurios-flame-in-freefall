"""Audit of test materials using the heater-wire fingerprint in the telemetry.

The sample is wound on a resistance-wire heater. Its cold resistance R0 and the hot/cold ratio Rt/R0
(the temperature set point) differ by material and match NASA's Rt/R0 column of the moment table, so they
identify the material of tests that have no TEM grid or label.

Output: data/processed/test_material_audit.csv
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from extraction.common import PROCESSED_DIR, write_csv

MATERIALS = ["Kapton", "Lampwick", "Pyrell", "Silicone", "Teflon"]
SCALE = (0.03, 0.04)  # typical within-class spread of (cold R in ohm, Rt/R0), used to scale distances


def fingerprints(ts: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for test, g in ts.groupby("test"):
        h = g[g.heating == 1]
        rec = {"test": int(test), "cold_r_ohm": np.nan, "hot_r_ohm": np.nan, "rt_r0_telemetry": np.nan}
        if len(h):
            cold = g[(g.heating == 0) & (g.t_s < h.t_s.min())].sample_resistance_ohm
            cold = cold[cold > 0.3].median()
            hot = h.sample_resistance_ohm.iloc[10:].median()
            rec.update(cold_r_ohm=cold, hot_r_ohm=hot, rt_r0_telemetry=hot / cold if cold else np.nan)
        rows.append(rec)
    return pd.DataFrame(rows)


def _classify(x: np.ndarray, ref: pd.DataFrame) -> tuple[str, str, float]:
    """1-nearest-neighbour per material in (cold R, Rt/R0); margin = runner-up distance / best distance."""
    z = (ref[["cold_r_ohm", "rt_r0_telemetry"]].to_numpy() - x) / np.array(SCALE)
    d = pd.Series(np.hypot(z[:, 0], z[:, 1]), index=ref.material.to_numpy()).groupby(level=0).min().sort_values()
    return d.index[0], d.index[1], float(d.iloc[1] / max(d.iloc[0], 0.05))


def build() -> pd.DataFrame:
    ts = pd.read_csv(PROCESSED_DIR / "hkp_timeseries_clean.csv.gz")
    tests = pd.read_csv(PROCESSED_DIR / "tests.csv")
    pushes = pd.read_csv(PROCESSED_DIR / "pushes.csv")
    moments = pd.read_csv(PROCESSED_DIR / "nasa_moment_table.csv")
    fp = fingerprints(ts).merge(tests[["test", "material", "material_source", "heat_duration_s",
                                       "gas_plume_temp_max_c", "n_pushes"]], on="test")
    fp["rt_r0_docx"] = fp.test.map(moments.groupby("run").rt_r0.first())
    resp = pushes.groupby("test").agg(max_dusttrak_mg_m3=("dusttrak_b_peak_mg_m3", "max"),
                                      max_ion_rise_v=("ion_b_delta_peak_v", "max"),
                                      max_iss_scatter_v=("iss_scatter_delta_peak_v", "max"))
    fp = fp.merge(resp, left_on="test", right_index=True, how="left")

    # Reference = tests whose material comes from NASA tables or TEM labels (not from the video match).
    ref = fp[(fp.material.isin(MATERIALS)) & (fp.material_source != "video_start_time_match_10s") &
             fp.cold_r_ohm.notna()]
    ref_tests = set(ref.test)

    out = []
    for r in fp.itertuples():
        x = np.array([r.cold_r_ohm, r.rt_r0_telemetry])
        if not np.isfinite(x).all():
            out.append(("", "", np.nan, "no_fingerprint"))
            continue
        pool = ref[ref.test != r.test] if r.test in ref_tests else ref  # leave-one-out for labelled tests
        out.append((*_classify(x, pool), "ok"))
    fp["fingerprint_class"], fp["fingerprint_runner_up"], fp["fingerprint_margin"], fp["fingerprint_status"] = zip(*out)
    fp["labelled"] = fp.material.isin(MATERIALS)

    def verdict(r):
        if r.fingerprint_status != "ok":
            return "no_fingerprint"
        if not r.labelled:
            return "inferred" if r.fingerprint_margin >= 2.5 else "inferred_low_margin"
        return "agrees" if r.fingerprint_class == r.material else "CONFLICT"

    fp["audit_result"] = fp.apply(verdict, axis=1)
    fp["probable_blank_or_purge"] = (fp.heat_duration_s < 30) | (fp.max_dusttrak_mg_m3.fillna(0) < 0.5) & \
        (fp.max_iss_scatter_v.fillna(0) < 0.1)
    cols = ["test", "material", "material_source", "audit_result", "fingerprint_class", "fingerprint_runner_up",
            "fingerprint_margin", "cold_r_ohm", "rt_r0_telemetry", "rt_r0_docx", "heat_duration_s",
            "gas_plume_temp_max_c", "n_pushes", "max_dusttrak_mg_m3", "max_ion_rise_v", "max_iss_scatter_v",
            "probable_blank_or_purge"]
    res = fp[cols].sort_values("test").reset_index(drop=True)
    write_csv(res, PROCESSED_DIR / "test_material_audit.csv")
    return res


if __name__ == "__main__":
    pd.set_option("display.width", 220)
    r = build()
    print(r.round(3).to_string())
    lab = r[r.audit_result.isin(["agrees", "CONFLICT"])]
    print("\nleave-one-out agreement on labelled tests:", (lab.audit_result == "agrees").sum(), "/", len(lab))
