"""Geometric spatial calibration from illuminated frames (independent of published spread rates).

Several BASS-II videos start with the glovebox lights on (e.g. B4, B7), showing the duct's
"movable scale" — a ruler with evenly spaced tick marks near the bottom of the frame
(Summary Report §2: "a movable scale" inside the 17 cm test section). The tick period is
measured here with an autocorrelation of the horizontal brightness profile.

The ruler shows cross-shaped major marks with finer graduations in between. The dominant
autocorrelation period (~52.5 native px on GMT 50) is the major-mark spacing, taken as
TICK_MM = 10 mm (1 cm marks). Why 10 mm and not 5 mm: with 10 mm the 76 mm duct spans ~360 px
and the edge-on sample sits mid-duct, as observed in the lit frames; 5 mm would make the duct
~31 mm tall, which is geometrically impossible. The graduation is not stated in the NASA documents,
so this remains an explicit assumption; validation against published spread rates on tests
not used to make the choice is reported in reports/ (G6).
The result is reported in mm per *physical* pixel (horizontal px × pixel_aspect), which is the
same unit as the vertical pixel used by `mm_per_px` in configs/calibration.yaml.
Perspective caveat: the scale sits near the duct floor, not in the sample plane, so the
magnification can differ by a few percent from the sample plane.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from .video import iter_frames, probe, valid_mask

TICK_MM = 10.0


def lit_frames(video: str | Path, osd: dict | None = None, threshold: float = 18, step: int = 5,
               max_frames: int = 400) -> list[tuple[int, np.ndarray]]:
    """Frames whose median brightness indicates the scene is illuminated."""
    info = probe(video)
    vm = valid_mask((info.height, info.width), osd or {"y0": 0, "y1": 90})
    out = []
    for i, _, f in iter_frames(video, step=step, max_frames=max_frames):
        if np.median(f.max(axis=2)[vm]) > threshold:
            out.append((i, f))
    return out


def tick_period(frame: np.ndarray, y0: int, y1: int, x0: int = 60, x1: int = 700,
                min_period: float = 12, max_period: float = 60) -> tuple[float, float]:
    """Dominant tick period (native px) in a horizontal band via autocorrelation.

    Returns (period_px, strength) where strength is the normalised autocorrelation peak (0–1).
    """
    band = frame[y0:y1, x0:x1].max(axis=2).astype(float)
    prof = band.max(axis=0)
    # remove the slow illumination trend so only the ticks remain
    k = 31
    trend = np.convolve(prof, np.ones(k) / k, mode="same")
    p = prof - trend
    p -= p.mean()
    ac = np.correlate(p, p, mode="full")[len(p) - 1:]
    ac /= ac[0] if ac[0] else 1
    lo, hi = int(min_period), int(max_period)
    lag = lo + int(np.argmax(ac[lo:hi]))
    # parabolic sub-pixel refinement
    if 1 <= lag < len(ac) - 1:
        a, b, c = ac[lag - 1], ac[lag], ac[lag + 1]
        den = a - 2 * b + c
        lag = lag + 0.5 * (a - c) / den if den else lag
    return float(lag), float(ac[int(round(lag))])


def find_ruler_band(frame: np.ndarray, y_search: tuple[int, int] = (380, 475), height: int = 20) -> tuple[int, int, float, float]:
    """Scan horizontal bands and return the one with the strongest periodic tick pattern."""
    best = (0, 0, np.nan, 0.0)
    for y in range(y_search[0], y_search[1] - height, 4):
        per, s = tick_period(frame, y, y + height)
        if s > best[3]:
            best = (y, y + height, per, s)
    return best


def calibrate_video(video: str | Path, pixel_aspect: float = 10 / 11, tick_mm: float = TICK_MM) -> dict:
    """Median ruler-based mm per physical px over the lit frames of a video."""
    frames = lit_frames(video)
    if not frames:
        return {"video": str(video), "n_lit": 0}
    rows = []
    for i, f in frames[:40]:
        y0, y1, per, s = find_ruler_band(f)
        if s > 0.3:
            rows.append({"frame": i, "y0": y0, "period_native_px": per, "strength": s})
    if not rows:
        return {"video": str(video), "n_lit": len(frames), "n_valid": 0}
    d = pd.DataFrame(rows)
    per = float(d.period_native_px.median())
    per_phys = per * pixel_aspect
    return {"video": str(video), "n_lit": len(frames), "n_valid": len(d),
            "period_native_px": per, "period_phys_px": per_phys,
            "period_iqr_native_px": float(d.period_native_px.quantile(0.75) - d.period_native_px.quantile(0.25)),
            "tick_mm_assumed": tick_mm, "mm_per_phys_px": tick_mm / per_phys,
            "band_y0": int(d.y0.median()), "strength": float(d.strength.median())}
