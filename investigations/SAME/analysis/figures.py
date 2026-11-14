"""Scientific figures for the SAME dashboard (static PNG, light surface).

Style rules (dataviz method): one categorical hue per material in fixed order, plus a marker
shape per material as secondary encoding; filled = unaged / with flow, hollow = aged / no flow;
thin marks; recessive grid; direct labels; no dual axes; text in neutral ink.
"""
from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import matplotlib.ticker  # noqa: E402,F401
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from analysis import physics as ph  # noqa: E402
from extraction.common import ANALYSIS_OUT, FIGURES_DIR, MATERIAL_ORDER  # noqa: E402

SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK2 = "#52514e"
GRID = "#e4e3df"
COLORS = dict(zip(MATERIAL_ORDER, ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4"]))
MARKERS = dict(zip(MATERIAL_ORDER, ["o", "s", "^", "D", "v"]))
DET_COLORS = {"ISS photoelectric": "#2a78d6", "Ionization chamber": "#eb6834", "STS alarm": "#6250d6"}

plt.rcParams.update({
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
    "axes.edgecolor": "#b9b8b3", "axes.labelcolor": INK, "xtick.color": INK2, "ytick.color": INK2,
    "text.color": INK, "axes.titleweight": "bold", "axes.titlesize": 11, "axes.labelsize": 9.5,
    "xtick.labelsize": 8.5, "ytick.labelsize": 8.5, "legend.fontsize": 8.5, "legend.frameon": False,
    "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.6, "axes.axisbelow": True,
    "axes.spines.top": False, "axes.spines.right": False, "font.family": "DejaVu Sans", "lines.linewidth": 2,
})


def _save(fig, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return path


def _note(fig, text, y=-0.02):
    fig.text(0.01, y, text, ha="left", va="top", fontsize=8, color=INK2, wrap=True)


def _material_legend(ax, loc="best", hollow_label=None, filled_label=None):
    handles = [plt.Line2D([], [], ls="", marker=MARKERS[m], ms=7, mfc=COLORS[m], mec=COLORS[m], label=m)
               for m in MATERIAL_ORDER]
    if filled_label:
        handles += [plt.Line2D([], [], ls="", marker="o", ms=7, mfc=INK2, mec=INK2, label=filled_label),
                    plt.Line2D([], [], ls="", marker="o", ms=7, mfc="none", mec=INK2, mew=1.5, label=hollow_label)]
    ax.legend(handles=handles, loc=loc, ncol=1)


# --------------------------------------------------------------------------- 1. overview
def overview(r) -> str:
    st = r["size_by_material"]
    pub = r["data"]["published_table1_baseline"]
    ov = r["detection_overall"]
    led = r["ledger"]
    fig, axs = plt.subplots(1, 3, figsize=(15.5, 4.8), gridspec_kw={"width_ratios": [1.15, 1, 0.9]})

    ax = axs[0]
    for i, m in enumerate(MATERIAL_ORDER):
        u = st[(st.material == m) & (st.aged_state == "unaged")].dm_um
        a = st[(st.material == m) & (st.aged_state == "aged")].dm_um
        if len(u) and len(a):
            ax.plot([u.iloc[0], a.iloc[0]], [i, i], color=COLORS[m], lw=2, zorder=1)
            ax.plot(u.iloc[0], i, MARKERS[m], ms=9, color=COLORS[m], zorder=2)
            ax.plot(a.iloc[0], i, MARKERS[m], ms=9, mfc=SURFACE, mec=COLORS[m], mew=2, zorder=2)
            ax.text(a.iloc[0] + 0.02, i + 0.18, f"{u.iloc[0]:.2f} → {a.iloc[0]:.2f} µm", fontsize=8, color=INK2)
        pu = pub[(pub.material == m)]
        ax.plot(pu.dm_um, [i, i], "|", color=INK, ms=11, mew=1.3, zorder=3)
    ax.set_yticks(range(5), MATERIAL_ORDER)
    ax.invert_yaxis()
    ax.set_xlim(0, 0.75)
    ax.set_xlabel("Diameter of average mass, Dm (µm)")
    ax.set_title("Smoke particles grow while they age (8 cm/s flow)")
    ax.legend(handles=[plt.Line2D([], [], ls="", marker="o", ms=8, color=INK2, label="unaged (~38 s)"),
                       plt.Line2D([], [], ls="", marker="o", ms=8, mfc=SURFACE, mec=INK2, mew=2,
                                  label="aged (~570–830 s)"),
                       plt.Line2D([], [], ls="", marker="|", ms=11, mew=1.3, color=INK,
                                  label="published Table 1")], loc="lower right")

    ax = axs[1]
    regimes = [("flow_8cm_s", "With flow (8 cm/s)"), ("no_flow", "No flow (quiescent)")]
    x = np.arange(2)
    w = 0.36
    for k, (det, key) in enumerate([("ISS photoelectric", "iss_rate"), ("Ionization chamber", "ion_rate")]):
        vals = [100 * ov[reg][key] for reg, _ in regimes]
        bars = ax.bar(x + (k - 0.5) * (w + 0.02), vals, w, color=DET_COLORS[det], label=det)
        for b, v in zip(bars, vals):
            ax.text(b.get_x() + b.get_width() / 2, v + 2, f"{v:.0f}%", ha="center", fontsize=9, color=INK)
    ax.set_xticks(x, [f"{lbl}\n(n={ov[reg]['n_pushes']} pushes)" for reg, lbl in regimes])
    ax.set_ylim(0, 112)
    ax.set_ylabel("Pushes above proxy response threshold (%)")
    ax.set_title("The two detector types fail in opposite regimes")
    ax.legend(loc="upper right", ncol=1)

    ax = axs[2]
    base, best = led.iloc[0], led.loc[led.val_score.idxmin()]
    cats = ["Particle size\n(NRMSE)", "Detection\n(Brier ratio)"]
    bv = [base.size_nrmse, base.detection_brier_ratio]
    mv = [best.size_nrmse, best.detection_brier_ratio]
    xx = np.arange(2)
    ax.bar(xx - 0.2, bv, 0.36, color="#b9b8b3", label="baseline (mean)")
    ax.bar(xx + 0.2, mv, 0.36, color="#1baf7a", label=f"selected model (#{int(best.attempt)})")
    for i in range(2):
        ax.text(xx[i] - 0.2, bv[i] + 0.03, f"{bv[i]:.2f}", ha="center", fontsize=9)
        ax.text(xx[i] + 0.2, mv[i] + 0.03, f"{mv[i]:.2f}", ha="center", fontsize=9)
    ax.set_xticks(xx, cats)
    ax.set_ylim(0, 1.3)
    ax.set_ylabel("Held-out error relative to spread (lower is better)")
    ax.set_title("AutoResearch model vs. baseline")
    ax.legend(loc="upper right")
    _note(fig, "Left: NASA moment-method medians per material (this study) with published Table 1 ticks. Middle: "
               "share of piston pushes whose response exceeded the proxy thresholds (ISS scatter drop ≥ 1.0 V; "
               "ionization-chamber rise ≥ 0.5 V) — not flight alarm set points. Right: leave-one-run/test-out errors; "
               "1.0 = no better than predicting the average.", y=-0.06)
    return _save(fig, ANALYSIS_OUT / "same-summary.png")


# --------------------------------------------------------------------------- 2. moments by material
def moments_by_material(r) -> str:
    s = r["data"]["size_dataset"]
    s = s[s.include_in_model & (s.no_flow == 0)]
    pub = r["data"]["published_table1_baseline"]
    panels = [("dg_um", "Dg, geometric mean (µm)", "dg_um"), ("amd_um", "AMD = M1/M0 (µm)", "amd_um"),
              ("dm_um", "Dm = (M3/M0)^(1/3) (µm)", "dm_um"), ("sigma_g", "σg, geometric std. dev.", "sigma_g")]
    fig, axs = plt.subplots(1, 4, figsize=(16, 4.4), sharey=False)
    for ax, (col, title, pcol) in zip(axs, panels):
        for i, m in enumerate(MATERIAL_ORDER):
            for j, (state, off) in enumerate([("unaged", -0.17), ("aged", 0.17)]):
                v = s[(s.material == m) & (s.aged_state == state)][col]
                xs = np.full(len(v), i + off) + np.linspace(-0.05, 0.05, max(len(v), 1))[:len(v)]
                ax.plot(xs, v, MARKERS[m], ms=6, color=COLORS[m], mfc=COLORS[m] if state == "unaged" else SURFACE,
                        mew=1.5, ls="")
                pv = pub[(pub.material == m) & (pub.aged_state == state)][pcol]
                if len(pv):
                    ax.plot(i + off, pv.iloc[0], "_", color=INK, ms=14, mew=1.6)
        ax.set_xticks(range(5), MATERIAL_ORDER, rotation=30)
        ax.set_title(title, fontsize=9.5)
    axs[0].legend(handles=[plt.Line2D([], [], ls="", marker="o", color=INK2, label="unaged"),
                           plt.Line2D([], [], ls="", marker="o", mfc=SURFACE, mec=INK2, mew=1.5, label="aged"),
                           plt.Line2D([], [], ls="", marker="_", ms=14, mew=1.6, color=INK, label="published")],
                  loc="upper left")
    fig.suptitle("Moment-method size statistics per material (SAME-R, 8 cm/s flow; one point per TEM grid / measurement)",
                 x=0.01, ha="left", fontsize=11.5, fontweight="bold")
    _note(fig, "Dg and σg assume a log-normal distribution; AMD and Dm do not. Kapton and Teflon smoke is the smallest "
               "(Dm ≈ 0.1–0.2 µm); Pyrell, lampwick and silicone are 2–4× larger. Aging narrows σg toward the "
               "self-preserving limit. Horizontal black ticks: Urban et al. (2012) Table 1.", y=-0.04)
    return _save(fig, FIGURES_DIR / "moments_by_material.png")


# --------------------------------------------------------------------------- 3. aging & coagulation
def aging_coagulation(r) -> str:
    p = r["aging_pairs"]
    k_med = r["coagulation"]["pairs_k_median_flow_cm3_s"]
    fig, axs = plt.subplots(1, 2, figsize=(12.5, 4.8))
    ax = axs[0]
    t = np.linspace(0, 900, 200)
    for n0, ls in [(3.0e6, "-"), (3.0e5, "--")]:
        ax.plot(t, 1 / (1 + k_med * n0 * t), ls, color=INK2, lw=1.4,
                label=f"Smoluchowski, K={k_med:.1e} cm³/s, N0={n0:.0e}/cm³")
    for r_ in p.itertuples():
        m = r_.material
        ax.plot(r_.delta_t_s, r_.m0_ratio_aged_over_unaged, MARKERS[m], ms=8, color=COLORS[m],
                mfc=COLORS[m] if r_.no_flow == 0 else SURFACE, mew=1.8, ls="")
    ax.set_xlabel("Extra time in the aging chamber, Δt (s)")
    ax.set_ylabel("Number concentration ratio, M0(aged) / M0(unaged)")
    ax.set_ylim(0, 1.05)
    ax.set_title("Brownian coagulation removes 50–75% of particles in ~10 min")
    ax.legend(loc="lower left", fontsize=7.8)
    ax = axs[1]
    lim = [0.95, 1.65]
    ax.plot(lim, lim, color=INK2, lw=1, ls=":")
    ax.text(1.5, 1.53, "1:1", color=INK2, fontsize=8)
    for r_ in p.itertuples():
        m = r_.material
        ax.plot(r_.dm_growth_if_mass_conserved, r_.dm_growth, MARKERS[m], ms=8, color=COLORS[m],
                mfc=COLORS[m] if r_.no_flow == 0 else SURFACE, mew=1.8, ls="")
    ax.set_xlim(lim)
    ax.set_ylim(lim)
    ax.set_xlabel("Dm growth predicted by mass conservation, (N_unaged / N_aged)^(1/3)")
    ax.set_ylabel("Observed Dm growth, Dm(aged) / Dm(unaged)")
    ax.set_title("Particle growth matches pure coagulation")
    _material_legend(ax, loc="upper left", filled_label="8 cm/s flow", hollow_label="no flow")
    _note(fig, "Each point is one run with both an unaged and an aged moment measurement. With flow, the measured "
               "growth equals what coagulation alone predicts (mass conserved, little wall loss). Without flow the smoke "
               "was already concentrated and coagulated near the heater before it reached the chamber, so further "
               "aging changes little (hollow markers near 1).", y=-0.02)
    return _save(fig, FIGURES_DIR / "aging_coagulation.png")


# --------------------------------------------------------------------------- 4. flow effect
def flow_effect(r) -> str:
    fe = r["flow_effect"]
    fig, axs = plt.subplots(1, 2, figsize=(11.5, 4.2))
    for ax, (a, b, lab, scale) in zip(axs, [("dm_flow_um", "dm_no_flow_um", "Dm (µm)", 1),
                                            ("m0_flow", "m0_no_flow", "M0 (particles/cm³)", 1)]):
        for i, row in enumerate(fe.itertuples()):
            m = row.material
            va, vb = getattr(row, a), getattr(row, b)
            ax.plot([va, vb], [i, i], color=COLORS[m], lw=2)
            ax.plot(va, i, MARKERS[m], ms=9, color=COLORS[m])
            ax.plot(vb, i, MARKERS[m], ms=9, mfc=SURFACE, mec=COLORS[m], mew=2)
            ax.text(max(va, vb) * (1.08 if a == "m0_flow" else 1.0) + (0 if a == "m0_flow" else 0.03), i,
                    f"×{vb / va:.1f}", va="center", fontsize=8.5, color=INK2)
        ax.set_yticks(range(len(fe)), fe.material)
        ax.invert_yaxis()
        ax.set_xlabel(lab)
        if a == "m0_flow":
            ax.set_xscale("log")
    axs[0].set_title("Quiescent smoke has larger particles…")
    axs[1].set_title("…but far fewer of them")
    axs[1].legend(handles=[plt.Line2D([], [], ls="", marker="o", color=INK2, label="8 cm/s flow"),
                           plt.Line2D([], [], ls="", marker="o", mfc=SURFACE, mec=INK2, mew=2, label="no flow")],
                  loc="lower left")
    _note(fig, "Unaged measurements only; medians per material (silicone had no no-flow test). Without flow, pyrolysis "
               "products stay concentrated around the heater (no buoyancy in microgravity), coagulate fast and part of "
               "the plume diffuses out of the inlet — the low-count, large-particle smoke that an avionics box or a "
               "stagnant cabin corner could produce.", y=-0.02)
    return _save(fig, FIGURES_DIR / "flow_effect.png")


# --------------------------------------------------------------------------- 5. detector comparison
def detector_comparison(r) -> str:
    d = r["data"]["detection_dataset"]
    d = d[d.include_in_model]
    fig, axs = plt.subplots(1, 2, figsize=(14, 5.2), gridspec_kw={"width_ratios": [1.1, 1], "wspace": 0.55})
    ax = axs[0]
    ax.axhline(1.0, color=DET_COLORS["ISS photoelectric"], lw=1, ls="--")
    ax.axvline(0.5, color=DET_COLORS["Ionization chamber"], lw=1, ls="--")
    for row in d.itertuples():
        m = row.material
        ax.plot(row.ion_b_delta_peak_v, row.iss_scatter_delta_peak_v, MARKERS[m], ms=7, color=COLORS[m],
                mfc=COLORS[m] if row.no_flow == 0 else SURFACE, mew=1.6, ls="", alpha=0.95)
    ax.set_xlabel("Ionization-chamber response (V rise; ~ first moment, M1)")
    ax.set_ylabel("ISS detector forward-scatter response (V drop; saturates ≈ 6.1)")
    ax.set_xlim(-0.1, 3.4)
    ax.set_ylim(-0.2, 7.4)
    ax.text(0.0, 7.3, "ISS sees it,\nionization does not", fontsize=8.5, color=INK2, va="top")
    ax.text(1.6, 0.25, "ionization sees it,\nISS does not", fontsize=8.5, color=INK2)
    ax.text(0.52, 1.08, "ISS proxy threshold 1.0 V", fontsize=7.5, color=DET_COLORS["ISS photoelectric"])
    ax.text(0.53, 3.4, "ion proxy\nthreshold 0.5 V", fontsize=7.5, color=DET_COLORS["Ionization chamber"], rotation=90)
    ax.set_title("Each push: response of the two detector principles")
    handles = [plt.Line2D([], [], ls="", marker=MARKERS[m], ms=7, mfc=COLORS[m], mec=COLORS[m], label=m)
               for m in MATERIAL_ORDER]
    handles += [plt.Line2D([], [], ls="", marker="o", ms=7, mfc=INK2, mec=INK2, label="8 cm/s flow"),
                plt.Line2D([], [], ls="", marker="o", ms=7, mfc="none", mec=INK2, mew=1.5, label="no flow")]
    ax.legend(handles=handles, loc="center right", ncol=1, bbox_to_anchor=(1.0, 0.42), framealpha=0.9,
              frameon=True, edgecolor=GRID)

    ax = axs[1]
    rates = r["detection_rates"]
    labels, iss, ion = [], [], []
    for row in rates.itertuples():
        labels.append(f"{row.material} · {'flow' if row.flow_regime == 'flow_8cm_s' else 'no flow'} (n={row.n_pushes})")
        iss.append(100 * row.iss_rate)
        ion.append(100 * row.ion_rate)
    y = np.arange(len(labels))
    ax.barh(y - 0.2, iss, 0.38, color=DET_COLORS["ISS photoelectric"], label="ISS photoelectric")
    ax.barh(y + 0.2, ion, 0.38, color=DET_COLORS["Ionization chamber"], label="Ionization chamber")
    for yi, a, b in zip(y, iss, ion):
        ax.text(a + 1.5, yi - 0.2, f"{a:.0f}%", va="center", fontsize=7.8)
        ax.text(b + 1.5, yi + 0.2, f"{b:.0f}%", va="center", fontsize=7.8)
    ax.set_yticks(y, labels, fontsize=8)
    ax.invert_yaxis()
    ax.set_xlim(0, 115)
    ax.set_xlabel("Pushes above proxy threshold (%)")
    ax.set_title("Detection rate by material and flow")
    ax.legend(loc="lower right")
    _note(fig, "Light scattering (ISS) weights particles by mass/area and misses the ~0.1 µm Kapton and Teflon smoke; the "
               "ionization chamber weights particle number × diameter and misses the dilute, large-particle smoke made "
               "without flow. Thresholds are project-defined proxies relative to each test's clean-air baseline, not the "
               "flight alarm logic.", y=-0.02)
    return _save(fig, FIGURES_DIR / "detector_comparison.png")


def threshold_sensitivity(r) -> str:
    t = r["threshold_sensitivity"]
    fig, axs = plt.subplots(1, 2, figsize=(11.5, 4.2), sharey=True)
    for ax, det, col, ref in [(axs[0], "ISS photoelectric (scatter)", DET_COLORS["ISS photoelectric"], 1.0),
                              (axs[1], "Ionization chamber (first moment)", DET_COLORS["Ionization chamber"], 0.5)]:
        for reg, ls, mk, lab in [("flow_8cm_s", "-", "o", "8 cm/s flow"), ("no_flow", "--", "s", "no flow")]:
            s = t[(t.detector == det) & (t.flow_regime == reg)]
            ax.plot(s.threshold_v, 100 * s.detection_rate, ls, marker=mk, color=col, mfc=col if reg == "flow_8cm_s" else SURFACE,
                    mew=1.6, ms=7, label=lab)
            ax.text(s.threshold_v.iloc[-1], 100 * s.detection_rate.iloc[-1] + 3, lab, fontsize=8, color=INK2, ha="right")
        ax.axvline(ref, color=INK2, lw=0.8, ls=":")
        ax.text(ref, 104, " used", fontsize=8, color=INK2)
        ax.set_title(det)
        ax.set_xlabel("Response threshold (V)")
        ax.set_ylim(0, 110)
    axs[0].set_ylabel("Pushes detected (%)")
    _note(fig, "How the conclusions depend on the chosen proxy thresholds. The opposite failure modes (ISS weaker with flow "
               "for small particles; ionization near-blind without flow) hold over the whole range tested.", y=-0.02)
    return _save(fig, FIGURES_DIR / "threshold_sensitivity.png")


# --------------------------------------------------------------------------- 6. example time series
def example_timeseries(r, test=64) -> str:
    ts = pd.read_csv(FIGURES_DIR.parent / "hkp_timeseries_clean.csv.gz")
    g = ts[ts.test == test]
    pu = r["data"]["pushes"]
    pu = pu[pu.test == test]
    t = g.t_s
    chans = [("gas_plume_temp_c", "Plume temperature (°C)", INK2),
             ("ptrak_raw_pt_cc", "P-Trak, diluted (#/cm³)  → M0", "#2a78d6"),
             ("ion_b_v", "Ionization chamber (V)  → M1", "#eb6834"),
             ("dusttrak_b_mg_m3", "DustTrak (mg/m³)  → M3", "#1baf7a"),
             ("iss_scatter_v", "ISS detector scatter (V)", "#6250d6")]
    fig, axs = plt.subplots(len(chans), 1, figsize=(12, 9), sharex=True)
    heat = g[g.heating == 1].t_s
    for ax, (c, lab, col) in zip(axs, chans):
        ax.plot(t, g[c], color=col, lw=1.3)
        ax.set_ylabel(lab, fontsize=8.5, rotation=0, ha="right", va="center")
        if len(heat):
            ax.axvspan(heat.min(), heat.max(), color="#fde7dc", zorder=0)
        for p in pu.itertuples():
            ax.axvspan(p.push_start_s, p.push_start_s + p.push_duration_s, color="#e3eefb", zorder=0)
    top = axs[0]
    if len(heat):
        top.text(heat.mean(), top.get_ylim()[1] * 0.95, "heating", ha="center", va="top", fontsize=8)
    for p in pu.itertuples():
        top.text(p.push_start_s, top.get_ylim()[1] * 0.95, f" push {p.push_index}\n aged {p.aging_s:.0f} s",
                 fontsize=8, va="top")
    axs[-1].set_xlabel("Seconds since start of test record")
    mat = r["data"]["tests"].set_index("test").loc[test, "material"]
    fig.suptitle(f"Anatomy of one SAME-R test (test {test}, {mat}): heat → fill → age → push to the detectors",
                 x=0.01, ha="left", fontsize=11.5, fontweight="bold")
    _note(fig, "Orange band: ~53 s of sample heating while the aging-chamber piston draws air past the sample. Blue bands: "
               "piston pushes that send aged smoke through the diagnostics duct. The second push carries the same smoke "
               "after ~13 more minutes of coagulation: P-Trak count falls while scattering instruments change little.",
          y=0.0)
    return _save(fig, FIGURES_DIR / "example_timeseries.png")


# --------------------------------------------------------------------------- 7. size distributions
def size_distributions(r) -> str:
    st = r["size_by_material"]
    fig, axs = plt.subplots(1, 2, figsize=(13, 4.6), gridspec_kw={"width_ratios": [1.3, 1]})
    ax = axs[0]
    d = np.logspace(-2.3, 0.7, 400)
    ax.axvspan(0.3, 5, color="#eef3fb", zorder=0)
    ax.text(0.33, 0.80, "light scattering\nmost efficient (≳ 0.3 µm)", fontsize=8, color=INK2, va="top")
    for m in MATERIAL_ORDER:
        for state, ls in [("unaged", "-"), ("aged", "--")]:
            row = st[(st.material == m) & (st.aged_state == state)]
            if not len(row):
                continue
            y = ph.lognormal_pdf_dlnd(d, row.dg_um.iloc[0], row.sigma_g.iloc[0])
            ax.plot(d, y, ls, color=COLORS[m], lw=1.8)
        row = st[(st.material == m) & (st.aged_state == "unaged")]
        ax.text(row.dg_um.iloc[0], ph.lognormal_pdf_dlnd(row.dg_um.iloc[0], row.dg_um.iloc[0], row.sigma_g.iloc[0]) + 0.02,
                m, color=INK, fontsize=8, ha="center")
    ax.set_xscale("log")
    ax.set_xlabel("Particle diameter (µm)")
    ax.set_ylabel("Number distribution dN/(N dlnD)")
    ax.set_title("Reconstructed log-normal number distributions")
    ax.legend(handles=[plt.Line2D([], [], color=INK2, ls="-", label="unaged"),
                       plt.Line2D([], [], color=INK2, ls="--", label="aged")], loc="upper right")

    ax = axs[1]
    tp = pd.read_csv(FIGURES_DIR.parent / "tem_particles.csv")
    tp = tp[tp.particle_set == "54_all_data"].diameter_um
    bins = np.logspace(np.log10(0.01), np.log10(2), 26)
    ax.hist(tp, bins=bins, density=False, color="#86b6ef", edgecolor=SURFACE, lw=1, label=f"TEM, run 54 (n={len(tp)})")
    mm = r["data"]["nasa_moment_table"].query("run == 54").iloc[0]
    dlog = np.log(bins[1]) - np.log(bins[0])
    yy = ph.lognormal_pdf_dlnd(d, mm.dg_um_from_amd, mm.sigma_g_hc) * len(tp) * dlog
    ax.plot(d, yy, color="#eb6834", lw=2, label=f"moment method (Dg={mm.dg_um_from_amd:.3f} µm, σg={mm.sigma_g_hc:.2f})")
    ax.set_xscale("log")
    ax.set_xlim(0.008, 3)
    ax.set_xlabel("Equivalent-circle diameter (µm)")
    ax.set_ylabel("Particles per bin")
    ax.set_title("TEM sizing vs. moment method (lampwick, run 54)")
    ax.legend(loc="upper left", fontsize=7.8)
    _note(fig, "Left: log-normal distributions rebuilt from each material's median Dg and σg (8 cm/s flow). Kapton and Teflon "
               "put almost no particles where light scattering is efficient. Right: TEM counts fewer of the smallest "
               "particles (hard to image, liquid droplets evaporate in the beam), so its mean diameter is 2–3× the "
               "moment-method value; the in-flight moments are the less biased number statistics.", y=-0.02)
    return _save(fig, FIGURES_DIR / "size_distributions.png")


# --------------------------------------------------------------------------- 8. model figures
def model_cv(r) -> str:
    full = r["attempts"]["best_full"]
    sz = pd.DataFrame(full["cv_predictions"]["size"])
    dt = pd.DataFrame(full["cv_predictions"]["detection"])
    fig, axs = plt.subplots(1, 4, figsize=(17, 4.3))
    for ax, (t, lab, tr) in zip(axs[:3], [("log10_dm_um", "Dm (µm)", lambda v: 10 ** v),
                                         ("ln_sigma_g", "σg", np.exp), ("log10_m0_per_cc", "M0 (#/cm³)", lambda v: 10 ** v)]):
        obs, pred = tr(sz[f"{t}_observed"]), tr(sz[f"{t}_predicted"])
        vmin, vmax = min(obs.min(), pred.min()) * 0.85, max(obs.max(), pred.max()) * 1.15
        ax.plot([vmin, vmax], [vmin, vmax], ":", color=INK2, lw=1)
        for m in MATERIAL_ORDER:
            k = sz.material == m
            ax.plot(obs[k], pred[k], MARKERS[m], ms=7, color=COLORS[m], ls="", alpha=0.9, label=m)
        if t != "ln_sigma_g":
            ax.set_xscale("log")
            ax.set_yscale("log")
            for axis in (ax.xaxis, ax.yaxis):
                axis.set_minor_formatter(matplotlib.ticker.NullFormatter())
            if t == "log10_m0_per_cc":
                tk = [2e5, 5e5, 1e6, 2e6, 4e6]
                ax.set_xticks(tk, ["2e5", "5e5", "1e6", "2e6", "4e6"])
                ax.set_yticks(tk, ["2e5", "5e5", "1e6", "2e6", "4e6"])
        ax.set_xlim(vmin, vmax)
        ax.set_ylim(vmin, vmax)
        ax.set_xlabel(f"Observed {lab}")
        ax.set_ylabel(f"Held-out prediction {lab}")
        nr = full["size_nrmse_by_target"][t]
        ax.set_title(f"{lab}: NRMSE {nr:.2f}")
    axs[0].legend(loc="upper left", fontsize=7.5)
    ax = axs[3]
    for det, col, lab in [("iss_detect", DET_COLORS["ISS photoelectric"], "ISS photoelectric"),
                          ("ion_detect", DET_COLORS["Ionization chamber"], "Ionization chamber")]:
        pr, ob = dt[f"{det}_probability"], dt[f"{det}_observed"]
        bins = np.array([0, 0.2, 0.4, 0.6, 0.8, 1.0001])
        idx = np.digitize(pr, bins) - 1
        xs, ys, ns = [], [], []
        for b in range(len(bins) - 1):
            k = idx == b
            if k.sum():
                xs.append(pr[k].mean()); ys.append(ob[k].mean()); ns.append(k.sum())
        ax.scatter(xs, ys, s=[18 + 6 * n for n in ns], color=col, alpha=0.75, edgecolor=SURFACE, lw=1,
                   label=f"{lab} (Brier ratio {full['detection_brier_ratio_by_target'][det]:.2f})")
        for x_, y_, n_ in zip(xs, ys, ns):
            ax.text(x_, y_ + (0.06 if det == "iss_detect" else -0.09), f"n={n_}", fontsize=7, color=col, ha="center")
    ax.plot([0, 1], [0, 1], ":", color=INK2, lw=1)
    ax.set_xlabel("Predicted probability (held out)")
    ax.set_ylabel("Observed detection frequency")
    ax.set_title("Detection probabilities: calibration")
    ax.set_xlim(-0.05, 1.05)
    ax.set_ylim(-0.15, 1.15)
    ax.legend(loc="upper left", fontsize=7.5)
    ax.text(0.98, 0.02, "marker area ∝ pushes in bin", fontsize=7, color=INK2, ha="right", transform=ax.transAxes)
    _note(fig, "Every prediction comes from a model that never saw that run (size) or test (detection). NRMSE = RMSE / spread "
               "of the target; 1.0 would be no better than the average. Dm is predicted within a typical factor of "
               f"{full['size_factor_error']['log10_dm_um']:.2f} and M0 within {full['size_factor_error']['log10_m0_per_cc']:.2f}.",
          y=-0.02)
    return _save(fig, FIGURES_DIR / "model_cv.png")


def autoresearch_progress(r) -> str:
    led = r["ledger"]
    fig, ax = plt.subplots(figsize=(11, 4.3))
    best = np.minimum.accumulate(led.val_score.where(led.status == "keep", np.inf).to_numpy())
    ax.step(led.attempt, best, where="post", color="#1baf7a", lw=2, label="best so far")
    for st, mk, col in [("keep", "o", "#1baf7a"), ("discard", "x", INK2), ("crash", "s", "#e34948")]:
        s = led[led.status == st]
        if len(s):
            ax.plot(s.attempt, s.val_score, mk, ls="", ms=8, color=col, mew=2, label=st)
    for row in led.itertuples():
        if row.status == "keep":
            ax.text(row.attempt, row.val_score + 0.03, f"{row.val_score:.3f}", fontsize=7.5, ha="center", color=INK2)
    ax.set_xlabel("Attempt")
    ax.set_ylabel("val_score (lower is better)")
    ax.set_xticks(led.attempt)
    ax.set_ylim(0.4, 1.15)
    ax.axhline(1.0, color=INK2, lw=0.8, ls=":")
    ax.text(15.2, 1.0, "mean baseline ≈ 1", fontsize=8, color=INK2, va="center")
    ax.set_title("AutoResearch search (same-run-01): 15 attempts, edits to train.py only")
    ax.legend(loc="upper right", ncol=4)
    _note(fig, "Each attempt is archived in runs/autoresearch/same-run-01 (attempt-XX.json and the exact train.py). The "
               "selected model is the lowest kept score. Choosing the best of 15 on the same folds is mildly optimistic.",
          y=-0.03)
    return _save(fig, FIGURES_DIR / "autoresearch_progress.png")


def model_scenarios(r) -> str:
    c = r["curves"]
    fig, axs = plt.subplots(1, 3, figsize=(16, 4.6))
    ax = axs[0]
    for m in MATERIAL_ORDER:
        s = c[(c.material == m) & (c.flow_regime == "flow_8cm_s")]
        inn = s[~s.extrapolated]
        ax.plot(inn.aging_s, inn.dm_um, "-", color=COLORS[m], marker=MARKERS[m], ms=5)
        ax.plot(s.aging_s, s.dm_um, ":", color=COLORS[m], lw=1.2)
        ax.text(s.aging_s.iloc[-1] + 30, s.dm_um.iloc[-1], m, fontsize=8, va="center")
    ax.set_xlabel("Smoke transport / aging time (s)")
    ax.set_ylabel("Predicted Dm (µm)")
    ax.set_xlim(0, 2150)
    ax.set_title("Predicted particle growth (8 cm/s flow)")
    for ax, key, title in [(axs[1], "iss_false_negative_risk", "ISS photoelectric: risk of no response"),
                           (axs[2], "ion_false_negative_risk", "Ionization chamber: risk of no response")]:
        sub = c[c.aging_s.isin([38.0, 566.0])]
        labels, vals_f, vals_n = [], [], []
        for m in MATERIAL_ORDER:
            for t_, tl in [(38.0, "fresh"), (566.0, "aged")]:
                labels.append(f"{m} · {tl}")
                vals_f.append(100 * sub[(sub.material == m) & (sub.aging_s == t_) & (sub.flow_regime == "flow_8cm_s")][key].iloc[0])
                vals_n.append(100 * sub[(sub.material == m) & (sub.aging_s == t_) & (sub.flow_regime == "no_flow")][key].iloc[0])
        y = np.arange(len(labels))
        col = DET_COLORS["ISS photoelectric"] if "iss" in key else DET_COLORS["Ionization chamber"]
        ax.barh(y - 0.2, vals_f, 0.38, color=col, label="8 cm/s flow")
        ax.barh(y + 0.2, vals_n, 0.38, color=SURFACE, edgecolor=col, hatch="////", lw=1.2, label="no flow")
        ax.set_yticks(y, labels, fontsize=7.8)
        ax.invert_yaxis()
        ax.set_xlim(0, 105)
        ax.set_xlabel("Predicted probability of no proxy response (%)")
        ax.set_title(title)
        ax.legend(loc="lower right", fontsize=7.8)
    axs[2].set_yticklabels([])
    _note(fig, "Selected AutoResearch model refitted on all rows. Left: dotted segments are extrapolations beyond the "
               "tested aging range. Middle/right: false-negative risk = 1 − predicted probability of exceeding the proxy "
               "threshold; silicone had no no-flow test, so its no-flow bars rely on pooled no-flow behaviour.", y=-0.02)
    return _save(fig, FIGURES_DIR / "model_scenarios.png")


CHARTS = [
    ("overview", overview), ("moments_by_material", moments_by_material), ("aging_coagulation", aging_coagulation),
    ("flow_effect", flow_effect), ("detector_comparison", detector_comparison),
    ("threshold_sensitivity", threshold_sensitivity), ("example_timeseries", example_timeseries),
    ("size_distributions", size_distributions), ("model_cv", model_cv),
    ("autoresearch_progress", autoresearch_progress), ("model_scenarios", model_scenarios),
]


def make_all(r) -> dict[str, str]:
    return {name: str(fn(r)) for name, fn in CHARTS}


if __name__ == "__main__":
    import warnings

    warnings.filterwarnings("ignore")
    from analysis.insights import compute_all

    for k, v in make_all(compute_all()).items():
        print(k, v)
