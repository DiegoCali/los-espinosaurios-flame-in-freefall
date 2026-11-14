"""Build the shareable HTML report (reports/site/index.html) from pipeline outputs.

Every number is read from files written by the pipeline; figures are referenced as files published next to
the page (figures/<name>.png). Run after `bass2 aggregate` and `python -m bass2.report`.
"""
from __future__ import annotations

import html
import json
import re
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
FIGS = ROOT / "reports/figures"
SITE = ROOT / "reports/site"


def md_inline(text: str) -> str:
    t = html.escape(text.strip())
    t = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", t)
    t = re.sub(r"`(.+?)`", r"<code>\1</code>", t)
    return t


def figure(rel: str, files: dict) -> str:
    p = FIGS / rel
    if not p.exists():
        return ""
    name = rel.replace("/", "__").replace("_ensemble__", "")
    files[f"figures/{name}"] = str(p)
    cap = p.with_suffix(".md").read_text(encoding="utf-8") if p.with_suffix(".md").exists() else ""
    return (f'<figure class="plate"><img src="figures/{name}" alt="{html.escape(p.stem)}" loading="lazy">'
            f"<figcaption>{md_inline(cap)}</figcaption></figure>")


def pct(x, nd=1) -> str:
    return "—" if x is None or not np.isfinite(x) else f"{100 * x:.{nd}f} %"


def main() -> dict:
    SITE.mkdir(parents=True, exist_ok=True)
    files: dict[str, str] = {}
    val = json.loads((ROOT / "reports/validation_summary.json").read_text())
    vt = pd.read_csv(ROOT / "reports/validation_published.csv").sort_values(["set", "test_id"])
    rates = pd.read_csv(FIGS / "_ensemble/steady_rates.csv")
    fs = pd.read_csv(FIGS / "_ensemble/forecast_summary.csv")
    cal = pd.read_csv(ROOT / "data/catalog/spatial_calibration.csv")
    sets = val.get("by_set", {})
    dev_all = sets.get("development", {}).get("all", {})
    hold_all = sets.get("holdout", {}).get("all", {})
    hold_ok = sets.get("holdout", {}).get("qc_passed", {})
    tle = val.get("thickness_law_extended_trusted", {})
    qc = rates.qc.value_counts().to_dict() if "qc" in rates else {}
    n_tests = len(rates)
    n_trusted = int(qc.get("trusted", 0))
    scale = cal.global_mm_per_px.iloc[0]
    scale_cv = 100 * cal.global_std.iloc[0] / scale
    ha = val.get("holdout_accounting", {})
    hold_txt = (f"Hold-out: {ha.get('n_tests', 0)} slab tests were processed once with frozen settings; "
                f"{ha.get('n_with_comparison', 0)} gave at least one comparison "
                f"({', '.join(ha.get('no_steady_spread', [])) or 'none'} showed no steady spread). Across their "
                f"{hold_all.get('n', 0)} flow-step comparisons the median error is "
                f"{pct(hold_all.get('median_abs_rel_error'), 0)}; these tests were not part of the physics review."
                if hold_all else
                "The hold-out slab tests could not be evaluated yet: the NASA download endpoint returned empty responses "
                "when this page was built; they will be added with frozen settings when it recovers.")
    hb1 = sets.get("holdout", {}).get("first_or_single_step", {})
    hb2 = sets.get("holdout", {}).get("later_steps", {})
    if hb1 or hb2:
        hold_txt += (f" Split by flow step: the first or only step of a test gives a median error of "
                     f"{pct(hb1.get('median_abs_rel_error'), 0)} (n = {hb1.get('n', 0)}, bias "
                     f"{100 * hb1.get('mean_rel_bias', float('nan')):+.0f} %), while later steps after a flow change give "
                     f"{pct(hb2.get('median_abs_rel_error'), 0)} (n = {hb2.get('n', 0)}). A thick slab needs minutes to "
                     "settle after the flow changes and the per-step window does not yet wait for that, so later-step rates "
                     "stay close to the previous step's rate.")
    sm = val.get("step_matching", [])
    steps_txt = ""
    if sm:
        steps_txt = (f" For slab tests with several flow steps, {sum(x['steps_matched'] for x in sm)} of "
                     f"{sum(x['steps_available'] for x in sm)} published steps could be matched to a measured flow plateau.")

    loop = ROOT / "research/results.tsv"
    loop_txt = ""
    if loop.exists():
        r = pd.read_csv(loop, sep="\t")
        r = r[np.isfinite(r.val_score)]
        kept = r[r.status == "keep"]
        if len(kept):
            b = kept.loc[kept.val_score.idxmin()]
            loop_txt = (f"<p>The autonomous research loop ran <strong>{len(r)}</strong> evaluations against a fixed "
                        f"harness. The best version scores <strong>{b.val_score:.3f}</strong> against "
                        f"<strong>{r.val_score.iloc[0]:.3f}</strong> for the baseline (lower is better). Best change: "
                        f"{html.escape(str(b.description))}.</p>")

    def row(x):
        cls = "ok" if abs(x.rel_error) <= 0.10 else "warn"
        tag = x.qc_status
        return (f"<tr><td>{x.test_id}</td><td>{x.set}</td><td>{tag}</td><td class='num'>{x.vf_measured_mm_s:.4g}</td>"
                f"<td class='num'>[{x.vf_lo:.3g}, {x.vf_hi:.3g}]</td><td class='num'>{x.vf_published_mm_s:.4g}</td>"
                f"<td class='num {cls}'>{100 * x.rel_error:+.1f} %</td></tr>")
    rows = "".join(row(x) for x in vt.itertuples())

    f = fs[fs.target == "leading_edge"] if "target" in fs else fs
    piv = f.pivot_table(index="model", columns="horizon_s", values="MASE")
    cov = f.groupby("model").coverage.mean()
    frows = "".join(f"<tr><td>{m}</td>" + "".join(f"<td class='num'>{v:.2f}</td>" for v in rw.values)
                    + f"<td class='num'>{cov[m]:.2f}</td></tr>" for m, rw in piv.iterrows())
    fhead = "".join(f"<th>h = {h:g} s</th>" for h in piv.columns)
    qc_txt = ", ".join(f"{v} {k.replace('_', ' ')}" for k, v in sorted(qc.items()))

    body = f"""
<title>Flame in Freefall</title>
<meta name="claude:viewport-fit-sides" content="cover">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;700&family=Inter:wght@400;600&family=JetBrains+Mono:wght@400;600&display=swap">
<style>
/* Layout: single reading column (~72ch) with full-width figure plates; key numbers as a 4-up strip */
:root {{
  --bg: #f6f7f9; --surface: #ffffff; --plate: #fcfcfb; --fg: #11161d; --muted: #586170; --line: #dfe3e8;
  --accent: #eb6834; --blue: #2a78d6; --ok: #0c7a3a; --warn: #a3520f; --capt: #3b434e;
  --display: "Space Grotesk", "Segoe UI", system-ui, sans-serif; --text: "Inter", "Segoe UI", system-ui, sans-serif;
  --mono: "JetBrains Mono", ui-monospace, Consolas, monospace;
}}
@media (prefers-color-scheme: dark) {{ :root:not([data-theme="light"]) {{
  --bg: #0e1217; --surface: #151b22; --plate: #fcfcfb; --fg: #e8ecf1; --muted: #9aa5b3; --line: #273039;
  --accent: #f07a48; --blue: #5c9be6; --ok: #4cc27a; --warn: #f0a35c; --capt: #3b434e; color-scheme: dark }} }}
:root[data-theme="dark"] {{ --bg: #0e1217; --surface: #151b22; --plate: #fcfcfb; --fg: #e8ecf1; --muted: #9aa5b3;
  --line: #273039; --accent: #f07a48; --blue: #5c9be6; --ok: #4cc27a; --warn: #f0a35c; --capt: #3b434e; color-scheme: dark }}
body {{ background: var(--bg); color: var(--fg); font: 16px/1.6 var(--text); }}
.wrap {{ max-width: 980px; margin: 0 auto; padding-block: 40px 64px;
  padding-left: max(16px, env(safe-area-inset-left, 0px)); padding-right: max(16px, env(safe-area-inset-right, 0px));
  display: grid; gap: 28px; }}
header {{ display: grid; gap: 10px; }}
.eyebrow {{ font: 600 12px/1.2 var(--mono); letter-spacing: .08em; text-transform: uppercase; color: var(--accent); }}
h1 {{ font: 700 clamp(30px, 5vw, 46px)/1.08 var(--display); margin: 0; text-wrap: balance; }}
h2 {{ font: 700 24px/1.2 var(--display); margin: 18px 0 0; text-wrap: balance; }}
p, li {{ max-width: 72ch; margin: 0; color: var(--fg); }}
.lede {{ font-size: 18px; color: var(--muted); max-width: 66ch; }}
.stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(190px, 1fr)); gap: 12px; }}
.stat {{ background: var(--surface); border: 1px solid var(--line); border-radius: 10px; padding: 14px 16px; display: grid; gap: 4px; }}
.stat b {{ font: 700 28px/1.1 var(--display); font-variant-numeric: tabular-nums; }}
.stat span {{ font-size: 13px; color: var(--muted); }}
ol.steps, ul {{ display: grid; gap: 8px; padding-left: 20px; margin: 0; }}
.plate {{ margin: 0; background: var(--plate); border: 1px solid var(--line); border-radius: 10px; padding: 12px; display: grid; gap: 10px; }}
.plate img {{ width: 100%; height: auto; display: block; }}
.plate figcaption {{ color: var(--capt); font-size: 14px; line-height: 1.55; max-width: none; }}
.tablebox {{ overflow-x: auto; background: var(--surface); border: 1px solid var(--line); border-radius: 10px; }}
table {{ border-collapse: collapse; width: 100%; font-size: 14px; }}
th, td {{ padding: 8px 12px; border-bottom: 1px solid var(--line); text-align: left; white-space: nowrap; }}
th {{ font: 600 12px/1.3 var(--mono); letter-spacing: .04em; text-transform: uppercase; color: var(--muted); }}
td.num {{ font-family: var(--mono); font-variant-numeric: tabular-nums; text-align: right; }}
td.ok {{ color: var(--ok); }} td.warn {{ color: var(--warn); }}
code {{ font: 13px var(--mono); background: var(--surface); border: 1px solid var(--line); border-radius: 4px; padding: 1px 4px; }}
.note {{ border-left: 3px solid var(--accent); padding: 4px 0 4px 14px; color: var(--muted); }}
</style>
<div class="wrap">
<header>
  <div class="eyebrow">NASA PSI-25 · BASS-II · ISS Microgravity Science Glovebox · 2014</div>
  <h1>Measuring and forecasting flame spread in microgravity from ISS video</h1>
  <p class="lede">An automatic computer-vision pipeline tracks the flame front in the Burning and Suppression of Solids II
  videos, converts it to millimetres with the duct's own ruler, compares the spread rates with those NASA investigators
  published, and forecasts how the flame front evolves.</p>
</header>
<section class="stats" aria-label="Key results">
  <div class="stat"><b>{tle.get('slope', float('nan')):.2f} ± {tle.get('slope_se', float('nan')):.2f}</b><span>thin-film thickness-law slope over {tle.get('n', 0)} films, 4 of them never used for tuning (theory −1; scale-independent)</span></div>
  <div class="stat"><b>{pct(dev_all.get('median_abs_rel_error'))}</b><span>median error on {dev_all.get('n', 0)} development tests (in-sample)</span></div>
  <div class="stat"><b>{pct(hold_all.get('median_abs_rel_error'), 0) if hold_all else 'pending'}</b><span>{'median error on ' + str(hold_all.get('n', 0)) + ' hold-out slab steps (frozen settings)' if hold_all else 'hold-out slab tests: NASA download endpoint unavailable at build time'}</span></div>
  <div class="stat"><b>{scale:.4f}</b><span>mm per pixel from the duct ruler (±{scale_cv:.1f} % across tests)</span></div>
</section>

<h2>How the measurement works</h2>
<ol class="steps">
  <li>Download each test's side-view video from the NASA PSI repository (720×480, 29.97 fps, non-square pixels corrected).</li>
  <li>Read the burned-in telemetry (air velocity, fan voltage, radiometer, clock) by template OCR and mask it out.</li>
  <li>Skip frames with the cabin lights on, mask static artefacts, and segment the luminous flame with thresholds relative to each frame's noise so faint blue edges survive.</li>
  <li>Convert pixels to millimetres with the duct's ruler, visible in the illuminated frames before ignition.</li>
  <li>Split the front's trajectory into linear regimes (ignition, spread under flow, spread after a flow change, extinction) and fit the steady spread rate with a robust Theil-Sen regression.</li>
  <li>Backtest forecasting models on the measured series and compare the rates with published values.</li>
</ol>

<h2>One test, end to end: B1 (100 µm PMMA film, opposed flow)</h2>
{figure('B1/G1_overlay.png', files)}
{figure('B1/G2_kymograph.png', files)}
{figure('B1/G3_edge_fit.png', files)}
{figure('B1/G18_telemetry.png', files)}

<h2>How close is it to NASA's published numbers?</h2>
<p class="note">The spatial calibration uses no published value. Published rates of the development tests (B1–B5, B7,
B12, M1) were used to choose the segmentation and regime settings, so their accuracy is in-sample. The hold-out slab
tests were processed only after every setting was frozen. A physics review that flagged implausible results was done
with the published values visible, so filtered statistics are shown next to unfiltered ones.</p>
<p>Development tests: median error {pct(dev_all.get('median_abs_rel_error'))}, bias {100 * dev_all.get('mean_rel_bias', float('nan')):+.1f} %.
{hold_txt}{steps_txt}
Thick slabs burn for 10 to 30 minutes with very dim late phases, which is where the automatic regime choice is least reliable.</p>
<div class="tablebox"><table>
<thead><tr><th>Comparison</th><th>Set</th><th>Physics QC</th><th>Measured V<sub>f</sub> (mm/s)</th><th>95 % CI</th><th>Published (mm/s)</th><th>Difference</th></tr></thead>
<tbody>{rows}</tbody></table></div>
{figure('_ensemble/G6_parity_published.png', files)}
{figure('_ensemble/G19_thickness_law.png', files)}
{figure('_ensemble/G15_threshold_sensitivity.png', files)}

<h2>What the whole dataset shows</h2>
<p>{n_tests} tests were processed. A physics review classified them as: {qc_txt}. Only the {n_trusted} trusted tests
enter the ensemble figures below; excluded tests are missed dim burns, igniter-flash or ignition-growth regimes, rods
where the video measures flame-length settling rather than spread, or tests with too little footage.</p>
{figure('_ensemble/G13_conditions.png', files)}
{figure('_ensemble/G5_spread_vs_flow.png', files)}

<h2>Forecasting the flame front</h2>
<p>Each steady-spread series of the trusted tests is cut at several points in time and every model forecasts the next
1 to 10 seconds of the leading-edge position. MASE below 1 beats a naive one-step forecast; coverage is the share of
observations inside the 90 % interval. The steady windows are chosen with hindsight, so these numbers describe
forecasting within a steady regime.</p>
<div class="tablebox"><table><thead><tr><th>Model</th>{fhead}<th>Coverage</th></tr></thead><tbody>{frows}</tbody></table></div>
{figure('B1/G9_forecast.png', files)}
{figure('_ensemble/G11_skill.png', files)}
{figure('_ensemble/G12_calibration.png', files)}
{figure('_ensemble/G10_residuals.png', files)}
{loop_txt}
{figure('_ensemble/G16_loop_progress.png', files)}

<h2>Limitations</h2>
<ul>
  <li>The ruler graduation (1 cm major marks) is inferred from the 76 mm duct geometry; NASA documents do not state it.</li>
  <li>Development-test accuracy is in-sample; the hold-out slab steps are the out-of-sample evidence.</li>
  <li>For thick slabs, rates after a flow change are over-estimated because the measurement window starts before the flame re-equilibrates.</li>
  <li>Faint flames depend on the segmentation threshold (figure G15); that systematic uncertainty is not in the per-test intervals.</li>
  <li>Segmentation is scored on synthetic flames until a hand-labelled gold set exists.</li>
  <li>The B14, B18 and B20 main videos are truncated on the NASA server; their original MPEG-TS recordings were used instead.</li>
</ul>
<p class="note">Data: NASA Physical Sciences Informatics, investigation PSI-25 (DOI 10.60555/4qc4-de67), CC0. Published reference
rates: SDSU BASS repository (B tests) and NASA/TM-20210011385 Table 5.1 (M tests).</p>
</div>
"""
    out = SITE / "index.html"
    out.write_text(body, encoding="utf-8")
    # publish map with paths relative to the project root (no absolute local paths in the repository)
    (SITE / "files.json").write_text(json.dumps({k: Path(v).relative_to(ROOT).as_posix() for k, v in files.items()}, indent=1))
    return {"page": str(out), "files": files}


if __name__ == "__main__":
    r = main()
    print(r["page"], len(r["files"]), "figures")
