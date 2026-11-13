#!/usr/bin/env python3
"""Export the traced dataset and the selected model; only generated_at varies."""
from __future__ import annotations
import csv
import json
import subprocess
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import numpy as np
import prepare
from extraction.common import ROOT, PROCESSED, INVENTORY, read_csv, numeric, write_json
from analysis.insights import compute, RELEVANCE, PREDICTION, CONTROLS

CONDITIONS={"material","thickness_nominal_mm","length_cm","width_cm","flow_direction","flow_pre_cm_s","pressure_pre_kpa","o2_pre_sensor_pct","o2_partial_pre_kpa","o2_table_pct","ignition_epoch_ms","ignition_duration_measured_s","ignition_duration_command_s","ignition_power_command_w","ignition_energy_measured_j","effective_grooved_thickness_mm"}
RUN=ROOT/"runs/autoresearch/saffire-run-01"


def metric_record(row):
    out=dict(row)
    out.pop("test_id");out.pop("metric")
    value=row["value"]
    out["value"] = (value if row["unit"] in ("category","reported_text") else numeric(value)) if value!="" else None
    out["uncertainty"]=numeric(row["uncertainty"])
    out["reason_if_null"]=row["reason_if_null"] or None
    return out


def tests_from_csv():
    tests={f"II-{i}":{"test_id":f"II-{i}","mission":"Saffire-II","conditions":{},"results":{},"source_files":[]} for i in range(1,10)}
    for row in read_csv(PROCESSED/"metrics.csv"):
        test=tests[row["test_id"]]
        test["conditions" if row["metric"] in CONDITIONS else "results"][row["metric"]]=metric_record(row)
        test["source_files"].append(row["source_file"])
    for test in tests.values():test["source_files"]=sorted(set(test["source_files"]))
    return list(tests.values())


def model_evidence():
    attempts=[]
    if (RUN/"results.tsv").exists():
        with (RUN/"results.tsv").open(newline="") as handle:
            for row in csv.DictReader(handle,delimiter="\t"):
                for k in ("val_rmse","val_mae","val_max_abs_err"):row[k]=numeric(row[k])
                for k in ("attempt","num_params"):row[k]=int(row[k]) if row[k] else None
                row["log_file"]=f"runs/autoresearch/saffire-run-01/attempt-{row['attempt']:02d}.log"
                attempts.append(row)
    best=json.loads((RUN/"best.json").read_text()) if (RUN/"best.json").exists() else prepare.evaluate_candidate()
    baseline=json.loads((RUN/"attempt-01.json").read_text()) if (RUN/"attempt-01.json").exists() else prepare.evaluate_candidate()
    # Runtime is not a scientific result and would make regeneration nondeterministic.
    best.pop("elapsed_seconds",None);baseline.pop("elapsed_seconds",None)
    return {"target":prepare.TARGET,"target_justification":"CO2 response at a fixed 180 s horizon is measured in all nine tests. One row per ignition avoids treating correlated frames as replicates. Only two published SIBAL spread rates exist; HRR and alarm delay lack required channels/calibration.","target_definition":"median of 1-s CO2 medians at [150,180) s minus median at [-30,0) s; ppm; electrical ignition reference; signed sensor response","inputs":list(prepare.INPUTS),"n_rows":best["n_rows"],"n_flights":1,"validation":best["validation"],"seed":prepare.SEED,"baseline":baseline,"best":best,"attempts":attempts,"max_attempts":15,"complexity_rule":"Added parameters require >=2% relative RMSE gain each; otherwise >=0.1% improvement","selection_limitation":"Repeated candidate selection on LOOCV makes best RMSE optimistic; no independent test set or causal atmosphere effect is claimed","source_file":"data/processed/model_dataset.csv","method":"protected_prepare.py_evaluation_and_clean_Git_experiment_gate"}


def plan_from_csv():
    groups=defaultdict(list)
    for row in read_csv(PROCESSED/"metrics.csv"):groups[row["metric"]].append(row)
    output=[]
    for name,rows in sorted(groups.items()):
        objective=RELEVANCE if name in CONDITIONS else CONTROLS if any(x in name for x in ("hazard","alarm","extinction","outcome","ground_")) else PREDICTION
        computed=any(r["value"]!="" for r in rows)
        output.append({"metric":name,"objective":objective,"source_files":sorted({r["source_file"] for r in rows}),"channels":sorted({r["source_channels"] for r in rows}),"method":sorted({r["method"] for r in rows}),"units":rows[0]["unit"],"computed":computed,"reason_if_not":None if computed else sorted({r["reason_if_null"] for r in rows}),"why_selected":rows[0]["selection_reason"],"uncertainty":sorted({r["uncertainty_type"] for r in rows}),"assumptions":"See DATA_PLAN.md and per-test conclusion; measurements with different physical definitions are not pooled"})
    return output


def predictive(autoresearch):
    X,y,rows=prepare.load_dataset()
    best=autoresearch["best"]
    ranges={k:sorted(set(v.tolist())) if k in prepare.CATEGORICAL else [float(np.min(v)),float(np.max(v))] for k,v in X.items()}
    derived=[{"test_id":r["test_id"],"quantity":"co2_change_at_180s","value":r["predicted"],"unit":"ppm","extrapolation":False,"validation":"held_out_test_prediction_within_mission_dataset; not_independent_mission","confidence":"low","source_file":r["source_file"],"method":"selected_model_LOOCV_prediction","conclusion":"Pilot estimate of signed local sensor response; not a hazard forecast"} for r in best["cv_predictions"]]
    derived.append({"environment":"lunar_or_martian_exploration_atmosphere","quantity":"co2_change_at_180s","value":None,"extrapolation":True,"reason_if_null":"No oxygen-enriched low-pressure or partial-gravity training data; no defensible transfer prediction","confidence":"low","source_file":"data/processed/model_dataset.csv","method":"unsupported_scenario_prediction_withheld","conclusion":"Collect appropriate atmosphere and gravity experiments before predicting"})
    return {"formula":best["model"]["formula"],"coefficients":best["model"]["coefficients"],"model_name":best["model_name"],"cv_predictions":best["cv_predictions"],"validity_range":{"inputs":ranges,"mission":"Saffire-II only; sequential tests in one vehicle","horizon_s":180,"sample_dimensions_cm":{"length":29,"width":5},"atmospheric_domain":"See findings.habitat_atmosphere; no O2 or pressure response was fitted","effective_thickness_note":"10 mm nominal for grooved PMMA; composite II-7 uses Nomex 0.37 mm plus PMMA lead-in","singleton_material":"PMMA_Nomex has one test; its transfer behavior is not validated"},"derived_predictions":derived,"source_file":"data/processed/model_dataset.csv","method":"best_training_only_fold_model; refit_all_data_for_coefficients"}


def pointer(document,path):
    current=document
    for part in path.strip("/").split("/"):
        key=part.replace("~1","/").replace("~0","~")
        current=current[int(key)] if isinstance(current,list) else current[key]
    return current


def build():
    inventory=json.loads((INVENTORY/"summary.json").read_text())
    tests=tests_from_csv()
    autoresearch=model_evidence()
    cabin=read_csv(PROCESSED/"cabin_metrics.csv")
    for row in cabin:row["value"]=numeric(row["value"]);row["reason_if_null"]=row["reason_if_null"] or None
    findings,ranking,insights=compute(tests,cabin,autoresearch,inventory)
    checks=read_csv(PROCESSED/"validation_checks.csv")
    verification_path=ROOT/"runs/verification/raw_integrity_final.json"
    integrity=json.loads(verification_path.read_text()) if verification_path.exists() else {"unchanged":True,"verification":"initial_hash_plus_current_size_mtime; final_full_hash_pending","n_files":inventory["n_files"]}
    limitations=["Nine test records in one flight; no independent flight validation or randomized replicates", "Model selected by repeated LOOCV; reported best error has selection optimism", "A single PMMA-Nomex composite test cannot validate material-specific generalization", "Material, geometry, sample location, flow and ignition energy are confounded", "Only two quantitative published spread rates; no independently calibrated optical-front extraction", "Sensor offsets and mixing dominate some small CO2 responses; negative changes are not physical CO2 consumption", "Uncertainty describes window variability, not absolute sensor accuracy or a confidence interval", "No CO, acid gas or particle-mass channels and no applicable exposure/alarm thresholds", "Cygnus clock alignment is unverified; mission telemetry cannot be assigned to per-test alarm delays", "No HRR from oxygen consumption without paired channels/mass flow or validated cabin mass balance", "No controlled ventilation cutoff or extinguishment effectiveness measurements", "No enriched-O2/low-pressure or lunar/Martian partial-gravity experiments in this archive", "Rankings use illustrative analyst atmosphere assumptions and subjective weights, not mission requirements", "Reported damage length, fuel regression, flame tip and pyrolysis propagation are different physical quantities"]
    document={"experiment":"Saffire (Spacecraft Fire Safety Demonstration)","psi_investigation":"PSI-99","challenge_objectives":[RELEVANCE,PREDICTION,CONTROLS],"generated_at":datetime.now(timezone.utc).isoformat(),"data_inventory_summary":inventory,"data_plan":plan_from_csv(),"tests":tests,"autoresearch":autoresearch,"predictive_model":predictive(autoresearch),"findings":findings,"relevance_ranking":ranking,"key_insights":insights,"data_quality":{"validation":checks,"discrepancies":inventory["missing_or_ambiguous"],"assumptions":["Nominal specimen geometry follows postflight matrix except preflight 10mm nominal for grooved PMMA", "Material inheritance for empty II-6 and II-9 cells and 037-to-0.37 correction are documented", "Electrical pulse defines t=0; optical ignition time may differ", "One-second medians and fixed windows reduce unequal-cadence and duration effects", "CO2 percent to ppm multiplier 10000; PSIA to kPa multiplier 6.894757293168; mW/cm2 to kW/m2 multiplier 0.01", "No published numeric spread value is represented as an independently calculated value", "Habitat atmospheres are analyst design scenarios"],"raw_integrity":integrity},"limitations":limitations,"dashboard_hints":{"display_language":"es","missing_values":"Render null with reason_if_null; never convert missing data to zero","value_structure":"Every condition/result carries value, source_file, source_channels, method, selection_reason, conclusion and uncertainty","charts":[{"id":"co2_windows","type":"time_series","source":"data/processed/sensor_timeseries.csv","figure":"data/processed/figures/co2_fixed_windows.png","purpose":"Show baselines and identical 180s response windows"},{"id":"model_cv","type":"observed_vs_predicted","source_pointer":"/predictive_model/cv_predictions","purpose":"Show held-out predictions and errors; label nine-test pilot"},{"id":"material_outcomes","type":"material_table","source_pointer":"/tests","purpose":"Keep microgravity versus ground outcomes and damage definitions"},{"id":"habitat_ranking","type":"ranked_table","source_pointer":"/relevance_ranking/environments","purpose":"Compare relevance while displaying assumed atmosphere and unsupported transfer"},{"id":"temperature_qc","type":"small_multiples","figure":"data/processed/figures/temperature_quality_control.png","purpose":"Expose uneven thermal sensor coverage"},{"id":"images","type":"contact_sheet","figure":"data/processed/figures/image_contact_sheet.jpg","purpose":"Visual sampling only; no quantitative flame-front claim"}]},"references":[{"source_file":"part-01/PSI-99_metadata_PSI-167_SAFFIRE-II.zip","doi":"10.60555/2chp-m469","role":"local investigation identification"},{"source_file":"part-01/PSI-99_Experimental table_SAFFIRE-2.csv","role":"postflight conditions and outcomes"},{"url":"https://ntrs.nasa.gov/api/citations/20180005168/downloads/20180005168.pdf","role":"external primary-source corroboration of 25cm/s sample II-6 and postflight table; does not add model rows"},{"url":"https://github.com/karpathy/autoresearch","role":"upstream training-only mutation pattern"},{"source_file":"/home/natalia/Documents/NASA/autoresearch-pendulum-study","role":"local scientific adaptation example; online example unavailable"}]}
    if len(insights)<6 or len(insights)>10:raise ValueError("Require 6–10 insights")
    for insight in insights:
        for path in insight["evidence"]:pointer(document,path)
    for objective in document["challenge_objectives"]:
        if sum(i["objective"]==objective for i in insights)<2:raise ValueError("At least two insights per objective")
    write_json(ROOT/"analysis-saffire.json",document)
    write_json(ROOT/"analysis/output/insights.json",{"findings":findings,"relevance_ranking":ranking,"key_insights":insights})
    summary(document)
    from analysis.build_summary import build_summary
    build_summary(document)
    return document


def summary(doc):
    """Generate the English analysis report without changing the scientific export."""
    ar = doc["autoresearch"]
    baseline, best = ar["baseline"], ar["best"]
    inventory = doc["data_inventory_summary"]
    materials = doc["findings"]["materials"]
    atmosphere = doc["findings"]["habitat_atmosphere"]
    products = doc["findings"]["detection_and_products"]
    statements = {
        "K1": f"The {inventory['n_files']} physical files contain nine measured Saffire-II tests, locally identified as PSI-99. They do not provide six independent mission datasets.",
        "K2": f"Pre-ignition pressure spans {atmosphere['pressure_kpa_range'][0]:.2f}-{atmosphere['pressure_kpa_range'][1]:.2f} kPa and sensor O2 spans {atmosphere['sensor_o2_pct_range'][0]:.2f}-{atmosphere['sensor_o2_pct_range'][1]:.2f}%. Atmospheric similarity favors the assumed ISS/Gateway scenarios.",
        "K3": "Lunar, Mars and rover relevance remains conditional: no local test validates low-pressure, enriched-O2 or partial-gravity transfer.",
        "K4": f"The nine-test pilot has selected leave-one-test-out RMSE {best['val_rmse']:.2f} ppm, versus {baseline['val_rmse']:.2f} ppm for the training mean. Repeated selection on this same evaluation requires external validation.",
        "K5": f"The two SIBAL tests publish {materials['sibal_spread_rates_mm_s'][0]:.1f} and {materials['sibal_spread_rates_mm_s'][1]:.1f} mm/s at measured airflow {materials['sibal_flow_cm_s'][0]:.2f} and {materials['sibal_flow_cm_s'][1]:.2f} cm/s. The {materials['sibal_relative_speed_increase']*100:.1f}% rate increase is descriptive, with n=2.",
        "K6": f"Pre-test CO2 ranges from about {products['co2_pre_ppm_range'][0]:.0f} to {products['co2_pre_ppm_range'][1]:.0f} ppm. Subtracting each local baseline avoids attributing all pre-existing CO2 to the current test.",
        "K7": f"All {materials['silicone_tests']} silicone specimens showed no sustained propagation under these conditions. The supplied 1g comparisons reinforce the need to preserve material, gravity, ventilation and geometry when interpreting prevention evidence.",
        "K8": "Cygnus smoke signals exist, but alarm thresholds/events and verified clock alignment are missing. Per-test detection delay and safe crew exposure time cannot be calculated.",
        "K9": "Paired inlet/outlet O2 with mass flow and a documented flow-cutoff intervention are missing. This archive alone cannot establish total HRR or suppression effectiveness.",
    }
    objective_labels = {
        "identify_relevant_investigations": "Identify relevant fire-safety evidence",
        "predictive_modeling_data": "Prepare and evaluate predictive data",
        "next_gen_fire_safety_controls": "Inform fire-safety controls and equipment",
    }
    lines = [
        "# Saffire-II analysis report", "",
        "Generated from [analysis-saffire.json](analysis-saffire.json). For a shorter explanation, start with [SAFFIRE_EXPLICADO.md](SAFFIRE_EXPLICADO.md).", "",
        f"The archive contains {inventory['n_files']} physical files ({inventory['total_size_gb']:.3f} decimal GB), nine Saffire-II ignition records and one flight. The investigation identifier is PSI-99.", "",
        'Dataset source: Urban DL, Ruff G. "Spacecraft Fire Experiment-II(SAFFIRE-II)", NASA PSI Data Repository, Version 5, [http://doi.org/10.60555/2chp-m469](http://doi.org/10.60555/2chp-m469).', "",
        "## What was extracted and why", "",
        "The workflow extracts pre-ignition conditions, electrical events, fixed-window CO2, O2, pressure, relative radiation and local temperatures. It also preserves published material outcomes and unaligned mission-level cabin statistics. Each test-level value has a source, channel, method, selection reason, interpretation and uncertainty or missing-value reason in [metrics.csv](data/processed/metrics.csv).", "",
        "The predictive target is `co2_increase_180s_ppm`: median CO2 at [150,180) seconds minus the median at [-30,0), using one-second medians. It provides nine comparable rows. It describes a local signed sensor response, not total emission, toxic dose or fire power.", "",
        "Only two published numeric spread rates exist, so they are retained as evidence rather than used to train a general propagation model. HRR, alarm delay, exposure hazard indices and ventilation-cutoff effectiveness lack the required channels, calibration, synchronization or interventions. Images were sampled for visual inspection without inventing a front trajectory. Duplicate ZIPs and image variants add no modeling rows.", "",
        "## Validation and unresolved measurement issues", "",
        "All nine electrical pulse durations agree with published commands within the fixed 0.15 s tolerance. Measured II-6 airflow is near 25 cm/s rather than the CSV's 20 or planning documents' 30; the postflight report corroborates 25. SIBAL length/duration differs by roughly 3-5% from the published spread rates, a bookkeeping comparison rather than independent optical validation. See [VALIDATION.md](data/processed/VALIDATION.md).", "",
        "The derived ignitor energy requires a channel-scale review: the archived voltage/current product gives about 26-112 kJ, while nominal power and duration imply 0.736 or 2.910 kJ. Pulse-timing agreement does not validate this absolute energy magnitude. Calculated energy was neither an input nor the target of the model.", "",
        "## AutoResearch evaluation and results", "",
        f"The experiment used fixed leave-one-test-out evaluation with seed {ar['seed']}, {len(ar['attempts'])} attempts and a maximum budget of 15. Each held-out response was predicted using only the other eight tests. There is no independent flight test set. All error metrics below are in ppm of the signed sensor response.", "",
        "| Model | RMSE | MAE | Maximum absolute error | Parameters |",
        "|---|---:|---:|---:|---:|",
        f"| Training-mean baseline | {baseline['val_rmse']:.6f} | {baseline['val_mae']:.6f} | {baseline['val_max_abs_err']:.6f} | {baseline['num_params']} |",
        f"| {best['model_name']} | {best['val_rmse']:.6f} | {best['val_mae']:.6f} | {best['val_max_abs_err']:.6f} | {best['num_params']} |", "",
        f"The selected model's mean absolute held-out error is about {best['val_mae']:.2f} ppm. RMSE gives larger misses more weight. Its reduction of {(1-best['val_rmse']/baseline['val_rmse'])*100:.2f}% relative to the baseline is not a percentage of correct predictions or a safety percentage. Repeated model selection on the same CV makes the selected error optimistic.", "",
        "### Recorded attempts", "",
        "| Attempt | Commit | Model | RMSE | Parameters | Decision | Description |",
        "|---:|---|---|---:|---:|---|---|",
    ]
    for row in ar["attempts"]:
        error = f"{row['val_rmse']:.6f}" if row["val_rmse"] is not None else "null"
        lines.append(f"| {row['attempt']} | {row['commit'][:10]} | {row['model_name']} | {error} | {row['num_params']} | {row['status']} | {row['description'].replace('|','/')} |")
    lines += [
        "", "### Selected formula", "", "```text", doc["predictive_model"]["formula"],
        json.dumps(doc["predictive_model"]["coefficients"], ensure_ascii=False, sort_keys=True), "```", "",
        "The displayed coefficients are fitted on all rows after calculating the held-out predictions. CV errors come from the held-out predictions, not from this full-data fit. The inverse-flow exponent is fixed rather than estimated as a universal physical law. Only one test has the higher flow, and one has PMMA-Nomex; their held-out folds lack matching cases.", "",
        "## Findings by challenge objective", "",
    ]
    for objective in doc["challenge_objectives"]:
        lines += ["### " + objective_labels[objective], ""]
        for item in doc["key_insights"]:
            if item["objective"] == objective:
                lines.append(f"- **{item['id']} ({item['confidence']} confidence):** {statements[item['id']]} Evidence in the detailed JSON: " + ", ".join("`" + ref + "`" for ref in item["evidence"]))
        lines.append("")
    lines += [
        "## Habitat relevance", "",
        "Scores rank evidence relevance under illustrative analyst scenarios, not ignition probability or material danger. Habitat atmosphere values are not official mission requirements. All experimental samples are small and all local tests are in microgravity.", "",
        "| Scenario | Assumed O2 (%) | Assumed pressure (kPa) | Assumed gravity (g) | Leading test | Score /100 |",
        "|---|---:|---:|---:|---|---:|",
    ]
    names = {"iss_like_spacecraft": "ISS-like spacecraft", "gateway_like_station": "Gateway-like station", "lunar_base": "Lunar base", "pressurized_rover": "Pressurized lunar rover", "mars_base": "Mars base"}
    relevance = doc["relevance_ranking"]
    for key, assumptions in relevance["environment_assumptions"].items():
        top = relevance["environments"][key][0]
        lines.append(f"| {names[key]} | {assumptions['o2_pct']:.1f} | {assumptions['pressure_kpa']:.1f} | {assumptions['gravity_g']:.3f} | {top['test_id']} | {top['score']:.2f} |")
    lines += ["", "The complete ranking, weights and transfer limits are in [DATA_PLAN.md](DATA_PLAN.md) and the detailed JSON. Small score differences do not establish scientifically significant ordering.", "", "## Figures", "", "![Observed CO2 changes and model error](analysis/output/saffire-summary.png)", "", "The left panel compares signed local CO2 responses. The right compares baseline and selected-model RMSE; smaller is better. Neither panel directly measures fire hazard. [README.md](README.md) explains the CO2 calculation windows, published SIBAL rates, local thermocouple coverage and camera samples.", "", "## Limitations", ""]
    lines += ["- " + item for item in doc["limitations"]]
    lines += [
        "", "## Reproduce or restore the reports", "",
        "With the processed CSVs and preserved experiment records available, this command recreates the detailed JSON, the English analysis report, the dashboard summary and the plain-language explanation:", "",
        "```bash", ".venv/bin/python analysis/build_analysis_json.py", ".venv/bin/python -m pytest -q", "```", "",
        "To repeat extraction, obtain the cited raw archive, set `SAFFIRE_RAW_DATA` and run `extraction/run_all.py`. Raw data remain excluded from Git. JSON exports, reports, CSVs, figures and run records are included in the publication.", "",
        "The historical experimental comparison `baseline-v1..2af682a96609f938a023eb5bf94d62441d4e0d4d` contains only `train.py`. Later English documentation and report generators preserve that completed model search.", "",
    ]
    text = "\n".join(lines)
    (ROOT / "analysis-saffire.md").write_text(text, encoding="utf-8")

if __name__=="__main__":
    result=build();print(ROOT/"analysis-saffire.json");print(f"{len(result['tests'])} tests; {len(result['key_insights'])} insights")
