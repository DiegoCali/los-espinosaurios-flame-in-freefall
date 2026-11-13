"""NASA PSI-25 metadata: file inventory and a cleaned experimental table.

Sources:
  * Investigation JSON (PSI API)         -> data/catalog/psi25_investigation.json
  * Experimental table CSV (129 tests)   -> data/docs/Experimental table_BASS-II.csv

  * As-run matrices (cross-check)        -> data/catalog/test_matrix_<PI>.csv (Test.Matrices.xlsx)
                                            knowledge/dataset/raw_text/BASS-II_Summary_Report.txt (App. A)

The experimental table is free-form operator text (e.g. "pot 1.2 (48)  0.9  0.4",
"5 down to ext"). The parser ALWAYS keeps the raw text. `parse_air_display()` turns the
Air display cell into imposed air velocities with a named rule and a confidence level
(it handles cm/s written inside parentheses with fan displays outside, e.g. O13a, explicit
"cm/s" units, pots mixed into the column, events such as "max"/"ext"/"blowoff", and
fan-column fallbacks). Every rule is documented in knowledge/dataset/test_matrix_notes.md §5.
The legacy columns `fan_steps` / `air_steps` (numbers outside parentheses) are kept for
backward compatibility only; use `flow_steps_cm_s` / `flow_initial_cm_s` for science.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import numpy as np
import pandas as pd
import requests

from .config import PROJECT_ROOT, load_config

PI_CODES = {"B": "Bhattacharjee", "F": "Ferkul", "M": "Miller", "O": "Olson",
            "P": "Fernandez-Pello", "T": "T'ien"}

# --------------------------------------------------------------------------- JSON


def fetch_investigation(force: bool = False) -> dict:
    cfg = load_config()
    out = cfg.path("catalog") / "psi25_investigation.json"
    if out.exists() and not force:
        return json.loads(out.read_text(encoding="utf-8"))
    r = requests.get(cfg["nasa"]["investigation_url"], timeout=120)
    r.raise_for_status()
    out.write_text(r.text, encoding="utf-8")
    return r.json()


_TEST_RE = re.compile(r"_TEST_([A-Z]\d+[a-z]?)", re.I)
_TP_RE = re.compile(r"_TP([A-Z]\d+[a-z]?)", re.I)
_GMT_RE = re.compile(r"GMT(?:2014_)?(\d{2,3})", re.I)
_SAMPLE_RE = re.compile(r"(?:SAMPLE_|_S)(\d{2,3})M?", re.I)


def classify_file(name: str) -> str:
    n = name.lower()
    if n.endswith(".pdf") and "proofsheet" in n:
        return "proofsheet"
    if n.endswith(".zip") and "original videos" in n:
        return "original_videos_zip"
    if n.endswith(".zip"):
        return "raw_images_zip"
    if n.endswith(".mp4"):
        if "still_sequence" in n:
            return "still_sequence"
        if "los" in n:
            return "los_clip"
        if "2nd_view" in n:
            return "second_view"
        if re.search(r"_test_?\s?[a-z]\d", n):  # "_TEST_B1", "_TESTB6", "_test T13"
            return "main_video"
        return "other_video"
    return "other"


def build_inventory(inv: dict | None = None, write: bool = True) -> pd.DataFrame:
    """One row per file with test id, kind and size."""
    inv = inv or fetch_investigation()
    rows = []
    for f in inv["added"]:
        if not f.get("visible", True):
            continue
        name = f["file_name"]
        sub = f.get("subcategory", "") or ""
        test_id = sub.rsplit("/", 1)[-1] if "/" in sub else None
        m = _TEST_RE.search(name) or _TP_RE.search(name)
        variant = m.group(1) if m else None  # e.g. O5a vs folder O5
        gmt = _GMT_RE.search(name)
        smp = _SAMPLE_RE.search(name)
        rows.append({
            "pi": sub.split("/")[1].strip() if sub.count("/") >= 2 else None,
            "test_id": test_id,
            "test_variant": variant,
            "file_name": name,
            "kind": classify_file(name),
            "ext": Path(name).suffix.lower(),
            "size_bytes": int(f.get("file_size") or 0),
            "gmt_day": int(gmt.group(1)) if gmt else None,
            "sample_id": smp.group(1) if smp else None,
            "category": f["remote_path"].split("/")[4],
            "subcategory": sub,
        })
    df = pd.DataFrame(rows)
    if write:
        df.to_csv(load_config().path("catalog") / "files_inventory.csv", index=False)
    return df


def best_video(inventory: pd.DataFrame, test_id: str, view: str = "main") -> pd.Series | None:
    """Recommended video for a test: the smallest file of the requested view."""
    kind = "main_video" if view == "main" else "second_view"
    sel = inventory[(inventory.test_id == test_id) & (inventory.kind == kind)]
    if sel.empty:
        return None
    return sel.sort_values("size_bytes").iloc[0]


# ------------------------------------------------------------ experimental table

_NUM = re.compile(r"(?<![\w.])[-+]?\d*\.?\d+")


def _numbers_outside_parens(text: str) -> list[float]:
    """Legacy helper (kept for `fan_steps` / `air_steps`): every number outside parentheses."""
    if not isinstance(text, str):
        return []
    t = re.sub(r"\([^)]*\)", " ", text)
    t = t.replace("p.", ".").replace("..", ".")
    out = []
    for tok in _NUM.findall(t):
        try:
            out.append(float(tok))
        except ValueError:
            pass
    return out


def _numbers_in_parens(text: str) -> list[float]:
    if not isinstance(text, str):
        return []
    inner = " ".join(re.findall(r"\(([^)]*)\)", text))
    return [float(x) for x in _NUM.findall(inner)]


def _to_float(x) -> float:
    if x is None or (isinstance(x, float) and np.isnan(x)):
        return np.nan
    m = _NUM.search(str(x))
    return float(m.group()) if m else np.nan


# ------------------------------------------------------------------- geometry

SIBAL_THICKNESS_MM = 0.32  # bass2_dataset.md §PI table (75 % cotton / 25 % fiberglass, 18.2 mg/cm²)


def _material(text: str) -> dict:
    """Material class and geometry from the free-text `Fuel Sample Material` cell.

    Rules (documented in knowledge/dataset/test_matrix_notes.md §5.3):
      * typos fixed before parsing: "2ide" -> "wide" (M19), "blac" -> "black" (P14);
      * rod diameter: fraction `a/b` (with or without `"`) or decimal inches `0.5"` -> × 25.4 mm;
      * thickness: `N micron` -> N/1000 mm, otherwise the first `N mm`; SIBAL -> 0.32 mm (dataset doc);
      * width: `N cm` (not for rods / spheres); "2 cm thick" in M5 is the width;
      * spherical section: `N cm spherical` -> sphere_diameter_mm = 10·N (width left empty);
      * sides: `N sided` -> sides_burned.
    """
    raw = text if isinstance(text, str) else ""
    t = re.sub(r"\s+", " ", raw.lower()).strip()
    flags = []
    if "2ide" in t:
        t = t.replace("2ide", "wide")
        flags.append("typo_2ide->wide")
    if re.search(r"\bblac\b", t):
        t = re.sub(r"\bblac\b", "black", t)
        flags.append("typo_blac->black")
    if "sibal" in t:
        cls, geom = "SIBAL (cotton-fiberglass fabric)", "fabric"
    elif "nomex" in t:
        cls, geom = "Nomex fabric", "fabric"
    elif "candle" in t or "wax" in t:
        cls, geom = "wax candle", "candle"
    elif "spherical" in t:
        cls, geom = "PMMA spherical section", "sphere"
    elif "rod" in t:
        cls, geom = "PMMA rod", "rod"
    elif "film" in t or "micron" in t:
        cls, geom = "PMMA thin film", "film"
    elif "pmma" in t or "slab" in t or "mm thick" in t:
        cls, geom = "PMMA slab", "slab"
    else:
        cls, geom = "unknown", None

    thick_mm = np.nan
    m = re.search(r"(\d+(?:\.\d+)?)\s*micron", t)
    if m:
        thick_mm = float(m.group(1)) / 1000
    else:
        m = re.search(r"(?<![\d.])(\d*\.?\d+)\s*mm\b", t)
        if m:
            thick_mm = float(m.group(1))
    if np.isnan(thick_mm) and geom == "fabric" and "sibal" in t:
        thick_mm = SIBAL_THICKNESS_MM
        flags.append("thickness_from_dataset_doc")
    if geom in ("film", "slab") and not np.isnan(thick_mm):
        geom = "film" if thick_mm <= 0.4 else "slab"
        cls = "PMMA thin film" if geom == "film" else "PMMA slab"

    diam_mm = np.nan
    if geom == "rod":
        m = re.search(r"(\d+)\s*/\s*(\d+)", t)
        if m:
            diam_mm = float(m.group(1)) / float(m.group(2)) * 25.4
        else:
            m = re.search(r"(\d*\.\d+|\d+)\s*(?:\"|in\b|inch)", t)
            if m:
                diam_mm = float(m.group(1)) * 25.4

    width_mm = np.nan
    sphere_mm = np.nan
    m = re.search(r"(\d*\.?\d+)\s*cm\b", t)
    if m:
        if geom == "sphere":
            sphere_mm = float(m.group(1)) * 10
        elif geom != "rod":
            width_mm = float(m.group(1)) * 10
    m = re.search(r"(\d)\s*sided", t)
    sides = int(m.group(1)) if m else np.nan
    return {"material_class": cls, "geometry": geom, "thickness_mm": thick_mm,
            "rod_diameter_mm": diam_mm, "width_mm": width_mm, "sphere_diameter_mm": sphere_mm,
            "sides_burned": sides,
            "rod_color": ("black" if "black" in t else "clear" if "clear" in t else None),
            "material_parse_flags": ";".join(flags)}


# ---------------------------------------------------------------- flow parsing
#
# The `Air display` cell is anemometer air velocity (cm/s) written by the crew as free text.
# The parser below turns it into a list of imposed air velocities. See test_matrix_notes.md §5.1.

U_ANEMOMETER_CORR = 1.0066   # U_centerline = 1.0066 · AIR display (fan calibration xlsx, bass2_dataset.md §4)
FAN_DISPLAY_MIN = 38.0       # fan display at pot 0 is ~38.2 (10 × fan volts); displays never go below
AIR_MAX_CM_S = 55.0          # plausible imposed velocities: 0–55 cm/s
AIR_MAX_BY_RESTRICTOR = {0: 55.0, 1: 41.0, 2: 41.0}  # fan calibration maxima: 59 / 40 / 40 cm/s
POT_TO_DISPLAY = (38.16, 8.384)  # fan_display ≈ 38.16 + 8.384·pot (bass2_dataset.md §4)

_TOK = re.compile(r"\(|\)|[,;]|cm/s|[<~]?\d*\.\d+\??|[<~]?\d+\??|>|\?|[a-z]+")
_EVENT_WORDS = {
    "ext": "extinction", "extinction": "extinction", "extinguished": "extinction", "out": "extinction",
    "blowoff": "blowoff", "max": "max", "maximum": "max", "low": "lower_unrecorded",
    "lower": "lower_unrecorded", "decr": "decrease", "decrease": "decrease", "down": "decrease",
    "incr": "ramp_up", "increase": "ramp_up", "ign": "ignition", "ignition": "ignition",
    "off": "flow_off", "etc": "periodic_etc", "ibid": "ibid", "brief": "brief",
}
_TAIL_LOWER = {"lower_unrecorded", "decrease", "flow_off"}


def _norm_flow_text(text) -> str:
    if not isinstance(text, str):
        return ""
    s = text.lower()
    s = re.sub(r"\bp\.(\d)", r".\1", s)          # "p.36" -> ".36"
    s = re.sub(r"\.{2,}(\d)", r".\1", s)          # "..305" -> ".305"
    s = re.sub(r"(\d)\.(?=[\s,;)]|$)", r"\1 ", s)  # "0.45." / "10." -> "0.45" / "10"
    return s


def _num(tok: str) -> tuple[float, str]:
    qual = ""
    if tok[0] in "<~":
        qual, tok = tok[0], tok[1:]
    if tok.endswith("?"):
        qual, tok = qual + "?", tok[:-1]
    return float(tok), qual


def _scan(text: str) -> tuple[list[dict], list[dict], list[str]]:
    """Tokenise flow text into outside items and parenthesised groups."""
    outside, groups, words = [], [], []
    cur = None
    for tok in _TOK.findall(_norm_flow_text(text)):
        if tok == "(":
            cur = {"nums": [], "words": [], "pos": len(outside),
                   "prev": outside[-1] if outside else None}
            continue
        if tok == ")":
            if cur is not None:
                groups.append(cur)
            cur = None
            continue
        if tok in ",;":
            if cur is None:
                outside.append({"kind": "sep"})
            continue
        is_num = bool(re.match(r"[<~]?\d|[<~]?\.\d", tok))
        if cur is not None:
            if is_num:
                cur["nums"].append(_num(tok)[0])
            else:
                cur["words"].append(tok)
            continue
        if is_num:
            v, q = _num(tok)
            outside.append({"kind": "num", "v": v, "qual": q, "pot": False, "unit": False,
                            "ramp": False, "max": False})
        else:
            outside.append({"kind": "word", "w": tok})
            words.append(tok)
    if cur is not None:  # unbalanced "(" -> treat as group
        groups.append(cur)
    return outside, groups, words


def _mark_pots_units(outside: list[dict]) -> None:
    """`pot` binds backward to the previous number when that number is fractional ("0.5 pot") or
    when `pot` closes an item ("5 pot,"); otherwise forward ("pot 0.4"). `pots` always binds
    forward; `cm/s` marks the previous number as explicit; `incr` / `max` flag the next number."""
    pot_mode = ramp_next = max_next = False
    for i, it in enumerate(outside):
        if it["kind"] == "sep":
            continue
        if it["kind"] == "num":
            if pot_mode:
                it["pot"] = True
            if ramp_next:
                it["ramp"], ramp_next = True, False
            if max_next:
                it["max"], max_next = True, False
            continue
        w = it["w"]
        prev = outside[i - 1] if i else None
        if w == "pots":
            pot_mode = True
        elif w == "pot":
            nxt = outside[i + 1] if i + 1 < len(outside) else None
            closes = nxt is None or nxt["kind"] != "num"
            if prev is not None and prev["kind"] == "num" and (prev["v"] != round(prev["v"]) or closes):
                prev["pot"] = True
            else:
                pot_mode = True
        elif w == "cm/s" and prev is not None and prev["kind"] == "num":
            prev["unit"] = True
        elif w in ("incr", "increase"):
            ramp_next = True
        elif w in ("max", "maximum"):
            max_next = ramp_next  # only "incr to max X" carries a value; "2, max, 0" does not
        elif w not in ("to", "and", "then", "in", "s", "at", "fan"):
            pot_mode = pot_mode and w in ("pot", "pots")


def _group_kind(g: dict) -> str:
    nums = g["nums"]
    if "pot" in g["words"] or "pots" in g["words"]:
        return "pot"
    if not nums:
        return "annotation"
    if g["prev"] is not None and g["prev"].get("w") in ("max", "maximum") and len(nums) == 1:
        return "max_value"
    if all(v >= FAN_DISPLAY_MIN for v in nums):
        return "fan_display"
    if max(nums) <= 10 and any(v != round(v) for v in nums):
        return "pot"
    return "cm_s"


def _fan_pots(fan_text) -> list[float]:
    """Pot settings in the Fan display column (values ≤ 10 outside or inside parentheses)."""
    out_items, groups, _ = _scan(fan_text)
    out = [it["v"] for it in out_items if it["kind"] == "num"]
    if out and all(v <= 10 for v in out):
        return out
    for g in groups:
        if g["nums"] and all(v <= 10 for v in g["nums"]):
            return g["nums"]
    return []


def _displays_match_pots(displays: list[float], pots: list[float], tol: float = 3.0) -> bool:
    n = min(len(displays), len(pots))
    if n == 0:
        return False
    a, b = POT_TO_DISPLAY
    return float(np.mean([abs(d - (a + b * p)) for d, p in zip(displays[:n], pots[:n])])) <= tol


def _fan_fallback(fan_text) -> tuple[list[float], str, str]:
    """Flow from the Fan display column when the Air display cell has no cm/s value."""
    s = _norm_flow_text(fan_text)
    m = re.search(r"(\d*\.?\d+)\s*cm/s", s)
    if m:
        return [float(m.group(1))], "fan_column_explicit_cm_s", "medium"
    items, _, _ = _scan(fan_text)
    nums = [it for it in items if it["kind"] == "num"]
    if len(nums) >= 2 and nums[0]["v"] == round(nums[0]["v"]) and 1 <= nums[0]["v"] <= 10 \
            and nums[1]["v"] < 1:
        # Olson/Pello convention: "5, .36, .32, ..." = 5 cm/s at ignition, then pots
        return [nums[0]["v"]], "fan_column_ignition_velocity", "low"
    return [], "no_numeric_flow", "low"


def parse_air_display(text, restrictor=None, fan_text=None) -> dict:
    """Robust parse of the free-text `Air display` cell into imposed air velocities.

    Returns a dict with: steps (AIR display values, cm/s, uncorrected), events (list[str]),
    rule (str), confidence ('high'|'medium'|'low'), initial_unknown (bool: ramp target only),
    min_upper_bound (bool), max_lower_bound (bool), notes (list[str]).
    """
    try:
        r = int(restrictor)
    except (TypeError, ValueError):
        r = None
    limit = min(AIR_MAX_CM_S, AIR_MAX_BY_RESTRICTOR.get(r, AIR_MAX_CM_S))
    outside, groups, words = _scan(text)
    _mark_pots_units(outside)
    events = []
    joined = " ".join(words)
    for w in words:
        e = _EVENT_WORDS.get(w)
        if e and e not in events:
            events.append(e)
    if re.search(r"\bno (ign|ignition)\b", joined):
        events = [e for e in events if e != "ignition"] + ["no_ignition"]
    if "would not stay lit" in joined:
        events.append("not_sustained")
    if "see fan" in joined:
        events.append("see_fan")
    notes: list[str] = []

    # attach max-values "(47)" and annotations "(?)" / "(brief)" to the outside sequence
    for g in groups:
        kind = _group_kind(g)
        g["kind"] = kind
        if kind == "annotation" and g["pos"] > 0:
            prev = outside[g["pos"] - 1]
            if prev["kind"] == "num" and "?" in g["words"]:
                prev["qual"] += "?"
    seq = []
    for i, it in enumerate(outside + [None]):
        for g in groups:
            if g["kind"] == "max_value" and g["pos"] == i:
                seq.append({"kind": "num", "v": g["nums"][0], "qual": "", "pot": False,
                            "unit": False, "ramp": False, "max": True})
        if it is not None:
            seq.append(it)
    nums = [it for it in seq if it["kind"] == "num" and not it["pot"]]
    pots_out = [it for it in seq if it["kind"] == "num" and it["pot"]]
    cms_groups = [g for g in groups if g["kind"] == "cm_s"]
    fan_groups = [g for g in groups if g["kind"] == "fan_display"]

    rule, conf = "plain_list", "high"
    chosen: list[dict]
    explicit = [it for it in nums if it["unit"]]
    if explicit:
        dropped = [it["v"] for it in nums if not it["unit"]]
        chosen, rule, conf = explicit, "explicit_cm_s_unit", "medium"
        if dropped:
            notes.append(f"dropped non-unit values {dropped} (fan display)")
    elif nums and all(it["v"] >= FAN_DISPLAY_MIN for it in nums) and cms_groups:
        disp = [it["v"] for it in nums]
        chosen = [{"v": v, "qual": "", "ramp": False, "max": False} for v in cms_groups[0]["nums"]]
        rule, conf = "swap_paren_cm_s_outside_fan_display", "medium"
        pots = _fan_pots(fan_text)
        if _displays_match_pots(disp, pots):
            notes.append("outside values match fan display predicted from Fan-column pots")
        else:
            conf = "low"
            notes.append("outside values not confirmed by Fan-column pots")
    elif nums and all(it["v"] >= FAN_DISPLAY_MIN for it in nums) and all(it["v"] > limit for it in nums):
        chosen, rule, conf = [], "only_fan_display_values", "low"
        notes.append(f"all values {[it['v'] for it in nums]} exceed {limit} cm/s")
    else:
        chosen = [it for it in nums if it["v"] <= limit]
        dropped = [it["v"] for it in nums if it["v"] > limit]
        if dropped:
            rule, conf = "dropped_implausible_values", "medium"
            notes.append(f"dropped values > {limit} cm/s: {dropped}")
        elif fan_groups:
            rule = "outside_cm_s_paren_fan_display"
        elif pots_out:
            rule = "cm_s_then_pots"

    steps = [it["v"] for it in chosen]
    initial_unknown = False
    if not steps:
        steps, rule, conf = _fan_fallback(fan_text)
        if "see_fan" in events and rule == "fan_column_ignition_velocity":
            conf = "medium"
    else:
        if chosen[0].get("ramp"):
            initial_unknown = True
            rule, conf = "ramp_target_only", "low"
        if conf == "high":
            if any(it.get("qual") for it in chosen):
                conf = "medium"
                notes.append("qualified value(s): " + ", ".join(
                    f"{it['qual']}{it['v']:g}" for it in chosen if it.get("qual")))
            if any(FAN_DISPLAY_MIN <= v <= limit for v in steps):
                conf = "medium"
                notes.append("value(s) in the fan-display/cm/s overlap zone (38-55)")
            if "approaching" in words:
                conf = "medium"
                notes.append("'approaching' value not reached")
    tail = [w for w in words if _EVENT_WORDS.get(w) in _TAIL_LOWER]
    lowest_lt = bool(chosen) and any(it.get("qual", "").startswith("<") and it["v"] == min(steps)
                                     for it in chosen)
    min_ub = bool(steps) and (bool(tail) or bool(pots_out) or "very" in words or lowest_lt)
    max_lb = "max" in events and not any(it.get("max") for it in chosen) and rule != "ramp_target_only"
    return {"steps": [float(v) for v in steps], "events": events, "rule": rule, "confidence": conf,
            "initial_unknown": initial_unknown, "min_upper_bound": bool(min_ub),
            "max_lower_bound": bool(max_lb), "notes": notes}


# ------------------------------------------------- as-run matrices (cross-check)

REPORT_TXT = PROJECT_ROOT / "knowledge/dataset/raw_text/BASS-II_Summary_Report.txt"
_REC_RE = re.compile(r"(?<!\S)(\d{1,3}|-{3,})\s+([BFMOPT]\d{1,2}[ab]?)\s+(\d{2,3}[mML]?)(?=\s)")
_REGIME_RE = re.compile(r"\s([012])\s+(Opposed|Concurrent|Stagnation|\?|1)\s")
_GAIN_RE = re.compile(
    r"(?<!\S)((?:1,000|1000|250|50|10)(?:\s*(?:>|,|and)\s*(?:1,000|1000|250|50|10))*)\s+"
    r"(?=-{2,}|saturated|nearly|\d+(?:\.\d+)?\s+maximum|\d\.\d\s*>|(?:\d+\s+)?NA\b)", re.I)
_OBS_CUT = re.compile(r"\s(?:\d{1,2}/\d{1,2}/\d{2,4}\b|aGreenwich|=====|TABLE A\.|Actual date|"
                      r"extinguished, burn time, color, etc\.\)c)")


def _f(tok) -> float:
    try:
        return float(str(tok).replace(",", ""))
    except ValueError:
        return np.nan


def _same(a, b, tol=0.051) -> bool:
    if (a is None or np.isnan(a)) and (b is None or np.isnan(b)):
        return True
    if a is None or b is None or np.isnan(a) or np.isnan(b):
        return False
    return abs(a - b) <= tol


def parse_summary_report_appendix_a(cal_o2: dict | None = None,
                                    path: str | Path | None = None) -> pd.DataFrame:
    """Per-test fields of Summary Report Appendix A (Tables A.1–A.6) from the PDF raw text.

    `cal_o2` maps test_id -> (calibrated initial O2, calibrated final O2) from the experimental
    table; it is used to locate the 8-number gas block (cal O2 i/f, raw O2 i/f, CO2 i/f, CO i/f)
    in the row text, which has no column delimiters. Returns one row per test found (126; the
    2016 tests O20–O22 are not in the report).
    """
    path = Path(path or REPORT_TXT)
    if not path.exists():
        return pd.DataFrame()
    t = path.read_text(encoding="utf-8")
    a = t.find("TABLE A.1")
    b = t.find("Appendix B.", a)
    s = t[a:b if b > 0 else None]
    s = s.replace("–", "-").replace("—", "-").replace("−", "-")
    s = re.sub(r"\s+", " ", s)
    ms = list(_REC_RE.finditer(s))
    rows = []
    for i, m in enumerate(ms):
        body = s[m.end():ms[i + 1].start() if i + 1 < len(ms) else len(s)]
        test = m.group(2)
        row = {"test_id": test, "report_as_run_no": m.group(1) if m.group(1).isdigit() else None,
               "report_sample": m.group(3)}
        reg = _REGIME_RE.search(body)
        rest = body
        if reg:
            row["report_restrictor"] = int(reg.group(1))
            row["report_regime_label"] = reg.group(2) if reg.group(2) not in ("1",) else None
            rest = body[reg.end() - 1:]
            g = None
            for cand in _GAIN_RE.finditer(rest):
                # "max 10 ------------ 250 ----": "10" is part of the Fan text and the dashes are
                # the empty Air display; the real gain follows the dashes.
                if re.match(r"-{2,}\s+(?:1,000|1000|250|50|10)[\s,]", rest[cand.end():]):
                    continue
                g = cand
                break
            if g:
                row["report_flow_text"] = rest[:g.start()].strip()
                row["report_radiometer_gain"] = g.group(1)
                rest = rest[g.end():]
        toks = rest.split()
        ci, cf = (cal_o2 or {}).get(test, (np.nan, np.nan))
        best = None
        for k in range(len(toks) - 3):
            if not _same(_f(toks[k]), ci):
                continue
            score = 2 if _same(_f(toks[k + 1]), cf) else 1
            if best is None or score > best[0]:
                best = (score, k)
            if score == 2:
                break
        if best is not None and not np.isnan(ci):
            k = best[1]
            vals = toks[k:k + 8]
            row.update({"report_o2_cal_initial_pct": _f(vals[0]), "report_o2_cal_final_pct": _f(vals[1]),
                        "report_o2_raw_initial_pct": _f(vals[2]), "report_o2_raw_final_pct": _f(vals[3]),
                        "report_gas_block_match": "cal_i+cal_f" if best[0] == 2 else "cal_i_only"})
            obs = " " + " ".join(toks[k + 8:])
            obs = _OBS_CUT.split(obs)[0]
            obs = re.sub(r"(\s+(-{2,}|GMT\s*\S*|\d{1,2}:\d{2}(:\d{2})?|msg))+\s*$", "", obs)
            row["report_observations"] = obs.strip()
        rows.append(row)
    return pd.DataFrame(rows)


def _canon(text) -> str:
    """Normalise flow text for textual comparison of report vs xlsx cells."""
    s = (text if isinstance(text, str) else "").lower()
    for a, b in (("extinction", "ext"), ("extinguished", "ext"), ("increase", "incr"),
                 ("decrease", "decr"), ("maximum", "max"), ("ignition", "ign"), ("etc.", "etc")):
        s = s.replace(a, b)
    s = re.sub(r"-{3,}", "", s)
    s = re.sub(r"(\d)\.(?=[\s,;)]|$)", r"\1", s)
    return re.sub(r"[\s,]+", "", s)


def _split_report_flow(seg, fan_text, air_text) -> tuple[str, str]:
    """Split the report's `Fan display + Air display` text (no delimiters) into the Air part."""
    if not isinstance(seg, str) or not seg.strip():
        return "", "none"
    toks = seg.split()
    fan_c, air_c = _canon(fan_text), _canon(air_text)
    if toks and re.fullmatch(r"-{3,}", toks[-1]) and len(toks) > 1:
        return "", "air_blank"
    while toks and re.fullmatch(r"-{3,}", toks[0]):
        toks = toks[1:]
        if not fan_c:
            return " ".join(toks), "fan_blank"
    for k in range(len(toks), -1, -1):
        if air_c and _canon(" ".join(toks[k:])) == air_c:
            return " ".join(toks[k:]), "air_suffix_match"
    if fan_c:
        for k in range(1, len(toks) + 1):
            if _canon(" ".join(toks[:k])) == fan_c:
                return " ".join(toks[k:]), "fan_prefix_match"
    if not fan_c:
        return " ".join(toks), "fan_blank"
    return " ".join(toks), "unsplit_whole_segment"


def load_test_matrices(catalog_dir: str | Path | None = None) -> pd.DataFrame:
    """Concatenate data/catalog/test_matrix_<PI>.csv (export of NASA Test.Matrices.xlsx)."""
    d = Path(catalog_dir or PROJECT_ROOT / "data/catalog")
    frames = []
    for f in sorted(d.glob("test_matrix_*.csv")):
        x = pd.read_csv(f, dtype=str)
        x.columns = [re.sub(r"\s+", " ", c).strip().lower() for c in x.columns]

        def pick(start):
            return next((c for c in x.columns if c.startswith(start)), None)
        frames.append(pd.DataFrame({
            "test_id": x[pick("test no")].str.strip(),
            "xlsx_fan_display": x[pick("fan display")],
            "xlsx_air_display": x[pick("air display")],
            "xlsx_flow_restrictor": x[pick("flow restrictor")].map(_to_float),
            "xlsx_o2_initial_pct": x[pick("calibrated initial o2")].map(_to_float),
            "xlsx_o2_final_pct": x[pick("calibrated final o2")].map(_to_float),
            "xlsx_sheet": f.stem.replace("test_matrix_", ""),
        }))
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame(columns=["test_id"])


_OBS_IGN = re.compile(r"ignit\w*\s+(?:\w+\s+)?at\s+(\d+(?:\.\d+)?)(\s*cm/s)?(?![\d.])", re.I)


def _obs_ignition_cm_s(obs) -> float:
    """Ignition velocity quoted in the report observations ("Ignition at 5 cm/s", "ignited at 10")."""
    if not isinstance(obs, str):
        return np.nan
    m = _OBS_IGN.search(obs)
    if not m:
        return np.nan
    v = float(m.group(1))
    if m.group(2) or v == round(v):  # without unit, decimals are pots (T7 "ignition at 3.4")
        return v
    return np.nan


# ---------------------------------------------------------------------- regime

_REGIME_LABEL = {"Opposed": "opposed", "Concurrent": "concurrent", "Stagnation": "stagnation"}
# Fallback per PI group (bass2_dataset.md PI table; flame_spread_physics.md §1):
_REGIME_BY_PI = {"B": "opposed", "M": "opposed", "P": "opposed", "T": "concurrent",
                 "F": "concurrent", "O": "mixed"}


def _regime(test_id: str, material_class: str, report_label) -> tuple[str, str]:
    if isinstance(report_label, str) and report_label in _REGIME_LABEL:
        return _REGIME_LABEL[report_label], "summary_report_appA"
    if material_class in ("PMMA spherical section", "wax candle"):
        return "stagnation", "pi_default"
    return _REGIME_BY_PI.get(test_id[:1], "unknown"), "pi_default"


# ---------------------------------------------------------------- main loader

O2_CONVENTION = ("calibrated_mca: CSA-CP O2 reading + daily MCA offset "
                 "(Experimental table 'Calibrated initial/final O2 % by vol')")


def _join(vals) -> str:
    return ";".join(f"{v:g}" for v in vals)


def load_experimental_table(path: str | Path | None = None, write: bool = True,
                            catalog_dir: str | Path | None = None,
                            report_path: str | Path | None = None) -> pd.DataFrame:
    """Cleaned experimental table (one row per run, 129) with robust flow / O2 / regime columns.

    Writes data/catalog/experimental_table_clean.{parquet,csv} and
    data/catalog/experimental_table_validation.csv when `write`.
    """
    path = Path(path or PROJECT_ROOT / "data/docs/Experimental table_BASS-II.csv")
    raw = pd.read_csv(path, encoding="utf-8-sig", dtype=str)
    raw.columns = [re.sub(r"\s+", " ", c).strip() for c in raw.columns]
    col = {c.split(" (")[0].split("  ")[0].lower(): c for c in raw.columns}

    def g(r, key_start):
        for k, c in col.items():
            if k.startswith(key_start):
                return r[c]
        return None

    rows = []
    for _, r in raw.iterrows():
        test = str(g(r, "test")).strip()
        fan, air = g(r, "fan display"), g(r, "air display")
        restr = _to_float(g(r, "flow restrictor"))
        events = " ".join(str(x) for x in (fan, air) if isinstance(x, str)).lower()
        air_steps = _numbers_outside_parens(air)
        fp = parse_air_display(air, restr, fan)
        steps = fp["steps"]
        base = re.match(r"[A-Z]\d+", test)
        mat = _material(g(r, "fuel sample"))
        u = [U_ANEMOMETER_CORR * v for v in steps]
        rows.append({
            "test_id": test,
            "test_base": base.group() if base else test,
            "run_suffix": test[len(base.group()):] if base else "",
            "pi": g(r, "pi"),
            "date": pd.to_datetime(g(r, "date"), format="%m/%d/%Y", errors="coerce"),
            "gmt_day": _to_float(g(r, "gmt")),
            "sample_id": g(r, "sample"),
            "material_raw": g(r, "fuel sample"),
            **mat,
            "flow_restrictor": restr,
            "fan_display_raw": fan,
            "fan_steps": _numbers_outside_parens(fan),
            "fan_paren": _numbers_in_parens(fan),
            "air_display_raw": air,
            "air_steps": air_steps,            # legacy: numbers outside parentheses (NOT always cm/s)
            "air_paren": _numbers_in_parens(air),
            "flow_steps_air_display": steps,   # AIR display values (cm/s, uncorrected)
            "flow_steps_cm_s": u,              # U = 1.0066 · AIR (duct centerline)
            "flow_initial_cm_s": np.nan if (not u or fp["initial_unknown"]) else u[0],
            "flow_max_cm_s": max(u) if u else np.nan,
            "flow_min_cm_s": min(u) if u else np.nan,
            "flow_max_is_lower_bound": fp["max_lower_bound"],
            "flow_min_is_upper_bound": fp["min_upper_bound"],
            "flow_events": ";".join(fp["events"]),
            "flow_parse_rule": fp["rule"],
            "flow_parse_confidence": fp["confidence"],
            "flow_parse_notes": " | ".join(fp["notes"]),
            "radiometer_gain_raw": g(r, "radiometer gain"),
            "total_frames_raw": g(r, "total frames"),
            "o2_initial_pct": _to_float(g(r, "calibrated initial o2")),
            "o2_final_pct": _to_float(g(r, "calibrated final o2")),
            "o2_convention": O2_CONVENTION,
            "co2_initial_pct": _to_float(g(r, "initial co2")),
            "co2_final_pct": _to_float(g(r, "final co2")),
            "co_initial_ppm": _to_float(r[col["initial co"]]) if "initial co" in col else np.nan,
            "co_final_ppm": _to_float(r[col["final co"]]) if "final co" in col else np.nan,
            "extinction": bool(re.search(r"\bext|extinguish|out\b|quench", events)),
            "blowoff": "blowoff" in events,
            "no_ignition": "no ign" in events or "would not stay lit" in events,
        })
    df = pd.DataFrame(rows)
    df, val = _cross_check(df, catalog_dir, report_path)
    if write:
        out = load_config().path("catalog") / "experimental_table_clean.parquet"
        df.to_parquet(out, index=False)
        csv = df.drop(columns=["fan_steps", "fan_paren", "air_steps", "air_paren"]).copy()
        for c in ("flow_steps_air_display", "flow_steps_cm_s"):
            csv[c] = csv[c].map(lambda v: _join(v) if isinstance(v, list) else "")
        csv.to_csv(out.with_suffix(".csv"), index=False)
        val.to_csv(out.parent / "experimental_table_validation.csv", index=False)
    return df


def _cross_check(df: pd.DataFrame, catalog_dir=None, report_path=None) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Add as-run columns (xlsx matrices + Summary Report App. A) and build the validation table."""
    xl = load_test_matrices(catalog_dir).set_index("test_id")
    cal = {r.test_id: (r.o2_initial_pct, r.o2_final_pct) for r in df.itertuples()}
    rep = parse_summary_report_appendix_a(cal, report_path)
    rep = rep.set_index("test_id") if not rep.empty else pd.DataFrame()

    add, val = [], []
    for r in df.itertuples():
        tid = r.test_id
        x = xl.loc[tid] if tid in xl.index else None
        p = rep.loc[tid] if tid in rep.index else None
        restr = r.flow_restrictor
        # --- xlsx as-run
        if x is not None:
            fx = parse_air_display(x.xlsx_air_display, restr, x.xlsx_fan_display)
            xs = [] if fx["initial_unknown"] else fx["steps"]
        else:
            fx, xs = None, []
        # --- Summary Report as-run
        rs, split, rep_air = [], "", ""
        if p is not None and isinstance(p.get("report_flow_text"), str):
            rep_air, split = _split_report_flow(p["report_flow_text"], x.xlsx_fan_display if x is not None
                                                else r.fan_display_raw,
                                                x.xlsx_air_display if x is not None else r.air_display_raw)
            fr = parse_air_display(rep_air, restr, None)
            rs = [] if fr["initial_unknown"] else fr["steps"]
        o2_rep = p.get("report_o2_cal_initial_pct", np.nan) if p is not None else np.nan
        o2_xl = x.xlsx_o2_initial_pct if x is not None else np.nan
        if rs:
            flow_asrun, fsrc = U_ANEMOMETER_CORR * rs[0], "summary_report_appA"
        elif xs:
            flow_asrun, fsrc = U_ANEMOMETER_CORR * xs[0], "test_matrix_xlsx"
        else:
            flow_asrun, fsrc = np.nan, "none"
        if not np.isnan(o2_rep if o2_rep is not None else np.nan):
            o2_asrun, osrc = o2_rep, "summary_report_appA"
        elif not np.isnan(o2_xl):
            o2_asrun, osrc = o2_xl, "test_matrix_xlsx"
        else:
            o2_asrun, osrc = np.nan, "none"
        regime, rsrc = _regime(tid, r.material_class, p.get("report_regime_label") if p is not None else None)
        obs = p.get("report_observations") if p is not None else None
        obs_ign = _obs_ignition_cm_s(obs)
        add.append({
            "flow_asrun_cm_s": flow_asrun,
            "o2_asrun_pct": o2_asrun,
            "asrun_source": f"flow:{fsrc};o2:{osrc}",
            "o2_raw_csa_cp_pct": p.get("report_o2_raw_initial_pct", np.nan) if p is not None else np.nan,
            "o2_raw_csa_cp_final_pct": p.get("report_o2_raw_final_pct", np.nan) if p is not None else np.nan,
            "regime": regime,
            "regime_source": rsrc,
            "report_observations": obs,
        })

        # --- disagreements (compare AIR display units, tolerance 0.5 cm/s)
        tsteps = list(r.flow_steps_air_display)
        t0 = np.nan if (not tsteps or r.flow_parse_rule == "ramp_target_only") else tsteps[0]
        notes = []

        def cmp(name, other):
            if not other:
                return False
            if np.isnan(t0) or abs(other[0] - t0) > 0.5:
                notes.append(f"initial table={t0:g} vs {name}={other[0]:g}")
                return True
            if len(other) != len(tsteps) or any(abs(a - b) > 0.5 for a, b in zip(other, tsteps)):
                notes.append(f"steps table=[{_join(tsteps)}] vs {name}=[{_join(other)}]")
            return False
        dis_x = cmp("xlsx", xs)
        dis_r = cmp("report", rs)
        steps_dis = any(n.startswith("steps") for n in notes)
        o2_dis = False
        for name, v in (("xlsx", o2_xl), ("report", o2_rep)):
            if v is not None and not np.isnan(v) and not _same(v, r.o2_initial_pct):
                o2_dis = True
                notes.append(f"O2 table={r.o2_initial_pct:g} vs {name}={v:g}")
        rr = p.get("report_restrictor", np.nan) if p is not None else np.nan
        restr_dis = rr is not None and not np.isnan(rr) and not np.isnan(restr) and rr != restr
        if restr_dis:
            notes.append(f"restrictor table={restr:g} vs report={rr:g}")
        obs_dis = not np.isnan(obs_ign) and not np.isnan(t0) and abs(obs_ign - t0) > 0.5
        if obs_dis:
            notes.append(f"report observations quote ignition at {obs_ign:g} cm/s vs table initial {t0:g}")
        val.append({
            "test_id": tid, "pi": r.pi, "flow_restrictor": restr,
            "fan_display_raw": r.fan_display_raw, "air_display_raw": r.air_display_raw,
            "flow_parse_rule": r.flow_parse_rule, "flow_parse_confidence": r.flow_parse_confidence,
            "flow_parse_notes": r.flow_parse_notes,
            "flow_steps_air_display": _join(tsteps),
            "flow_initial_cm_s": r.flow_initial_cm_s, "flow_max_cm_s": r.flow_max_cm_s,
            "flow_min_cm_s": r.flow_min_cm_s,
            "xlsx_air_display": x.xlsx_air_display if x is not None else None,
            "xlsx_steps": _join(xs),
            "report_flow_text": p.get("report_flow_text") if p is not None else None,
            "report_air_text": rep_air, "report_split": split,
            "report_steps": _join(rs),
            "report_obs_ignition_cm_s": obs_ign,
            "flow_asrun_cm_s": flow_asrun,
            "o2_initial_pct": r.o2_initial_pct, "o2_xlsx_pct": o2_xl, "o2_report_cal_pct": o2_rep,
            "o2_raw_csa_cp_pct": add[-1]["o2_raw_csa_cp_pct"],
            "asrun_source": add[-1]["asrun_source"],
            "regime": regime, "regime_source": rsrc,
            "report_regime_label": p.get("report_regime_label") if p is not None else None,
            "flow_initial_disagree": bool(dis_x or dis_r),
            "flow_steps_disagree": bool(steps_dis),
            "o2_disagree": bool(o2_dis),
            "restrictor_disagree": bool(restr_dis),
            "obs_ignition_mismatch": bool(obs_dis),
            "disagreement": bool(dis_x or dis_r or steps_dis or o2_dis or restr_dis),
            "disagreement_notes": " | ".join(notes),
        })
    return pd.concat([df, pd.DataFrame(add, index=df.index)], axis=1), pd.DataFrame(val)
