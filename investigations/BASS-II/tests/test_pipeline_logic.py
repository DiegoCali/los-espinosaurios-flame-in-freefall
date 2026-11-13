"""Tests for steady-window detection, flow-step segmentation and the adaptive segmenter."""
import numpy as np
import pandas as pd

from bass2 import evaluation, pipeline, segmentation, spread
from bass2.video import valid_mask


def _series(rate_fn, t_end=60.0, fps=10.0, fan_fn=None):
    t = np.arange(0, t_end, 1 / fps)
    x = np.cumsum(rate_fn(t)) / fps
    df = pd.DataFrame({"time_s": t, "area_px": 500, "cx_px": 100 + x, "cy_px": 240.0,
                       "x_left_sub_px": 80 + x, "x_right_sub_px": 120 + x,
                       "x_left_sub_mm": (80 + x) * 0.2, "x_right_sub_mm": (120 + x) * 0.2})
    if fan_fn is not None:
        df["osd_fan"] = fan_fn(t)
        df["osd_air_cm_s"] = np.interp(t - 60, t, fan_fn(t) / 10, left=fan_fn(t)[0] / 10)
    df = spread.edge_series(df, "right")
    return spread.spread_rates(df, {"savgol_window_s": 1.0, "savgol_order": 2, "rolling_window_s": 3.0})


def test_steady_window_finds_constant_spread():
    df = _series(lambda t: np.where(t < 10, 0.0, 5.0))
    t0, t1 = pipeline.steady_window(df)
    assert 9 <= t0 <= 14 and t1 > 50
    st = spread.steady_spread_rate(df, t0, t1)
    assert abs(st["rate"] - 5.0 * 0.2 * 10 / 11 * 11 / 10) < 0.05  # mm/s (edges given in mm already)


def test_steady_window_returns_nan_without_spread():
    """A stationary flame (position jitter, no drift) must not produce a steady spread rate."""
    rng = np.random.default_rng(0)
    df = _series(lambda t: np.zeros_like(t))
    jitter = rng.normal(0, 0.3, len(df))
    df["leading_edge_mm"] = df["leading_edge_mm"] + jitter
    t0, t1 = pipeline.steady_window(df)
    assert np.isnan(t0) and np.isnan(t1)


def test_flow_steps_detects_fan_plateaus():
    df = _series(lambda t: np.where(t < 30, 6.0, 3.0), t_end=60,
                 fan_fn=lambda t: np.where(t < 30, 62.0, 45.0))
    steps = pipeline.flow_steps(df, min_len_s=8)
    assert len(steps) == 2
    assert steps[0]["rate"] > steps[1]["rate"]


def test_adaptive_segmenter_catches_faint_flame():
    img = np.zeros((480, 720, 3), np.uint8)
    yy, xx = np.mgrid[:480, :720]
    m = ((xx - 300) / 40) ** 2 + ((yy - 300) / 8) ** 2 <= 1
    img[m] = [30, 8, 25]  # faint magenta/blue flame, peak 30 < hysteresis high 90
    valid = valid_mask(img.shape, {"y0": 0, "y1": 90})
    v0 = segmentation.segment(img, valid, {"method": "hysteresis", "low": 40, "high": 90})
    ad = segmentation.segment(img, valid, {"method": "adaptive", "blur_sigma": 1.0, "min_component_area": 25})
    assert v0.sum() == 0
    assert evaluation.dice(ad, m) > 0.8
