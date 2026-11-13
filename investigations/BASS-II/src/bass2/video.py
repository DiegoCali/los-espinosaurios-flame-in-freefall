"""Video reading and frame preprocessing.

Format facts (knowledge/dataset/video_format_probe.md):
  * 720x480 @ 29.97 fps, NON-square pixels (SAR 10:11) -> physical px width = 10/11 of its height.
  * Telemetry (OSD) burned into the top band (y < ~90 px) -> masked out before segmentation.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

import cv2
import numpy as np


@dataclass
class VideoInfo:
    path: Path
    width: int
    height: int
    fps: float
    n_frames: int

    @property
    def duration_s(self) -> float:
        return self.n_frames / self.fps if self.fps else float("nan")


def probe(path: str | Path) -> VideoInfo:
    cap = cv2.VideoCapture(str(path))
    if not cap.isOpened():
        raise IOError(f"Cannot open {path}")
    info = VideoInfo(Path(path), int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
                     int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
                     float(cap.get(cv2.CAP_PROP_FPS)) or 29.97,
                     int(cap.get(cv2.CAP_PROP_FRAME_COUNT)))
    cap.release()
    return info


def iter_frames(path: str | Path, step: int = 1, start: int = 0,
                max_frames: int | None = None) -> Iterator[tuple[int, float, np.ndarray]]:
    """Yield (index, time_s, BGR uint8 frame). Sequential reads (more robust than seeking in H.264)."""
    cap = cv2.VideoCapture(str(path))
    fps = cap.get(cv2.CAP_PROP_FPS) or 29.97
    idx, emitted = 0, 0
    try:
        while True:
            ok = cap.grab()
            if not ok:
                break
            if idx >= start and (idx - start) % step == 0:
                ok, frame = cap.retrieve()
                if not ok:
                    break
                yield idx, idx / fps, frame
                emitted += 1
                if max_frames and emitted >= max_frames:
                    break
            idx += 1
    finally:
        cap.release()


def read_frame(path: str | Path, index: int) -> np.ndarray:
    for _, _, f in iter_frames(path, start=index, max_frames=1):
        return f
    raise IndexError(index)


def valid_mask(shape: tuple[int, int], osd: dict | None = None, roi: list[int] | None = None) -> np.ndarray:
    """Boolean mask of analysable pixels (excludes the OSD band and everything outside the ROI)."""
    h, w = shape[:2]
    m = np.ones((h, w), bool)
    if osd:
        m[int(osd.get("y0", 0)):int(osd.get("y1", 0)), :] = False
    if roi:
        x0, y0, x1, y1 = roi
        r = np.zeros_like(m)
        r[y0:y1, x0:x1] = True
        m &= r
    return m


def to_channel(frame: np.ndarray, channel: str = "value") -> np.ndarray:
    """Scalar 0-255 (float32) channel used for segmentation.

    value       max(R,G,B): robust for blue, magenta or yellow flames.
    luma        Y' (BT.601).
    blue_excess B - (R+G)/2 clipped: highlights blue chemiluminescence (CH*), ignores soot.
    soot        R - B clipped: highlights soot emission (yellow/orange).
    """
    f = frame.astype(np.float32)
    b, g, r = f[..., 0], f[..., 1], f[..., 2]
    if channel == "value":
        return f.max(axis=2)
    if channel == "luma":
        return 0.299 * r + 0.587 * g + 0.114 * b
    if channel == "blue_excess":
        return np.clip(b - 0.5 * (r + g), 0, 255)
    if channel == "soot":
        return np.clip(r - b, 0, 255)
    raise ValueError(channel)


def linearize(x: np.ndarray, gamma: float = 2.2) -> np.ndarray:
    """Approximate linear intensity from gamma-encoded values (0-255 -> 0-1)."""
    return np.power(np.clip(x, 0, 255) / 255.0, gamma)


def background_model(path: str | Path, n: int = 30, channel: str = "value", step: int = 1) -> np.ndarray:
    """Median of the first n frames (before ignition) as a static background."""
    frames = [to_channel(f, channel) for _, _, f in iter_frames(path, step=step, max_frames=n)]
    return np.median(np.stack(frames), axis=0) if frames else None
