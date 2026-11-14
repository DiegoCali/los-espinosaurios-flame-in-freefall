"""Flame-front position and spread rate with uncertainty.

Definitions (see knowledge/physics/flame_spread_physics.md):
  * leading edge  = end of the luminous region in the spread direction
                    (opposed flow: upstream; concurrent flow: downstream).
  * trailing edge = opposite end (≈ burnout front for thin films).
  * s(t)          = leading-edge position projected on the spread direction, with origin at
                    the first detection -> s grows while the flame advances.
  * V_f           = ds/dt (mm/s when calibrated, otherwise physical px/s).
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.signal import savgol_filter
from scipy.stats import theilslopes

DIRS = {"left": ("x_left_sub", "x_right_sub", -1), "right": ("x_right_sub", "x_left_sub", +1),
        "up": ("y_top_sub", "y_bot_sub", -1), "down": ("y_bot_sub", "y_top_sub", +1)}


def _unit(df: pd.DataFrame) -> str:
    return "mm" if "x_left_sub_mm" in df and df["x_left_sub_mm"].notna().any() else "px"


def infer_direction(df: pd.DataFrame) -> str:
    """Dominant direction from the robust slope of the centroid."""
    d = df.dropna(subset=["cx_px", "cy_px"])
    if len(d) < 5:
        return "left"
    sx = theilslopes(d["cx_px"], d["time_s"])[0]
    sy = theilslopes(d["cy_px"], d["time_s"])[0]
    if abs(sx) >= abs(sy):
        return "right" if sx > 0 else "left"
    return "down" if sy > 0 else "up"


def hampel(x: pd.Series, window: int = 31, n_sigma: float = 4.0) -> pd.Series:
    """Set isolated outliers to NaN: points further than n_sigma robust SDs from the centred rolling median.

    Genuine regime changes persist for more than half a window and are kept; single-frame jumps of the edge
    onto reflections, hot pixels or partially lit frames are removed.
    """
    med = x.rolling(window, center=True, min_periods=5).median()
    mad = (x - med).abs().rolling(window, center=True, min_periods=5).median()
    sigma = 1.4826 * mad
    floor = 0.25 * np.nanmedian(sigma) if np.isfinite(np.nanmedian(sigma)) else 0.0
    bad = (x - med).abs() > n_sigma * np.maximum(sigma, floor)
    return x.mask(bad)


def edge_series(df: pd.DataFrame, direction: str = "auto", pixel_aspect: float = 10 / 11) -> pd.DataFrame:
    """Add leading/trailing edges along the spread direction and the flame length."""
    direction = infer_direction(df) if direction == "auto" else direction
    lead, trail, sign = DIRS[direction]
    unit = _unit(df)
    horiz = direction in ("left", "right")
    if unit == "mm":
        le, te = df[f"{lead}_mm"], df[f"{trail}_mm"]
    else:  # physical px
        k = pixel_aspect if horiz else 1.0
        le, te = df[f"{lead}_px"] * k, df[f"{trail}_px"] * k
    le, te = hampel(le), hampel(te)  # isolated artefact detections (reviewer M9)
    first = le.first_valid_index()
    s0 = le.loc[first] if first is not None else np.nan
    out = df.copy()
    out["direction"] = direction
    out["unit"] = unit
    out[f"leading_edge_{unit}"] = sign * (le - s0)
    out[f"trailing_edge_{unit}"] = sign * (te - s0)
    out[f"flame_length_{unit}"] = (le - te).abs()
    return out


def _savgol_derivative(t: np.ndarray, y: np.ndarray, window_s: float, order: int) -> np.ndarray:
    dt = np.median(np.diff(t)) if len(t) > 1 else 1.0
    w = max(order + 2, int(round(window_s / dt)))
    w += (w % 2 == 0)  # Savitzky-Golay requires an odd window
    if len(y) < w or np.isnan(y).all():
        return np.full_like(y, np.nan)
    yi = pd.Series(y).interpolate(limit_direction="both").to_numpy()
    return savgol_filter(yi, w, order, deriv=1, delta=dt)


def rolling_rate(t: np.ndarray, y: np.ndarray, window_s: float) -> tuple[np.ndarray, np.ndarray]:
    """Local OLS slope and its standard error in a centred window."""
    rate = np.full(len(t), np.nan)
    se = np.full(len(t), np.nan)
    half = window_s / 2
    for i, ti in enumerate(t):
        sel = (t >= ti - half) & (t <= ti + half) & ~np.isnan(y)
        if sel.sum() < 5:
            continue
        x, z = t[sel] - ti, y[sel]
        A = np.vstack([x, np.ones_like(x)]).T
        coef, res, *_ = np.linalg.lstsq(A, z, rcond=None)
        n = sel.sum()
        s2 = (res[0] / (n - 2)) if len(res) and n > 2 else np.nan
        rate[i] = coef[0]
        se[i] = np.sqrt(s2 / ((x - x.mean()) ** 2).sum()) if s2 == s2 else np.nan
    return rate, se


def spread_rates(df: pd.DataFrame, cfg_spread: dict) -> pd.DataFrame:
    unit = df["unit"].iloc[0]
    col = f"leading_edge_{unit}"
    t = df["time_s"].to_numpy()
    y = df[col].to_numpy(dtype=float)
    out = df.copy()
    out[f"spread_rate_sg_{unit}_s"] = _savgol_derivative(t, y, cfg_spread.get("savgol_window_s", 1.0),
                                                          cfg_spread.get("savgol_order", 2))
    r, se = rolling_rate(t, y, cfg_spread.get("rolling_window_s", 3.0))
    out[f"spread_rate_roll_{unit}_s"] = r
    out[f"spread_rate_roll_se_{unit}_s"] = se
    return out


def steady_spread_rate(df: pd.DataFrame, t0: float | None = None, t1: float | None = None) -> dict:
    """Robust 'steady' spread rate (Theil-Sen) over [t0, t1] with a 95 % CI."""
    unit = df["unit"].iloc[0]
    d = df.dropna(subset=[f"leading_edge_{unit}"])
    if t0 is not None:
        d = d[d.time_s >= t0]
    if t1 is not None:
        d = d[d.time_s <= t1]
    if len(d) < 5:
        return {"rate": np.nan, "lo": np.nan, "hi": np.nan, "unit": f"{unit}/s", "n": len(d)}
    slope, intercept, lo, hi = theilslopes(d[f"leading_edge_{unit}"], d.time_s, 0.95)
    return {"rate": slope, "lo": lo, "hi": hi, "intercept": intercept, "unit": f"{unit}/s",
            "n": len(d), "t0": float(d.time_s.min()), "t1": float(d.time_s.max())}


# ------------------------------------------------------------------ piecewise-linear regimes

def _bin_median(t: np.ndarray, y: np.ndarray, dt: float) -> tuple[np.ndarray, np.ndarray]:
    """Median of y in bins of width dt (robust to frame-to-frame flicker of faint flames)."""
    ok = ~np.isnan(y)
    t, y = t[ok], y[ok]
    if len(t) == 0:
        return t, y
    edges = np.arange(t.min(), t.max() + dt, dt)
    idx = np.digitize(t, edges)
    tb, yb = [], []
    for k in np.unique(idx):
        sel = idx == k
        if sel.sum() >= 2:
            tb.append(np.median(t[sel]))
            yb.append(np.median(y[sel]))
    return np.asarray(tb), np.asarray(yb)


def piecewise_linear(t: np.ndarray, y: np.ndarray, min_len: int = 6, penalty_scale: float = 12.0) -> list[tuple[int, int]]:
    """Optimal partition of (t, y) into linear segments (dynamic programming, BIC-like penalty).

    Cost of a segment = SSE of its OLS line; penalty per segment = penalty_scale · σ² · log(n), where σ² is
    a robust noise variance from second differences. Returns [(i0, i1_exclusive), ...].
    """
    n = len(t)
    if n < 2 * min_len:
        return [(0, n)]
    d2 = np.diff(y, 2)
    sigma2 = max((1.4826 * np.median(np.abs(d2 - np.median(d2)))) ** 2 / 6.0, 1e-12)
    beta = penalty_scale * sigma2 * np.log(n)
    # prefix sums for O(1) OLS SSE of any segment
    S = {k: np.r_[0, np.cumsum(v)] for k, v in {"1": np.ones(n), "t": t, "y": y, "tt": t * t,
                                                "ty": t * y, "yy": y * y}.items()}

    def sse(i, j):
        m = S["1"][j] - S["1"][i]
        st, sy = S["t"][j] - S["t"][i], S["y"][j] - S["y"][i]
        stt, sty, syy = S["tt"][j] - S["tt"][i], S["ty"][j] - S["ty"][i], S["yy"][j] - S["yy"][i]
        vt = stt - st * st / m
        cov = sty - st * sy / m
        vy = syy - sy * sy / m
        return max(vy - (cov * cov / vt if vt > 0 else 0.0), 0.0)

    F = np.full(n + 1, np.inf)
    F[0] = -beta
    prev = np.zeros(n + 1, int)
    for j in range(min_len, n + 1):
        best, arg = np.inf, 0
        for i in range(0, j - min_len + 1):
            if F[i] == np.inf:
                continue
            c = F[i] + sse(i, j) + beta
            if c < best:
                best, arg = c, i
        F[j], prev[j] = best, arg
    segs, j = [], n
    while j > 0:
        segs.append((prev[j], j))
        j = prev[j]
    return segs[::-1]


def regimes(df: pd.DataFrame, bin_s: float | None = None, min_len_s: float = 3.0,
            min_frac: float = 0.10) -> pd.DataFrame:
    """Linear spread regimes of the leading edge: one row per segment with Theil-Sen slope and CI.

    Regimes last at least max(min_len_s, min_frac × burn duration); with the BIC-like penalty of
    piecewise_linear (12·σ²·log n) this keeps physical regimes (ignition, steady spread, flow change,
    extinction) and ignores edge jitter of faint flames.
    """
    unit = df["unit"].iloc[0]
    t, y = df["time_s"].to_numpy(), df[f"leading_edge_{unit}"].to_numpy(dtype=float)
    span = np.nanmax(t[~np.isnan(y)]) - np.nanmin(t[~np.isnan(y)]) if (~np.isnan(y)).any() else 0
    min_len_s = max(min_len_s, min_frac * span)
    bin_s = bin_s or float(np.clip(span / 120, 0.25, 10.0))  # ~120 bins per burn, 0.25–10 s each
    tb, yb = _bin_median(t, y, bin_s)
    if len(tb) < 8:
        return pd.DataFrame()
    min_len = max(4, int(round(min_len_s / bin_s)))
    rows = []
    for i0, i1 in piecewise_linear(tb, yb, min_len=min_len):
        ts, ys = tb[i0:i1], yb[i0:i1]
        if len(ts) < 3:
            continue
        slope, icpt, lo, hi = theilslopes(ys, ts, 0.95)
        # Widen the CI for residual autocorrelation (binned medians are not independent): factor
        # sqrt((1+ρ1)/(1−ρ1)) from the lag-1 autocorrelation of the residuals (AR(1) effective sample size).
        res = ys - (icpt + slope * ts)
        rho = float(np.corrcoef(res[:-1], res[1:])[0, 1]) if len(res) > 4 and np.std(res) > 0 else 0.0
        rho = min(max(rho if np.isfinite(rho) else 0.0, 0.0), 0.95)
        infl = np.sqrt((1 + rho) / (1 - rho))
        lo, hi = slope - infl * (slope - lo), slope + infl * (hi - slope)
        rows.append({"t0": float(ts[0]), "t1": float(ts[-1]), "duration_s": float(ts[-1] - ts[0]),
                     "n_bins": len(ts), "rate": float(slope), "lo": float(lo), "hi": float(hi),
                     "intercept": float(icpt), "significant": bool(lo > 0), "ci_inflation": float(infl)})
    return pd.DataFrame(rows)
