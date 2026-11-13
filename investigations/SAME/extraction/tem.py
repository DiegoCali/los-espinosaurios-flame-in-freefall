"""TEM image-analysis spreadsheets (lampwick runs 54 and 55): per-particle diameters and statistics.

Outputs (data/processed/):
- tem_particles.csv   one row per sized particle (equivalent-circle diameter, µm)
- tem_summary.csv     count-based log-normal statistics per particle set, plus the
                      quarter-by-quarter SPV statistics for grid 54-7L
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from extraction.common import PROCESSED_DIR, find_raw_dir, write_csv

TEM_SETS = [
    # (run, file, sheet, set label)
    (54, "54 lampwick binneddatacorr from GWM.xlsx", "all data", "54_all_data"),
    (55, "55 Lampwick.xlsx", "all data", "55_all_data"),
    (55, "55 Lampwick.xlsx", "all data (2)", "55_all_data_2_extended"),
]
SPV_FILE = "SPV of 54-7L_21 all quarters (3).xlsx"
FIRST_PARTICLE_ROW = 18  # rows above hold the spreadsheet's own summary block


def particle_stats(d: np.ndarray) -> dict:
    d = d[np.isfinite(d) & (d > 0)]
    ln = np.log(d)
    return {
        "n_particles": int(d.size),
        "amd_um": float(d.mean()),                       # count mean diameter, D0.5
        "dm_um": float(np.mean(d ** 3) ** (1 / 3)),      # diameter of average mass, D1.5
        "dg_um": float(np.exp(ln.mean())),               # count geometric mean diameter
        "sigma_g": float(np.exp(ln.std(ddof=1))),
        "d_min_um": float(d.min()),
        "d_median_um": float(np.median(d)),
        "d_max_um": float(d.max()),
        "frac_above_0p3um": float(np.mean(d > 0.3)),
        "frac_above_1um": float(np.mean(d > 1.0)),
    }


def run(raw_dir: Path | None = None) -> dict[str, pd.DataFrame]:
    raw = find_raw_dir(raw_dir)
    parts, summ = [], []
    for run_id, fname, sheet, label in TEM_SETS:
        x = pd.read_excel(raw / fname, sheet_name=sheet, header=None)
        body = x.iloc[FIRST_PARTICLE_ROW:, [1, 2]].apply(pd.to_numeric, errors="coerce").dropna()
        body.columns = ["area_um2", "diameter_um"]
        body = body[body["diameter_um"] > 0]
        parts.append(body.assign(run=run_id, particle_set=label, source_file=fname, sheet=sheet))
        summ.append({"run": run_id, "particle_set": label, "material": "Lampwick", "method":
                     "count_statistics_of_equivalent_circle_diameters", "source_file": fname, "sheet": sheet,
                     **particle_stats(body["diameter_um"].to_numpy())})
    spv = pd.read_excel(raw / SPV_FILE, sheet_name="Statistics", header=None)
    for q, col in zip("ABCD", [1, 5, 9, 13]):
        summ.append({"run": 54, "particle_set": f"54_SPV_quarter_{q}", "material": "Lampwick",
                     "method": "published_spreadsheet_statistics", "source_file": SPV_FILE, "sheet": "Statistics",
                     "amd_um": float(spv.iat[2, col]), "dg_um": float(spv.iat[5, col]),
                     "sigma_g": float(spv.iat[6, col]), "d_avg_vol_um": float(spv.iat[7, col])})
    particles = pd.concat(parts, ignore_index=True)
    summary = pd.DataFrame(summ)
    write_csv(particles, PROCESSED_DIR / "tem_particles.csv")
    write_csv(summary, PROCESSED_DIR / "tem_summary.csv")
    return {"tem_particles": particles, "tem_summary": summary}


if __name__ == "__main__":
    out = run()
    print(out["tem_summary"].round(3).to_string())
