"""Shared paths, constants and helpers for the SAME / SAME-R extraction.

Raw NASA files are never modified. They are located, in priority order, at:

1. the directory given by the ``SAME_RAW_DATA`` environment variable;
2. ``investigations/SAME/data/raw/`` when it contains housekeeping CSVs;
3. the repository-level ``data/`` folder (git-ignored), when it contains them.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
from pathlib import Path

import numpy as np
import pandas as pd

MODULE_DIR = Path(__file__).resolve().parents[1]
REPO_DIR = MODULE_DIR.parents[1]
DATA_DIR = MODULE_DIR / "data"
PROCESSED_DIR = DATA_DIR / "processed"
INVENTORY_DIR = DATA_DIR / "inventory"
FIGURES_DIR = PROCESSED_DIR / "figures"
ANALYSIS_OUT = MODULE_DIR / "analysis" / "output"

# Sample-code letter -> material (SAMERFLT <n><letter>, e.g. "31L").
MATERIALS = {
    "K": "Kapton",
    "L": "Lampwick",
    "P": "Pyrell",
    "S": "Silicone",
    "T": "Teflon",
    "D": "DBP",
}
MATERIAL_ORDER = ["Kapton", "Lampwick", "Pyrell", "Silicone", "Teflon"]
MATERIAL_DESCRIPTION = {
    "Kapton": "Polyimide film (wire insulation)",
    "Lampwick": "Cellulose (cotton lamp wick)",
    "Pyrell": "Polyurethane foam (Pyrell)",
    "Silicone": "Silicone rubber",
    "Teflon": "PTFE (Teflon wire insulation)",
    "DBP": "Dibutyl phthalate on a porous wick (reference aerosol)",
}

# Nominal duct velocity reported by NASA/NIST for the baseline flow (TEMflowvsnoflow.xls,
# "Inlet Velocity" = 8.1 cm/s). The aging-chamber fill flow measured by the MFC during the
# heating period (~4.3 LPM) is mapped linearly to that anchor.
NOMINAL_VELOCITY_CM_S = 8.1
NOMINAL_FILL_FLOW_LPM = 4.29

# Housekeeping channels kept in the cleaned time series (raw name -> clean name).
HKP_CHANNELS = {
    "Time": "unix_time_s",
    "TestNumber": "test",
    "RunMode": "run_mode",
    "EventCode": "event_code",
    "HeatingInProgress": "heating",
    "GasPlumeTemperature(DegC)": "gas_plume_temp_c",
    "SampleResistance(Ohms)": "sample_resistance_ohm",
    "MFCMassFlowRate(LPM)": "mfc_flow_lpm",
    "LFEFlowRate[AT08](SCCM)": "lfe_flow_sccm",
    "PTrakMeasurement(PtPerCC)": "ptrak_raw_pt_cc",
    "DustTrakBMeasurement(MgPerM3)": "dusttrak_b_mg_m3",
    "DustTrakAMeasurement(MgPerM3)": "dusttrak_a_raw",
    "IonDetectorAMeasurement(Volts)": "ion_a_v",
    "IonDetectorBMeasurement(Volts)": "ion_b_v",
    "ISSDetectorScatterMeasurement(Volts)": "iss_scatter_v",
    "ISSDetectorObscurationMeasurement(Volts)": "iss_obscuration_v",
    "STSDetectorMeasurement(Volts)": "sts_v",
    "STSDetectorAlarm": "sts_alarm",
    "STSDetectorPower": "sts_power",
    "PistonVacuumSolenoid[BN16]": "piston_fill",
    "PistonGN2Solenoid[BN18]": "piston_push",
    "DynamicDilutorSolenoid[PN15]": "dynamic_diluter",
    "PTrakSolenoid[VR06]": "ptrak_valve",
    "ThermalPrecipitatorPreAgeHeater": "tp_preage_heater",
    "ThermalPrecipitatorPostAgeHeater": "tp_postage_heater",
    "MixingFanPower": "mixing_fan",
}


def find_raw_dir(explicit: str | os.PathLike | None = None) -> Path:
    candidates = []
    if explicit:
        candidates.append(Path(explicit))
    if os.environ.get("SAME_RAW_DATA"):
        candidates.append(Path(os.environ["SAME_RAW_DATA"]))
    candidates += [DATA_DIR / "raw", REPO_DIR / "data"]
    for c in candidates:
        if c.is_dir() and any(c.glob("HKPData_gmt*.csv")):
            return c.resolve()
    raise FileNotFoundError(
        "SAME-R raw data not found. Put the PSI-101 files in investigations/SAME/data/raw/ "
        "or set SAME_RAW_DATA. See data/raw/README.md for the required file list."
    )


def sha256_file(path: Path, chunk: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(chunk), b""):
            h.update(block)
    return h.hexdigest()


def sha256_partial(path: Path, span: int = 1 << 20) -> str:
    """Hash of size + first and last MiB; used for multi-hundred-MB videos."""
    h = hashlib.sha256()
    size = path.stat().st_size
    h.update(str(size).encode())
    with open(path, "rb") as f:
        h.update(f.read(span))
        if size > span:
            f.seek(max(size - span, span))
            h.update(f.read(span))
    return h.hexdigest()


def rel(path: Path, base: Path | None = None) -> str:
    base = base or MODULE_DIR
    try:
        return str(Path(path).resolve().relative_to(base))
    except ValueError:
        return Path(path).name


def to_float(v) -> float:
    """Parse a spreadsheet/table cell to float; thousands separators allowed; else NaN."""
    if v is None:
        return np.nan
    if isinstance(v, (int, float, np.number)):
        return float(v)
    s = str(v).strip().replace(",", "").replace(" ", "")
    if s in {"", "#", "?", "n/a", "NA", "-"}:
        return np.nan
    try:
        return float(s)
    except ValueError:
        return np.nan


def parse_run(text: str) -> int | None:
    m = re.search(r"#?\s*(\d{2,3})\b", str(text))
    return int(m.group(1)) if m else None


def jsonable(o):
    if isinstance(o, dict):
        return {str(k): jsonable(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [jsonable(v) for v in o]
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating, float)):
        return None if not np.isfinite(o) else float(o)
    if isinstance(o, np.bool_):
        return bool(o)
    if isinstance(o, Path):
        return str(o)
    if o is pd.NA or o is pd.NaT:
        return None
    return o


def write_json(path: Path, obj, indent: int = 2) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(jsonable(obj), indent=indent, ensure_ascii=False) + "\n", encoding="utf-8")


def write_csv(df: pd.DataFrame, path: Path, **kw) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False, float_format="%.6g", **kw)
