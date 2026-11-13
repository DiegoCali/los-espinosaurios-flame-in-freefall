"""Build analysis-same.json (detailed scientific export), analysis-same.md and every figure,
then the dashboard summary (analysis/build_summary.py).

    .venv/bin/python analysis/build_analysis_json.py
"""
from __future__ import annotations

import sys
import warnings
from datetime import datetime, timezone
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from analysis import figures  # noqa: E402
from analysis.insights import compute_all  # noqa: E402
from extraction.common import MODULE_DIR, PROCESSED_DIR, rel, write_json  # noqa: E402
from extraction.housekeeping import ION_B_THRESHOLD_V, ISS_SCATTER_THRESHOLD_V  # noqa: E402

OUT_JSON = MODULE_DIR / "analysis-same.json"
OUT_MD = MODULE_DIR / "analysis-same.md"

REFERENCES = [
    {"id": "urban2012", "citation": "Urban DL, Ruff GA, Greenberg PS, Fischer D, Meyer M, Mulholland G, Yuan Z, Bryg V, "
     "Cleary T, Yang J. Particle Morphology and Size Results from the Smoke Aerosol Measurement Experiment-2. "
     "AIAA 2012-3536, 42nd International Conference on Environmental Systems, 2012.",
     "url": "https://ntrs.nasa.gov/citations/20130000422", "use": "Moment method, instruments, Table 1, flow/aging design"},
    {"id": "yang2015", "citation": "Yang J, Cleary T, Mulholland G, et al. Smoke Characterization and Feasibility of the "
     "Moment Method for Spacecraft Fire Detection. Aerosol Science and Technology 49 (2015).",
     "url": "https://doi.org/10.1080/02786826.2015.1025124", "use": "Validation of the moment method"},
    {"id": "vpred2007", "citation": "ZIN Technologies. SAME Verification Plan and Engineering Requirements Document "
     "(SAME-PLN-005 Rev F), January 2007 (file in the PSI download).", "url": None,
     "use": "Hardware: aging chamber, piston, dilution, thermal precipitator, sample materials incl. DBP"},
    {"id": "daft", "citation": "NASA Glenn Research Center. Dust and Aerosol measurement Feasibility Test (DAFT), ISS "
     "Expedition 13 (2006).", "url": "https://ntrs.nasa.gov/citations/20070031686",
     "use": "Risk-reduction flight of the modified P-Trak condensation nuclei counter used by SAME"},
    {"id": "psi", "citation": "NASA Physical Sciences Informatics (PSI) repository, investigations PSI-101 (SAME-R) and "
     "PSI-102 (SAME).", "url": "https://psi.nasa.gov/physci/repo/data/investigations/PSI-101",
     "use": "Dataset source"},
]


def df_records(df: pd.DataFrame, cols=None, nd=4) -> list[dict]:
    d = df if cols is None else df[cols]
    d = d.replace({np.nan: None})
    out = []
    for rec in d.to_dict(orient="records"):
        out.append({k: (round(v, nd) if isinstance(v, float) else v) for k, v in rec.items()})
    return out


def pct(x):
    return f"{100 * x:.0f}%"


def key_insights(r) -> list[dict]:
    pc = r["published_comparison"]
    ap = r["aging_pairs"]
    apf = ap[ap.no_flow == 0]
    fe = r["flow_effect"]
    ov = r["detection_overall"]
    rates = r["detection_rates"].set_index(["material", "flow_regime"])
    sts = r["sts"]
    co = r["coagulation"]
    best = r["attempts"]["best"]
    base = r["attempts"]["baseline"]
    narrowed = int((apf.sigma_g_aged < apf.sigma_g_unaged).sum())
    st = r["size_by_material"]
    small = st[st.material.isin(["Kapton", "Teflon"])].dm_um
    large = st[~st.material.isin(["Kapton", "Teflon"])].dm_um
    tvm = r["tem_vs_moments"]
    return [
        {"id": "K1", "objective": "reproduce_nasa_results",
         "statement": f"The moment-method statistics re-derived here match the published SAME-2 Table 1: the diameter "
                      f"of average mass agrees within {100 * (pc.dm_ratio_this_over_published - 1).abs().max():.0f}% for "
                      f"all 10 material × aging cases.",
         "evidence": ["data/processed/size_dataset.csv", "data/processed/published_table1_baseline.csv"],
         "confidence": "high"},
        {"id": "K2", "objective": "particle_size_by_material",
         "statement": f"Kapton and Teflon (wire-insulation polymers) produce the smallest smoke: Dm {small.min():.2f}–"
                      f"{small.max():.2f} µm, versus {large.min():.2f}–{large.max():.2f} µm for lampwick (cellulose), "
                      f"Pyrell foam and silicone rubber at 8 cm/s flow.",
         "evidence": ["analysis-same.json#/size/by_material"], "confidence": "high"},
        {"id": "K3", "objective": "aging_coagulation",
         "statement": f"With flow, {apf.delta_t_s.min():.0f}–{apf.delta_t_s.max():.0f} s of extra aging cut the particle "
                      f"count to {pct(apf.m0_ratio_aged_over_unaged.min())}–{pct(apf.m0_ratio_aged_over_unaged.max())} of "
                      f"its initial value and grew Dm by ×{apf.dm_growth.min():.2f}–{apf.dm_growth.max():.2f}. The growth "
                      f"equals the mass-conserving coagulation prediction (N0/N)^1/3, giving a coagulation coefficient of "
                      f"{co['pairs_k_median_flow_cm3_s']:.1e} cm³/s, consistent with NASA's note "
                      f"({min(co['nasa_note_k_cm3_s']):.1e}–{max(co['nasa_note_k_cm3_s']):.1e}) and Brownian theory.",
         "evidence": ["analysis-same.json#/aging/pairs", "data/processed/figures/aging_coagulation.png"],
         "confidence": "high"},
        {"id": "K4", "objective": "aging_distribution_width",
         "statement": f"Aging narrowed the size distribution (σg fell) in {narrowed} of {len(apf)} flow runs, the trend "
                      f"expected as coagulating smoke approaches a self-preserving distribution.",
         "evidence": ["analysis-same.json#/aging/pairs"], "confidence": "medium"},
        {"id": "K5", "objective": "microgravity_no_flow",
         "statement": f"Without flow (possible only in microgravity, where there is no buoyant plume) smoke had "
                      f"×{fe.dm_ratio_no_flow_over_flow.min():.1f}–{fe.dm_ratio_no_flow_over_flow.max():.1f} larger Dm "
                      f"and {1 / fe.m0_ratio_no_flow_over_flow.max():.0f}–{1 / fe.m0_ratio_no_flow_over_flow.min():.0f}× "
                      f"fewer particles, and further aging changed it little because it had already coagulated near "
                      f"the heater.",
         "evidence": ["analysis-same.json#/flow_effect", "data/processed/figures/flow_effect.png"],
         "confidence": "medium"},
        {"id": "K6", "objective": "detector_comparison",
         "statement": f"The two detection principles fail in opposite regimes. With 8 cm/s flow the ISS photoelectric "
                      f"(scattering) detector responded to {pct(ov['flow_8cm_s']['iss_rate'])} of pushes and the "
                      f"ionization chamber to {pct(ov['flow_8cm_s']['ion_rate'])}; for Kapton the ISS detector responded "
                      f"to only {pct(rates.loc[('Kapton', 'flow_8cm_s'), 'iss_rate'])}. Without flow the ISS detector "
                      f"responded to {pct(ov['no_flow']['iss_rate'])} and the ionization chamber to "
                      f"{pct(ov['no_flow']['ion_rate'])}. Either detector would have responded to "
                      f"{pct(ov['all']['either_rate'])} of all pushes.",
         "evidence": ["analysis-same.json#/detectors", "data/processed/figures/detector_comparison.png",
                      "data/processed/figures/threshold_sensitivity.png"], "confidence": "medium"},
        {"id": "K7", "objective": "shuttle_detector",
         "statement": f"The Space Shuttle ionization smoke detector (powered in {len(sts)} pushes) alarmed in "
                      f"{int(sts.sts_alarm.sum())}; it stayed silent for aged Kapton (test 70), a weak Teflon test (89) "
                      f"and a dilute lampwick test (92).",
         "evidence": ["analysis-same.json#/detectors/sts_pushes"], "confidence": "medium"},
        {"id": "K8", "objective": "predictive_model",
         "statement": f"The AutoResearch-selected model predicts held-out Dm within a typical factor of "
                      f"{best['size_factor_error']['log10_dm_um']:.2f} and M0 within "
                      f"{best['size_factor_error']['log10_m0_per_cc']:.2f}, and reduces the detection Brier score by "
                      f"{100 * (1 - best['detection_brier_ratio']):.0f}% relative to the prevalence; its combined score "
                      f"is {best['val_score']:.3f} versus {base['val_score']:.3f} for the mean baseline.",
         "evidence": ["runs/autoresearch/same-run-01/best.json", "data/processed/figures/model_cv.png"],
         "confidence": "medium"},
        {"id": "K9", "objective": "tem_vs_moments",
         "statement": f"TEM image sizing of lampwick grids gives mean diameters ×{(tvm.tem_amd_um / tvm.moment_amd_um).min():.1f}–"
                      f"{(tvm.tem_amd_um / tvm.moment_amd_um).max():.1f} the in-flight moment value: small particles and "
                      f"liquid droplets are under-counted on grids, so in-flight moments are the better number statistic.",
         "evidence": ["data/processed/tem_summary.csv", "data/processed/figures/size_distributions.png"],
         "confidence": "medium"},
        {"id": "K10", "objective": "fire_safety_implication",
         "statement": "A single-moment detector is not enough for spacecraft: overheated wire insulation (Kapton, "
                      "Teflon) in ventilated areas makes ~0.1 µm smoke that light scattering misses, while smoke "
                      "trapped in still air (avionics boxes, stagnant corners) is dilute and coarse and weakens the "
                      "ionization signal. Measuring two moments (e.g. the MPASS demonstrated on SAME-R, or combining "
                      "ionization and scattering) covers both cases.",
         "evidence": ["K2", "K5", "K6"], "confidence": "medium"},
    ]


def limitations(r) -> list[str]:
    return [
        "Local raw data cover SAME-R (PSI-101, ISS Expedition 24, 2010) only; no SAME-1 (PSI-102, 2007) flight "
        "telemetry or moment tables are present.",
        "Calibrated moments (M0, M1/M0, Dm, σg) are NASA/NIST reduced values from 'Sample descriptions tables.docx'; "
        "raw P-Trak counts are diluted and raw ionization/DustTrak signals are uncalibrated, so they are used only as "
        "detector responses, not re-calibrated moments.",
        f"Detector 'detection' is a project-defined proxy: ISS scatter drop ≥ {ISS_SCATTER_THRESHOLD_V} V and "
        f"ionization-chamber rise ≥ {ION_B_THRESHOLD_V} V over each test's clean-air baseline. These are not the "
        "flight alarm algorithms; the threshold-sensitivity figure shows the conclusions hold across a range.",
        "Smoke amount per test was chosen by NASA (heater temperature set for a measurable signal), so detection "
        "rates describe these test conditions, not real-fire probabilities.",
        "Ten tests (59, 61, 65, 66, 86, 90, 91, 99, 102, 103) have telemetry but no material label in any local file. "
        "They are real heated tests, not blanks. A heater-wire fingerprint (cold resistance and Rt/R0, 34/36 "
        "leave-one-out agreement on labelled tests) infers silicone for 59, 65, 66, 86, 91, 99, 103 (DBP cannot be "
        "excluded) and Kapton for 61, 90, 102. These inferences are reported in test_material_audit.csv but were not "
        "used in the frozen model datasets; adding them changes the detection Brier ratio from 0.491 to 0.499.",
        "The material of test 92 was first assigned as lampwick from the start time of a labelled MSG video; its heater "
        "fingerprint matches Kapton instead. The frozen run keeps lampwick; relabelling it changes the detection "
        "Brier ratio from 0.491 to 0.511 (runs/verification/material_audit_sensitivity.json).",
        "Some grids have an ambiguous aging label (docx '?' or blank); they are excluded from the models. Seven "
        "moment rows have typographical or log-normal-inconsistent values and are flagged, not corrected.",
        "No-flow conditions have 1–2 labelled runs per material and no labelled silicone run (tests 99 and 103 are probably silicone); low-flow (2 cm/s) runs reported in the "
        "literature are not identifiable in the local telemetry (MFC = 0 during heating).",
        "The ISS scatter channel saturates near 6.1 V; obscuration percentage is provided as an unsaturated companion.",
        "Response delays are measured from the piston push and include transport to each sensor's duct position; "
        "they do not compare intrinsic sensor speed.",
        "The model was selected as the best of 15 attempts on the same cross-validation folds (~50–65 rows), so its "
        "apparent gain is mildly optimistic; it has not been validated on another flight.",
    ]


def build() -> dict:
    warnings.filterwarnings("ignore")
    r = compute_all()
    figs = figures.make_all(r)
    d = r["data"]
    inv = pd.read_csv(MODULE_DIR / "data" / "inventory" / "files.csv")
    best, base, best_full = r["attempts"]["best"], r["attempts"]["baseline"], r["attempts"]["best_full"]
    tests = d["tests"]
    out = {
        "experiment": "SAME-R — Smoke Aerosol Measurement Experiment Reflight (a.k.a. SAME-2)",
        "psi_investigation": "PSI-101 (SAME-R); companion PSI-102 (SAME, 2007) not present locally",
        "challenge": "NASA Space Apps 2026 — Flame in Freefall",
        "challenge_objectives": [
            "Characterise smoke particle size from spacecraft materials in microgravity",
            "Quantify smoke aging (coagulation) between source and detector",
            "Compare spacecraft smoke-detector principles and their false-negative risk",
            "Build a predictive model of particle size and detector response from test conditions",
        ],
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "data_inventory_summary": {
            "n_files": int(len(inv)), "size_gb": round(inv.size_bytes.sum() / 1e9, 2),
            "by_category": inv.category.value_counts().to_dict(),
            "flight": "ISS Expedition 24, Microgravity Science Glovebox, GMT day 210–252 of 2010",
            "identification": "Grid labels 'SAMERFLT <n><material>' and 2010 timestamps identify SAME-R (SAME-2).",
            "n_tests_with_telemetry": int(len(tests)),
            "n_tests_with_material": int((tests.material != "unknown").sum()),
            "n_pushes": int(len(d["pushes"])), "n_moment_measurements": int(len(d["nasa_moment_table"])),
            "inventory_file": "data/inventory/files.csv",
        },
        "methods": {
            "moment_method": {
                "M0": "Number concentration — P-Trak condensation nuclei counter (isopropanol, 0.02–1 µm, diluted with N2)",
                "M1": "Diameter concentration — residential ionization chamber (alpha source); signal ∝ Σ N·d",
                "M3": "Mass/volume concentration — DustTrak 90° light scattering, calibrated per material",
                "relations": "AMD = D0.5 = M1/M0; Dm = D1.5 = (M3/M0)^(1/3); log-normal: D_p = Dg·exp(p·ln²σg), "
                             "hence ln²σg = ln(Dm/AMD) and Dg = AMD/exp(0.5·ln²σg)",
            },
            "telemetry_segmentation": "Heating = HeatingInProgress flag; fill end = last closing of the piston vacuum "
                                      "(fill) valve before the first push; push = rising edge of the piston GN2 valve; "
                                      "aging = push start − fill end; aged when aging ≥ 120 s.",
            "flow_velocity": "Median MFC fill flow during heating mapped linearly to the 8.1 cm/s nominal duct velocity "
                             "(4.29 L/min ↔ 8.1 cm/s, NASA TEMflowvsnoflow.xls).",
            "detector_response": f"Peak change within 180 s of each push vs the pre-heating clean-air median. ISS: drop "
                                 f"of the forward-scatter channel; ionization: rise of Ion B voltage; STS: alarm bit. "
                                 f"Proxy thresholds {ISS_SCATTER_THRESHOLD_V} V and {ION_B_THRESHOLD_V} V.",
            "coagulation": "Constant-kernel Smoluchowski: 1/N − 1/N0 = K·t; mass conservation gives Dm ∝ N^(−1/3).",
            "model_validation": "Leave-one-run-out (size) and leave-one-test-out (detection) cross-validation, fixed "
                                "in prepare.py.",
        },
        "tests": df_records(tests),
        "size": {
            "measurements": df_records(d["size_dataset"]),
            "by_material": df_records(r["size_by_material"]),
            "published_comparison": df_records(r["published_comparison"].drop(columns=["source"])),
            "optical_visibility": df_records(r["visibility"]),
            "tem_vs_moments": df_records(r["tem_vs_moments"]),
        },
        "aging": {"pairs": df_records(r["aging_pairs"]), "coagulation": r["coagulation"]},
        "flow_effect": df_records(r["flow_effect"]),
        "detectors": {
            "overall": r["detection_overall"],
            "rates_by_material_flow": df_records(r["detection_rates"]),
            "threshold_sensitivity": df_records(r["threshold_sensitivity"]),
            "sts_pushes": df_records(r["sts"]),
            "response_delays_s": r["delays"],
            "pushes": df_records(d["detection_dataset"]),
        },
        "autoresearch": {
            "upstream": "karpathy/autoresearch @ " + (MODULE_DIR / "upstream_reference" / "UPSTREAM_COMMIT.txt").read_text().strip(),
            "adaptation": "prepare.py fixes data, folds and metric; train.py is the only editable file; attempts are "
                          "archived as files (no git commits).",
            "run_dir": "runs/autoresearch/same-run-01",
            "metric": "val_score = 0.5·mean NRMSE(5 size targets) + 0.5·mean Brier ratio(2 detectors); ~1 = mean baseline",
            "ledger": df_records(r["ledger"]),
            "baseline": {k: base[k] for k in ("val_score", "size_nrmse", "detection_brier_ratio")},
            "best": {k: best[k] for k in ("attempt", "description", "train_sha256", "model", "val_score", "size_nrmse",
                                          "detection_brier_ratio", "size_rmse", "size_nrmse_by_target",
                                          "size_factor_error", "detection_brier", "detection_brier_ratio_by_target",
                                          "detection_accuracy_at_0p5", "n_size_rows", "n_size_groups",
                                          "n_detection_rows", "n_detection_groups")},
        },
        "predictive_model": {
            "selected_attempt": best["attempt"],
            "description": best["model"],
            "cv_predictions": best_full["cv_predictions"],
            "scenario_curves": df_records(r["curves"]),
            "rt_r0_used_for_scenarios": r["rt_r0_median"],
        },
        "key_insights": key_insights(r),
        "data_quality": {
            "moment_table": r["qc"],
            "telemetry_provenance": df_records(pd.read_csv(PROCESSED_DIR / "hkp_provenance.csv")),
            "material_audit": {
                "method": "Heater-wire fingerprint: cold resistance and Rt/R0 from telemetry, 1-nearest-neighbour per "
                          "material against tests labelled by NASA tables or TEM files; leave-one-out for labelled tests.",
                "records": df_records(pd.read_csv(PROCESSED_DIR / "test_material_audit.csv")),
                "sensitivity": __import__("json").loads(
                    (MODULE_DIR / "runs" / "verification" / "material_audit_sensitivity.json").read_text()),
            },
            "label_warnings": df_records(inv[inv.label_flags.fillna("") != ""][["file", "run", "sample_id", "label_flags"]]),
            "notes": [
                "Run 54 aging: NASA lists 56.8 s net aging; the valve-edge definition gives 38 s (279 s push). The "
                "other 11 comparable values agree within 8 s.",
                "Test 63 telemetry starts after the fill; its aging is estimated as first push + nominal 38 s.",
                "Test 85 first push: P-Trak reads 1,510 /cm³, matching NASA's note 'low ptrak on peak one'.",
                "DustTrak A reads ~10,000/20,000 codes in SAME-R (slot repurposed); it is discarded.",
                "Smoke remains in the diagnostics duct between pushes until it is purged; responses are taken within "
                "180 s of each push.",
                "Test 92: material assigned as lampwick from an MSG video starting 10 s after the test record, but its "
                "heater fingerprint (0.645 ohm, Rt/R0 1.368) matches Kapton, not lampwick (0.76 ohm, 1.27).",
            ],
        },
        "limitations": limitations(r),
        "dashboard_hints": {
            "summary_file": "analysis-same-summary.json",
            "insights_file": "analysis/output/insights.json",
            "overview_figure": "analysis/output/same-summary.png",
            "figures": {k: rel(Path(v)) for k, v in figs.items()},
            "null_policy": "null = unavailable / not applicable; never zero",
        },
        "references": REFERENCES,
    }
    write_json(OUT_JSON, out)
    OUT_MD.write_text(markdown_report(out, r), encoding="utf-8")
    return out


def markdown_report(a: dict, r) -> str:
    best = a["autoresearch"]["best"]
    led = r["ledger"]
    L = [
        "# SAME-R (PSI-101): smoke particle size, aging and detector response — analysis report",
        "",
        f"_Generated {a['generated_at'][:19]} UTC by `analysis/build_analysis_json.py`._",
        "",
        "## Scope",
        "",
        f"- {a['data_inventory_summary']['n_files']} raw files ({a['data_inventory_summary']['size_gb']} GB): "
        f"{a['data_inventory_summary']['n_tests_with_telemetry']} tests with 1 Hz telemetry "
        f"({a['data_inventory_summary']['n_tests_with_material']} with an identified material), "
        f"{a['data_inventory_summary']['n_pushes']} smoke pushes, {a['data_inventory_summary']['n_moment_measurements']} "
        "NASA moment measurements, TEM sizing for lampwick runs 54–55.",
        f"- {a['data_inventory_summary']['identification']}",
        "",
        "## Key insights",
        "",
    ]
    for k in a["key_insights"]:
        L.append(f"- **{k['id']}** ({k['confidence']} confidence) — {k['statement']}")
    L += ["", "## Particle size by material (8 cm/s flow, medians)", "",
          "| Material | State | n | Dg (µm) | AMD (µm) | Dm (µm) | σg | M0 (#/cm³) | Published Dm |",
          "|---|---|---:|---:|---:|---:|---:|---:|---:|"]
    pc = r["published_comparison"].set_index(["material", "aged_state"])
    for row in r["size_by_material"].itertuples():
        pdm = pc.loc[(row.material, row.aged_state), "dm_um_published"] if (row.material, row.aged_state) in pc.index else None
        L.append(f"| {row.material} | {row.aged_state} | {row.n} | {row.dg_um:.3f} | {row.amd_um:.3f} | {row.dm_um:.3f} | "
                 f"{row.sigma_g:.2f} | {row.m0_per_cc:,.0f} | {pdm if pdm is not None else '—'} |")
    L += ["", "## Detector comparison (proxy thresholds)", "",
          "| Material | Flow | Pushes | ISS photoelectric | Ionization chamber | Either |", "|---|---|---:|---:|---:|---:|"]
    for row in r["detection_rates"].itertuples():
        L.append(f"| {row.material} | {row.flow_regime} | {row.n_pushes} | {pct(row.iss_rate)} | {pct(row.ion_rate)} | "
                 f"{pct(row.either_rate)} |")
    L += ["", "## AutoResearch ledger (`runs/autoresearch/same-run-01/results.tsv`)", "",
          "| # | Model | val_score | size NRMSE | detection Brier ratio | params | status |", "|---:|---|---:|---:|---:|---:|---|"]
    for row in led.itertuples():
        L.append(f"| {row.attempt} | `{row.model_name}` | {row.val_score:.4f} | {row.size_nrmse:.4f} | "
                 f"{row.detection_brier_ratio:.4f} | {row.num_params} | {row.status} |")
    L += ["", f"Selected: attempt {best['attempt']} — {best['model']['formula']}", "",
          "Held-out errors of the selected model:", "",
          "| Target | NRMSE | typical factor error |", "|---|---:|---:|"]
    for t, v in best["size_nrmse_by_target"].items():
        fe = best["size_factor_error"].get(t)
        L.append(f"| {t} | {v:.3f} | {('×%.2f' % fe) if fe else '—'} |")
    for t, v in best["detection_brier_ratio_by_target"].items():
        L.append(f"| {t} (Brier ratio) | {v:.3f} | accuracy {pct(best['detection_accuracy_at_0p5'][t])} |")
    L += ["", "## Figures", ""]
    for k, v in a["dashboard_hints"]["figures"].items():
        L.append(f"- [{k}]({v})")
    L += ["", "## Data quality notes", ""] + [f"- {n}" for n in a["data_quality"]["notes"]]
    L += ["", "Flagged moment rows:", ""] + [f"- run {f['run']} ({f['material']}, {f['aged_state']}): {f['qc_flags']}"
                                              for f in a["data_quality"]["moment_table"]["flagged"]]
    L += ["", "## Limitations", ""] + [f"- {x}" for x in a["limitations"]]
    L += ["", "## References", ""] + [f"- {x['citation']}" + (f" {x['url']}" if x["url"] else "") for x in a["references"]]
    return "\n".join(L) + "\n"


if __name__ == "__main__":
    build()
    from analysis.build_reports import build as build_reports
    from analysis.build_summary import build_summary

    build_summary()
    build_reports()
    print(f"wrote {OUT_JSON.name}, {OUT_MD.name}, analysis-same-summary.json, analysis/output/insights.json, SAME_EXPLICADO.md, SAME_ANALYSIS_REPORT_EN.md, data/processed/VALIDATION.md")
