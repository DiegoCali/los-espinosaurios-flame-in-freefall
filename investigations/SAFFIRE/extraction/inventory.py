"""Inventory files and ZIP central directories without expanding image payloads."""
from __future__ import annotations
import argparse
import hashlib
import json
import re
import subprocess
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from pathlib import Path
from zipfile import ZipFile
from extraction.common import RAW, INVENTORY, write_csv, write_json, source_path

def file_hash(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        while block := handle.read(8 * 1024 * 1024):
            digest.update(block)
    return digest.hexdigest()

def verify_integrity(full=False):
    original = json.loads((INVENTORY / "raw_integrity_initial.json").read_text())
    current = {source_path(p): p for p in RAW.rglob("*") if p.is_file()}
    if set(current) != {r["path"] for r in original}:
        raise RuntimeError("Raw file list changed")
    for row in original:
        path = current[row["path"]]
        stat = path.stat()
        if stat.st_size != row["size_bytes"] or stat.st_mtime_ns != row["mtime_ns"]:
            raise RuntimeError(f"Raw metadata changed: {path}")
        if full and file_hash(path) != row["sha256"]:
            raise RuntimeError(f"Raw content changed: {path}")
    return {"n_files": len(original), "verification": "sha256_all_files" if full else "size_and_mtime_all_files", "unchanged": True}

def write_inventory_markdown(summary):
    """Render the inventory explanation in English without reading raw payloads."""
    lines = [
        "# Saffire inventory", "",
        f"{summary['n_files']} physical files; {summary['total_size_gb']:.3f} decimal GB, including two redundant delivery containers.", "",
        "Only Saffire-II has local raw test data: specimens II-1 through II-9. F1/F2 are pre/post-flow sets, and BIT is an equipment check. Image variants are not experimental replicates.", "",
        "The metadata ZIP declares `Study Identifier PSI-99`, DOI 10.60555/2chp-m469.", "",
        "## Observed variables", "", ", ".join(summary["variables_found"]), "",
        "The `Calibrated Data` worksheets provide headers and units: gas fractions in %, pressure in PSIA, flow in cm/s, radiation in mW/cm2 and temperature in degrees C. Stored Excel values are read without executing formulas. Zero-filled Cygnus entries are excluded.", "",
        "## Missing or ambiguous information", "",
    ]
    lines += ["- " + item for item in summary["missing_or_ambiguous"]]
    lines += [
        "", "## Provenance decisions", "",
        "Flow and pressure use pre-ignition measurements. Material, nominal thickness and outcomes use the postflight table. Empty material cells for II-6 and II-9 are inherited and corroborated by documentation. The CSV text `037 mm` is interpreted as 0.37 mm. Measured II-6 flow is near 25 cm/s, versus 20 in the CSV and 30 in planning documents. SFS-W-009 gives SIBAL B thermocouple heights of 4.445 and 3.175 mm; their peaks are not used to infer spread rates.", "",
        "`inventory.csv` lists every physical file and initial SHA-256. `archives.csv` counts ZIP members without expanding image payloads. `raw_integrity_initial.json` preserves the original size, modification time and hash for each file. The completed experiment included full SHA-256 verification; later documentation work checks that raw file sizes and modification times remain unchanged.", "",
        "The derived ignitor energy has an unresolved voltage/current scaling discrepancy. Its magnitude is unvalidated and was not a model input. See `data/processed/VALIDATION.md` and the English analysis reports.", "",
        'Dataset source: Urban DL, Ruff G. "Spacecraft Fire Experiment-II(SAFFIRE-II)", NASA PSI Data Repository, Version 5, [http://doi.org/10.60555/2chp-m469](http://doi.org/10.60555/2chp-m469).', "",
    ]
    (INVENTORY / "INVENTORY.md").write_text("\n".join(lines), encoding="utf-8")


def run():
    INVENTORY.mkdir(parents=True, exist_ok=True)
    hashes = {r["path"]: r for r in json.loads((INVENTORY / "raw_integrity_initial.json").read_text())}
    verify_integrity()
    rows, archives = [], []
    checksums = defaultdict(list)
    image_counts = Counter()
    for path in sorted(RAW.rglob("*")):
        if not path.is_file():
            continue
        rel, name = source_path(path), path.name
        match = re.search(r"S(\d)C[12]|Sample (\d)", name)
        trial = f"II-{next(g for g in match.groups() if g)}" if match else ""
        if path.suffix == ".xlsx":
            description = "Calibrated sensor series" if "Sensor" in name else "Cygnus cabin/smoke telemetry; ambiguous clock alignment" if "Telemetry" in name else "Image timestamp and received-image manifest"
        elif path.suffix == ".csv":
            description = "Nine postflight conditions and material outcomes; transcription errors"
        elif path.suffix == ".docx":
            description = "Telemetry plots" if "Graphs" in name else "Dataset description, preflight sample table and diagnostics"
        elif path.suffix == ".pdf":
            description = "Documentation, preflight design, image nomenclature or thermocouple waiver"
        elif name in ("part-01.zip", "part-02.zip"):
            description = "Redundant delivery container; expanded contents already present"
        elif "Distortion" in name:
            description = "Preflight camera calibration grids; not a fire test"
        elif "metadata" in name:
            description = "Study PSI-99 metadata; filename also contains historical PSI-167"
        else:
            description = "Camera images; converted/remapped variants of the same tests"
        if path.suffix == ".zip":
            with ZipFile(path) as z:
                members = [i for i in z.infolist() if not i.is_dir()]
                counts = Counter(Path(i.filename).suffix.lower() for i in members)
                archives.append({"source_file": rel, "n_members": len(members), "uncompressed_bytes": sum(i.file_size for i in members), "extensions": json.dumps(dict(sorted(counts.items()))), "method": "zip_central_directory_only"})
                if name not in ("part-01.zip", "part-02.zip"):
                    image_counts.update(counts)
        digest = hashes[rel]["sha256"]
        checksums[digest].append(rel)
        rows.append({"path": rel, "size_bytes": path.stat().st_size, "type": path.suffix.lstrip("."), "mission": "Saffire-II", "test_id_inferred": trial, "description": description, "sha256": digest, "method": "metadata; filename_inference; initial_streaming_sha256"})
    write_csv(INVENTORY / "inventory.csv", rows)
    write_csv(INVENTORY / "archives.csv", archives)
    summary = {"n_files": len(rows), "total_size_gb": sum(r["size_bytes"] for r in rows) / 1e9, "missions_found": ["Saffire-II"], "tests_found": [f"II-{i}" for i in range(1,10)], "n_independent_tests": 9, "file_types": dict(sorted(Counter(r["type"] for r in rows).items())), "archive_image_variant_counts": dict(sorted(image_counts.items())), "exact_duplicate_file_groups": [v for v in checksums.values() if len(v)>1], "redundant_outer_containers": ["part-01.zip", "part-02.zip"], "variables_found": ["CO2_pct", "O2_pct", "flow_cm_s", "pressure_psia", "radiation_mW_cm2", "plume_temperature_C", "sample_temperature_C", "humidity_pct", "inlet_temperature_C", "igniter_current_A", "igniter_voltage_V", "fan_speed_rpm", "camera_timestamp_ms", "cabin_pressure_psi", "cabin_temperature_C", "smoke_obscuration_V", "smoke_scatter_V"], "identified_psi_investigation": "PSI-99", "missing_or_ambiguous": ["No raw tests from Saffire I, III, IV, V or VI", "CO, acid gases, particle mass, alarm thresholds and exposure limits unavailable", "No inlet/outlet O2 pair, exhaust mass flow, or validated mixed cabin volume for HRR", "Preflight and postflight thicknesses and sample-6 flow disagree", "Published O2 is CO2-derived; sensor O2 fluctuates; no atmosphere-response fit is supported", "Grooved sample-8 effective thickness undefined", "Radiometers have different views of samples; local flux is not total power", "Repeated image variants and zero-filled cabin telemetry require filtering", "Cygnus and Saffire clocks cannot be assigned per-test reliably from cached alignment columns"]}
    summary["n_flights"]=1
    summary["independence_note"]="Nine distinct ignition records in a single shared cabin; not independent flight replicates"
    write_json(INVENTORY / "summary.json", summary)
    text_dir = INVENTORY / "document_text"
    text_dir.mkdir(exist_ok=True)
    for path in sorted(RAW.rglob("*.pdf")):
        subprocess.run(["pdftotext", "-layout", str(path), str(text_dir / (path.stem + ".txt"))], check=True)
    for path in sorted(RAW.rglob("*.docx")):
        with ZipFile(path) as z:
            root = ET.fromstring(z.read("word/document.xml"))
            ns = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
            paragraphs = ["".join(n.text or "" for n in p.iter(ns + "t")) for p in root.iter(ns + "p")]
            (text_dir / (path.stem + ".txt")).write_text("\n".join(paragraphs)+"\n", encoding="utf-8")
    write_inventory_markdown(summary)
    return summary

if __name__ == "__main__":
    p=argparse.ArgumentParser();p.add_argument("--verify-full",action="store_true");a=p.parse_args()
    print(verify_integrity(full=True) if a.verify_full else run())
