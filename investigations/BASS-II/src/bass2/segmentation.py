"""Segmentation of the luminous flame region (classic baseline, no training).

Designed to be swappable: every segmenter must satisfy
    segment(frame_bgr, valid_mask, params) -> bool mask (H, W)
and be registered in SEGMENTERS. The autoresearch loop (research/) compares variants
against the hand-labelled gold set (data/gold/).
"""
from __future__ import annotations

from typing import Callable

import cv2
import numpy as np
from skimage.filters import apply_hysteresis_threshold, threshold_otsu

from .video import to_channel


def _postprocess(mask: np.ndarray, p: dict) -> np.ndarray:
    k = int(p.get("morph_close", 0) or 0)
    if k > 0:
        ker = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k, k))
        mask = cv2.morphologyEx(mask.astype(np.uint8), cv2.MORPH_CLOSE, ker).astype(bool)
    n, lab, stats, _ = cv2.connectedComponentsWithStats(mask.astype(np.uint8), connectivity=8)
    if n <= 1:
        return mask
    areas = stats[1:, cv2.CC_STAT_AREA]
    keep = np.where(areas >= p.get("min_component_area", 0))[0] + 1
    if p.get("keep", "all") == "largest_k" and len(keep):
        keep = keep[np.argsort(stats[keep, cv2.CC_STAT_AREA])[::-1][: int(p.get("k", 1))]]
    return np.isin(lab, keep)


def seg_hysteresis(frame: np.ndarray, valid: np.ndarray, p: dict) -> np.ndarray:
    x = to_channel(frame, p.get("channel", "value"))
    if p.get("blur_sigma", 0):
        x = cv2.GaussianBlur(x, (0, 0), p["blur_sigma"])
    x = np.where(valid, x, 0)
    m = apply_hysteresis_threshold(x, p.get("low", 40), p.get("high", 90))
    return _postprocess(m & valid, p)


def seg_otsu(frame: np.ndarray, valid: np.ndarray, p: dict) -> np.ndarray:
    x = to_channel(frame, p.get("channel", "value"))
    if p.get("blur_sigma", 0):
        x = cv2.GaussianBlur(x, (0, 0), p["blur_sigma"])
    vals = x[valid]
    if vals.max() - vals.min() < 10:  # no flame in this frame
        return np.zeros_like(valid)
    t = max(threshold_otsu(vals), p.get("low", 40))
    return _postprocess((x > t) & valid, p)


def seg_fixed(frame: np.ndarray, valid: np.ndarray, p: dict) -> np.ndarray:
    x = to_channel(frame, p.get("channel", "value"))
    if p.get("blur_sigma", 0):
        x = cv2.GaussianBlur(x, (0, 0), p["blur_sigma"])
    return _postprocess((x > p.get("fixed_threshold", 60)) & valid, p)


def seg_adaptive(frame: np.ndarray, valid: np.ndarray, p: dict) -> np.ndarray:
    """Hysteresis with thresholds relative to the frame's own background noise.

    Faint, mostly blue flames (e.g. thin films at low flow after the ignition flash, B3/B12) peak at
    ~15–30 on 0–255, below fixed thresholds. The background of these videos is near zero with sparse
    compression speckle, so robust statistics of the valid area give the noise floor:
        low  = max(min_low,  median + k_low  · σ),   high = max(min_high, median + k_high · σ),
    σ = 1.4826·MAD (floored at sigma_floor). Blur suppresses single-pixel speckle; small components
    are removed afterwards. The `blue_excess` channel is OR-ed in so a faint blue leading edge next
    to a sooty core is not lost.
    """
    x = to_channel(frame, p.get("channel", "value"))
    if p.get("blur_sigma", 0):
        x = cv2.GaussianBlur(x, (0, 0), p["blur_sigma"])
    vals = x[valid]
    med = float(np.median(vals))
    sigma = max(1.4826 * float(np.median(np.abs(vals - med))), p.get("sigma_floor", 1.5))
    low = max(p.get("min_low", 10), med + p.get("k_low", 6) * sigma)
    high = max(p.get("min_high", 22), med + p.get("k_high", 12) * sigma)
    m = apply_hysteresis_threshold(np.where(valid, x, 0), low, high)
    if p.get("use_blue", True):
        b = to_channel(frame, "blue_excess")
        if p.get("blur_sigma", 0):
            b = cv2.GaussianBlur(b, (0, 0), p["blur_sigma"])
        m |= apply_hysteresis_threshold(np.where(valid, b, 0), p.get("blue_low", 6), p.get("blue_high", 14))
    return _postprocess(m & valid, p)


SEGMENTERS: dict[str, Callable[[np.ndarray, np.ndarray, dict], np.ndarray]] = {
    "adaptive": seg_adaptive,
    "hysteresis": seg_hysteresis,
    "otsu": seg_otsu,
    "fixed": seg_fixed,
}


def segment(frame: np.ndarray, valid: np.ndarray, params: dict) -> np.ndarray:
    return SEGMENTERS[params.get("method", "hysteresis")](frame, valid, params)
