"""Metrics and the scalar objective `val_score` (lower is better).

Implements knowledge/methods/evaluation_protocol.md §3:
    val_score = 0.15·D + 0.20·E + 0.20·R + 0.25·C + 0.10·M + 0.10·P
each component = error / baseline_error (frozen v0 or the local linear model).
If a component cannot be computed yet (e.g. no gold set), it is dropped and the
remaining weights are renormalised; `components_used` records which were used.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.stats import norm, trim_mean

WEIGHTS = {"D": 0.15, "E": 0.20, "R": 0.20, "C": 0.25, "M": 0.10, "P": 0.10}


# ------------------------------------------------------------------ segmentation

def dice(pred: np.ndarray, gold: np.ndarray, ignore: np.ndarray | None = None) -> float:
    if ignore is not None:
        pred, gold = pred[~ignore], gold[~ignore]
    s = pred.sum() + gold.sum()
    return 1.0 if s == 0 else 2.0 * (pred & gold).sum() / s


def iou(pred: np.ndarray, gold: np.ndarray, ignore: np.ndarray | None = None) -> float:
    if ignore is not None:
        pred, gold = pred[~ignore], gold[~ignore]
    u = (pred | gold).sum()
    return 1.0 if u == 0 else (pred & gold).sum() / u


def edge_error_mm(pred_mm: np.ndarray, gold_mm: np.ndarray, miss_penalty_mm: float = 5.0) -> np.ndarray:
    pred_mm, gold_mm = np.asarray(pred_mm, float), np.asarray(gold_mm, float)
    err = np.abs(pred_mm - gold_mm)
    return np.where(np.isnan(pred_mm) & ~np.isnan(gold_mm), miss_penalty_mm, err)


# ------------------------------------------------------------------ forecasting

def crps_gaussian(y: np.ndarray, mu: np.ndarray, sigma: np.ndarray) -> np.ndarray:
    """Closed-form CRPS for N(mu, sigma²) (Gneiting & Raftery 2007)."""
    sigma = np.maximum(np.asarray(sigma, float), 1e-12)
    z = (np.asarray(y) - mu) / sigma
    return sigma * (z * (2 * norm.cdf(z) - 1) + 2 * norm.pdf(z) - 1 / np.sqrt(np.pi))


def add_crps(bt: pd.DataFrame, interval: float = 0.9) -> pd.DataFrame:
    """Approximate sigma from the central interval (Gaussian assumption) and add CRPS."""
    z = norm.ppf(0.5 + interval / 2)
    out = bt.copy()
    out["sigma"] = (out["hi"] - out["lo"]) / (2 * z)
    out["crps"] = crps_gaussian(out.y_true, out.y_pred, out.sigma)
    return out


def interval_score(y, lo, hi, alpha: float = 0.1):
    """Winkler/interval score: width + penalty for falling outside."""
    return (hi - lo) + (2 / alpha) * (lo - y) * (y < lo) + (2 / alpha) * (y - hi) * (y > hi)


def forecast_summary(bt: pd.DataFrame, by=("model", "horizon_s")) -> pd.DataFrame:
    bt = add_crps(bt) if "crps" not in bt else bt
    return bt.groupby(list(by)).agg(MAE=("abs_err", "mean"), MASE=("scaled_err", "mean"),
                                    CRPS=("crps", "mean"), coverage=("covered", "mean"),
                                    width=("width", "mean"), n=("abs_err", "size")).reset_index()


def skill_vs_reference(bt: pd.DataFrame, reference: str = "drift") -> pd.DataFrame:
    """Relative skill per (test, target, horizon) against the local linear model ('drift')."""
    bt = add_crps(bt) if "crps" not in bt else bt
    keys = [k for k in ("test_id", "target", "horizon_s") if k in bt]
    agg = bt.groupby(keys + ["model"]).agg(MAE=("abs_err", "mean"), CRPS=("crps", "mean"),
                                           cov=("covered", "mean")).reset_index()
    ref = agg[agg.model == reference].drop(columns=["model", "cov"]).rename(
        columns={"MAE": "MAE_ref", "CRPS": "CRPS_ref"})
    out = agg.merge(ref, on=keys)
    out["MAE_rel"] = out.MAE / out.MAE_ref.replace(0, np.nan)
    out["CRPS_rel"] = out.CRPS / out.CRPS_ref.replace(0, np.nan)
    return out


# ------------------------------------------------------------------ objective

def coverage_penalty(cov90: float) -> float:
    if cov90 != cov90:
        return np.nan
    return float(np.clip(max(0.0, abs(cov90 - 0.90) - 0.03) / 0.07, 0, 1))


def val_score(components: dict[str, float]) -> dict:
    """Combine already-normalised components (≈1 for the baseline). NaN => dropped."""
    used = {k: v for k, v in components.items() if k in WEIGHTS and v is not None and v == v}
    if not used:
        return {"val_score": np.nan, "components_used": ""}
    wsum = sum(WEIGHTS[k] for k in used)
    score = sum(WEIGHTS[k] * v for k, v in used.items()) / wsum
    return {"val_score": float(score), "components_used": ",".join(sorted(used)), **used}


def forecast_components(bt: pd.DataFrame, model: str, reference: str = "drift",
                        target_weights: dict | None = None) -> dict:
    """C, M, P for one model from a multi-test backtest (columns test_id, target)."""
    sk = skill_vs_reference(bt, reference)
    sk = sk[sk.model == model]
    if sk.empty:
        return {"C": np.nan, "M": np.nan, "P": np.nan, "cov90": np.nan}
    tw = target_weights or {}
    sk = sk.assign(w=sk["target"].map(lambda t: tw.get(t, 1.0)) if "target" in sk else 1.0)
    per_test = sk.groupby("test_id").apply(
        lambda g: pd.Series({"C": np.average(g.CRPS_rel.fillna(1), weights=g.w),
                             "M": np.average(g.MAE_rel.fillna(1), weights=g.w)}),
        include_groups=False)
    cov = bt[bt.model == model]["covered"].mean()
    return {"C": float(trim_mean(per_test.C, 0.1)), "M": float(trim_mean(per_test.M, 0.1)),
            "P": coverage_penalty(cov), "cov90": float(cov)}


def paired_bootstrap_se(per_test_new: pd.Series, per_test_old: pd.Series, B: int = 500,
                        seed: int = 0) -> float:
    """SE of the paired mean difference across tests (acceptance rule §3.4)."""
    d = (per_test_new - per_test_old).dropna().to_numpy()
    if len(d) < 2:
        return np.nan
    rng = np.random.default_rng(seed)
    boots = [rng.choice(d, len(d), replace=True).mean() for _ in range(B)]
    return float(np.std(boots))
