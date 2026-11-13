"""Dashboard exports derived from analysis-same.json:

- analysis-same-summary.json   English, schema 1.0.0 (same top-level layout as analysis-saffire-summary.json)
- analysis/output/insights.json  findings + key insights
- SAME_EXPLICADO.md            plain-English explanation (file name kept for parity with SAFFIRE_EXPLICADO.md)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from extraction.common import ANALYSIS_OUT, MODULE_DIR, write_json  # noqa: E402

SUMMARY = MODULE_DIR / "analysis-same-summary.json"
EXPLAINED = MODULE_DIR / "SAME_EXPLICADO.md"

CHART_TEXT = {
    "overview": ("Particle growth, detector complementarity and model error",
                 "Left: Dm before/after aging per material with published ticks. Middle: share of pushes each detector "
                 "type responded to, with and without flow. Right: held-out error of the selected model vs the mean baseline.",
                 "Detection rates use proxy thresholds, not flight alarm logic; error ratios are not accuracy percentages."),
    "moments_by_material": ("Moment-method size statistics per material",
                            "Dg, AMD, Dm and σg for every grid measured with 8 cm/s flow; filled = unaged, hollow = aged; "
                            "black ticks = published Table 1.", "Dg and σg assume a log-normal distribution."),
    "aging_coagulation": ("Aging and Brownian coagulation",
                          "Left: fall of particle count vs extra aging time with Smoluchowski curves. Right: observed Dm "
                          "growth vs the growth that mass-conserving coagulation predicts.",
                          "Each point is one run with paired unaged/aged measurements."),
    "flow_effect": ("Flow versus no-flow smoke", "Median Dm and M0 per material for unaged smoke made with 8 cm/s flow "
                    "and without flow.", "One or two no-flow runs per material; silicone has none."),
    "detector_comparison": ("ISS photoelectric vs ionization response", "Left: every push placed by its ionization and "
                            "ISS scatter response with the proxy thresholds. Right: detection rate per material and flow.",
                            "ISS scatter saturates near 6.1 V."),
    "threshold_sensitivity": ("Sensitivity to the proxy thresholds", "Detection rate of each detector across a range "
                              "of thresholds, with and without flow.", "Shows conclusions are not an artefact of one threshold."),
    "example_timeseries": ("Anatomy of one test", "Plume temperature, P-Trak, ionization chamber, DustTrak and ISS "
                           "scatter through heating, fill, aging and two pushes (test 64, Pyrell).",
                           "P-Trak counts are diluted; DustTrak is per-material calibrated by NASA, not here."),
    "size_distributions": ("Size distributions and TEM check", "Left: log-normal number distributions per material. "
                           "Right: TEM particle sizes for run 54 vs the moment-method distribution.",
                           "TEM under-counts the smallest particles."),
    "model_cv": ("Held-out model predictions", "Observed vs predicted Dm, σg and M0 and calibration of detection "
                 "probabilities, all from cross-validation.", "Predictions for unseen runs within this flight only."),
    "autoresearch_progress": ("AutoResearch search history", "val_score of the 15 attempts with keep/discard status.",
                              "Lower is better; ~1 = mean baseline."),
    "model_scenarios": ("Model scenarios and false-negative risk", "Predicted Dm growth with aging and the predicted "
                        "risk that each detector type gives no response, by material and flow.",
                        "Risk relative to proxy thresholds under SAME-R smoke amounts; dotted = extrapolation."),
}


def _r(x, n=3):
    return None if x is None else round(float(x), n)


def build_summary() -> dict:
    a = json.loads((MODULE_DIR / "analysis-same.json").read_text())
    inv = a["data_inventory_summary"]
    best = a["autoresearch"]["best"]
    base = a["autoresearch"]["baseline"]
    ov = a["detectors"]["overall"]
    pushes = a["detectors"]["pushes"]
    tests = a["tests"]
    size = a["size"]["measurements"]
    coag = a["aging"]["coagulation"]
    ki = a["key_insights"]
    figs = a["dashboard_hints"]["figures"]

    # ---------------- test_results: one entry per test with telemetry
    by_test = {}
    for p in pushes:
        by_test.setdefault(p["test"], []).append(p)
    audit = {r["test"]: r for r in a["data_quality"]["material_audit"]["records"]}
    test_results = []
    for i, t in enumerate(tests):
        ps = sorted(by_test.get(t["test"], []), key=lambda p: p["push_index"])
        test_results.append({
            "test_id": f"R-{t['test']}",
            "run": t["test"],
            "material_code": t["material"],
            "material": t["material"] if t["material"] != "unknown" else None,
            "material_source": t["material_source"],
            "material_inferred": audit.get(t["test"], {}).get("fingerprint_class") if t["material"] == "unknown"
            or audit.get(t["test"], {}).get("audit_result") == "CONFLICT" else None,
            "material_inference_note": (
                "Heater-wire fingerprint (not a NASA label); not used in the models." if t["material"] == "unknown" else
                "Assigned material conflicts with the heater fingerprint; see data_quality.material_audit."
                if audit.get(t["test"], {}).get("audit_result") == "CONFLICT" else None),
            "flow_velocity_cm_s": t["flow_velocity_cm_s"],
            "flow_regime": t["flow_regime_hkp"],
            "heating_s": t["heat_duration_s"],
            "plume_temp_max_c": _r(t["gas_plume_temp_max_c"], 1),
            "sts_detector_installed": t["sts_detector_powered"],
            "pushes": [{
                "push": p["push_index"], "aging_s": p["aging_s"], "aged_state": p["aged_state"],
                "iss_scatter_response_v": _r(p["iss_scatter_delta_peak_v"], 2),
                "iss_obscuration_drop_pct": _r(p["iss_obscuration_drop_pct"], 2),
                "ionization_response_v": _r(p["ion_b_delta_peak_v"], 2),
                "dusttrak_peak_mg_m3": _r(p["dusttrak_b_peak_mg_m3"], 1),
                "iss_detect_proxy": bool(p["iss_detect"]), "ionization_detect_proxy": bool(p["ion_detect"]),
                "sts_alarm": p["sts_alarm"],
            } for p in ps],
            "detail_ref": f"analysis-same.json#/tests/{i}",
        })

    size_results = [{
        "run": s["run"], "material": s["material"], "aged_state": s["aged_state"], "aging_s": s["aging_s"],
        "flow_velocity_cm_s": s["flow_velocity_cm_s"], "rt_r0": s["rt_r0"],
        "m0_per_cm3": s["m0_per_cc"], "amd_um": s["amd_um"], "dm_um": s["dm_um"], "dg_um": _r(s["dg_um"], 4),
        "sigma_g": s["sigma_g"], "used_in_model": s["include_in_model"],
        "quality_flags": s["qc_flags"] or None, "detail_ref": f"analysis-same.json#/size/measurements/{i}",
    } for i, s in enumerate(size)]

    material_summary = [{
        "material": m["material"], "aged_state": m["aged_state"], "n_measurements": m["n"],
        "median_aging_s": m["aging_s"], "dg_um": _r(m["dg_um"]), "amd_um": _r(m["amd_um"]), "dm_um": _r(m["dm_um"]),
        "sigma_g": _r(m["sigma_g"], 2), "m0_per_cm3": _r(m["m0_per_cc"], 0),
    } for m in a["size"]["by_material"]]

    insights = [{
        "id": k["id"].replace("K", "S"),
        "title": t,
        "evidence": k["statement"],
        "meaning": meaning,
        "why_it_matters": why,
        "confidence": k["confidence"],
        "evidence_refs": k["evidence"],
    } for k, (t, meaning, why) in zip(ki, [
        ("Published SAME-2 particle sizes reproduced", "The extraction and moment calculations are consistent with NASA's analysis.",
         "Builds trust in every derived number shown on the dashboard."),
        ("Wire insulation makes the smallest smoke", "Kapton and Teflon smoke is mostly below 0.2 µm.",
         "Electrical overheating of wiring is a leading spacecraft fire precursor."),
        ("Smoke grows while it travels", "Brownian coagulation removes small particles and enlarges the rest.",
         "The size a detector sees depends on how long the smoke took to reach it."),
        ("Aging narrows the distribution", "Size spread shrinks toward a self-preserving shape.",
         "Supports physics-based extrapolation of smoke properties."),
        ("Still air changes the smoke", "Without buoyancy, quiescent smoke is concentrated, coagulates fast and is coarse but dilute.",
         "Smoke trapped in avionics boxes or stagnant corners will not look like ventilated smoke."),
        ("Scattering and ionization detectors fail in opposite cases", "Light scattering misses tiny particles; ionization misses dilute coarse smoke.",
         "A single-principle detector leaves a blind spot."),
        ("The Shuttle ionization detector also missed some smoke", "Its alarm stayed silent for aged Kapton and weak tests.",
         "Real flight hardware confirms the proxy-based pattern."),
        ("A small model predicts size and detector response", "Conditions predict Dm within ~23% and detection with half the error of a constant guess.",
         "Gives a quick what-if tool for material, flow and transport time, within the tested range."),
        ("TEM grids under-count small particles", "Image sizing gives larger means than in-flight moments.",
         "In-flight moment instruments are preferable for number statistics."),
        ("Measure at least two moments", "Combining two size moments covers both blind spots.",
         "Design recommendation for future spacecraft smoke detectors."),
    ])]

    errs = best["size_factor_error"]
    used = [x for x in size if x["include_in_model"]]
    m0f = [x["m0_per_cc"] for x in used if x["no_flow"] == 0]
    m0n = [x["m0_per_cc"] for x in used if x["no_flow"] == 1]
    amd = [x["amd_um"] for x in used]
    dm = [x["dm_um"] for x in used]
    first = [p["aging_s"] for p in a["detectors"]["pushes"] if p["push_index"] == 1 and p["aged_state"] == "unaged"]
    aged = [p["aging_s"] for p in a["detectors"]["pushes"] if p["aged_state"] == "aged"]
    summary = {
        "schema_version": "1.0.0",
        "language": "en",
        "id": "same-r",
        "title": "SAME-R: smoke particle size, aging and detector response in microgravity",
        "summary": (f"{inv['n_tests_with_telemetry']} smoke tests from the 2010 ISS reflight of the Smoke Aerosol "
                    "Measurement Experiment were organised. Smoke from overheated spacecraft materials was aged and "
                    "sent past particle instruments and real ISS and Space Shuttle smoke detectors. The analysis "
                    "reproduces NASA's particle sizes, quantifies Brownian coagulation and shows that light-scattering "
                    "and ionization detectors fail in opposite conditions. An AutoResearch-selected model predicts "
                    "particle size and detector response from the test conditions."),
        "source_analysis": "analysis-same.json",
        "reading_guide": {
            "measured": "Recorded by a SAME-R instrument or detector during flight.",
            "published": "Reduced by NASA/NIST or reported in the SAME-2 paper.",
            "calculated": "Derived in this study from the measurements.",
            "insight": "An interpretation supported by the results.",
            "predicted": "A model estimate compared with an observation it did not see.",
            "null": "Unavailable or not applicable; never interpret null as zero.",
        },
        "scope": {
            "mission": "SAME-R (SAME-2), ISS Expedition 24",
            "setting": "Microgravity Science Glovebox on the International Space Station, July–September 2010.",
            "local_investigation_id": "PSI-101",
            "companion_investigation_id": "PSI-102 (SAME, 2007) — not present locally",
            "n_files": inv["n_files"], "raw_size_gb": inv["size_gb"],
            "n_tests": inv["n_tests_with_telemetry"], "n_tests_with_material": inv["n_tests_with_material"],
            "n_pushes": inv["n_pushes"], "n_moment_measurements": inv["n_moment_measurements"],
            "materials": ["Kapton", "Lampwick", "Pyrell", "Silicone", "Teflon"],
            "note": "All tests come from one flight and one hardware set; they are not independent flights.",
        },
        "measurements": [
            {"id": "m0", "label": "Particle number concentration (M0)", "origin": "P-Trak condensation nuclei counter (published reduction)",
             "result": f"{min(m0f) / 1e6:.2f}–{max(m0f) / 1e6:.1f} million particles per cm³ with flow; "
                       f"{min(m0n) / 1e6:.2f}–{max(m0n) / 1e6:.2f} million without flow.",
             "why_it_matters": "Zeroth moment; with M1 and M3 it gives the mean sizes.", "detail_ref": "analysis-same.json#/size/measurements"},
            {"id": "m1", "label": "Diameter concentration (M1)", "origin": "Ionization chamber (published reduction)",
             "result": f"Count mean diameter AMD = M1/M0 of {min(amd):.2f}–{max(amd):.2f} µm.", "why_it_matters": "Proportional to the signal of an ionization smoke detector.",
             "detail_ref": "analysis-same.json#/size/by_material"},
            {"id": "m3", "label": "Mass concentration (M3)", "origin": "DustTrak light scattering (published reduction)",
             "result": f"Diameter of average mass Dm = (M3/M0)^1/3 of {min(dm):.2f}–{max(dm):.2f} µm.", "why_it_matters": "Related to what light-scattering detectors see.",
             "detail_ref": "analysis-same.json#/size/by_material"},
            {"id": "aging", "label": "Aging time", "origin": "Calculated from piston valve telemetry",
             "result": f"Unaged pushes {min(first):.0f}–{max(first):.0f} s after the fill; aged pushes {min(aged):.0f}–{max(aged):.0f} s.", "why_it_matters": "Stands in for smoke transport time from source to detector.",
             "detail_ref": "analysis-same.json#/methods/telemetry_segmentation"},
            {"id": "iss_detector", "label": "ISS smoke detector (photoelectric)", "origin": "Measured forward-scatter and obscuration channels",
             "result": f"Responded to {round(100 * ov['flow_8cm_s']['iss_rate'])}% of pushes with flow and {round(100 * ov['no_flow']['iss_rate'])}% without.",
             "why_it_matters": "The detector type flying on the ISS.", "detail_ref": "analysis-same.json#/detectors/overall"},
            {"id": "ionization", "label": "Ionization chamber", "origin": "Measured Ion B voltage",
             "result": f"Responded to {round(100 * ov['flow_8cm_s']['ion_rate'])}% of pushes with flow and {round(100 * ov['no_flow']['ion_rate'])}% without.",
             "why_it_matters": "Same principle as the Space Shuttle detector.", "detail_ref": "analysis-same.json#/detectors/overall"},
            {"id": "sts_detector", "label": "Space Shuttle smoke detector", "origin": "Measured alarm bit (9 pushes)",
             "result": f"Alarmed in {sum(1 for p in a['detectors']['sts_pushes'] if p['sts_alarm'])} of {len(a['detectors']['sts_pushes'])} pushes.",
             "why_it_matters": "Real flight-qualified alarm behaviour.", "detail_ref": "analysis-same.json#/detectors/sts_pushes"},
        ],
        "moment_method": {
            "rule": "Three instruments measure three moments of the size distribution: M0 (count), M1 (count × diameter) "
                    "and M3 (count × diameter³). AMD = M1/M0 and Dm = (M3/M0)^1/3 need no assumption; assuming a "
                    "log-normal shape, σg = exp(√ln(Dm/AMD)) and Dg = AMD / exp(½ ln²σg).",
            "real_example": {
                "run": 63, "material": "Pyrell", "state": "unaged",
                "m0_per_cm3": 3862680, "amd_um": 0.207, "dm_um": 0.392,
                "sigma_g": 2.22, "dg_um": 0.151,
                "plain_explanation": "3.9 million particles per cm³ averaging 0.21 µm across; the mass-weighted size is "
                                     "0.39 µm, so the spread is wide (σg 2.2) and the typical (median) particle is 0.15 µm.",
            },
            "interpretation_limit": "Moments are NASA/NIST-calibrated values; raw instrument voltages are not re-calibrated here.",
        },
        "material_summary": material_summary,
        "test_results": test_results,
        "size_results": size_results,
        "detector_comparison": {
            "overall": ov,
            "by_material_and_flow": a["detectors"]["rates_by_material_flow"],
            "proxy_thresholds": {"iss_scatter_drop_v": 1.0, "ionization_rise_v": 0.5},
            "response_delay_median_s": {"iss_scatter": a["detectors"]["response_delays_s"]["iss_scatter_median_s"],
                                        "ionization_chamber": a["detectors"]["response_delays_s"]["ion_b_median_s"],
                                        "sts_alarm": a["detectors"]["response_delays_s"]["sts_alarm_median_s"]},
            "meaning": "Light scattering misses small (≈0.1 µm) Kapton/Teflon smoke in ventilated air; ionization misses "
                       "dilute coarse smoke made in still air.",
        },
        "coagulation": {
            "k_this_study_cm3_s": coag["pairs_k_median_flow_cm3_s"],
            "k_nasa_note_cm3_s": coag["nasa_note_k_cm3_s"],
            "k_brownian_theory_0p2um_cm3_s": coag["brownian_monodisperse_k_cm3_s_at_0p2um"],
            "meaning": "Particles collide and merge; after ~10 minutes about 60% of them are gone and the rest are larger.",
        },
        "insights": insights,
        "predictive_model": {
            "model_name": best["model"]["model_name"],
            "n_parameters": best["model"]["num_params"],
            "targets": ["log10 Dg", "log10 Dm", "log10 AMD", "ln σg", "log10 M0", "P(ISS response)", "P(ionization response)"],
            "inputs": ["material", "aging time", "flow velocity / no-flow", "heater Rt/R0 (temperature proxy)"],
            "what_was_fitted": "Ridge regression on material, a Brownian-coagulation variable ln(1+K·N0·t), no-flow and "
                               "heater temperature for Dm, σg and M0 (Dg and AMD follow from Hatch–Choate); hierarchical "
                               "beta-binomial detection rates by flow regime, material and aging.",
            "formula_optional": best["model"]["formula"],
            "evaluation": "Leave-one-run-out (size) and leave-one-test-out (detection) cross-validation; 15 attempts by "
                          "an AutoResearch loop editing only train.py.",
            "n_attempts": len(a["autoresearch"]["ledger"]),
            "selected_attempt": best["attempt"],
            "score": {"baseline": _r(base["val_score"], 4), "best_model": _r(best["val_score"], 4),
                      "meaning": "Average of size NRMSE and detection Brier ratio; 1 ≈ predicting the average."},
            "errors": {
                "dm_typical_factor": _r(errs["log10_dm_um"]), "dg_typical_factor": _r(errs["log10_dg_um"]),
                "amd_typical_factor": _r(errs["log10_amd_um"]), "m0_typical_factor": _r(errs["log10_m0_per_cc"]),
                "sigma_g_rmse_ln": _r(best["size_rmse"]["ln_sigma_g"]),
                "detection_brier": {k: _r(v) for k, v in best["detection_brier"].items()},
                "detection_accuracy": {k: _r(v) for k, v in best["detection_accuracy_at_0p5"].items()},
                "meaning": "A typical factor of 1.23 means predictions are usually within about ±23% of the measured value.",
            },
            "cv_predictions": a["predictive_model"]["cv_predictions"],
            "scenarios": a["predictive_model"]["scenario_curves"],
            "limitations": [
                f"Valid only within the tested materials, aging times ({min(first):.0f}–{max(aged):.0f} s) and flow regimes (0 or ~8 cm/s).",
                "Detection targets are proxy thresholds, not flight alarm logic.",
                "Best of 15 attempts on the same folds: mildly optimistic.",
                "No validation on SAME-1 (PSI-102) or other flights.",
            ],
        },
        "habitat_relevance": {
            "iss_and_gateway": "Directly relevant: microgravity, cabin-like air, and the ISS detector principle tested.",
            "lunar_mars": "Partial gravity restores some buoyancy, so quiescent-smoke effects should be weaker; not tested.",
            "design_assumptions": "Smoke amount was set by NASA for measurable signals; real fires vary.",
        },
        "unavailable_results": [
            {"id": "same1", "label": "SAME-1 (PSI-102, 2007) flight data", "status": "unavailable", "value": None,
             "reason": "No SAME-1 telemetry or moment tables in the local download."},
            {"id": "flight_alarm_logic", "label": "ISS detector alarm decisions", "status": "unavailable", "value": None,
             "reason": "Only analog channels were logged; the flight alarm algorithm/threshold is not in the dataset."},
            {"id": "mpass", "label": "MPASS two-moment sensor output", "status": "not_extracted", "value": None,
             "reason": "MPASS channel is not identified in the housekeeping columns (DustTrak A slot reads status codes)."},
            {"id": "low_flow", "label": "Low-flow (2 cm/s) runs", "status": "not_identifiable", "value": None,
             "reason": "Telemetry shows 0 or ~8 cm/s fill flow during heating only."},
            {"id": "unlabeled_tests", "label": "NASA-labelled material of 10 tests", "status": "inferred_only", "value": None,
             "reason": "No NASA table or TEM file names the material of tests 59, 61, 65, 66, 86, 90, 91, 99, 102, 103. "
                       "They are heated tests; the heater fingerprint suggests silicone (59, 65, 66, 86, 91, 99, 103) or "
                       "Kapton (61, 90, 102), reported in test_results[].material_inferred and not used in models."},
        ],
        "source": {
            "citation": "NASA Physical Sciences Informatics, PSI-101: Smoke Aerosol Measurement Experiment Reflight (SAME-R). "
                        "Principal investigator D. L. Urban, NASA Glenn Research Center.",
            "url": "https://psi.nasa.gov/physci/repo/data/investigations/PSI-101",
            "paper": "Urban DL et al., AIAA 2012-3536 (NTRS 20130000422)",
            "attribution": "NASA supplied the telemetry, reduced moment tables, TEM analyses and documents. Extraction, "
                           "telemetry segmentation, detector-response metrics, coagulation analysis, modelling and "
                           "interpretation were produced in this project.",
        },
        "charts": [{"id": k, "title": CHART_TEXT[k][0], "path": v, "description": CHART_TEXT[k][1],
                    "interpretation_note": CHART_TEXT[k][2]} for k, v in figs.items()],
        "files": {
            "plain_explanation": "SAME_EXPLICADO.md",
            "knowledge_base": "knowledge/SAME_KNOWLEDGE_BASE.md",
            "detailed_analysis": "analysis-same.json",
            "report": "analysis-same.md",
            "moment_table": "data/processed/nasa_moment_table.csv",
            "pushes": "data/processed/pushes.csv",
            "tests": "data/processed/tests.csv",
            "clean_timeseries": "data/processed/hkp_timeseries_clean.csv.gz",
            "model_size_dataset": "data/processed/size_dataset.csv",
            "model_detection_dataset": "data/processed/detection_dataset.csv",
            "experiment_ledger": "runs/autoresearch/same-run-01/results.tsv",
            "overview_figure": "analysis/output/same-summary.png",
        },
    }
    write_json(SUMMARY, summary)

    findings = {
        "particle_size": {"by_material": material_summary, "published_comparison": a["size"]["published_comparison"],
                          "source_file": "data/processed/size_dataset.csv", "method": "median_of_nasa_moment_rows_8cm_s"},
        "aging": {"pairs": a["aging"]["pairs"], "coagulation": coag, "source_file": "data/processed/size_dataset.csv",
                  "method": "paired_unaged_aged_moments; smoluchowski_constant_kernel"},
        "flow": {"by_material": a["flow_effect"], "method": "median_unaged_no_flow_vs_8cm_s"},
        "detection": {"overall": ov, "by_material_and_flow": a["detectors"]["rates_by_material_flow"],
                      "threshold_sensitivity": a["detectors"]["threshold_sensitivity"],
                      "sts": a["detectors"]["sts_pushes"], "delays_s": a["detectors"]["response_delays_s"],
                      "source_file": "data/processed/pushes.csv", "method": "peak_response_within_180s_vs_clean_air_baseline"},
        "model": {"baseline": base, "best": {k: best[k] for k in ("attempt", "val_score", "size_nrmse",
                                                                  "detection_brier_ratio", "size_factor_error")},
                  "ledger_file": "runs/autoresearch/same-run-01/results.tsv"},
    }
    write_json(ANALYSIS_OUT / "insights.json", {"findings": findings, "key_insights": ki})
    EXPLAINED.write_text(plain_explanation(a, summary), encoding="utf-8")
    return summary


def plain_explanation(a: dict, s: dict) -> str:
    """Plain-English explainer (file name kept as SAME_EXPLICADO.md for parity with SAFFIRE_EXPLICADO.md)."""
    ov = a["detectors"]["overall"]
    best = a["autoresearch"]["best"]
    base = a["autoresearch"]["baseline"]
    rates = {(r["material"], r["flow_regime"]): r for r in a["detectors"]["rates_by_material_flow"]}
    co = a["aging"]["coagulation"]
    ms = {(m["material"], m["aged_state"]): m for m in s["material_summary"]}
    pairs = [p for p in a["aging"]["pairs"] if p["no_flow"] == 0]
    max_dm_gap = max(abs(c["dm_ratio_this_over_published"] - 1) for c in a["size"]["published_comparison"]) * 100
    sts = a["detectors"]["sts_pushes"]
    n_alarm = sum(1 for p in sts if p["sts_alarm"])
    L = [
        "# SAME-R explained in plain English",
        "",
        "**Smoke from overheated spacecraft materials is made of very small particles, and those particles grow while "
        "the smoke travels. Detectors built on different physical principles miss different smoke: light scattering "
        "misses tiny particles, ionization misses dilute, coarse smoke. Using both would have caught almost every case.**",
        "",
        "## 1. What was measured",
        "",
        "In 2010, aboard the International Space Station (Expedition 24), the **SAME-R** experiment (the reflight of the "
        "*Smoke Aerosol Measurement Experiment*, investigation PSI-101) heated small samples of materials used in "
        "spacecraft until they gave off smoke, **without letting them ignite**. The materials were **Kapton** and "
        "**Teflon** (wire insulation), **Pyrell** (polyurethane foam), **silicone rubber** and a **cotton lamp wick** "
        "(cellulose). This smoke is the first sign of an electrical fire, which is exactly what a detector must catch early.",
        "",
        "Each test has four steps (see `data/processed/figures/example_timeseries.png`):",
        "",
        "1. **Heat** the sample for about 53 s while a piston draws air past it at 8 cm/s (or with no flow).",
        "2. **Hold** the smoke in an aging chamber. This stands in for the time smoke needs to travel from a fire to a detector.",
        "3. **Push** the smoke through a duct with instruments: a particle counter (P-Trak), an ionization chamber, a laser "
        "photometer (DustTrak), and the real smoke detectors of the ISS (photoelectric) and the Space Shuttle (ionization).",
        "4. **Collect** particles on grids for electron microscopy (TEM) on the ground.",
        "",
        "## 2. What was calculated",
        "",
        "With the **moment method**, three instruments give three averages of the particle population: how many particles "
        "there are (M0), the sum of their diameters (M1) and the sum of their volumes (M3). From them come the mean "
        "diameter (AMD = M1/M0), the diameter of average mass (Dm) and, assuming a log-normal distribution, the typical "
        "diameter (Dg) and the width of the distribution (σg).",
        "",
        "From the second-by-second telemetry we also calculated how long each smoke aged, the flow it was made with and "
        "how strongly each detector responded.",
        "",
        "## 3. Main results",
        "",
        f"- **NASA's published sizes are reproduced** (Dm differs by at most {max_dm_gap:.0f}%).",
        f"- **Wire-insulation smoke is tiny:** Kapton about {ms[('Kapton', 'unaged')]['dm_um']:.2f} µm and Teflon about "
        f"{ms[('Teflon', 'unaged')]['dm_um']:.2f} µm (Dm, unaged), against about {ms[('Pyrell', 'unaged')]['dm_um']:.2f} µm "
        f"for Pyrell and {ms[('Silicone', 'unaged')]['dm_um']:.2f} µm for silicone.",
        f"- **Smoke grows while it travels:** in about 10 minutes 50–75% of the particles disappear because they collide "
        f"and merge (Brownian coagulation), and Dm grows by a factor of {min(p['dm_growth'] for p in pairs):.2f} to "
        f"{max(p['dm_growth'] for p in pairs):.2f}. The measured rate ({co['pairs_k_median_flow_cm3_s']:.1e} cm³/s) agrees "
        "with theory and with NASA's own note.",
        "- **With no flow (possible only in microgravity, where smoke does not rise)** the smoke stays concentrated near "
        "its source, coagulates very quickly and arrives with larger but far fewer particles.",
        f"- **The two detector types fail in opposite situations.** With flow, the ISS photoelectric detector responded to "
        f"{round(100 * ov['flow_8cm_s']['iss_rate'])}% of pushes, but to only "
        f"{round(100 * rates[('Kapton', 'flow_8cm_s')]['iss_rate'])}% for Kapton, while the ionization chamber responded to "
        f"{round(100 * ov['flow_8cm_s']['ion_rate'])}%. Without flow it reverses: ISS {round(100 * ov['no_flow']['iss_rate'])}%, "
        f"ionization {round(100 * ov['no_flow']['ion_rate'])}%. With **both** detectors, "
        f"{round(100 * ov['all']['either_rate'])}% of cases would have produced a response.",
        f"- **The Space Shuttle detector** alarmed in {n_alarm} of the {len(sts)} pushes in which it was powered.",
        "",
        "## 4. What it means for fire safety",
        "",
        "A detector that measures **one property** of smoke has a blind spot. Scattered light barely sees 0.1 µm particles "
        "(overheated wiring in ventilated areas), and an ionization chamber loses signal in dilute, coarse smoke (smoke "
        "trapped in avionics boxes or unventilated corners). **Measuring at least two moments**, as the MPASS sensor "
        "demonstrated on SAME-R did, or combining ionization and scattering, covers both cases.",
        "",
        "## 5. The predictive model (autoresearch)",
        "",
        "An *autoresearch*-style loop (adapted from karpathy/autoresearch, without git commits) tried 15 versions of "
        "`train.py` and kept the best. The selected model uses the material, the aging time (through coagulation physics), "
        "the flow and the heater temperature.",
        "",
        f"- On tests it **never saw**, it predicts Dm with a typical error factor of ×{best['size_factor_error']['log10_dm_um']:.2f} "
        f"(about ±{round(100 * (best['size_factor_error']['log10_dm_um'] - 1))}%), comparable to the ±15% repeatability NASA reports.",
        f"- Its combined score is {best['val_score']:.3f}, against {base['val_score']:.3f} for \"always predict the average\" "
        "(lower is better).",
        "- It also estimates each detector type's **false-negative risk** by material, flow and transport time "
        "(`data/processed/figures/model_scenarios.png`).",
        "",
        "## 6. Important limits",
        "",
        "- Only **SAME-R (PSI-101)** data are available locally; SAME-1 (PSI-102, 2007) is not in the download.",
        "- \"Detected\" means exceeding a **proxy threshold** defined in this project (ISS: scatter drop of at least 1 V; "
        "ionization: rise of at least 0.5 V), not the real alarm logic. The sensitivity figure shows the conclusion does "
        "not depend on the threshold.",
        "- NASA chose the amount of smoke to give a measurable signal, so these are not probabilities for real fires.",
        "- The model is the best of 15 attempts on about 50–65 rows, so its gain is somewhat optimistic and it has not "
        "been validated on another flight.",
        "- Ten tests have no NASA material label; their materials are inferred from the heater wire and were not used in "
        "the models (see `data/processed/VALIDATION.md`).",
        "",
        "## 7. Files",
        "",
        "- Dashboard: `analysis-same-summary.json` (schema 1.0.0) and `analysis/output/same-summary.png`.",
        "- Detail: `analysis-same.json`, `analysis-same.md`, `SAME_ANALYSIS_REPORT_EN.md`, `data/processed/*.csv`.",
        "- Knowledge base: `knowledge/SAME_KNOWLEDGE_BASE.md`.",
    ]
    return "\n".join(L) + "\n"


if __name__ == "__main__":
    build_summary()
    print("wrote analysis-same-summary.json, analysis/output/insights.json, SAME_EXPLICADO.md")
