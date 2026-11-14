"""Build the two fixed modelling tables used by prepare.py / train.py.

size_dataset.csv       one row per NASA moment measurement (grid), conditions joined from telemetry.
                       Targets: log10 Dg, log10 Dm, log10 AMD, ln sigma_g, log10 M0.
detection_dataset.csv  one row per piston push with a known material.
                       Targets: ISS photoelectric response >= 1.0 V (proxy alarm) and ionization-chamber
                       response >= 0.5 V (proxy alarm).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from extraction.common import MATERIAL_ORDER, NOMINAL_VELOCITY_CM_S, PROCESSED_DIR, write_csv

DOC_FLOW_VELOCITY = {"nominal_flow": NOMINAL_VELOCITY_CM_S, "low_flow": 2.0, "no_flow": 0.0}


def _aging_lookup(pushes: pd.DataFrame) -> dict:
    lut = {}
    for (test, state), g in pushes.groupby(["test", "aged_state"]):
        g = g.sort_values("push_index")
        lut[(int(test), state)] = (float(g["aging_s"].iloc[0]), "telemetry_push")
    return lut


def build_size_dataset(moments: pd.DataFrame, tests: pd.DataFrame, pushes: pd.DataFrame) -> pd.DataFrame:
    aging_lut = _aging_lookup(pushes)
    tests_i = tests.set_index("test")
    nominal_aged = float(pushes.loc[(pushes.aged_state == "aged") & (pushes.flow_velocity_cm_s > 5), "aging_s"].median())
    nominal_unaged = float(pushes.loc[pushes.aged_state == "unaged", "aging_s"].median())
    rows = []
    for r in moments.itertuples():
        rec = {"run": int(r.run), "source_row": int(r.source_row), "material": r.material,
               "aged_state": r.aged_state, "rt_r0": r.rt_r0, "temperature_regime_doc": r.temperature_regime_doc,
               "flow_regime_doc": r.flow_regime_doc}
        if r.run in tests_i.index:
            t = tests_i.loc[r.run]
            rec["flow_velocity_cm_s"], rec["flow_source"] = t.flow_velocity_cm_s, "telemetry_mfc_during_heating"
            rec["gas_plume_temp_max_c"] = t.gas_plume_temp_max_c
        else:
            rec["flow_velocity_cm_s"], rec["flow_source"] = DOC_FLOW_VELOCITY[r.flow_regime_doc], "document_description"
            rec["gas_plume_temp_max_c"] = np.nan
        if not np.isfinite(rec["flow_velocity_cm_s"]):
            rec["flow_velocity_cm_s"], rec["flow_source"] = DOC_FLOW_VELOCITY[r.flow_regime_doc], "document_description"
        key = (int(r.run), r.aged_state)
        if key in aging_lut:
            rec["aging_s"], rec["aging_source"] = aging_lut[key]
        elif r.aged_state in ("aged", "unaged"):
            rec["aging_s"] = nominal_aged if r.aged_state == "aged" else nominal_unaged
            rec["aging_source"] = "nominal_median_of_telemetry"
        else:
            rec["aging_s"], rec["aging_source"] = np.nan, "unknown_grid_age"
        rec.update({
            "m0_per_cc": r.m0_per_cc, "amd_um": r.amd_um, "dm_um": r.dm_um, "sigma_g": r.sigma_g_hc,
            "dg_um": r.dg_um_from_amd, "qc_flags": r.qc_flags,
        })
        rows.append(rec)
    d = pd.DataFrame(rows)
    d["aged"] = (d["aged_state"] == "aged").astype(int)
    d["no_flow"] = (d["flow_velocity_cm_s"] < 0.5).astype(int)
    d["log10_dg_um"] = np.log10(d["dg_um"])
    d["log10_dm_um"] = np.log10(d["dm_um"])
    d["log10_amd_um"] = np.log10(d["amd_um"])
    d["ln_sigma_g"] = np.log(d["sigma_g"])
    d["log10_m0_per_cc"] = np.log10(d["m0_per_cc"])
    targets = ["log10_dg_um", "log10_dm_um", "log10_amd_um", "ln_sigma_g", "log10_m0_per_cc"]
    usable = moments.set_index("source_row")["usable_size_stats"]
    d["include_in_model"] = (
        d["source_row"].map(usable).astype(bool)
        & d["aged_state"].isin(["aged", "unaged"])
        & d["material"].isin(MATERIAL_ORDER)
        & d[targets + ["rt_r0", "aging_s", "flow_velocity_cm_s"]].notna().all(axis=1)
    )
    d["exclusion_reason"] = np.where(d["include_in_model"], "",
                                     np.where(~d["aged_state"].isin(["aged", "unaged"]), "unknown_grid_age",
                                              np.where(d["qc_flags"].fillna("") != "", "qc_flag", "missing_value")))
    return d


def build_detection_dataset(pushes: pd.DataFrame, moments: pd.DataFrame) -> pd.DataFrame:
    rt = moments.groupby("run")["rt_r0"].first()
    mat_rt = moments.groupby("material")["rt_r0"].median()
    d = pushes.copy()
    d["rt_r0"] = d["test"].map(rt)
    d["rt_r0_source"] = np.where(d["rt_r0"].notna(), "nasa_moment_table", "material_median")
    d["rt_r0"] = d["rt_r0"].fillna(d["material"].map(mat_rt))
    d["no_flow"] = (d["flow_velocity_cm_s"] < 0.5).astype(int)
    d["iss_detect"] = d["iss_detect_proxy"].astype(int)
    d["ion_detect"] = d["ion_detect_proxy"].astype(int)
    d["include_in_model"] = (d["material"].isin(MATERIAL_ORDER)
                             & d[["aging_s", "flow_velocity_cm_s", "rt_r0"]].notna().all(axis=1))
    keep = ["test", "push_index", "material", "aging_s", "aging_source", "aged_state", "flow_velocity_cm_s",
            "no_flow", "rt_r0", "rt_r0_source", "sts_detector_powered", "iss_scatter_delta_peak_v",
            "iss_scatter_saturated", "iss_obscuration_drop_pct", "ion_b_delta_peak_v", "dusttrak_b_peak_mg_m3",
            "ptrak_peak_raw_pt_cc", "sts_alarm", "iss_detect", "ion_detect", "include_in_model"]
    return d[keep]


def run() -> dict[str, pd.DataFrame]:
    moments = pd.read_csv(PROCESSED_DIR / "nasa_moment_table.csv")
    tests = pd.read_csv(PROCESSED_DIR / "tests.csv")
    pushes = pd.read_csv(PROCESSED_DIR / "pushes.csv")
    size = build_size_dataset(moments, tests, pushes)
    det = build_detection_dataset(pushes, moments)
    write_csv(size, PROCESSED_DIR / "size_dataset.csv")
    write_csv(det, PROCESSED_DIR / "detection_dataset.csv")
    return {"size_dataset": size, "detection_dataset": det}


if __name__ == "__main__":
    out = run()
    for k, v in out.items():
        print(k, v.shape, "in model:", int(v["include_in_model"].sum()))
