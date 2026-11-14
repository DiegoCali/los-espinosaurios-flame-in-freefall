"""Sensitivity of the frozen best model to the material audit (no retraining, no protocol change).

Scenarios for the detection task (the size task has no rows for these tests):
  frozen        the dataset used in same-run-01 (test 92 labelled Lampwick from a video match)
  relabel_92    test 92 relabelled with its heater fingerprint class
  add_audited   additionally include the 10 tests with no label, using fingerprint-inferred materials

Writes runs/verification/material_audit_sensitivity.json.
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import prepare  # noqa: E402

RUN_DIR = ROOT / "runs" / "autoresearch" / "same-run-01"


def scenario_frame(kind: str) -> pd.DataFrame:
    det = pd.read_csv(prepare.DET_CSV)
    aud = pd.read_csv(prepare.PROCESSED / "test_material_audit.csv").set_index("test")
    if kind in ("relabel_92", "add_audited"):
        det.loc[det.test == 92, "material"] = aud.loc[92, "fingerprint_class"]
    if kind == "add_audited":
        unk = det.material == "unknown"
        det.loc[unk, "material"] = det.loc[unk, "test"].map(aud.fingerprint_class)
        det.loc[unk, "rt_r0"] = det.loc[unk, "test"].map(aud.rt_r0_telemetry)
        det["include_in_model"] = det.material.isin(prepare.MATERIALS) & det[
            ["aging_s", "flow_velocity_cm_s", "rt_r0"]].notna().all(axis=1)
    return det[det.include_in_model].sort_values(["test", "push_index"]).reset_index(drop=True)


def main() -> dict:
    spec = importlib.util.spec_from_file_location("best_train", RUN_DIR / "best_train.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    Xs, Ys, gs, dfs = prepare.load_size()
    size_pred = np.vstack([mod.fit_predict_size({k: v[gs != g] for k, v in Xs.items()}, Ys[gs != g].copy(),
                                                {k: v[gs == g] for k, v in Xs.items()}, 0) for g in np.unique(gs)])
    out = {"note": "Detection task only; model and hyper-parameters frozen from attempt 11."}
    for kind in ("frozen", "relabel_92", "add_audited"):
        df = scenario_frame(kind)
        X, Y, g = prepare._frame_to_X(df, prepare.DET_FEATURES), df[prepare.DET_TARGETS].to_numpy(int), df.test.to_numpy(int)
        pred = np.clip(prepare._logo_predict(mod.fit_predict_detection, X, Y, g, 0, 2, "detection"), *prepare.P_CLIP)
        prev = Y.mean(axis=0)
        ratio = np.mean((pred - Y) ** 2, axis=0) / (prev * (1 - prev))
        out[kind] = {"n_pushes": int(len(df)), "n_tests": int(df.test.nunique()),
                     "brier_ratio_iss": float(ratio[0]), "brier_ratio_ion": float(ratio[1]),
                     "brier_ratio_mean": float(ratio.mean()),
                     "accuracy_iss": float(np.mean((pred[:, 0] >= .5) == Y[:, 0])),
                     "accuracy_ion": float(np.mean((pred[:, 1] >= .5) == Y[:, 1]))}
    out["frozen_matches_best_json"] = abs(out["frozen"]["brier_ratio_mean"] - json.loads(
        (RUN_DIR / "best.json").read_text())["detection_brier_ratio"]) < 1e-9
    p = ROOT / "runs" / "verification" / "material_audit_sensitivity.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(out, indent=2) + "\n")
    return out


if __name__ == "__main__":
    print(json.dumps(main(), indent=2))
