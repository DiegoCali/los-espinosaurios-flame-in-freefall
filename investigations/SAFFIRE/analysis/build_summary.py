#!/usr/bin/env python3
"""Build the English dashboard summary, plain-language report and overview figure."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from extraction.common import ROOT, PROCESSED, read_csv, write_json

SCHEMA_VERSION = "1.0.0"
MATERIALS = {
    "Silicone": "Silicone",
    "SIBAL": "SIBAL: cotton and fiberglass fabric",
    "PMMA_Nomex": "PMMA followed by Nomex",
    "PMMA": "PMMA: acrylic plastic",
}
BEHAVIOR = {
    "no_sustained_spread": "The flame did not spread in a sustained way.",
    "complete_fabric_spread": "The flame spread along the full 29 cm fabric sample.",
    "PMMA_consumed_Nomex_not_ignited": "The PMMA section was consumed; the Nomex did not ignite.",
    "anchored_flame_slow_regression": "The flame stayed near the leading edge while the material continued burning slowly.",
}
CITATION = 'Urban DL, Ruff G. "Spacecraft Fire Experiment-II(SAFFIRE-II)", NASA PSI Data Repository, Version 5'
DOI = "http://doi.org/10.60555/2chp-m469"


def value(test, section, name):
    return test[section][name]["value"]


def brief(document):
    ar = document["autoresearch"]
    baseline, best = ar["baseline"], ar["best"]
    tests = document["tests"]
    findings = document["findings"]
    inventory = document["data_inventory_summary"]
    rows = []
    for i, test in enumerate(tests):
        material = value(test, "conditions", "material")
        outcome = value(test, "results", "material_outcome")
        rows.append({
            "test_id": test["test_id"],
            "material_code": material,
            "material": MATERIALS[material],
            "nominal_thickness_mm": value(test, "conditions", "thickness_nominal_mm"),
            "airflow_cm_s": round(value(test, "conditions", "flow_pre_cm_s"), 2),
            "flow_direction": value(test, "conditions", "flow_direction"),
            "pressure_kpa": round(value(test, "conditions", "pressure_pre_kpa"), 2),
            "oxygen_pct": round(value(test, "conditions", "o2_pre_sensor_pct"), 2),
            "outcome_code": outcome,
            "documented_behavior": BEHAVIOR[outcome],
            "co2_before_ppm": round(value(test, "results", "co2_pre_ppm"), 2),
            "co2_change_180s_ppm": round(value(test, "results", "co2_increase_180s_ppm"), 2),
            "plume_peak_180s_c": round(value(test, "results", "plume_peak_180s_c"), 2),
            "radiation_peak_excess_180s_kw_m2": round(value(test, "results", "radiation_peak_excess_180s_kw_m2"), 3),
            "spread_rate_published_mm_s": value(test, "results", "spread_rate_reported_mm_s"),
            "burn_duration_published_s": value(test, "results", "burn_duration_reported_s"),
            "detail_ref": f"analysis-saffire.json#/tests/{i}",
        })
    example = next(t for t in tests if t["test_id"] == "II-5")
    pre = value(example, "results", "co2_pre_ppm")
    change = value(example, "results", "co2_increase_180s_ppm")
    worst = max(best["cv_predictions"], key=lambda r: abs(r["error"]))
    atmosphere = findings["habitat_atmosphere"]
    radiation = [value(t, "results", "radiation_peak_excess_180s_kw_m2") for t in tests]
    temperatures = [value(t, "results", "plume_peak_180s_c") for t in tests]
    energy = [value(t, "conditions", "ignition_energy_measured_j") / 1000 for t in tests]
    nominal_energy = [value(t, "conditions", "ignition_power_command_w") * value(t, "conditions", "ignition_duration_command_s") / 1000 for t in tests]
    sensor_rows = read_csv(PROCESSED / "sensor_timeseries.csv")

    def measurement(identifier, label, origin, result, why, reference):
        return {"id": identifier, "label": label, "origin": origin, "result": result,
                "why_it_matters": why, "detail_ref": reference}

    measurements = [
        measurement("materials", "Materials and flame behavior", "Published outcomes supplied with the dataset", "Four silicone specimens showed no sustained spread; flames spread over both SIBAL fabrics; Nomex did not ignite in the composite; both PMMA slabs sustained anchored flames.", "Supports material comparisons under the tested conditions.", "analysis-saffire.json#/findings/materials"),
        measurement("atmosphere", "Airflow, oxygen and pressure", "Sensor readings before ignition", f"Airflow ranged from {min(r['airflow_cm_s'] for r in rows):.2f} to {max(r['airflow_cm_s'] for r in rows):.2f} cm/s; oxygen readings from {atmosphere['sensor_o2_pct_range'][0]:.2f} to {atmosphere['sensor_o2_pct_range'][1]:.2f}%; pressure from {atmosphere['pressure_kpa_range'][0]:.2f} to {atmosphere['pressure_kpa_range'][1]:.2f} kPa.", "Defines the experimental conditions; behavior in another atmosphere requires additional evidence.", "analysis-saffire.json#/findings/habitat_atmosphere"),
        measurement("co2_response", "CO2 change after three minutes", "New calculation from sensor readings", f"Signed changes ranged from {findings['detection_and_products']['co2_response_180s_ppm_range'][0]:.2f} to {findings['detection_and_products']['co2_response_180s_ppm_range'][1]:.2f} ppm.", "Provides a common response for comparing all nine tests and training the pilot model.", "analysis-saffire.json#/autoresearch/target_definition"),
        measurement("flame_spread", "Flame spread rate", "Two published values; no new optical front tracking", "The SIBAL rates are 2.1 and 2.6 mm/s.", "Quantifies flame advance where a rate is available; two cases cannot establish a general law.", "analysis-saffire.json#/findings/materials/sibal_spread_rates_mm_s"),
        measurement("thermal_signals", "Local plume temperature and radiation", "Calculations from local sensors during the first three minutes", f"Per-test sampled plume peaks range from {min(temperatures):.2f} to {max(temperatures):.2f} degrees C; relative radiation peaks range from {min(radiation):.3f} to {max(radiation):.3f} kW/m2.", "Shows thermal signals at instrumented locations; geometry limits their interpretation as flame temperature or total fire power.", "data/processed/metrics.csv"),
        measurement("cabin_and_smoke", "Cabin and smoke signals", "Cygnus telemetry", "Sensor signals exist, but per-fire alarm events and clock synchronization were not verified.", "Provides information for future detection analysis; alarm delays remain unavailable.", "data/processed/cabin_metrics.csv"),
        measurement("ignition_and_images", "Ignition timing and images", "Electrical channels and sampled images", "Pulses last about 9.2 or 30 s; 27 images were sampled, three per test. The ignitor energy scale requires review.", "Supports event timing and visual inspection. Image sampling did not produce new spread-rate measurements.", "data/processed/VALIDATION.md"),
    ]

    def insight(identifier, title, evidence, meaning, usefulness, confidence, pointers):
        return {"id": identifier, "title": title, "evidence": evidence, "meaning": meaning,
                "why_it_matters": usefulness, "confidence": confidence,
                "evidence_refs": ["analysis-saffire.json#" + pointer for pointer in pointers]}

    insights = [
        insight("S1", "Silicone did not sustain flame spread in these tests", "This occurred in all four silicone specimens.", "The observed behavior was limited under this combination of airflow, oxygen, pressure and specimen geometry.", "Provides evidence for material comparisons; it does not certify all silicone configurations as safe.", "medium", ["/findings/materials/silicone_no_sustained_spread"]),
        insight("S2", "Flames spread over both SIBAL fabrics", "Published rates were 2.1 mm/s at roughly 20 cm/s airflow and 2.6 mm/s at roughly 25 cm/s.", f"The second rate was {findings['materials']['sibal_relative_speed_increase'] * 100:.1f}% higher. This is a comparison of two tests, not a universal airflow law.", "Identifies a relationship worth testing with more ventilation and propagation experiments.", "low", ["/findings/materials/sibal_spread_rates_mm_s", "/findings/materials/sibal_flow_cm_s"]),
        insight("S3", "A flame can advance slowly while burning persists for minutes", "The PMMA slabs have published burn durations of 10 and 15 minutes, with flames near the leading edge.", "Limited advance and extinguishment are different outcomes.", "Fire-safety analysis must also consider how long burning persists.", "low", ["/tests/7/results/burn_duration_reported_s", "/tests/8/results/burn_duration_reported_s"]),
        insight("S4", "The composite's PMMA burned, but Nomex did not ignite", "Only one specimen used this combination.", "The fire did not transfer from the PMMA section to the Nomex section in that test.", "Provides a material comparison case that needs replication under other conditions.", "low", ["/tests/6/results/material_outcome"]),
        insight("S5", "Each test needs its own CO2 baseline", f"Pre-test readings ranged from approximately {findings['detection_and_products']['co2_pre_ppm_range'][0]:.0f} to {findings['detection_and_products']['co2_pre_ppm_range'][1]:.0f} ppm.", "The tests started at different CO2 levels, so each response subtracts its own initial reading.", "Avoids attributing CO2 already present to the current test.", "medium", ["/findings/detection_and_products/co2_pre_ppm_range", "/autoresearch/target_definition"]),
        insight("S6", "The model improved one specific prediction in a small pilot", f"Its mean absolute held-out error was {best['val_mae']:.2f} ppm.", "It estimates the three-minute sensor change within this pilot; another flight is needed for external validation.", "Provides a first tool for comparing predicted and observed responses.", "low", ["/autoresearch/best/val_mae", "/predictive_model/cv_predictions"]),
        insight("S7", "The data are closer to the assumed ISS and Gateway scenarios", "The tests used near-terrestrial pressure, airlike oxygen and microgravity.", "They more closely match those reference scenarios used in the relevance comparison.", "Helps prioritize which evidence to consult for a given environment.", "medium", ["/findings/habitat_atmosphere", "/relevance_ranking/environment_assumptions"]),
        insight("S8", "Transfer to lunar, Mars and rover environments remains unvalidated", "The local archive has no enriched-oxygen, low-pressure or lunar/Martian partial-gravity tests.", "Comparisons with those habitats are indicative and use analyst design assumptions.", "Identifies additional experiments needed before extrapolating.", "medium", ["/data_inventory_summary/missing_or_ambiguous", "/relevance_ranking/limitations"]),
        insight("S9", "Smoke signals alone cannot establish alarm timing", "Alarm events, thresholds and verified clock synchronization are missing.", "A reliable detection delay is unavailable for each test.", "Identifies the information needed to evaluate detection equipment.", "low", ["/findings/detection_and_products/alarm_delays_s", "/findings/cabin_impact/note"]),
    ]

    charts = [
        {"id": "overview", "title": "Observed CO2 response and model error", "path": "analysis/output/saffire-summary.png", "description": "Left: signed CO2 changes for the nine tests. Right: baseline and selected-model RMSE; lower is better.", "interpretation_note": "CO2 change is not a hazard score. Error reduction is not an accuracy or safety percentage."},
        {"id": "co2_windows", "title": "CO2 comparison windows", "path": "data/processed/figures/co2_fixed_windows.png", "description": "Each panel shows baseline-subtracted CO2 over time. Gray marks the pre-ignition window; orange marks 150-180 seconds.", "interpretation_note": "The shaded regions define the calculation windows, not exposure limits."},
        {"id": "sibal_spread", "title": "Published SIBAL spread rates", "path": "data/processed/figures/sibal_published_rates.png", "description": "Two published flame spread rates plotted against measured pre-ignition airflow.", "interpretation_note": "Two observations do not establish a causal or universal airflow law."},
        {"id": "temperature_qc", "title": "Temperature sensor coverage", "path": "data/processed/figures/temperature_quality_control.png", "description": "Maximum sampled plume-thermocouple readings and duct inlet temperature for each test.", "interpretation_note": "Different sensor positions and coverage prevent interpreting these as maximum flame or average cabin temperatures."},
        {"id": "images", "title": "Sampled camera frames", "path": "data/processed/figures/image_contact_sheet.jpg", "description": "Three camera frames per test, selected near 30, 90 and 150 seconds after the electrical marker.", "interpretation_note": "Visual quality control only; no independently calibrated flame-front measurement."},
    ]
    metric_meanings = {
        "mean_absolute_error": "Average absolute distance between predicted and observed CO2 change; about 18 ppm for the selected model.",
        "rmse": "Error measure that gives larger mistakes more weight. Lower is better.",
        "maximum_absolute_error": "Largest absolute held-out error observed in these nine tests; not a bound for future experiments.",
    }
    errors = {name: {"baseline": round(baseline[key], 2), "best_model": round(best[key], 2), "meaning": metric_meanings[name]}
              for name, key in [("mean_absolute_error", "val_mae"), ("rmse", "val_rmse"), ("maximum_absolute_error", "val_max_abs_err")]}

    return {
        "schema_version": SCHEMA_VERSION,
        "language": "en",
        "id": "saffire-ii",
        "title": "Saffire-II: a plain-language summary",
        "summary": "Nine fire tests were organized, material behavior was compared, and a pilot model was built to estimate a local CO2 sensor change three minutes after ignition.",
        "source_analysis": "analysis-saffire.json",
        "reading_guide": {"measured": "Recorded by a NASA sensor.", "published": "An outcome already reported in the supplied NASA documentation.", "calculated": "Derived in this study by processing the readings.", "insight": "An interpretation supported by the results.", "predicted": "A model estimate compared with an observation to measure error.", "null": "Unavailable or not applicable; never interpret null as zero."},
        "scope": {"mission": "Saffire-II", "setting": "Inside an uncrewed Cygnus spacecraft in microgravity.", "local_investigation_id": "PSI-99", "n_files": inventory["n_files"], "raw_size_gb": round(inventory["total_size_gb"], 2), "n_tests": len(tests), "n_flights": ar["n_flights"], "n_sensor_records": sum(int(r["n_raw_records"]) for r in sensor_rows), "sample_dimensions_cm": {"length": 29, "width": 5}, "note": "The nine tests share a flight and cabin; they are not nine independent flight replicates. Local raw data do not cover all six Saffire missions."},
        "measurements": measurements,
        "co2_calculation": {"rule": "Subtract the pre-ignition typical reading from the typical reading at 150-180 seconds. Each is a median of one-second medians over a 30-second window.", "unit": "ppm: parts per million, a way to express concentration.", "real_example": {"test_id": "II-5", "before_ppm": round(pre, 2), "around_180s_ppm": round(pre + change, 2), "change_ppm": round(change, 2), "plain_explanation": "The sensor rose from approximately 3350 to 3390 ppm: a change of 40 ppm."}, "negative_values": "A reading below its initial level can reflect variation or air mixing. It does not demonstrate that the fire consumed CO2.", "interpretation_limit": "This response is not total emitted gas mass, total fire power or a crew exposure threshold."},
        "test_results": rows,
        "insights": insights,
        "predictive_model": {
            "model_name": best["model_name"],
            "n_parameters": best["num_params"],
            "active_inputs": ["material_code", "airflow_cm_s"],
            "target": "co2_change_180s_ppm",
            "target_description": "Change in the local CO2 sensor three minutes after the electrical ignition marker.",
            "why_this_target": "Available for all nine tests and comparable at a common time horizon.",
            "what_was_fitted": "Two typical responses: one for silicone and another for the other materials, with the latter adjusted for airflow.",
            "evaluation": "Train on eight tests, predict the ninth, and repeat for all nine. All 15 candidate models used this same evaluation.",
            "n_attempts": len(ar["attempts"]),
            "baseline_description": "Always predict the mean response of the eight training tests.",
            "errors_ppm": errors,
            "cv_predictions": [{"test_id": r["test_id"], "observed_ppm": round(r["observed"], 2), "predicted_ppm": round(r["predicted"], 2), "error_ppm": round(r["error"], 2), "absolute_error_ppm": round(abs(r["error"]), 2)} for r in best["cv_predictions"]],
            "rmse_reduction_pct": round((1 - best["val_rmse"] / baseline["val_rmse"]) * 100, 1),
            "improvement_meaning": "RMSE decreased relative to the baseline. This percentage is not a percentage of correct predictions or of safety.",
            "worst_case": {"test_id": worst["test_id"], "observed_ppm": round(worst["observed"], 2), "predicted_ppm": round(worst["predicted"], 2), "absolute_error_ppm": round(abs(worst["error"]), 2), "meaning": "The model misses much of the only PMMA-Nomex specimen's response; material-specific differences remain."},
            "formula_optional": "CO2 change = -2.372 ppm for silicone; 55.612 * (20 / airflow in cm/s) for the other observed materials.",
            "limitations": ["Only nine tests from one flight; no validation on another flight.", "Repeated selection used the same evaluation, so the selected error is optimistic.", "The inverse-airflow exponent was fixed for this candidate, not learned as a universal physical law.", "Only II-6 has the higher airflow and only II-7 uses PMMA-Nomex; their held-out folds lack matching cases.", "The model does not directly estimate flame spread, fire size, alarm delay or crew risk."],
        },
        "habitat_relevance": {"iss_and_gateway": "Greater similarity to the assumed atmosphere and microgravity reference scenarios.", "lunar_mars_rover": "Additional enriched-oxygen, low-pressure and partial-gravity evidence is needed.", "ranking_meaning": "Ranks the usefulness of evidence under design assumptions, not material danger or ignition probability.", "assumptions": "Habitat atmospheres are analyst scenarios, not official mission requirements.", "detail_ref": "analysis-saffire.json#/relevance_ranking"},
        "unavailable_results": [
            {"id": "hrr", "label": "Total fire power, or HRR", "status": "unavailable", "value": None, "reason": "Missing validated inlet/outlet oxygen with mass flow, or a validated cabin mass balance."},
            {"id": "alarm_delay", "label": "Time until smoke alarm", "status": "unavailable", "value": None, "reason": "Missing alarm events, thresholds and synchronized clocks."},
            {"id": "crew_exposure", "label": "Safe crew exposure time", "status": "unavailable", "value": None, "reason": "Applicable exposure channels and limits were not established."},
            {"id": "ventilation_cutoff", "label": "Effect of stopping ventilation", "status": "unavailable", "value": None, "reason": "No documented controlled flow-cutoff and extinction intervention."},
            {"id": "ignitor_energy", "label": "Ignitor energy", "status": "requires_validation", "value": None, "reason": "The archived voltage/current product conflicts with nominal power and duration; units, scaling and channel interpretation require review.", "archived_calculation_kj_range": [round(min(energy), 2), round(max(energy), 2)], "commanded_energy_kj": sorted(set(round(x, 3) for x in nominal_energy)), "model_use": "The calculated energy was not used to train the model."},
        ],
        "source": {"citation": CITATION, "url": DOI, "version": "5", "attribution": "NASA supplied measurements and published outcomes. Extraction, the CO2 response, modeling and interpretations were produced in this study."},
        "charts": charts,
        "files": {"plain_explanation": "SAFFIRE_EXPLICADO.md", "detailed_analysis": "analysis-saffire.json", "metrics_and_provenance": "data/processed/metrics.csv", "model_dataset": "data/processed/model_dataset.csv", "experiment_ledger": "runs/autoresearch/saffire-run-01/results.tsv", "overview_figure": "analysis/output/saffire-summary.png"},
    }


def figure(summary):
    os.environ.setdefault("MPLCONFIGDIR", "/tmp/saffire-summary-matplotlib")
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Patch

    rows = summary["test_results"]
    palette = {"Silicone": "#8297b0", "SIBAL": "#d99d2b", "PMMA_Nomex": "#9a75bf", "PMMA": "#269c96"}
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5), gridspec_kw={"width_ratios": [1.65, 1]})
    response = [r["co2_change_180s_ppm"] for r in rows]
    axes[0].bar([r["test_id"] for r in rows], response, color=[palette[r["material_code"]] for r in rows])
    axes[0].axhline(0, color="#334155", linewidth=.8)
    axes[0].set(title="Observed sensor change after 3 minutes", ylabel="CO2 change (ppm)", ylim=(-31, 126))
    axes[0].tick_params(axis="x", labelsize=9)
    axes[0].legend(handles=[Patch(color=color, label=label.replace("PMMA_Nomex", "PMMA + Nomex")) for label, color in palette.items()], loc="upper left", frameon=False, fontsize=8)
    for i, y in enumerate(response):
        axes[0].text(i, y + (3 if y >= 0 else -3), f"{y:.2f}", ha="center", va="bottom" if y >= 0 else "top", fontsize=9)
    errors = summary["predictive_model"]["errors_ppm"]["rmse"]
    heights = [errors["baseline"], errors["best_model"]]
    axes[1].bar(["Simple baseline", "Selected model"], heights, color=["#94a3b8", "#2674b8"], width=.6)
    axes[1].set(title="RMSE: lower is better", ylabel="Error (ppm)", ylim=(0, 49))
    for i, y in enumerate(heights):
        axes[1].text(i, y + 1, f"{y:.2f}", ha="center", fontsize=11)
    for ax in axes:
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
    fig.text(.5, .015, "Left: sensor changes, not hazard scores. Right: internal evaluation on nine tests from one flight.", ha="center", fontsize=9)
    fig.tight_layout(rect=(0, .055, 1, 1))
    path = ROOT / "analysis/output/saffire-summary.png"
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=150)
    plt.close(fig)


def markdown(summary):
    s = summary
    model = s["predictive_model"]
    errors = model["errors_ppm"]
    example = s["co2_calculation"]["real_example"]
    lines = [
        "# Saffire-II explained in plain English", "",
        "**Nine specimens were compared. All four silicone specimens showed no sustained flame spread. Flames spread over the full length of both SIBAL fabrics. The PMMA slabs sustained flames near the leading edge for several minutes.**", "",
        "Our work organized NASA's evidence, calculated comparable measurements and built a first predictive model. **The model estimates one thing: how much CO2 changes at one sensor three minutes after the electrical ignition marker.**", "",
        "## 1. What data we had", "",
        "NASA ignited material specimens inside an uncrewed Cygnus spacecraft in microgravity. Flame spread means the flame advances into new areas of the material.", "",
        f"There were {s['scope']['n_files']} physical files, but only **nine Saffire-II tests from one flight**. Each specimen was approximately 29 by 5 cm. Duplicate files and many camera frames are not additional experiments.", "",
        "Sensors recorded CO2, oxygen, airflow, pressure, temperatures, radiation and smoke signals. Documentation also reported how the materials burned. The dataset is identified as **PSI-99**.", "",
        "The results have three different origins:", "",
        "- **Published observation:** NASA had already reported, for example, that flame spread over the SIBAL fabric.",
        "- **Calculation in this study:** sensor readings were processed to measure the CO2 change after three minutes.",
        "- **Model prediction:** an estimate of that change, compared with the observation to measure its error.", "",
        "## 2. What the CO2 number means", "",
        "CO2 is carbon dioxide. Its concentration is expressed in **ppm**, or parts per million. Each test's pre-ignition reading is subtracted from its reading around three minutes later.", "",
        "A real example from SIBAL test II-5:", "",
        "| Time | CO2 sensor reading |", "|---|---:|",
        f"| Before ignition | {example['before_ppm']:.0f} ppm |",
        f"| Around three minutes | {example['around_180s_ppm']:.0f} ppm |",
        f"| Change used for comparison | **+{example['change_ppm']:.0f} ppm** |", "",
        "Typical readings are medians over 30-second windows, reducing the influence of isolated readings. Every test uses the same comparison period. **This is a local sensor response; it is not total gas emitted or a direct measure of danger to people.**", "",
        "## 3. What happened in each test", "",
        "The CO2 column is our calculation. The behavior description comes from the supplied documentation. A negative CO2 change means the reading fell slightly below its initial level, potentially because of variation or air mixing; it does not demonstrate CO2 consumption by the fire.", "",
        "| Test | Material | CO2 change after 3 min | Documented behavior |", "|---|---|---:|---|",
    ]
    for row in s["test_results"]:
        lines.append(f"| {row['test_id']} | {row['material']} | {row['co2_change_180s_ppm']:+.2f} ppm | {row['documented_behavior']} |")
    lines += ["", "**The PMMA-Nomex specimen had the largest early CO2 change, even though its Nomex did not ignite.** A larger CO2 change alone cannot rank materials by overall fire hazard.", "", "## 4. What we learned and why it matters", ""]
    for item in s["insights"]:
        lines += [f"**{item['id']}. {item['title']}.** {item['evidence']} {item['meaning']} {item['why_it_matters']} Confidence: {item['confidence']}.", ""]
    worst = model["worst_case"]
    lines += [
        "## 5. What the model did and what its error means", "",
        "To evaluate a model, one test was held out, the other eight were used for training, and the held-out response was predicted. This was repeated for all nine tests. Fifteen model candidates used the same procedure.", "",
        "The simple baseline always predicted the training-data mean. The selected model uses one group for silicone and another for the other materials, with an airflow adjustment.", "",
        "| Error measure | Simple baseline | Selected model |", "|---|---:|---:|",
        f"| Mean absolute error | {errors['mean_absolute_error']['baseline']:.2f} ppm | **{errors['mean_absolute_error']['best_model']:.2f} ppm** |",
        f"| RMSE: gives larger mistakes more weight | {errors['rmse']['baseline']:.2f} ppm | **{errors['rmse']['best_model']:.2f} ppm** |",
        f"| Largest absolute error | {errors['maximum_absolute_error']['baseline']:.2f} ppm | {errors['maximum_absolute_error']['best_model']:.2f} ppm |", "",
        f"The easiest interpretation is: **the selected model missed the observed change by about {errors['mean_absolute_error']['best_model']:.0f} ppm on average in this nine-test evaluation**. Errors vary: for {worst['test_id']}, it predicted about {worst['predicted_ppm']:.0f} ppm while the observed change was {worst['observed_ppm']:.0f} ppm, a miss of about {worst['absolute_error_ppm']:.0f} ppm.", "",
        f"RMSE decreased by {model['rmse_reduction_pct']:.1f}% relative to the baseline. **This is a reduction in an error measure, not a {model['rmse_reduction_pct']:.1f}% accuracy rate or a safety percentage.**", "",
        "This remains a pilot: nine tests share one flight, and the best model was selected using the same evaluation repeatedly. Only one test used the substantially higher flow, and only one used PMMA-Nomex. New experiments are needed for external validation.", "",
        "![Observed CO2 changes and model error comparison](analysis/output/saffire-summary.png)", "",
        "On the left, each bar is a sensor change; colors group materials. On the right, shorter bars indicate smaller prediction errors. Neither panel directly measures overall fire hazard.", "",
        "## 6. How this helps fire safety and what remains unknown", "",
        "These results help compare materials, examine flame spread and persistence, prepare predictive data and identify missing information for detector studies. The conditions are closer to the assumed ISS/Gateway reference scenarios. Lunar, Mars and rover comparisons use design assumptions; experiments under those conditions are still missing.", "",
        "| Topic | What is still needed |", "|---|---|",
        "| Total fire power, also called HRR | Inlet/outlet oxygen with mass flow, or a validated cabin mass balance. |",
        "| Time until smoke alarm | Alarm events, thresholds and synchronized clocks. |",
        "| Safe crew exposure time | Applicable measurement channels and exposure limits. |",
        "| Effectiveness of stopping ventilation | A documented controlled flow-cutoff and extinction intervention. |",
        "| Actual ignitor energy | Review of voltage/current scaling: the archived calculation conflicts with nominal power and duration. That calculated energy was not a model input. |", "",
        "## 7. Where to find the results and data source", "",
        "- [Dashboard summary JSON](analysis-saffire-summary.json): English measurement summaries, test results, insights, model errors and limitations.",
        "- [Project README](README.md): project overview, dashboard field guide and explanations of the figures.",
        "- [Detailed JSON](analysis-saffire.json): full values, provenance, methods and predictions.",
        "- [Metrics CSV](data/processed/metrics.csv): the source and method for each metric.",
        "- [Technical English report](SAFFIRE_ANALYSIS_REPORT_EN.md): a longer account, including the electrical-energy discrepancy.", "",
        f"Dataset source: {CITATION}, [{DOI}]({DOI}).", "",
        "NASA supplied the measurements and published outcomes. Organization, calculations, modeling and interpretations were produced in this study.", "",
    ]
    (ROOT / "SAFFIRE_EXPLICADO.md").write_text("\n".join(lines), encoding="utf-8")


def build_summary(document=None):
    if document is None:
        document = json.loads((ROOT / "analysis-saffire.json").read_text(encoding="utf-8"))
    summary = brief(document)
    write_json(ROOT / "analysis-saffire-summary.json", summary)
    markdown(summary)
    figure(summary)
    return summary


if __name__ == "__main__":
    result = build_summary()
    print(ROOT / "SAFFIRE_EXPLICADO.md")
    print(ROOT / "analysis-saffire-summary.json")
    print(f"{len(result['test_results'])} tests; {len(result['insights'])} explained insights; schema {SCHEMA_VERSION}; language en")
