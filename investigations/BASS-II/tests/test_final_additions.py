"""Tests for the Hampel edge filter, autocorrelation-aware CIs and the promoted forecasters."""
import warnings

import numpy as np
import pandas as pd

from bass2 import forecast, spread


def test_hampel_removes_isolated_spikes_but_keeps_steps():
    x = pd.Series(np.r_[np.linspace(0, 10, 100), np.linspace(30, 40, 100)])
    x.iloc[50] = 80.0  # isolated artefact
    y = spread.hampel(x)
    assert np.isnan(y.iloc[50])
    assert y.iloc[150] == x.iloc[150]  # a genuine regime change survives
    assert y.notna().sum() >= 195


def test_regime_ci_is_widened_for_autocorrelated_residuals():
    rng = np.random.default_rng(0)
    t = np.arange(0, 120, 0.1)
    ar = np.zeros(len(t))
    for i in range(1, len(t)):
        ar[i] = 0.97 * ar[i - 1] + rng.normal(0, 0.2)
    df = pd.DataFrame({"time_s": t, "leading_edge_mm": 0.5 * t + ar, "unit": "mm"})
    reg = spread.regimes(df)
    assert (reg.ci_inflation >= 1).all()
    assert reg.ci_inflation.max() > 1.2


def test_kalman_mle_noise_free_has_floors_and_no_warnings():
    t = np.arange(0, 20, 0.5)
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        m = forecast.KalmanMLE(0.9).fit(t, 2 * t)
        mean, lo, hi = m.predict(np.array([21.0, 25.0]))
    assert m.kw["r"] > 0 and m.kw["q"] > 0
    assert abs(mean[0] - 42) < 0.5 and np.all(hi >= lo)


def test_kalman_conformal_runs_and_widens_with_horizon():
    rng = np.random.default_rng(3)
    t = np.arange(0, 40, 0.5)
    y = 1.5 * t + rng.normal(0, 0.3, len(t))
    m, lo, hi = forecast.MODELS["kalman_conformal"](0.9).fit(t, y).predict(t[-1] + np.arange(1, 21) * 0.5)
    width = hi - lo
    assert np.all(np.diff(width) >= -1e-9)
    assert abs(m[-1] - 1.5 * (t[-1] + 10)) < 2.0
