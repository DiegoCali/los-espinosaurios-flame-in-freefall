"""Inventory of the raw SAME-R (PSI-101) files: category, run/sample mapping and hashes."""
from __future__ import annotations

import re
import zipfile
from pathlib import Path

import pandas as pd

from extraction.common import INVENTORY_DIR, MATERIALS, find_raw_dir, sha256_file, sha256_partial, write_csv

FULL_HASH_LIMIT = 64 * 1024 * 1024
SAMPLE_TO_RUN_OFFSET = 47  # SAMERFLT sample n <-> run n + 47 (verified on every labelled file)

CATEGORY_RULES = [
    (r"^HKPData_gmt\d+_\d+\.csv$", "housekeeping_timeseries", "1 Hz instrument and control telemetry for one test"),
    (r"^2010_\d+_.*\.xls$", "run_spreadsheet", "Housekeeping copy for one run plus the analyst's plotting sheet"),
    (r"^Sample descriptions tables\.docx$", "reduced_moment_table", "NASA/NIST per-grid moment results and TEM notes"),
    (r"^TEMflowvsnoflow\.xls$", "reduced_moment_table", "Reduced moments, inlet velocity and net aging for flow/no-flow runs"),
    (r"^thermal precipitator map.*\.xlsx$", "precipitator_map", "TEM grid to run/sample mapping and viewing notes"),
    (r"^ISS Coagulation\.doc$", "coagulation_reference", "Start/end concentration and coagulation time examples"),
    (r"binneddatacorr|^55 Lampwick\.xlsx$|^SPV of", "tem_particle_sizing", "Per-particle TEM image analysis and binned statistics"),
    (r"VPRED|Verification Plan", "engineering_document", "Verification plan and engineering requirements"),
    (r"\.mp4$|vlc-record", "video", "Downlinked MSG video"),
    (r"\.tif$", "tem_image", "Single TEM micrograph"),
    (r"\.pptx$|\.pdf$", "tem_presentation", "TEM image presentation for one grid"),
    (r"\.zip$", "tem_image_archive", "Archive of TEM micrographs for one grid"),
]


def classify(name: str) -> tuple[str, str]:
    for pat, cat, desc in CATEGORY_RULES:
        if re.search(pat, name, flags=re.I):
            return cat, desc
    return "other", ""


def parse_names(name: str, category: str) -> dict:
    out = {"run": None, "sample_id": None, "material": None, "grid_age": None, "label_flags": ""}
    if category in {"housekeeping_timeseries", "video", "engineering_document", "coagulation_reference",
                    "precipitator_map", "reduced_moment_table"}:
        return out
    stem = Path(name).stem
    m = re.search(r"(?<![\d])(\d{1,2})\s*([KLPSTklpst])(?![a-z])", stem)
    first = re.search(r"^[#\s]*(?:Run\s*)?0*(\d{1,3})", stem)
    run_first = int(first.group(1)) if first else None
    first_is_run = run_first is not None and 48 <= run_first <= 110
    if m and not (first_is_run and int(m.group(1)) == run_first):
        n, letter = int(m.group(1)), m.group(2).upper()
        out["sample_id"] = f"{n}{letter}"
        out["material"] = MATERIALS.get(letter)
        run_s = n + SAMPLE_TO_RUN_OFFSET
        # A plausible leading run number wins; the sample code is a secondary check.
        out["run"] = run_first if first_is_run else run_s
        if first_is_run and run_first != run_s:
            out["label_flags"] = f"run_{run_first}_but_sample_code_implies_{run_s}"
    elif first_is_run:
        out["run"] = run_first
    for word in ("lampwick", "kapton", "teflon", "pyrell", "silicone", "silcon"):
        if word in name.lower() and out["material"] is None:
            out["material"] = {"silcon": "Silicone"}.get(word, word.capitalize())
    low = name.lower()
    if re.search(r"pre[\s_-]*age|preage|\bpre\b", low):
        out["grid_age"] = "preage"
    elif re.search(r"post[\s_-]*age|postage|\bpost\b", low):
        out["grid_age"] = "postage"
    if "mislabel" in low or "mis labeled" in low or "wrong" in low:
        out["label_flags"] = (out["label_flags"] + ";" if out["label_flags"] else "") + "source_label_warning"
    return out


def zip_summary(path: Path) -> tuple[int | None, int | None]:
    try:
        with zipfile.ZipFile(path) as z:
            names = [i.filename for i in z.infolist() if not i.is_dir()]
        img = sum(1 for n in names if re.search(r"\.(tif|tiff|jpg|jpeg|png|bmp|dm3)$", n, re.I))
        return len(names), img
    except (zipfile.BadZipFile, OSError):
        return None, None


def build_inventory(raw_dir: Path | None = None, hashes: bool = True) -> pd.DataFrame:
    raw = find_raw_dir(raw_dir)
    rows = []
    for p in sorted(raw.iterdir()):
        if not p.is_file():
            continue
        cat, desc = classify(p.name)
        info = parse_names(p.name, cat)
        size = p.stat().st_size
        row = {"file": p.name, "category": cat, "description": desc, "size_bytes": size, **info}
        if p.suffix.lower() == ".zip":
            row["zip_entries"], row["zip_images"] = zip_summary(p)
        if hashes:
            if size <= FULL_HASH_LIMIT:
                row["sha256"], row["hash_kind"] = sha256_file(p), "full"
            else:
                row["sha256"], row["hash_kind"] = sha256_partial(p), "size+first+last_MiB"
        rows.append(row)
    return pd.DataFrame(rows)


def write_inventory(df: pd.DataFrame, raw_dir: Path) -> None:
    INVENTORY_DIR.mkdir(parents=True, exist_ok=True)
    write_csv(df, INVENTORY_DIR / "files.csv")
    by_cat = df.groupby("category").agg(files=("file", "count"), size_mb=("size_bytes", lambda s: s.sum() / 1e6))
    runs = sorted({int(r) for r in df["run"].dropna()})
    lines = [
        "# SAME-R raw data inventory (PSI-101)",
        "",
        f"Source folder: `{raw_dir.name}/` ({len(df)} files, {df.size_bytes.sum() / 1e9:.2f} GB). "
        "Files are read-only inputs; nothing in the raw folder is modified.",
        "",
        "| Category | Files | Size (MB) |",
        "|---|---:|---:|",
    ]
    lines += [f"| {c} | {int(r.files)} | {r.size_mb:.1f} |" for c, r in by_cat.iterrows()]
    lines += [
        "",
        f"Runs referenced by TEM file names: {', '.join(map(str, runs))}.",
        "",
        "Name parsing rule: the SAMERFLT sample number plus 47 equals the run number "
        "(e.g. `53T` = run 100). Files whose leading number disagrees, or that the source "
        "itself labels as wrong/mislabeled, are flagged in `label_flags`.",
        "",
        "Hashes: SHA-256 of the whole file up to 64 MB; for larger videos/archives the hash covers "
        "file size plus the first and last MiB (`hash_kind`).",
    ]
    flagged = df[df.label_flags.fillna("") != ""]
    if len(flagged):
        lines += ["", "## Label warnings", ""]
        lines += [f"- `{r.file}`: {r.label_flags}" for r in flagged.itertuples()]
    (INVENTORY_DIR / "INVENTORY.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    raw = find_raw_dir()
    inv = build_inventory(raw)
    write_inventory(inv, raw)
    print(inv.category.value_counts().to_string())
