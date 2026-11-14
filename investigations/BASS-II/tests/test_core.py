"""Synthetic tests with known answers (no downloads required)."""
import numpy as np
import pandas as pd
import pytest

from bass2 import catalog, evaluation, forecast, metrics, segmentation, spread
from bass2.video import valid_mask


def synthetic_flame(x_center: float, h=480, w=720, length=80, height=20, y=300, value=220):
    """Luminous ellipse (BGR) on a dark, slightly noisy background."""
    rng = np.random.default_rng(int(x_center))
    img = rng.normal(6, 2, (h, w, 3)).clip(0, 255)
    yy, xx = np.mgrid[:h, :w]
    m = ((xx - x_center) / (length / 2)) ** 2 + ((yy - y) / (height / 2)) ** 2 <= 1
    img[m] = [value, 80, value]  # magenta, as BASS-II flames appear on the camcorder
    return img.astype(np.uint8), m


def test_segmentation_recovers_ellipse():
    img, gold = synthetic_flame(300)
    valid = valid_mask(img.shape, {"y0": 0, "y1": 90})
    pred = segmentation.segment(img, valid, {"method": "hysteresis", "low": 40, "high": 90,
                                             "blur_sigma": 1.0, "min_component_area": 25, "morph_close": 3})
    # Baseline v0: Dice ≈ 0.937. Blur + low threshold dilates the edge by ~1 px (known bias that
    # matters for small objects). Target for the research/ loop: raise this without hurting edges.
    d = evaluation.dice(pred, gold)
    assert d > 0.9
    assert pred.sum() >= gold.sum()  # the bias is dilation, not erosion


def test_osd_band_is_masked():
    img, _ = synthetic_flame(300)
    img[30:80, 150:600] = 255  # bright OSD text
    valid = valid_mask(img.shape, {"y0": 0, "y1": 90})
    pred = segmentation.segment(img, valid, {"method": "hysteresis", "low": 40, "high": 90})
    assert not pred[:90].any()


def test_spread_rate_recovered():
    """A flame moving at +6 px/s must measure ~6·(10/11) physical px/s."""
    fps, v = 10.0, 6.0
    rows = []
    for k in range(200):
        t = k / fps
        img, m = synthetic_flame(150 + v * t)
        r = metrics.frame_metrics(img, m)
        r["time_s"] = t
        rows.append(r)
    df = spread.edge_series(pd.DataFrame(rows), "auto")
    assert df.direction.iloc[0] == "right"
    st = spread.steady_spread_rate(df)
    assert st["rate"] == pytest.approx(v * 10 / 11, rel=0.02)


def test_forecast_models_run_and_physics_linear_wins_on_line():
    t = np.arange(0, 30, 0.5)
    y = 2.0 * t + np.random.default_rng(0).normal(0, 0.2, len(t))
    s = pd.DataFrame({"time_s": t, "y": y})
    bt = forecast.rolling_origin(s, "y", list(forecast.MODELS), [1, 5], 5, 6)
    assert set(bt.model) == set(forecast.MODELS)
    mae = bt[bt.horizon_s == 5].groupby("model").abs_err.mean()
    assert mae["physics_linear"] < mae["persistence"]


def test_val_score_baseline_is_one_and_renormalizes():
    assert evaluation.val_score({"D": 1, "E": 1, "R": 1, "C": 1, "M": 1, "P": 1})["val_score"] == pytest.approx(1.0)
    r = evaluation.val_score({"C": 0.5, "M": np.nan})
    assert r["val_score"] == pytest.approx(0.5) and r["components_used"] == "C"


def test_crps_gaussian_matches_mae_limit():
    y = np.array([1.0])
    assert evaluation.crps_gaussian(y, np.array([0.0]), np.array([1e-9]))[0] == pytest.approx(1.0, rel=1e-3)


def test_material_parser():
    assert catalog._material("1/4\" clear rod")["rod_diameter_mm"] == pytest.approx(6.35)
    assert catalog._material("100 micron PMMA film   2 cm wide")["thickness_mm"] == pytest.approx(0.1)
    assert catalog._material("2 cm SIBAL")["material_class"].startswith("SIBAL")
    assert catalog._numbers_outside_parens("pot 1.2 (48)   0.9   0.4") == [1.2, 0.9, 0.4]
