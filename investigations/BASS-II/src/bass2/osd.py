"""Template OCR of the telemetry burned into the video (OSD).

Format (native 720x480, 3 monospaced lines, white text on a grey box):
    y≈31–45  "FUEL   AIR   FAN   RAD"          (fixed labels)
    y≈49–63  "-1     5     61    1.10"         (values)
    y≈67–81  "02/20/14 10:09:55"               (date is +1 day due to a leap-year bug; time)
Meaning (knowledge/dataset/bass2_dataset.md): FUEL = N₂ flow, AIR = air velocity
in cm/s (lags the fan by ≈ 15–25 s), FAN = 10× fan voltage, RAD = uncalibrated radiometer.

No external dependencies (no Tesseract): the text sits on a fixed monospaced grid; each
cell is compared against templates learned from frames with known text:
    learn_templates(frame, {"values": "-1 5 61 1.10", "clock": "02/20/14 10:09:55"})
Templates are stored in configs/osd_templates.npz (grid in configs/osd_grid.npz) and reused for all videos.
"""
from __future__ import annotations

import re

import cv2
import numpy as np

from .config import CONFIG_DIR

LINES = {"labels": (30, 46), "values": (48, 64), "clock": (66, 82)}
GLYPH_SHAPE = (16, 10)  # normalised (height, width)
TEMPLATE_PATH = CONFIG_DIR / "osd_templates.npz"


THR = 130          # text ≈ 160–255 over a grey box ≈ 40–100
GRID_PATH = CONFIG_DIR / "osd_grid.npz"


def _binarize(band: np.ndarray, thr: int = THR) -> np.ndarray:
    return (band.max(axis=2) > thr).astype(np.uint8)


def detect_lines(frame: np.ndarray, y_range: tuple[int, int] = (18, 115), min_ink: int = 15) -> dict | None:
    """Locate the three OSD text lines by vertical ink projection (positions vary by a few px per video).

    Each band is (top - 2, top + 14), the same relative placement used when the templates were learned.
    """
    ya, yb = y_range
    ink = _binarize(frame[ya:yb, 100:]).sum(axis=1)
    rows = np.where(ink > min_ink)[0]
    if len(rows) == 0:
        return None
    bands, start, prev = [], rows[0], rows[0]
    for r in rows[1:]:
        if r - prev > 2:
            bands.append((start, prev))
            start = r
        prev = r
    bands.append((start, prev))
    bands = [(a, b) for a, b in bands if 9 <= b - a <= 18]  # OSD glyphs are ~13 px tall
    # The OSD is three lines with a regular ~18 px pitch; pick the first triplet with that signature
    # (bright hardware near the top of some videos produces extra bands).
    trip = next((bands[i:i + 3] for i in range(len(bands) - 2)
                 if 15 <= bands[i + 1][0] - bands[i][0] <= 21 and 15 <= bands[i + 2][0] - bands[i + 1][0] <= 21), None)
    if trip is None:
        return None
    bands = trip
    return {name: (ya + a - 2, ya + a + 14) for name, (a, b) in zip(("labels", "values", "clock"), bands)}


def detect_layout(frame: np.ndarray) -> dict:
    """Per-video OSD layout: line bands + monospaced grid. Falls back to the B1 defaults."""
    lines = detect_lines(frame) or dict(LINES)
    x0, pitch = fit_grid(frame, lines=lines, x0s=range(130, 185), save=False)
    return {"lines": lines, "x0": x0, "pitch": pitch}


def fit_grid(frame: np.ndarray, pitches=np.arange(26.0, 31.0, 0.05), x0s=range(140, 175),
             lines: dict | None = None, save: bool = True) -> tuple[float, float]:
    """Fit the monospaced grid (x0, pitch) by minimising ink on cell boundaries."""
    ink = sum(_binarize(frame[a:b]).sum(axis=0) for a, b in (lines or LINES).values()).astype(float)
    best = (np.inf, 0.0, 0.0)
    xs = np.arange(len(ink))
    for p in pitches:
        for x0 in x0s:
            ph = ((xs - x0) % p)
            border = (ph < 1.5) | (ph > p - 1.5)
            cost = ink[border & (xs >= x0)].sum()
            if cost < best[0]:
                best = (cost, float(x0), float(p))
    if save:
        np.savez(GRID_PATH, x0=best[1], pitch=best[2])
    return best[1], best[2]


def _grid() -> tuple[float, float]:
    if GRID_PATH.exists():
        z = np.load(GRID_PATH)
        return float(z["x0"]), float(z["pitch"])
    return 157.0, 28.4


def glyphs(frame: np.ndarray, line: str, min_ink: int = 3, layout: dict | None = None) -> list[tuple[int, np.ndarray]]:
    """Non-empty cells of a line: (cell index, normalised bitmap)."""
    y0, y1 = (layout["lines"] if layout else LINES)[line]
    b = _binarize(frame[y0:y1])
    x0, p = (layout["x0"], layout["pitch"]) if layout else _grid()
    out = []
    i = 0
    while x0 + (i + 1) * p <= b.shape[1] + p / 2:
        a, z = int(round(x0 + i * p)), int(round(x0 + (i + 1) * p))
        cell = b[:, a:min(z, b.shape[1])]
        if cell.sum() >= min_ink and cell.shape[1] > 4:
            out.append((i, cv2.resize(cell.astype(np.float32), GLYPH_SHAPE[::-1], interpolation=cv2.INTER_AREA)))
        i += 1
    return out


def load_templates() -> dict[str, list[np.ndarray]]:
    if not TEMPLATE_PATH.exists():
        return {}
    z = np.load(TEMPLATE_PATH)
    out: dict[str, list[np.ndarray]] = {}
    for k in z.files:
        ch = k.split("__")[0].replace("SLASH", "/").replace("COLON", ":").replace("DOT", ".").replace("MINUS", "-")
        out.setdefault(ch, []).append(z[k])
    return out


def save_templates(t: dict[str, list[np.ndarray]]) -> None:
    enc = {"/": "SLASH", ":": "COLON", ".": "DOT", "-": "MINUS"}
    arrs = {f"{enc.get(ch, ch)}__{i}": a for ch, lst in t.items() for i, a in enumerate(lst[:8])}
    np.savez_compressed(TEMPLATE_PATH, **arrs)


def learn_templates(frame: np.ndarray, known: dict[str, str]) -> dict[str, int]:
    """Add templates from known text. Returns the number of glyphs per line, or raises
    if the glyph count does not match (text is compared without spaces)."""
    t = load_templates()
    report = {}
    for line, text in known.items():
        chars = [c for c in text if not c.isspace()]
        gs = glyphs(frame, line)
        if len(gs) != len(chars):
            raise ValueError(f"{line}: {len(gs)} glyphs vs {len(chars)} characters in {text!r}")
        for c, (_, g) in zip(chars, gs):
            t.setdefault(c, []).append(g)
        report[line] = len(gs)
    save_templates(t)
    return report


CHARSETS = {"values": set("-0123456789."), "clock": set("0123456789/:")}


def _match(g: np.ndarray, t: dict[str, list[np.ndarray]], charset: set | None = None) -> tuple[str, float]:
    best, score = "?", -1.0
    gv = g.ravel() - g.mean()
    for ch, lst in t.items():
        if charset is not None and ch not in charset:
            continue
        for a in lst:
            av = a.ravel() - a.mean()
            den = np.linalg.norm(gv) * np.linalg.norm(av)
            s = float(gv @ av / den) if den else 0.0
            if s > score:
                best, score = ch, s
    return best, score


def read_line(frame: np.ndarray, line: str, t: dict | None = None, min_score: float = 0.5,
              layout: dict | None = None) -> tuple[str, float]:
    t = t or load_templates()
    if not t:
        raise RuntimeError("No OSD templates: run `bass2 osd-learn` first")
    out, conf, prev = [], [], None
    for i, g in glyphs(frame, line, layout=layout):
        if prev is not None and i - prev > 1:
            out.append(" ")
        ch, s = _match(g, t, CHARSETS.get(line))
        out.append(ch if s >= min_score else "?")
        conf.append(s)
        prev = i
    return "".join(out), (float(np.min(conf)) if conf else 0.0)


def read_telemetry(frame: np.ndarray, t: dict | None = None, layout: dict | None = None) -> dict:
    """Return FUEL, AIR (cm/s), FAN, RAD, OSD clock time and minimum match confidence."""
    t = t or load_templates()
    vals, c1 = read_line(frame, "values", t, layout=layout)
    clock, c2 = read_line(frame, "clock", t, layout=layout)
    toks = vals.split()  # one token per field; a token containing '?' becomes NaN (never guess)
    keys = ["osd_fuel", "osd_air_cm_s", "osd_fan", "osd_rad"]
    out = {}
    for i, k in enumerate(keys):
        tok = toks[i] if len(toks) == len(keys) else ""
        out[k] = float(tok) if re.fullmatch(r"-?\d+(?:\.\d+)?", tok) else np.nan
    m = re.search(r"(\d{2}):(\d{2}):(\d{2})", clock)
    out["osd_clock_s"] = int(m.group(1)) * 3600 + int(m.group(2)) * 60 + int(m.group(3)) if m else np.nan
    out["osd_values_raw"], out["osd_clock_raw"] = vals, clock
    out["osd_conf"] = min(c1, c2)
    return out
