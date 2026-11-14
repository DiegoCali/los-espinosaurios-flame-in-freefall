"""Tests for the ruler calibration and the published-rate validation helpers."""
import numpy as np
import pandas as pd
import pytest

from bass2 import calibration, validation


def synthetic_ruler(period: float = 52.5, h=480, w=720, y=440):
    """Dark frame with a bright ruler band carrying ticks every `period` px."""
    img = np.full((h, w, 3), 30, np.uint8)
    img[y - 4:y + 4, 60:700] = 90
    x = 70.0
    while x < 690:
        xi = int(round(x))
        img[y - 12:y + 6, xi:xi + 3] = 220
        x += period
    return img


@pytest.mark.parametrize("period", [26.3, 52.5, 41.0])
def test_tick_period_recovered(period):
    f = synthetic_ruler(period)
    y0, y1, per, strength = calibration.find_ruler_band(f)
    assert per == pytest.approx(period, abs=0.6)
    assert strength > 0.3


def test_match_published_uses_flow_step(monkeypatch, tmp_path):
    meas = pd.DataFrame([{"test_id": "M2", "rate": 0.034, "lo": 0.032, "hi": 0.036, "unit": "mm/s",
                          "osd_air_median_cm_s": 15.1, "mm_per_px_rel_sigma": 0.02}])
    v = validation.match_published(meas)
    assert len(v) == 1
    assert v.published_step.iloc[0] == 2  # 15 cm/s step, not the first (20 cm/s)
    assert v.vf_published_mm_s.iloc[0] == pytest.approx(0.033)
