"""Fixed data, folds and metric for the SAME AutoResearch study. DO NOT EDIT DURING A RUN.

Adapted from karpathy/autoresearch (upstream_reference/prepare.py): there, prepare.py fixes the
tokenizer, data and `evaluate_bpb`; here it fixes the SAME-R tables, the cross-validation folds
and `evaluate`, and `train.py` is the only file the agent edits.

Two tasks share one score (lower is better):

size       one row per NASA moment measurement. Predict 5 targets from the experimental conditions:
           log10 Dg, log10 Dm, log10 AMD (all µm), ln sigma_g, log10 M0 (#/cm^3).
           Metric: RMSE of each target / SD of that target over the whole table (NRMSE), averaged.
detection  one row per piston push. Predict the probability that the ISS photoelectric detector and
           the ionization chamber each exceed their proxy response threshold.
           Metric: Brier score / Brier score of the overall prevalence, averaged over the 2 detectors.

val_score = 0.5 * size_nrmse + 0.5 * detection_brier_ratio   (a constant-mean model scores ~1.0)

Validation is leave-one-group-out: every grid of a run (size) or every push of a test (detection)
is held out together, so pre-age and post-age measurements of the same smoke never leak.

    .venv/bin/python prepare.py --check     # verify data/protected-file hashes and print dataset info
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
PROCESSED = ROOT / "data" / "processed"
SIZE_CSV = PROCESSED / "size_dataset.csv"
DET_CSV = PROCESSED / "detection_dataset.csv"
MANIFEST = ROOT / "runs" / "autoresearch" / "same-run-01" / "protected_manifest.json"
PROTECTED = ["prepare.py", "scripts/run_experiment.py", "data/processed/size_dataset.csv",
             "data/processed/detection_dataset.csv", "tests/test_experiment_gate.py"]

MATERIALS = ["Kapton", "Lampwick", "Pyrell", "Silicone", "Teflon"]
SIZE_FEATURES = ["material", "aged", "aging_s", "flow_velocity_cm_s", "no_flow", "rt_r0"]
SIZE_TARGETS = ["log10_dg_um", "log10_dm_um", "log10_amd_um", "ln_sigma_g", "log10_m0_per_cc"]
DET_FEATURES = ["material", "aging_s", "flow_velocity_cm_s", "no_flow", "rt_r0", "push_index"]
DET_TARGETS = ["iss_detect", "ion_detect"]
P_CLIP = (1e-3, 1 - 1e-3)
TIME_BUDGET_S = 120.0


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _frame_to_X(df: pd.DataFrame, cols: list[str]) -> dict[str, np.ndarray]:
    X = {}
    for c in cols:
        X[c] = df[c].astype(str).to_numpy() if c == "material" else df[c].astype(float).to_numpy()
    return X


def load_size() -> tuple[dict, np.ndarray, np.ndarray, pd.DataFrame]:
    df = pd.read_csv(SIZE_CSV)
    df = df[df["include_in_model"]].sort_values(["run", "source_row"]).reset_index(drop=True)
    return _frame_to_X(df, SIZE_FEATURES), df[SIZE_TARGETS].to_numpy(float), df["run"].to_numpy(int), df


def load_detection() -> tuple[dict, np.ndarray, np.ndarray, pd.DataFrame]:
    df = pd.read_csv(DET_CSV)
    df = df[df["include_in_model"]].sort_values(["test", "push_index"]).reset_index(drop=True)
    return _frame_to_X(df, DET_FEATURES), df[DET_TARGETS].to_numpy(int), df["test"].to_numpy(int), df


def _subset(X: dict, idx: np.ndarray) -> dict:
    return {k: v[idx] for k, v in X.items()}


def _logo_predict(fn, X, Y, groups, seed, n_out, kind):
    pred = np.full((len(Y), n_out), np.nan)
    for g in np.unique(groups):
        te = groups == g
        tr = ~te
        out = np.asarray(fn(_subset(X, np.where(tr)[0]), Y[tr].copy(), _subset(X, np.where(te)[0]), seed),
                         dtype=float)
        if out.shape != (te.sum(), n_out):
            raise ValueError(f"{kind}: expected prediction shape {(te.sum(), n_out)}, got {out.shape}")
        if not np.all(np.isfinite(out)):
            raise ValueError(f"{kind}: non-finite predictions for held-out group {g}")
        pred[te] = out
    return pred


def evaluate(model, seed: int = 0) -> dict:
    """Run both cross-validations for a module exposing fit_predict_size / fit_predict_detection."""
    t0 = time.time()
    Xs, Ys, gs, dfs = load_size()
    Xd, Yd, gd, dfd = load_detection()
    size_pred = _logo_predict(model.fit_predict_size, Xs, Ys, gs, seed, len(SIZE_TARGETS), "size")
    det_pred = np.clip(_logo_predict(model.fit_predict_detection, Xd, Yd, gd, seed, len(DET_TARGETS),
                                     "detection"), *P_CLIP)
    sd = Ys.std(axis=0, ddof=0)
    rmse = np.sqrt(np.mean((size_pred - Ys) ** 2, axis=0))
    nrmse = rmse / sd
    prev = Yd.mean(axis=0)
    brier = np.mean((det_pred - Yd) ** 2, axis=0)
    brier_ratio = brier / (prev * (1 - prev))
    size_score, det_score = float(nrmse.mean()), float(brier_ratio.mean())
    elapsed = time.time() - t0
    if elapsed > TIME_BUDGET_S:
        raise TimeoutError(f"evaluation took {elapsed:.1f}s > {TIME_BUDGET_S}s budget")
    return {
        "val_score": 0.5 * size_score + 0.5 * det_score,
        "size_nrmse": size_score,
        "detection_brier_ratio": det_score,
        "size_rmse": dict(zip(SIZE_TARGETS, rmse.tolist())),
        "size_nrmse_by_target": dict(zip(SIZE_TARGETS, nrmse.tolist())),
        "size_factor_error": {t: float(10 ** r) for t, r in zip(SIZE_TARGETS, rmse) if t.startswith("log10")},
        "detection_brier": dict(zip(DET_TARGETS, brier.tolist())),
        "detection_brier_ratio_by_target": dict(zip(DET_TARGETS, brier_ratio.tolist())),
        "detection_accuracy_at_0p5": {t: float(np.mean((det_pred[:, j] >= 0.5) == Yd[:, j]))
                                      for j, t in enumerate(DET_TARGETS)},
        "n_size_rows": int(len(Ys)), "n_size_groups": int(len(np.unique(gs))),
        "n_detection_rows": int(len(Yd)), "n_detection_groups": int(len(np.unique(gd))),
        "elapsed_seconds": elapsed,
        "seed": seed,
        "_size_pred": size_pred, "_det_pred": det_pred, "_size_df": dfs, "_det_df": dfd,
    }


def cv_prediction_records(res: dict) -> dict:
    dfs, dfd = res["_size_df"], res["_det_df"]
    size = []
    for i, r in dfs.iterrows():
        rec = {"run": int(r.run), "source_row": int(r.source_row), "material": r.material, "aged_state": r.aged_state}
        for j, t in enumerate(SIZE_TARGETS):
            rec[f"{t}_observed"] = float(r[t])
            rec[f"{t}_predicted"] = float(res["_size_pred"][i, j])
        size.append(rec)
    det = []
    for i, r in dfd.iterrows():
        rec = {"test": int(r.test), "push_index": int(r.push_index), "material": r.material,
               "flow_velocity_cm_s": float(r.flow_velocity_cm_s), "aging_s": float(r.aging_s)}
        for j, t in enumerate(DET_TARGETS):
            rec[f"{t}_observed"] = int(r[t])
            rec[f"{t}_probability"] = float(res["_det_pred"][i, j])
        det.append(rec)
    return {"size": size, "detection": det}


def write_manifest() -> dict:
    m = {p: _sha(ROOT / p) for p in PROTECTED}
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(json.dumps(m, indent=2) + "\n")
    return m


def check_manifest() -> list[str]:
    if not MANIFEST.exists():
        return ["protected_manifest.json missing (run: prepare.py --init-manifest)"]
    m = json.loads(MANIFEST.read_text())
    return [p for p, h in m.items() if not (ROOT / p).exists() or _sha(ROOT / p) != h]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="verify protected hashes and print dataset summary")
    ap.add_argument("--init-manifest", action="store_true", help="freeze protected files (run once, at baseline)")
    a = ap.parse_args(argv)
    if a.init_manifest:
        print(json.dumps(write_manifest(), indent=2))
        return 0
    Xs, Ys, gs, dfs = load_size()
    Xd, Yd, gd, dfd = load_detection()
    print(f"size: {len(Ys)} rows / {len(np.unique(gs))} runs; targets {SIZE_TARGETS}")
    print(f"detection: {len(Yd)} pushes / {len(np.unique(gd))} tests; prevalence "
          f"{dict(zip(DET_TARGETS, Yd.mean(axis=0).round(3).tolist()))}")
    if a.check:
        bad = check_manifest()
        print("protected files: OK" if not bad else f"protected files CHANGED: {bad}")
        return 1 if bad else 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
