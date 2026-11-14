"""Configuration loading and project paths."""
from __future__ import annotations

import copy
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[2]  # investigations/BASS-II
CONFIG_DIR = PROJECT_ROOT / "configs"


def _deep_update(base: dict, upd: dict) -> dict:
    out = copy.deepcopy(base)
    for k, v in (upd or {}).items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _deep_update(out[k], v)
        else:
            out[k] = v
    return out


def load_yaml(path: str | Path) -> dict:
    with open(path, encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


@dataclass
class Config:
    raw: dict

    def __getitem__(self, key: str) -> Any:
        return self.raw[key]

    def get(self, key: str, default: Any = None) -> Any:
        return self.raw.get(key, default)

    def path(self, key: str) -> Path:
        """Absolute path for a `paths:` entry (created if missing)."""
        p = PROJECT_ROOT / self.raw["paths"][key]
        p.mkdir(parents=True, exist_ok=True)
        return p

    def with_overrides(self, overrides: dict | None) -> "Config":
        return Config(_deep_update(self.raw, overrides or {}))


def load_config(path: str | Path | None = None, overrides: dict | None = None) -> Config:
    cfg = load_yaml(path or CONFIG_DIR / "pipeline.yaml")
    return Config(_deep_update(cfg, overrides or {}))


def test_calibration(test_id: str) -> dict:
    """Calibration for one test with defaults applied.

    Priority for mm_per_px: explicit value in configs/calibration.yaml > geometric ruler calibration in
    data/catalog/spatial_calibration.csv (scripts/calibrate_study.py; per-test ruler or global fixed-FOV
    camera scale) > None (metrics stay in px).
    """
    cal = load_yaml(CONFIG_DIR / "calibration.yaml")
    out = dict(cal.get("defaults", {}))
    out.update((cal.get("tests") or {}).get(test_id, {}) or {})
    if not out.get("mm_per_px"):
        p = PROJECT_ROOT / "data/catalog/spatial_calibration.csv"
        if p.exists():
            import pandas as pd
            d = pd.read_csv(p)
            row = d[d.test_id == test_id]
            if len(row) and row.iloc[0].get("mm_per_px_final") == row.iloc[0].get("mm_per_px_final"):
                out["mm_per_px"] = float(row.iloc[0]["mm_per_px_final"])
                out["mm_per_px_method"] = str(row.iloc[0]["method"])
                out["mm_per_px_rel_sigma"] = float(row.iloc[0]["mm_per_px_rel_sigma"])
            elif len(d) and "global_mm_per_px" in d:  # test not calibrated yet: fixed-FOV camera scale
                out["mm_per_px"] = float(d["global_mm_per_px"].iloc[0])
                out["mm_per_px_method"] = "global_fixed_fov (test not in calibration table)"
                out["mm_per_px_rel_sigma"] = float(d["mm_per_px_rel_sigma"].iloc[0])
    return out
