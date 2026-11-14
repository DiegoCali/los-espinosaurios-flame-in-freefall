"""Parse the NASA/NIST reduced tables shipped with SAME-R (PSI-101).

Outputs (data/processed/):
- nasa_moment_table.csv      one row per TEM grid / moment measurement (Sample descriptions tables.docx)
- nasa_flow_aging_table.csv  reduced flow / no-flow comparison (TEMflowvsnoflow.xls)
- thermal_precipitator_map.csv  grid -> run / sample mapping and viewing notes
- coagulation_reference.csv  start/end concentrations and implied coagulation coefficient
- published_table1_baseline.csv  Table 1 of Urban et al. (2012), transcribed with citation
"""
from __future__ import annotations

import re
import shutil
import subprocess
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd

from extraction.common import MATERIALS, PROCESSED_DIR, find_raw_dir, parse_run, to_float, write_csv

DOCX = "Sample descriptions tables.docx"
FLOW_XLS = "TEMflowvsnoflow.xls"
TP_XLSX = "thermal precipitator map updated.xlsx"
COAG_DOC = "ISS Coagulation.doc"

PUBLISHED_REF = (
    "Urban DL, Ruff GA, Greenberg PS, et al. Particle Morphology and Size Results from the Smoke "
    "Aerosol Measurement Experiment-2. AIAA 2012-3536 (42nd ICES), Table 1. NTRS 20130000422."
)


# --------------------------------------------------------------------------- moment table (docx)
def _flow_regime(text: str) -> str:
    t = text.lower()
    if "no flow" in t:
        return "no_flow"
    if "low flow" in t:
        return "low_flow"
    return "nominal_flow"


def _temperature_regime(text: str) -> str:
    t = text.lower()
    if "mid high" in t:
        return "mid_high"
    if "high" in t:
        return "high"
    if "mid" in t:
        return "mid"
    if "low temp" in t:
        return "low"
    return "baseline"


def _tem_particles_seen(morph: str) -> bool:
    t = morph.strip().lower()
    return not re.match(r"^(no |no$|again, no|very few|extremely few|not enough|some ‘junk’|torn|some debris)", t)


def parse_moment_table(raw: Path, tp_map: pd.DataFrame) -> pd.DataFrame:
    import docx  # python-docx

    table = docx.Document(str(raw / DOCX)).tables[0]
    rows = []
    for r_i, row in enumerate(table.rows[1:], start=1):
        c = [cell.text.strip().replace("\n", " ") for cell in row.cells]
        rows.append({
            "source_row": r_i,
            "precipitator": int(to_float(c[0])),
            "run": parse_run(c[1]),
            "material": c[2],
            "aged_label_raw": c[3],
            "tem_date": c[4],
            "description": c[5],
            "rt_r0_raw": to_float(c[6]),
            "morphology": c[7].replace("m)", "µm)").replace("1.0m", "1.0µm"),
            "m0_per_cc_raw": to_float(c[10]),
            "amd_um_raw": to_float(c[11]),
            "dm_um_raw": to_float(c[12]),
            "sigma_g_hc_raw": to_float(c[13]),
        })
    df = pd.DataFrame(rows)

    # Rt/R0 is written once per run; later grid rows of the same run inherit it.
    df["rt_r0"] = df.groupby("run")["rt_r0_raw"].transform(lambda s: s.ffill().bfill())

    # Aging state of each grid: explicit docx label, else the precipitator map label, else order.
    tp_age = (tp_map.dropna(subset=["grid_age"]).groupby("run")["grid_age"].apply(list).to_dict())
    states, sources = [], []
    for run, grp in df.groupby("run", sort=False):
        labels = grp["aged_label_raw"].str.lower().tolist()
        norm = ["aged" if l == "aged" else "unaged" if l == "unaged" else None for l in labels]
        tp = tp_age.get(run, [])
        conflict = len(grp) == 2 and norm[0] is not None and norm[0] == norm[1]
        for k, idx in enumerate(grp.index):
            if norm[k] is not None and not conflict:
                st, src = norm[k], "docx_label"
            elif len(tp) == len(grp) and len(grp) > 1:
                st = "unaged" if tp[k] == "preage" else "aged"
                src = "precipitator_map_order" + ("_docx_label_conflict" if conflict else "")
            elif len(grp) == 2:
                st, src = ("unaged", "aged")[k], "row_order_within_run"
            else:
                st, src = "unknown", "no_label"
            states.append((idx, st))
            sources.append((idx, src))
    df["aged_state"] = pd.Series(dict(states))
    df["aged_state_source"] = pd.Series(dict(sources))

    df["flow_regime_doc"] = df["description"].map(_flow_regime)
    df["temperature_regime_doc"] = df["description"].map(_temperature_regime)
    df["tem_particles_seen"] = df["morphology"].map(_tem_particles_seen)

    # Quality control of the reduced values.
    flags = [[] for _ in range(len(df))]
    m0, amd, dm, sg = (df[c].copy() for c in ["m0_per_cc_raw", "amd_um_raw", "dm_um_raw", "sigma_g_hc_raw"])
    for i in range(len(df)):
        if np.isnan(m0[i]):
            flags[i].append("m0_missing")
        if not np.isnan(amd[i]) and amd[i] > 2.0:
            flags[i].append("amd_out_of_range_likely_unit_or_typo")
            amd[i] = np.nan
        if not np.isnan(dm[i]) and dm[i] <= 0:
            flags[i].append("dm_zero")
            dm[i] = np.nan
        if not np.isnan(sg[i]) and (sg[i] > 4.0 or sg[i] < 1.0):
            flags[i].append("sigma_g_out_of_range")
            sg[i] = np.nan
        if not (np.isnan(amd[i]) or np.isnan(dm[i])) and dm[i] < amd[i]:
            flags[i].append("dm_below_amd_not_lognormal_consistent")
    df["m0_per_cc"] = m0
    df["amd_um"] = amd
    df["dm_um"] = dm
    df["sigma_g_hc"] = sg

    # Derived log-normal quantities (Hatch-Choate, p=0.5 for AMD, p=1.5 for Dm).
    ln2 = np.log(df["sigma_g_hc"]) ** 2
    df["dg_um_from_amd"] = df["amd_um"] / np.exp(0.5 * ln2)
    df["dg_um_from_dm"] = df["dm_um"] / np.exp(1.5 * ln2)
    ratio = df["dm_um"] / df["amd_um"]
    df["sigma_g_from_ratio"] = np.where(ratio > 1, np.exp(np.sqrt(np.log(ratio.where(ratio > 1)))), np.nan)
    df["m1_um_per_cc"] = df["m0_per_cc"] * df["amd_um"]
    df["m3_um3_per_cc"] = df["m0_per_cc"] * df["dm_um"] ** 3
    df["qc_flags"] = [";".join(f) for f in flags]
    df["usable_size_stats"] = df[["amd_um", "dm_um", "sigma_g_hc", "m0_per_cc"]].notna().all(axis=1) & ~df[
        "qc_flags"].str.contains("not_lognormal")
    df["source_file"] = DOCX
    return df


# --------------------------------------------------------------------------- flow / aging table (xls)
def parse_flow_table(raw: Path) -> pd.DataFrame:
    t = pd.read_excel(raw / FLOW_XLS, sheet_name=0, header=None)
    names = ["flight", "material", "same_id", "description", "inlet_velocity_cm_s", "rt_r0", "net_aging_s",
             "m0_per_cc", "m1_mm_per_cc", "dusttrak_b_mg_m3", "amd_um", "dm_um", "mpass_3_2", "sigma_g_hc",
             "dg_um_hc", "ion_b_moment_mm_per_cc", "tem_max_diam_um", "tem_bg_diam_um", "tem_shape",
             "tem_distribution"]
    d = t.iloc[2:, :20].copy()
    d.columns = names
    d = d[d["same_id"].notna()].reset_index(drop=True)
    d["same_id"] = d["same_id"].astype(str).str.strip()
    d["run"] = d["same_id"].str.extract(r"(\d+)").astype(int)
    d["aged_state"] = np.where(d["same_id"].str.endswith("a"), "aged", "unaged")  # "a" suffix = aged grid
    d["flight"] = d["flight"].ffill()
    for c in names[4:18]:
        if c not in ("tem_shape", "tem_distribution"):
            d[c] = d[c].map(to_float)
    d["mpass_3_2"] = d["mpass_3_2"].where(d["mpass_3_2"] > 0)  # 0 means not recorded
    d["material"] = d["material"].astype(str).str.strip()
    d["source_file"] = FLOW_XLS
    return d


# --------------------------------------------------------------------------- precipitator map
def parse_tp_map(raw: Path) -> pd.DataFrame:
    tp = pd.read_excel(raw / TP_XLSX, header=None)
    blocks = []  # (row, col, precipitator)
    for (r, c), v in tp.stack().items():
        if isinstance(v, str) and (m := re.match(r"Thermal Precipitator (\d)", v)):
            blocks.append((r, c, int(m.group(1))))
    rows = []
    for (r, c), v in tp.stack().items():
        if not (isinstance(v, str) and "SAMERFLT" in v):
            continue
        # The owning block: same column band (c in [blk_c, blk_c+2]) and nearest header row above.
        cand = [b for b in blocks if b[0] < r and b[1] <= c <= b[1] + 2]
        blk = max(cand, key=lambda b: b[0])
        m = re.search(r"SAMERFLT\s*(\d+)\s*([A-Z])", v)
        note = tp.iat[r, c - 1] if c >= 1 else None
        low = v.lower()
        rows.append({
            "precipitator": blk[2],
            "slot": int(tp.iat[r, blk[1] - 2]) if pd.notna(tp.iat[r, blk[1] - 2]) else None,
            "side": "A" if c == blk[1] else "B",
            "label": v.strip(),
            "run": parse_run(v),
            "sample_id": f"{m.group(1)}{m.group(2)}" if m else None,
            "material": MATERIALS.get(m.group(2)) if m else None,
            "grid_age": "preage" if "preage" in low else "postage" if "postage" in low else None,
            "viewing_note": str(note).strip() if isinstance(note, str) else None,
            "source_file": TP_XLSX,
        })
    out = pd.DataFrame(rows).sort_values(["precipitator", "side", "slot"]).reset_index(drop=True)
    # Within a run keep preage before postage so that row order is meaningful.
    out["_o"] = out["grid_age"].map({"preage": 0, "postage": 1}).fillna(0)
    return out.sort_values(["run", "_o"]).drop(columns="_o").reset_index(drop=True)


# --------------------------------------------------------------------------- coagulation doc
COAG_TRANSCRIPTION = [
    ("Lampwick", 2.833e6, 0.138, 1.96e6, 126.0),
    ("Lampwick", 2.65e6, 0.112, 1.83e6, 134.0),
    ("Teflon", 2.63e6, 0.160, 2.28e6, 35.0),
]


def _doc_text(path: Path) -> str | None:
    exe = shutil.which("soffice") or shutil.which("libreoffice")
    if not exe:
        return None
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run([exe, "--headless", "--convert-to", "txt:Text", str(path), "--outdir", tmp],
                       check=False, capture_output=True, timeout=120)
        out = list(Path(tmp).glob("*.txt"))
        return out[0].read_text(encoding="utf-8-sig", errors="ignore") if out else None


def parse_coagulation(raw: Path) -> pd.DataFrame:
    text = _doc_text(raw / COAG_DOC)
    pat = re.compile(r"(\w+)\s+Starting number conc\.\s*([\d.]+e\d+).*?diameter\s+([\d.]+)\s*micrometers.*?"
                     r"Ending number concentration\s*([\d.]+e\d+).*?Coagulation time\s*=\s*([\d.]+)", re.S | re.I)
    recs, method = [], "parsed_with_libreoffice"
    if text:
        recs = [(m[0], float(m[1]), float(m[2]), float(m[3]), float(m[4])) for m in pat.findall(text)]
    if not recs:
        recs, method = COAG_TRANSCRIPTION, "manual_transcription_fallback"
    df = pd.DataFrame(recs, columns=["material", "n_start_per_cc", "amd_start_um", "n_end_per_cc", "time_s"])
    # Smoluchowski with constant kernel: 1/N - 1/N0 = K t
    df["k_coag_cm3_s"] = (1 / df["n_end_per_cc"] - 1 / df["n_start_per_cc"]) / df["time_s"]
    df["method"] = method
    df["source_file"] = COAG_DOC
    return df


# --------------------------------------------------------------------------- published table 1
def published_table1() -> pd.DataFrame:
    mats = ["Kapton", "Lampwick", "Silicone", "Teflon", "Pyrell"]
    dg = [0.042, 0.089, 0.090, 0.229, 0.128, 0.269, 0.081, 0.070, 0.149, 0.293]
    amd = [0.056, 0.109, 0.128, 0.276, 0.196, 0.355, 0.101, 0.105, 0.204, 0.359]
    dm = [0.101, 0.161, 0.258, 0.398, 0.465, 0.619, 0.170, 0.232, 0.384, 0.539]
    sg = [2.154, 1.872, 2.312, 1.834, 2.530, 2.108, 2.198, 2.442, 2.211, 1.892]
    rows = []
    for i in range(10):
        rows.append({"material": mats[i // 2], "aged_state": ("unaged", "aged")[i % 2],
                     "aging_s_nominal": (None, 720)[i % 2], "dg_um": dg[i], "amd_um": amd[i], "dm_um": dm[i],
                     "sigma_g": sg[i], "source": PUBLISHED_REF})
    return pd.DataFrame(rows)


def run(raw_dir: Path | None = None) -> dict[str, pd.DataFrame]:
    raw = find_raw_dir(raw_dir)
    tp = parse_tp_map(raw)
    out = {
        "thermal_precipitator_map": tp,
        "nasa_moment_table": parse_moment_table(raw, tp),
        "nasa_flow_aging_table": parse_flow_table(raw),
        "coagulation_reference": parse_coagulation(raw),
        "published_table1_baseline": published_table1(),
    }
    for name, df in out.items():
        write_csv(df, PROCESSED_DIR / f"{name}.csv")
    return out


if __name__ == "__main__":
    for k, v in run().items():
        print(k, v.shape)
