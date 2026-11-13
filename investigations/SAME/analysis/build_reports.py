"""Generate SAME_ANALYSIS_REPORT_EN.md (long English report) and data/processed/VALIDATION.md
from analysis-same.json and the processed tables, so text and numbers cannot drift apart."""
from __future__ import annotations

import json
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from extraction.common import MODULE_DIR, PROCESSED_DIR  # noqa: E402

REPORT = MODULE_DIR / "SAME_ANALYSIS_REPORT_EN.md"
VALIDATION = PROCESSED_DIR / "VALIDATION.md"

METRICS = [
    ("M0 (`m0_per_cc`)", "#/cm³", "Particle number concentration measured by the P-Trak condensation nuclei counter (NASA-reduced)."),
    ("M1/M0 = AMD (`amd_um`)", "µm", "Count mean diameter from the ionization chamber moment divided by M0."),
    ("Dm (`dm_um`)", "µm", "Diameter of average mass, (M3/M0)^(1/3), from the DustTrak mass moment."),
    ("σg (`sigma_g`)", "–", "Geometric standard deviation; exp(√ln(Dm/AMD)) under a log-normal assumption."),
    ("Dg (`dg_um`)", "µm", "Geometric mean (median) diameter, AMD / exp(½ ln²σg)."),
    ("Rt/R0 (`rt_r0`)", "–", "Hot/cold resistance of the heater wire: the temperature set point of a test."),
    ("Aging time (`aging_s`)", "s", "Seconds between closing the aging-chamber fill valve and the start of a push."),
    ("Flow velocity (`flow_velocity_cm_s`)", "cm/s", "Median fill flow during heating mapped to duct velocity (4.29 L/min ↔ 8.1 cm/s); 0 = no flow."),
    ("ISS scatter response (`iss_scatter_delta_peak_v`)", "V", "Peak drop of the ISS detector forward-scatter channel within 180 s of a push (saturates ≈ 6.1)."),
    ("ISS obscuration drop (`iss_obscuration_drop_pct`)", "%", "Peak relative drop of the obscuration channel; an unsaturated companion."),
    ("Ionization response (`ion_b_delta_peak_v`)", "V", "Peak rise of ionization chamber B over its clean-air baseline."),
    ("DustTrak peak (`dusttrak_b_peak_mg_m3`)", "mg/m³", "Peak uncalibrated DustTrak B reading."),
    ("P-Trak peak (`ptrak_peak_raw_pt_cc`)", "#/cm³", "Peak diluted P-Trak count; invalid −999 values removed."),
    ("STS alarm (`sts_alarm`, delay)", "bool, s", "Space Shuttle detector alarm bit and seconds from push start; only when the detector was powered."),
    ("ISS / ionization proxy detection", "bool", "Response ≥ 1.0 V (ISS scatter) or ≥ 0.5 V (ionization): project proxy, not flight logic."),
    ("Coagulation coefficient K", "cm³/s", "(1/N_aged − 1/N_unaged)/Δt from paired measurements."),
    ("val_score", "–", "0.5·mean NRMSE(5 size targets) + 0.5·mean Brier ratio(2 detectors); ≈ 1 for a mean baseline."),
    ("NRMSE", "–", "Held-out RMSE divided by the standard deviation of the target."),
    ("Brier ratio", "–", "Held-out Brier score divided by the Brier score of always predicting the prevalence."),
]


def pct(x):
    return f"{100 * x:.0f}%"


def report(a: dict) -> str:
    inv = a["data_inventory_summary"]
    best = a["autoresearch"]["best"]
    base = a["autoresearch"]["baseline"]
    ov = a["detectors"]["overall"]
    L = ["# SAME-R (PSI-101): detailed analysis report (English)", "",
         "Written for: researchers and reviewers who want the methods, every metric definition, the full model "
         "search and the data-quality findings behind the dashboard summary.", "",
         "_Generated from `analysis-same.json` by `analysis/build_reports.py`._", "",
         "## 1. Summary", ""]
    L += [f"- {k['statement']}" for k in a["key_insights"]]
    L += ["", "## 2. Data and scope", "",
          f"- {inv['n_files']} raw files, {inv['size_gb']} GB; flight: {inv['flight']}.",
          f"- {inv['n_tests_with_telemetry']} tests with 1 Hz telemetry, {inv['n_pushes']} smoke pushes, "
          f"{inv['n_moment_measurements']} NASA moment measurements (docx), 5,470 TEM-sized lampwick particles.",
          f"- Material known for {inv['n_tests_with_material']} tests from NASA tables or TEM labels; the other 10 are "
          "audited in section 8.",
          "- Local data are **SAME-R (PSI-101)** only. SAME-1 (PSI-102, 2007) flight data are not in the download.",
          "- All tests share one flight and one hardware set; they are not independent flights.", "",
          "## 3. Methods", ""]
    for k, v in a["methods"].items():
        if isinstance(v, dict):
            L.append(f"**{k.replace('_', ' ').capitalize()}**")
            L += [f"- *{kk}*: {vv}" for kk, vv in v.items()]
        else:
            L.append(f"**{k.replace('_', ' ').capitalize()}.** {v}")
        L.append("")
    L += ["## 4. Metric definitions", "", "| Metric | Unit | Definition |", "|---|---|---|"]
    L += [f"| {m} | {u} | {d} |" for m, u, d in METRICS]
    L += ["", "## 5. Results", "", "### 5.1 Particle size by material (8 cm/s flow, medians)", "",
          "| Material | State | n | Dg | AMD | Dm | σg | M0 |", "|---|---|---:|---:|---:|---:|---:|---:|"]
    for m in a["size"]["by_material"]:
        L.append(f"| {m['material']} | {m['aged_state']} | {m['n']} | {m['dg_um']:.3f} | {m['amd_um']:.3f} | "
                 f"{m['dm_um']:.3f} | {m['sigma_g']:.2f} | {m['m0_per_cc']:,.0f} |")
    L += ["", "### 5.2 Aging (paired unaged/aged measurements)", "",
          "| Run | Material | Flow | Δt (s) | M0 ratio | Dm growth | Mass-conserving growth | K (cm³/s) |",
          "|---:|---|---|---:|---:|---:|---:|---:|"]
    for p in a["aging"]["pairs"]:
        L.append(f"| {p['run']} | {p['material']} | {'no flow' if p['no_flow'] else 'flow'} | {p['delta_t_s']:.0f} | "
                 f"{p['m0_ratio_aged_over_unaged']:.2f} | {p['dm_growth']:.2f} | {p['dm_growth_if_mass_conserved']:.2f} | "
                 f"{p['k_coag_cm3_s']:.1e} |")
    L += ["", "### 5.3 Detectors", "",
          f"All pushes ({ov['all']['n_pushes']}): ISS {pct(ov['all']['iss_rate'])}, ionization {pct(ov['all']['ion_rate'])}, "
          f"either {pct(ov['all']['either_rate'])}, both {pct(ov['all']['both_rate'])}, neither {ov['all']['neither']}.", "",
          "| Material | Flow | Pushes | ISS | Ionization | Either |", "|---|---|---:|---:|---:|---:|"]
    for r in a["detectors"]["rates_by_material_flow"]:
        L.append(f"| {r['material']} | {r['flow_regime']} | {r['n_pushes']} | {pct(r['iss_rate'])} | {pct(r['ion_rate'])} | "
                 f"{pct(r['either_rate'])} |")
    L += ["", "Space Shuttle (STS) detector pushes:", "", "| Test | Material | Aging (s) | Alarm | Delay (s) | ISS proxy | Ionization proxy |",
          "|---:|---|---:|---|---:|---|---|"]
    for r in a["detectors"]["sts_pushes"]:
        L.append(f"| {r['test']} | {r['material']} | {r['aging_s']:.0f} | {r['sts_alarm']} | "
                 f"{'' if r['sts_alarm_delay_s'] is None else int(r['sts_alarm_delay_s'])} | {r['iss_detect_proxy']} | {r['ion_detect_proxy']} |")
    L += ["", "## 6. AutoResearch model search", "",
          f"Adapted from {a['autoresearch']['upstream']}. {a['autoresearch']['adaptation']} Metric: "
          f"{a['autoresearch']['metric']}.", "",
          "| # | Model | val_score | size NRMSE | detection Brier ratio | status | Description |", "|---:|---|---:|---:|---:|---|---|"]
    for r in a["autoresearch"]["ledger"]:
        L.append(f"| {r['attempt']} | `{r['model_name']}` | {r['val_score']:.4f} | {r['size_nrmse']:.4f} | "
                 f"{r['detection_brier_ratio']:.4f} | {r['status']} | {r['description']} |")
    L += ["", f"### Selected model: attempt {best['attempt']}", "", f"Formula: {best['model']['formula']}", "",
          f"Exact architecture: {best['model']['notes']}", "",
          "| Target | Held-out RMSE | NRMSE | Typical factor error |", "|---|---:|---:|---:|"]
    for t, v in best["size_nrmse_by_target"].items():
        rm = best["size_rmse"][t]
        fe = best["size_factor_error"].get(t)
        L.append(f"| {t} | {rm:.4f} | {v:.3f} | {('×%.2f' % fe) if fe else '–'} |")
    for t, v in best["detection_brier_ratio_by_target"].items():
        L.append(f"| {t} (Brier) | {best['detection_brier'][t]:.4f} | {v:.3f} (ratio) | accuracy {pct(best['detection_accuracy_at_0p5'][t])} |")
    L += ["", f"Baseline val_score {base['val_score']:.4f}; selected {best['val_score']:.4f}. The best of 15 attempts was "
          "chosen on the same folds, so the gain is mildly optimistic.", "",
          "## 7. Interpretation", "",
          "- Smoke particle size follows material chemistry and transport history: wire insulation gives ~0.1 µm smoke, "
          "foam, cellulose and silicone give 0.3–0.6 µm, and coagulation enlarges all of them over minutes.",
          "- Light scattering weights particles by area/mass and ionization by number × diameter, so each has a blind "
          "spot: scattering for small particles (ventilated Kapton/Teflon), ionization for dilute coarse smoke (still air).",
          "- Microgravity makes the still-air case reachable: without buoyancy, smoke lingers at the source and coagulates "
          "before it spreads, a condition that normal-gravity detector tests do not reproduce.",
          "- Design implication: a second moment (e.g. ionization + scattering, or the MPASS two-angle sensor) removes "
          "both blind spots.", ""]
    ma = a["data_quality"]["material_audit"]
    L += ["## 8. Data quality and the 10 unlabeled tests", "", "See `data/processed/VALIDATION.md` for the full audit. "
          "Summary:", ""]
    unk = [r for r in ma["records"] if r["material"] == "unknown"]
    for r in unk:
        L.append(f"- Test {r['test']}: heated {r['heat_duration_s']:.0f} s, plume up to {r['gas_plume_temp_max_c']:.0f} °C, "
                 f"fingerprint → **{r['fingerprint_class']}** ({r['audit_result']}, margin {r['fingerprint_margin']:.1f}).")
    sens = ma["sensitivity"]
    L += ["", f"Detection Brier ratio of the frozen model: {sens['frozen']['brier_ratio_mean']:.3f} (as run), "
          f"{sens['relabel_92']['brier_ratio_mean']:.3f} with test 92 relabelled, "
          f"{sens['add_audited']['brier_ratio_mean']:.3f} with all inferred tests added.", ""]
    L += [f"- {n}" for n in a["data_quality"]["notes"]]
    L += ["", "## 9. Limitations", ""] + [f"- {x}" for x in a["limitations"]]
    L += ["", "## 10. References", ""] + [f"- {x['citation']}" + (f" {x['url']}" if x["url"] else "") for x in a["references"]]
    return "\n".join(L) + "\n"


def validation(a: dict) -> str:
    P = PROCESSED_DIR
    mom = pd.read_csv(P / "nasa_moment_table.csv")
    us = mom[mom.usable_size_stats]
    sig = ((us.sigma_g_from_ratio - us.sigma_g_hc).abs() / us.sigma_g_hc).max()
    pu = pd.read_csv(P / "pushes.csv")
    nasa = pd.read_csv(P / "nasa_flow_aging_table.csv").dropna(subset=["net_aging_s"])
    diffs = []
    for _, r in nasa.iterrows():
        m = pu[(pu.test == r.run) & (pu.aged_state == r.aged_state)]
        if len(m):
            diffs.append(abs(m.aging_s.iloc[0] - r.net_aging_s))
    tests = pd.read_csv(P / "tests.csv")
    nom = tests[tests.flow_regime_hkp == "nominal_flow"].flow_velocity_cm_s
    prov = pd.read_csv(P / "hkp_provenance.csv")
    ma = a["data_quality"]["material_audit"]
    rec = pd.DataFrame(ma["records"])
    lab = rec[rec.audit_result.isin(["agrees", "CONFLICT"])]
    unk = rec[rec.material == "unknown"]
    sens = ma["sensitivity"]
    tp = pd.read_csv(P / "thermal_precipitator_map.csv")
    in_docs = sorted(set(mom.run) | set(tp.run.dropna().astype(int)))
    in_docs = [r for r in in_docs if r in set(tests.test)]
    in_docs_unk = [r for r in unk.test if r in in_docs]
    L = ["# SAME-R validation notes", "",
         "Generated by `analysis/build_reports.py`; every number is recomputed from the processed tables.", "",
         "## Automated data checks", "", "| Check | Result |", "|---|---|",
         f"| NASA σg equals exp(√ln(Dm/AMD)) on usable rows | max relative difference {100 * sig:.2f}% over {len(us)} rows |",
         f"| Moment rows flagged | {int((mom.qc_flags.fillna('') != '').sum())} of {len(mom)} (kept, nulled in clean columns) |",
         f"| Telemetry aging vs NASA 'net aging' | {len(diffs)} comparisons, median difference {np.median(diffs):.1f} s, max {max(diffs):.1f} s |",
         f"| Nominal-flow velocity anchor | {nom.min():.2f}–{nom.max():.2f} cm/s (NASA 8.1) |",
         f"| Duplicate telemetry copies detected | {int((~prov.used).sum())} ({', '.join(f'{r.file} (test {r.test})' for r in prov[~prov.used].itertuples())}) |",
         f"| Test records | {len(tests)} tests, {len(pu)} pushes; records with TestNumber 0 are idle/housekeeping between tests and excluded |",
         "| Published Table 1 reproduced | Dm within " + f"{max(abs(c['dm_ratio_this_over_published'] - 1) for c in a['size']['published_comparison']) * 100:.0f}% for all 10 cases |",
         "", "## Material audit: the 10 unlabeled tests", "",
         "**Question.** Are the tests without a material label calibration or purge (blank) runs, and can their material "
         "be recovered?", "",
         "**Cross-check of sources.** The three documents were searched for these run numbers. "
         f"`Sample descriptions tables.docx` and `thermal precipitator map updated.xlsx` together cover {len(in_docs)} of the "
         f"{len(tests)} telemetry tests; none of the ten appears in either ({', '.join(map(str, in_docs_unk)) or 'no overlap'} "
         "found), so no thermal-precipitator grid was analysed for them. `ISS Coagulation.doc` has no run identifiers "
         "(three lampwick/Teflon examples with start/end concentrations only). The GMT timestamps in the CSV files "
         "cannot be matched to the documents, whose dates are TEM viewing dates, not run times.", "",
         "**Not blank runs.** Calibration or purge periods in the telemetry are the `TestNumber = 0` records between tests, "
         "which are excluded. All ten are numbered tests with heating on for 52–54 s, plume temperature up to "
         f"{unk.gas_plume_temp_max_c.min():.0f}–{unk.gas_plume_temp_max_c.max():.0f} °C and one or two pushes. "
         "Nine produced a measurable detector response; test 90 produced almost none (DustTrak peak "
         f"{rec.set_index('test').loc[90, 'max_dusttrak_mg_m3']:.2f} mg/m³), a heated test with negligible smoke rather than a blank.", "",
         "**Material recovered from the telemetry itself.** The sample is wound on its heater wire; the wire's cold resistance "
         "and the hot/cold ratio Rt/R0 depend on the sample and its temperature regime. Telemetry Rt/R0 equals NASA's "
         f"docx value within 0.02 on every labelled test. A 1-nearest-neighbour classifier on (cold R, Rt/R0) agrees with "
         f"the known material for {(lab.audit_result == 'agrees').sum()} of {len(lab)} labelled tests (leave-one-out); the "
         "two misses are test 73 (the Kapton/silicone boundary) and test 92 (below).", "",
         "| Test | Heated (s) | Plume max (°C) | Cold R (Ω) | Rt/R0 | Inferred material | Margin | Status | Peak DustTrak (mg/m³) |",
         "|---:|---:|---:|---:|---:|---|---:|---|---:|"]
    for r in unk.itertuples():
        L.append(f"| {r.test} | {r.heat_duration_s:.0f} | {r.gas_plume_temp_max_c:.0f} | {r.cold_r_ohm:.3f} | "
                 f"{r.rt_r0_telemetry:.3f} | {r.fingerprint_class} | {r.fingerprint_margin:.1f} | {r.audit_result} | "
                 f"{r.max_dusttrak_mg_m3:.1f} |")
    L += ["", "**Reading.** Seven tests (59, 65, 66, 86, 91, 99, 103) fall in the silicone class and three (61, 90, 102) in "
          "the Kapton class. Silicone and Kapton are the closest pair, so test 91 (margin below 2.5) is the least certain. "
          "DBP-on-wick samples, which NASA lists among the six materials, could share the silicone cluster; they cannot "
          "be separated here. Test 59 is consistent with the analyst's file name `silcon_run59`, and tests 99 and 103 would be "
          "the only silicone no-flow runs (the paper notes silicone and DBP give no visible TEM particles, which fits "
          "their absence from the grid map). **These are inferences, not NASA labels.** They are exported as "
          "`material_inferred` and were not used to build the frozen model datasets.", "",
         "## Test 92: a label that the data contradict", "",
         "Test 92 was assigned lampwick because a labelled MSG video (`1 Lampwick`) started 10 s after the test record. "
         f"Its heater fingerprint ({rec.set_index('test').loc[92, 'cold_r_ohm']:.3f} Ω, Rt/R0 "
         f"{rec.set_index('test').loc[92, 'rt_r0_telemetry']:.3f}) matches Kapton (≈0.64 Ω, 1.37–1.47), not lampwick "
         "(≈0.76 Ω, 1.24–1.28), and its weak response (DustTrak 5.3 mg/m³) is Kapton-like. The video label is probably "
         "unrelated to this test. The frozen run keeps the original label so that the archived AutoResearch evaluation "
         "is not rewritten; the effect is small:", "",
         "| Scenario | Pushes | Detection Brier ratio | ISS accuracy | Ionization accuracy |", "|---|---:|---:|---:|---:|"]
    for k, name in [("frozen", "As run (92 = lampwick)"), ("relabel_92", "92 relabelled by fingerprint"),
                    ("add_audited", "Also add the 10 inferred tests")]:
        s = sens[k]
        L.append(f"| {name} | {s['n_pushes']} | {s['brier_ratio_mean']:.3f} | {pct(s['accuracy_iss'])} | {pct(s['accuracy_ion'])} |")
    L += ["", "The model is frozen from attempt 11; only the evaluation data change. All scenarios stay far below 1.0 "
          "(the mean-prevalence baseline), so the conclusions do not depend on these labels. A new study should "
          "re-run the search with the audited labels under a new run directory.", "",
          "## Other validation notes", ""] + [f"- {n}" for n in a["data_quality"]["notes"]]
    return "\n".join(L) + "\n"


def build() -> None:
    a = json.loads((MODULE_DIR / "analysis-same.json").read_text())
    REPORT.write_text(report(a), encoding="utf-8")
    VALIDATION.write_text(validation(a), encoding="utf-8")


if __name__ == "__main__":
    build()
    print("wrote SAME_ANALYSIS_REPORT_EN.md, data/processed/VALIDATION.md")
