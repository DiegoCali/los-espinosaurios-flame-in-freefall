"""Per-frame metrics computed from the mask and the image.

Conventions:
  * x grows to the right and y downward (image coordinates, native px).
  * Horizontal distances in "physical px" = px * pixel_aspect (corrects SAR 10:11).
  * *_mm = physical px * mm_per_px (NaN when the test is not calibrated).
  * Sub-pixel edges: mask·intensity profile projected on the flow axis; crossing at
    `edge_threshold_frac` of the profile maximum with linear interpolation.
"""
from __future__ import annotations

import numpy as np

from .video import linearize, to_channel


def _subpixel_edges(profile: np.ndarray, frac: float) -> tuple[float, float]:
    if profile.max() <= 0:
        return np.nan, np.nan
    thr = frac * profile.max()
    above = np.where(profile >= thr)[0]
    i0, i1 = above[0], above[-1]

    def interp(i_out, i_in):
        if i_out < 0 or i_out >= len(profile):
            return float(i_in)
        a, b = profile[i_out], profile[i_in]
        return i_out + (thr - a) / (b - a) * (i_in - i_out) if b != a else float(i_in)

    return interp(i0 - 1, i0), interp(i1 + 1, i1)


def frame_metrics(frame: np.ndarray, mask: np.ndarray, *, pixel_aspect: float = 10 / 11,
                  mm_per_px: float | None = None, edge_frac: float = 0.5,
                  gamma: float = 2.2) -> dict:
    area_px = int(mask.sum())
    v = to_channel(frame, "value")
    lin = linearize(v, gamma)
    out = {"area_px": area_px, "n_components": np.nan}
    nan_keys = ["cx_px", "cy_px", "x_min_px", "x_max_px", "y_min_px", "y_max_px",
                "x_left_sub_px", "x_right_sub_px", "y_top_sub_px", "y_bot_sub_px",
                "length_px", "height_px", "mean_value", "max_value",
                "integrated_intensity", "saturated_frac", "blue_ratio", "eccentricity"]
    if area_px == 0:
        out.update({k: np.nan for k in nan_keys})
        out["integrated_intensity"] = 0.0
    else:
        ys, xs = np.nonzero(mask)
        wts = lin[ys, xs]
        sw = wts.sum() or 1.0
        weighted = np.where(mask, lin, 0)
        xl, xr = _subpixel_edges(weighted.sum(axis=0), edge_frac)
        yt, yb = _subpixel_edges(weighted.sum(axis=1), edge_frac)
        b, g, r = (frame[..., i][mask].astype(float).mean() for i in range(3))
        cov = np.cov(np.vstack([xs * pixel_aspect, ys])) if area_px > 2 else np.eye(2)
        ev = np.sort(np.linalg.eigvalsh(cov))
        out.update({
            "cx_px": float((xs * wts).sum() / sw), "cy_px": float((ys * wts).sum() / sw),
            "x_min_px": float(xs.min()), "x_max_px": float(xs.max()),
            "y_min_px": float(ys.min()), "y_max_px": float(ys.max()),
            "x_left_sub_px": xl, "x_right_sub_px": xr, "y_top_sub_px": yt, "y_bot_sub_px": yb,
            "length_px": float(xs.max() - xs.min() + 1), "height_px": float(ys.max() - ys.min() + 1),
            "mean_value": float(v[mask].mean()), "max_value": float(v[mask].max()),
            "integrated_intensity": float(wts.sum()),
            "saturated_frac": float((frame[mask] >= 250).any(axis=1).mean()),
            "blue_ratio": float(b / (r + g + b + 1e-9)),
            "eccentricity": float(np.sqrt(1 - ev[0] / ev[1])) if ev[1] > 0 else np.nan,
        })
    # Physical units
    out["length_phys_px"] = out["length_px"] * pixel_aspect if area_px else np.nan
    out["area_phys_px"] = area_px * pixel_aspect
    s = mm_per_px if mm_per_px else np.nan
    for k in ("cx_px", "x_left_sub_px", "x_right_sub_px", "x_min_px", "x_max_px"):
        out[k.replace("_px", "_mm")] = out[k] * pixel_aspect * s
    for k in ("cy_px", "y_top_sub_px", "y_bot_sub_px"):
        out[k.replace("_px", "_mm")] = out[k] * s
    out["length_mm"] = out["length_phys_px"] * s
    out["height_mm"] = out["height_px"] * s
    out["area_mm2"] = out["area_phys_px"] * s * s
    return out
