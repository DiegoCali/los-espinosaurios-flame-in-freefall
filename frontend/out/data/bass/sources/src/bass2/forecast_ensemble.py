"""Ensemble forecaster promoted from the autoresearch loop (research/runs/013, val_score 1.187 -> 0.643).

Per-horizon inverse-MSE combination of a constant-velocity Kalman filter (λ = q/r by profile maximum
likelihood), a 5 s local linear trend and persistence, with normalised split-conformal prediction intervals.
Unit-invariant. Registered in bass2.forecast.MODELS as "kalman_conformal".
"""
from __future__ import annotations

import numpy as np

# Grid of lambda = q / r (acceleration noise / measurement noise, units 1/s^3). The ratio does not
# depend on the units of y, so the profile likelihood below is unit-invariant.
LAMBDAS = np.logspace(-6, 2, 33)
DRIFT_WINDOW_S = 5.0  # local linear trend window (same as the reference 'drift' model)


def _kalman_grid(t, y, lam):
    """Constant-velocity Kalman filter with r = 1 run for every lambda at once (vectorised).

    Returns filtered states at every step (G, n, 2), profiled r and log-likelihood per lambda.
    With P0 proportional to r, every covariance scales with r, so r is concentrated out analytically:
    r_hat = mean(v^2/S~),  ll = -1/2 [n ln(2 pi r_hat) + sum ln S~ + n].
    Numerically equivalent to bass2.forecast.KalmanMLE but ~50x faster.
    """
    G, n = len(lam), len(t)
    k5 = min(5, n - 1)
    v0 = (y[k5] - y[0]) / max(t[k5] - t[0], 1e-9)
    xs = np.empty((G, n, 2))
    xs[:, 0, 0], xs[:, 0, 1] = y[0], v0
    P00, P01, P11 = np.ones(G), np.zeros(G), 10.0 + lam
    sum_logS, sum_v2S = np.zeros(G), np.zeros(G)
    for k in range(1, n):
        dt = t[k] - t[k - 1]
        x0p = xs[:, k - 1, 0] + dt * xs[:, k - 1, 1]
        a00 = P00 + 2 * dt * P01 + dt * dt * P11 + lam * dt ** 3 / 3
        a01 = P01 + dt * P11 + lam * dt ** 2 / 2
        a11 = P11 + lam * dt
        S = a00 + 1.0
        v = y[k] - x0p
        sum_logS += np.log(S)
        sum_v2S += v * v / S
        K0, K1 = a00 / S, a01 / S
        xs[:, k, 0] = x0p + K0 * v
        xs[:, k, 1] = xs[:, k - 1, 1] + K1 * v
        P00, P01, P11 = a00 - K0 * a00, a01 - K0 * a01, a11 - K1 * a01
    m = max(n - 1, 1)
    r = np.maximum(sum_v2S / m, 1e-300)
    ll = -0.5 * (m * np.log(2 * np.pi * r) + sum_logS + m)
    return xs, r, ll


def _conformal_quantile(err, level):
    """Split-conformal quantile with the finite-sample correction ceil((n+1)*level)/n."""
    n = len(err)
    return float(np.quantile(err, min(1.0, np.ceil((n + 1) * level) / n), method="higher"))


def _local_linear(t, y, window_s):
    """Rolling OLS line over the trailing window ending at every index -> (level at t_i, slope,
    residual variance)."""
    n = len(t)
    tc = t - t[0]
    dt = float(np.median(np.diff(t))) if n > 1 else 1.0
    L = int(np.floor(window_s / dt + 1e-9)) + 1
    c = [np.concatenate([[0.0], np.cumsum(a)]) for a in (np.ones(n), tc, y, tc * tc, tc * y, y * y)]
    i = np.arange(n)
    lo = np.maximum(0, i - L + 1)
    N, St, Sy, Stt, Sty, Syy = (a[i + 1] - a[lo] for a in c)
    den = N * Stt - St * St
    ok = (N >= 3) & (den > 0)
    slp = np.where(ok, (N * Sty - St * Sy) / np.where(ok, den, 1.0), 0.0)
    icp = np.where(ok, (Sy - slp * St) / np.maximum(N, 1), y)
    lev = np.where(ok, icp + slp * tc, y)
    ssr = Syy - icp * Sy - slp * Sty  # OLS residual sum of squares
    var = np.where(ok, np.maximum(ssr, 0.0) / np.maximum(N, 1), np.nan)
    return lev, slp, var


class KalmanConformal:
    """Per-horizon inverse-MSE (Bates-Granger) combination of three members:
    CV Kalman with lambda = q/r by profile maximum likelihood (adaptive trend), the local linear fit
    over the last DRIFT_WINDOW_S (local trend) and persistence (no trend: plateauing area, stalled
    edge). Weights come from each member's in-history h-step MSE. The interval at each horizon is the
    split-conformal quantile of the combination's own in-history h-step errors, normalised by a local
    noise scale (locally adaptive width, marginal coverage preserved). Unit-invariant."""

    def __init__(self, interval: float = 0.9):
        self.interval = interval

    def fit(self, t, y):
        self.t, self.y = np.asarray(t, float), np.asarray(y, float)
        return self

    def predict(self, tf):
        t, y = self.t, self.y
        tf = np.asarray(tf, float)
        xs, r, ll = _kalman_grid(t, y, LAMBDAS)
        xs = xs[int(np.argmax(ll))]
        lev_d, slp_d, var_d = _local_linear(t, y, DRIFT_WINDOW_S)
        # Normalised conformal: errors are scaled by a local noise level (trailing-window residual
        # variance, regularised by its history mean so flat stretches do not get zero width).
        var_d = np.where(np.isnan(var_d), np.nanmean(var_d), var_d)
        scale = np.sqrt(np.maximum(var_d + np.nanmean(var_d), 1e-24))
        # members as (level, slope) at every origin: Kalman, local linear, persistence
        levs = np.stack([xs[:, 0], lev_d, y])
        slps = np.stack([xs[:, 1], slp_d, np.zeros_like(y)])
        h = tf - t[-1]
        dt = float(np.median(np.diff(t))) if len(t) > 1 else 1.0
        m = np.empty(len(tf))
        half = np.empty(len(tf))
        prev, w = None, np.array([0.5, 0.5, 0.0])
        for j, hj in enumerate(h):
            k = int(round(hj / dt))
            if k >= 1 and len(t) - k >= 7:  # at least a couple of in-history errors at this horizon
                src = np.arange(5, len(t) - k)  # skip the filter's burn-in
                e = y[src + k][None, :] - (levs[:, src] + k * dt * slps[:, src])
                inv = 1 / np.maximum(np.mean(e ** 2, axis=1), 1e-24)
                w = inv / inv.sum()
                err = np.abs(w @ e) / scale[src]
                half[j] = _conformal_quantile(err, self.interval) * scale[-1]
                if prev is not None:
                    half[j] = max(half[j], prev)  # uncertainty does not shrink with horizon
            elif prev is not None:
                half[j] = prev * np.sqrt((j + 1) / j)  # random-walk growth beyond the history
            else:
                half[j] = 1.645 * np.nanstd(np.diff(y))
            m[j] = w @ (levs[:, -1] + hj * slps[:, -1])
            prev = half[j]
        half = np.maximum(half, 1e-9)
        return m, m - half, m + half


KalmanConformal.name = "kalman_conformal"
