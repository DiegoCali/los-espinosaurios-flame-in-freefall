"""Forecasting the evolution of flame measurements (short, noisy series).

Common model interface:
    model.fit(t, y) ; model.predict(t_future) -> (mean, lo, hi)
Rolling-origin evaluation within each test (no temporal leakage) and aggregation
per test/PI to measure generalisation (see knowledge/methods/evaluation_protocol.md).

Included baselines (must be beaten before proposing complex models):
  persistence     y(t+h) = y(t)
  drift           linear extrapolation of the last window
  holt_damped     additive ETS with damped trend (statsmodels)
  kalman_cv       constant-velocity Kalman filter (physics: V_f ~ const)
  physics_linear  Theil-Sen over the whole history (steady spread)
"""
from __future__ import annotations

import warnings

import numpy as np
import pandas as pd
from scipy.stats import norm, theilslopes


class Forecaster:
    name = "base"

    def __init__(self, interval: float = 0.9, **kw):
        self.z = norm.ppf(0.5 + interval / 2)
        self.kw = kw

    def fit(self, t: np.ndarray, y: np.ndarray) -> "Forecaster":
        self.t, self.y = np.asarray(t, float), np.asarray(y, float)
        d = np.diff(self.y)
        self.sigma1 = np.nanstd(d) if len(d) > 1 else 0.0
        return self

    def predict(self, tf: np.ndarray):
        raise NotImplementedError


class Persistence(Forecaster):
    name = "persistence"

    def predict(self, tf):
        h = np.arange(1, len(tf) + 1)
        m = np.full(len(tf), self.y[-1])
        s = self.sigma1 * np.sqrt(h)
        return m, m - self.z * s, m + self.z * s


class Drift(Forecaster):
    name = "drift"

    def predict(self, tf):
        win = self.kw.get("window_s", 5.0)
        sel = self.t >= self.t[-1] - win
        if sel.sum() < 3:
            return Persistence(0.9).fit(self.t, self.y).predict(tf)
        A = np.vstack([self.t[sel], np.ones(sel.sum())]).T
        coef, *_ = np.linalg.lstsq(A, self.y[sel], rcond=None)
        resid = self.y[sel] - A @ coef
        m = coef[0] * tf + coef[1]
        s = np.std(resid) * np.sqrt(1 + (tf - self.t[-1]) / max(win, 1e-9))
        return m, m - self.z * s, m + self.z * s


class PhysicsLinear(Forecaster):
    """Steady spread: s(t) = s0 + V_f t, robust V_f (Theil-Sen)."""
    name = "physics_linear"

    def predict(self, tf):
        slope, icpt, lo, hi = theilslopes(self.y, self.t, 0.9)
        m = slope * tf + icpt
        resid = self.y - (slope * self.t + icpt)
        dt = tf - self.t[-1]
        s = np.sqrt(np.var(resid) + ((hi - lo) / (2 * 1.645) * dt) ** 2)
        return m, m - self.z * s, m + self.z * s


class HoltDamped(Forecaster):
    name = "holt_damped"

    def predict(self, tf):
        from statsmodels.tsa.exponential_smoothing.ets import ETSModel
        if len(self.y) < 10:
            return Drift(0.9).fit(self.t, self.y).predict(tf)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            res = ETSModel(pd.Series(self.y), error="add", trend="add", damped_trend=True).fit(disp=False)
            pr = res.get_prediction(start=len(self.y), end=len(self.y) + len(tf) - 1)
            sf = pr.summary_frame(alpha=2 * (1 - norm.cdf(self.z)))
        return sf["mean"].to_numpy(), sf["pi_lower"].to_numpy(), sf["pi_upper"].to_numpy()


class KalmanCV(Forecaster):
    """Constant-velocity Kalman; q = acceleration noise (units²/s³)."""
    name = "kalman_cv"

    def predict(self, tf):
        t, y = self.t, self.y
        floor = max(1e-6 * float(np.nanvar(y)), 1e-12)  # avoids r -> 0 on noise-free series
        r = max(self.kw.get("r", None) or (self.sigma1 ** 2) / 2, floor)
        q = max(self.kw.get("q", None) or r, 1e-12)
        x, P = _cv_init(t, y, r, q)
        H = np.array([[1.0, 0.0]])
        for k in range(1, len(t)):
            dt = t[k] - t[k - 1]
            F = np.array([[1, dt], [0, 1]])
            Q = q * np.array([[dt ** 3 / 3, dt ** 2 / 2], [dt ** 2 / 2, dt]])
            x, P = F @ x, F @ P @ F.T + Q
            if not np.isnan(y[k]):
                S = H @ P @ H.T + r
                K = P @ H.T / S
                x = x + (K * (y[k] - H @ x)).ravel()
                P = (np.eye(2) - K @ H) @ P
        m, s = [], []
        tp = t[-1]
        for tk in tf:
            dt = tk - tp
            F = np.array([[1, dt], [0, 1]])
            Q = q * np.array([[dt ** 3 / 3, dt ** 2 / 2], [dt ** 2 / 2, dt]])
            x, P = F @ x, F @ P @ F.T + Q
            m.append(x[0])
            s.append(np.sqrt(P[0, 0] + r))
            tp = tk
        m, s = np.array(m), np.array(s)
        return m, m - self.z * s, m + self.z * s


def _cv_init(t: np.ndarray, y: np.ndarray, r: float, q: float) -> tuple[np.ndarray, np.ndarray]:
    """Shared initial state for fitting and predicting: velocity from the first 5 samples; the velocity
    variance is a velocity scale (units²/s²) derived from r and the sampling step."""
    k = min(5, len(y) - 1)
    dt = max(float(t[k] - t[0]), 1e-9)
    x = np.array([y[0], (y[k] - y[0]) / dt])
    P = np.diag([r, 2 * r / dt ** 2 + q * dt])
    return x, P


def _kalman_cv_loglik(t: np.ndarray, y: np.ndarray, q: float, r: float) -> float:
    """Gaussian log-likelihood of the innovations of a constant-velocity Kalman filter."""
    x, P = _cv_init(t, y, r, q)
    ll = 0.0
    for k in range(1, len(t)):
        dt = t[k] - t[k - 1]
        F = np.array([[1, dt], [0, 1]])
        Q = q * np.array([[dt ** 3 / 3, dt ** 2 / 2], [dt ** 2 / 2, dt]])
        x, P = F @ x, F @ P @ F.T + Q
        if np.isnan(y[k]):
            continue
        S = max(P[0, 0] + r, 1e-300)
        v = y[k] - x[0]
        ll += -0.5 * (np.log(2 * np.pi * S) + v * v / S)
        K = P[:, 0] / S
        x = x + K * v
        P = P - np.outer(K, P[0, :])
    return ll


class KalmanMLE(KalmanCV):
    """Constant-velocity Kalman with q (acceleration noise) and r (measurement noise) estimated by
    maximum likelihood of the innovations on the observed history. Unit-invariant (works in px, mm or
    log-area alike) and calibrates its prediction intervals to the series' own variability."""
    name = "kalman_mle"

    def fit(self, t, y):
        super().fit(t, y)
        from scipy.optimize import minimize
        yy = np.asarray(y, float)
        s2 = max(np.nanvar(np.diff(yy)), 1e-12)
        def nll(p):
            return -_kalman_cv_loglik(self.t, yy, np.exp(p[0]), np.exp(p[1]))
        best = None
        for q0 in (s2 * 1e-2, s2):  # two starts: smooth vs. agile trend
            res = minimize(nll, x0=[np.log(q0), np.log(s2 / 2)], method="Nelder-Mead",
                           options={"xatol": 1e-2, "fatol": 1e-3, "maxiter": 200})
            if best is None or res.fun < best.fun:
                best = res
        floor = max(1e-6 * float(np.nanvar(yy)), 1e-12)
        self.kw["q"], self.kw["r"] = max(float(np.exp(best.x[0])), 1e-12), max(float(np.exp(best.x[1])), floor)
        return self


from .forecast_ensemble import KalmanConformal as _KC  # noqa: E402


class KalmanConformal(Forecaster):
    """Wrapper exposing the loop-promoted ensemble with the common Forecaster interface."""
    name = "kalman_conformal"

    def fit(self, t, y):
        super().fit(t, y)
        self._m = _KC(float(2 * norm.cdf(self.z) - 1)).fit(t, y)
        return self

    def predict(self, tf):
        return self._m.predict(tf)


MODELS = {c.name: c for c in (Persistence, Drift, PhysicsLinear, HoltDamped, KalmanCV, KalmanMLE, KalmanConformal)}


def resample(df: pd.DataFrame, col: str, hz: float) -> pd.DataFrame:
    d = df[["time_s", col]].dropna()
    if d.empty:
        return d
    grid = np.arange(d.time_s.min(), d.time_s.max() + 1e-9, 1.0 / hz)
    return pd.DataFrame({"time_s": grid, col: np.interp(grid, d.time_s, d[col])})


def rolling_origin(series: pd.DataFrame, col: str, models: list[str], horizons_s: list[float],
                   min_history_s: float, n_origins: int, interval: float = 0.9,
                   model_kwargs: dict | None = None) -> pd.DataFrame:
    """Evaluate every model at n_origins origins; one row per (origin, model, horizon)."""
    t, y = series.time_s.to_numpy(), series[col].to_numpy()
    if len(t) < 3:
        return pd.DataFrame()
    dt = np.median(np.diff(t))
    hmax = max(horizons_s)
    first, last = t[0] + min_history_s, t[-1] - hmax
    if last <= first:
        return pd.DataFrame()
    naive_scale = np.nanmean(np.abs(np.diff(y))) or 1e-9  # MASE: in-sample naive 1-step
    rows = []
    for t0 in np.linspace(first, last, n_origins):
        hist = t <= t0
        tf = t[hist][-1] + dt * np.arange(1, int(round(hmax / dt)) + 1)
        truth = np.interp(tf, t, y)
        for name in models:
            mdl = MODELS[name](interval, **(model_kwargs or {}).get(name, {}))
            try:
                m, lo, hi = mdl.fit(t[hist], y[hist]).predict(tf)
            except Exception as e:  # a failing model must not abort the evaluation
                warnings.warn(f"{name} failed at t0={t0:.1f}: {e}")
                continue
            for h in horizons_s:
                k = int(round(h / dt)) - 1
                if k >= len(tf):
                    continue
                rows.append({"model": name, "origin_s": t0, "horizon_s": h, "y_true": truth[k],
                             "y_pred": m[k], "lo": lo[k], "hi": hi[k],
                             "abs_err": abs(m[k] - truth[k]), "scaled_err": abs(m[k] - truth[k]) / naive_scale,
                             "covered": lo[k] <= truth[k] <= hi[k], "width": hi[k] - lo[k]})
    return pd.DataFrame(rows)


def forecast_path(series: pd.DataFrame, col: str, model: str, t_cut: float, horizon_s: float,
                  interval: float = 0.9) -> pd.DataFrame:
    """Forecast trajectory from t_cut (for forecast-vs-observed figures)."""
    t, y = series.time_s.to_numpy(), series[col].to_numpy()
    dt = np.median(np.diff(t))
    hist = t <= t_cut
    tf = t[hist][-1] + dt * np.arange(1, int(round(horizon_s / dt)) + 1)
    m, lo, hi = MODELS[model](interval).fit(t[hist], y[hist]).predict(tf)
    return pd.DataFrame({"time_s": tf, "mean": m, "lo": lo, "hi": hi, "model": model})
