"""Standard scientific figures (catalog G1–G18; see knowledge/methods/evaluation_protocol.md §6).

Style rules (dataviz skill + evaluation protocol):
  * Fixed-order categorical palette (never cycled); sequential = a single hue (blue).
  * Never a dual y-axis: different magnitudes -> stacked panels sharing the x axis.
  * Legend whenever there are ≥ 2 series; thin marks (2 px lines), recessive grid.
  * Every figure returns (fig, caption). `save()` writes a 300 dpi PNG + the data as CSV +
    the caption as .md (what is shown and what to conclude), so the report is reproducible.
"""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.colors import LinearSegmentedColormap  # noqa: E402

# Validated reference palette (dataviz/references/palette.md, light mode)
SERIES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6", "#e34948"]
SURFACE, INK, INK2, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#e4e3df"
SEQ_BLUE = ["#fcfcfb", "#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"]
CMAP_SEQ = LinearSegmentedColormap.from_list("bass2_blue", SEQ_BLUE)
CMAP_DIV = LinearSegmentedColormap.from_list("bass2_div", ["#184f95", "#6da7ec", "#f0efec", "#ec8a89", "#b42f2f"])
LE_COLOR, TE_COLOR = SERIES[1], SERIES[2]  # leading edge always orange, trailing edge aqua


def style():
    plt.rcParams.update({
        "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
        "axes.edgecolor": INK2, "axes.labelcolor": INK, "xtick.color": INK2, "ytick.color": INK2,
        "text.color": INK, "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.6,
        "axes.spines.top": False, "axes.spines.right": False, "lines.linewidth": 2,
        "font.size": 9, "axes.titlesize": 10, "axes.titleweight": "bold", "legend.frameon": False,
        "axes.prop_cycle": matplotlib.cycler(color=SERIES),
    })


style()


def save(fig, caption: str, out_dir: str | Path, name: str, data: pd.DataFrame | None = None) -> Path:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    png = out_dir / f"{name}.png"
    fig.savefig(png, dpi=300, bbox_inches="tight")
    plt.close(fig)
    (out_dir / f"{name}.md").write_text(caption.strip() + "\n", encoding="utf-8")
    if data is not None:
        data.to_csv(out_dir / f"{name}.csv", index=False)
    return png


def _ok(x) -> bool:
    return x is not None and x == x


def _title(test_id: str, cond: dict | None) -> str:
    if not cond:
        return test_id
    parts = [test_id, " ".join(str(cond.get("material_raw") or "").split()),
             f"O₂ {cond['o2_initial_pct']:.1f} %" if _ok(cond.get("o2_initial_pct")) else "",
             f"initial flow {cond['flow_initial_cm_s']:.1f} cm/s" if _ok(cond.get("flow_initial_cm_s")) else ""]
    return " · ".join(p for p in parts if p)


# ------------------------------------------------------------------ G1 overlay

def fig_overlay(frames: list[np.ndarray], masks: list[np.ndarray], rows: list[dict], test_id: str,
                cond: dict | None = None):
    n = len(frames)
    fig, axes = plt.subplots(2, n, figsize=(3.2 * n, 4.6), squeeze=False)
    for i, (f, m, r) in enumerate(zip(frames, masks, rows)):
        rgb = f[..., ::-1]
        axes[0, i].imshow(rgb)
        axes[0, i].set_title(f"t = {r['time_s']:.1f} s", fontsize=9)
        over = rgb.copy().astype(float) / 255
        over[m] = 0.45 * over[m] + 0.55 * np.array([0.16, 0.47, 0.84])
        axes[1, i].imshow(over)
        axes[1, i].contour(m, levels=[0.5], colors=[SERIES[3]], linewidths=0.8)
        if _ok(r.get("le_x_px")):
            axes[1, i].axvline(r["le_x_px"], color=LE_COLOR, lw=1.2, ls="--")
        for a in axes[:, i]:
            a.set_xticks([]); a.set_yticks([]); a.grid(False)
    axes[0, 0].set_ylabel("original")
    axes[1, 0].set_ylabel("mask + leading edge")
    fig.suptitle(f"G1 · Flame segmentation — {_title(test_id, cond)}", fontsize=10)
    cap = (f"**G1 — {test_id}.** Top row: original frames (720×480, OSD telemetry visible). Bottom row: flame "
           "mask (translucent blue), contour (yellow) and leading edge (dashed orange line). A good segmentation "
           "covers the faint flame base and excludes the OSD, reflections and the igniter; the leading edge must "
           "sit at the advancing tip.")
    return fig, cap


# ------------------------------------------------------------------ G2 kymograph

def fig_kymograph(kymo: np.ndarray, times: np.ndarray, x_axis: np.ndarray, df: pd.DataFrame | None,
                  test_id: str, unit: str = "px", cond: dict | None = None):
    fig, ax = plt.subplots(figsize=(6.4, 4.2))
    k = np.log1p(kymo / (np.nanpercentile(kymo, 99.5) + 1e-12) * 50)
    ax.imshow(k, aspect="auto", origin="lower", cmap=CMAP_SEQ,
              extent=[x_axis[0], x_axis[-1], times[0], times[-1]])
    ax.grid(False)
    if df is not None and "le_x_axis" in df:
        ax.plot(df["le_x_axis"], df["time_s"], color=LE_COLOR, lw=1.2, label="leading edge")
        ax.plot(df["te_x_axis"], df["time_s"], color=TE_COLOR, lw=1.2, label="trailing edge")
        ax.legend(loc="upper right")
    ax.set_xlabel(f"horizontal position x ({unit})")
    ax.set_ylabel("time t (s)")
    ax.set_title(f"G2 · Space-time diagram — {_title(test_id, cond)}")
    cap = (f"**G2 — kymograph of {test_id}.** Each row is the horizontal flame-intensity profile at one instant "
           "(darker = brighter, log scale). A slanted band means spread: since time runs vertically, the visual "
           "slope is 1/V_f (flatter = faster). Straight band = constant speed; curvature = acceleration or "
           "deceleration; fading = approach to extinction; horizontal stripes = exposure changes or bad frames.")
    return fig, cap


# ------------------------------------------------------------------ G3 edge + fit

def fig_edge_fit(df: pd.DataFrame, steady: dict, test_id: str, cond: dict | None = None):
    unit = df["unit"].iloc[0]
    col = f"leading_edge_{unit}"
    d = df.dropna(subset=[col])
    fig, (ax, axr) = plt.subplots(2, 1, figsize=(6.4, 5), sharex=True, gridspec_kw={"height_ratios": [3, 1]})
    ax.plot(d.time_s, d[col], ".", ms=2.5, color=LE_COLOR, label="measured leading edge")
    fit = None
    if _ok(steady.get("rate")):
        tt = np.array([steady["t0"], steady["t1"]])
        ax.plot(tt, steady["rate"] * tt + steady["intercept"], color=INK, lw=1.2,
                label=f"Theil-Sen: V_f = {steady['rate']:.3g} [{steady['lo']:.3g}, {steady['hi']:.3g}] {steady['unit']}")
        ax.axvspan(*tt, color=SERIES[0], alpha=0.06, lw=0)
        fit = steady["rate"] * d.time_s + steady["intercept"]
        axr.plot(d.time_s, d[col] - fit, ".", ms=2, color=INK2)
        axr.axhline(0, color=INK, lw=0.8)
    ax.set_ylabel(f"front position s(t) ({unit})")
    axr.set_ylabel(f"residual ({unit})")
    axr.set_xlabel("time t (s)")
    ax.legend(loc="upper left")
    ax.set_title(f"G3 · Flame-front advance — {_title(test_id, cond)}")
    cap = (f"**G3 — {test_id}.** Dots: leading-edge position projected on the spread direction (origin at first "
           "detection). Line: robust Theil-Sen fit over the shaded steady window; its slope is the spread rate V_f "
           "with a 95 % CI. Bottom panel: residuals, which should look like structureless noise. Systematic "
           "curvature means the spread is not steady (growth or approach to extinction) and a linear model is not "
           "enough.")
    data = d[["time_s", col]].assign(fit=fit if fit is not None else np.nan)
    return fig, cap, data


# ------------------------------------------------------------------ G4 rate(t)

def fig_rate(df: pd.DataFrame, test_id: str, cond: dict | None = None):
    unit = df["unit"].iloc[0]
    sg, rr, se = (f"spread_rate_sg_{unit}_s", f"spread_rate_roll_{unit}_s", f"spread_rate_roll_se_{unit}_s")
    fig, ax = plt.subplots(figsize=(6.4, 3.4))
    ax.plot(df.time_s, df[sg], color=SERIES[0], lw=1, alpha=0.6, label="Savitzky-Golay")
    ax.plot(df.time_s, df[rr], color=LE_COLOR, label="local regression (±2 SE)")
    ax.fill_between(df.time_s, df[rr] - 2 * df[se], df[rr] + 2 * df[se], color=LE_COLOR, alpha=0.15, lw=0)
    ax.axhline(0, color=INK2, lw=0.8)
    vals = df[rr].dropna()
    if len(vals) > 10:  # robust range: ignition/extinction artefacts must not hide the steady plateau
        q1, q99 = np.percentile(vals, [2, 98])
        pad = 0.15 * (q99 - q1 + 1e-9)
        ax.set_ylim(min(0, q1 - pad), q99 + pad)
    ax.set_xlabel("time t (s)")
    ax.set_ylabel(f"instantaneous V_f ({unit}/s)")
    ax.legend(loc="upper right")
    ax.set_title(f"G4 · Spread rate over time — {_title(test_id, cond)}")
    cap = (f"**G4 — {test_id}.** Instantaneous front speed from a Savitzky-Golay derivative (blue) and from a "
           "sliding-window regression with a ±2 standard-error band (orange). A plateau marks the steady regime "
           "(it defines the fit window of G3); drops at the end anticipate extinction; jumps that coincide with FAN "
           "changes reflect the flow steps imposed by the crew.")
    return fig, cap, df[["time_s", sg, rr, se]]


# ------------------------------------------------------------------ G7 size(t)

def fig_size(df: pd.DataFrame, test_id: str, cond: dict | None = None):
    unit = df["unit"].iloc[0]
    a_col = "area_mm2" if unit == "mm" else "area_phys_px"
    l_col = f"flame_length_{unit}"
    panels = [(a_col, f"visible area ({'mm²' if unit == 'mm' else 'px²'})"),
              (l_col, f"flame length ({unit})"),
              ("integrated_intensity", "integrated intensity (a.u.)")]
    fig, axes = plt.subplots(len(panels), 1, figsize=(6.4, 6.2), sharex=True)
    for ax, (c, lab), color in zip(axes, panels, SERIES):
        ax.plot(df.time_s, df[c], color=color, lw=1.2)
        ax.set_ylabel(lab)
    axes[-1].set_xlabel("time t (s)")
    axes[0].set_title(f"G7 · Flame size and brightness — {_title(test_id, cond)}")
    cap = (f"**G7 — {test_id}.** Stacked panels (shared time axis, independent scales, no dual axis): luminous "
           "area, length along the spread direction and integrated intensity (≈ visible radiated energy). Growth "
           "to a plateau = flame reaching a steady size; decay = approach to extinction. Compare with the RAD "
           "radiometer trace (OSD, G18) as an independent check.")
    return fig, cap, df[["time_s", a_col, l_col, "integrated_intensity"]]


# ------------------------------------------------------------------ G9 forecast

def fig_forecast(series: pd.DataFrame, col: str, paths: list[pd.DataFrame], test_id: str,
                 ylabel: str, cond: dict | None = None):
    models = sorted({p.model.iloc[0] for p in paths})
    fig, axes = plt.subplots(1, len(models), figsize=(3.4 * len(models), 3.4), sharey=True, squeeze=False)
    for ax, mdl in zip(axes[0], models):
        ax.plot(series.time_s, series[col], color=INK2, lw=1, label="observed")
        for p in [p for p in paths if p.model.iloc[0] == mdl]:
            ax.fill_between(p.time_s, p.lo, p.hi, color=SERIES[0], alpha=0.18, lw=0)
            ax.plot(p.time_s, p["mean"], color=SERIES[0], lw=1.6)
            ax.axvline(p.time_s.iloc[0], color=GRID, lw=0.8)
        ax.set_title(mdl, fontsize=9)
        ax.set_xlabel("time t (s)")
    axes[0, 0].set_ylabel(ylabel)
    axes[0, 0].legend(["observed", "forecast ± 90 % PI"], loc="upper left")
    fig.suptitle(f"G9 · Forecast vs. observed — {_title(test_id, cond)}", fontsize=10)
    cap = (f"**G9 — {test_id}.** Grey: observed series. Blue: forecasts from several origins (vertical lines) with "
           "90 % prediction intervals. An honest model contains the observation ~9 times out of 10 and its bands "
           "widen with the horizon. A median that flattens against a linear advance indicates a model that is "
           "mis-specified for steady spread.")
    return fig, cap


# ------------------------------------------------------------------ G11 skill

def fig_skill(summary: pd.DataFrame, metric: str = "MASE", title_suffix: str = ""):
    fig, ax = plt.subplots(figsize=(6.0, 3.6))
    for i, (mdl, g) in enumerate(summary.groupby("model")):
        g = g.sort_values("horizon_s")
        ax.plot(g.horizon_s, g[metric], marker="o", ms=5, color=SERIES[i % len(SERIES)], label=mdl)
    ax.set_xlabel("horizon h (s)")
    ax.set_ylabel(metric)
    ax.legend(loc="upper left")
    ax.set_title(f"G11 · Forecast error vs. horizon {title_suffix}")
    cap = (f"**G11.** Mean {metric} per model and horizon (rolling-origin evaluation, no temporal leakage). Lower is "
           "better; MASE < 1 beats the naive one-step forecast. Some models usually win at short horizons and lose "
           "at long ones: choose according to the operational horizon.")
    return fig, cap


# ------------------------------------------------------------------ G12 calibration

def fig_calibration(bt: pd.DataFrame):
    from scipy.stats import norm
    levels = np.array([0.5, 0.8, 0.9, 0.95])
    fig, ax = plt.subplots(figsize=(4.4, 4.2))
    ax.plot([0.4, 1], [0.4, 1], color=INK2, lw=1, ls="--", label="perfect calibration")
    for i, (mdl, g) in enumerate(bt.groupby("model")):
        sig = (g.hi - g.lo) / (2 * norm.ppf(0.95))
        z = np.abs(g.y_true - g.y_pred) / sig.replace(0, np.nan)
        emp = [(z <= norm.ppf(0.5 + lv / 2)).mean() for lv in levels]
        ax.plot(levels, emp, marker="o", ms=5, color=SERIES[i % len(SERIES)], label=mdl)
    ax.set_xlabel("nominal coverage")
    ax.set_ylabel("empirical coverage")
    ax.legend(loc="upper left")
    ax.set_title("G12 · Prediction-interval calibration")
    cap = ("**G12.** Empirical vs. nominal coverage of the prediction intervals (Gaussian assumption). Points below "
           "the diagonal = intervals too narrow (over-confidence); above it = too wide.")
    return fig, cap


# ------------------------------------------------------------------ G13 conditions map

def fig_conditions(table: pd.DataFrame):
    d = table.dropna(subset=["flow_initial_cm_s", "o2_initial_pct"]).copy()
    d["outcome"] = np.where(d.extinction | d.blowoff | d.no_ignition, "extinction / blowoff / no ignition",
                            "spread recorded")
    markers = dict(zip(sorted(d.material_class.unique()), "osD^vP*X"))
    fig, ax = plt.subplots(figsize=(6.6, 4.4))
    rng = np.random.default_rng(0)
    for i, (_, g) in enumerate(d.groupby("outcome")):
        for mat, gm in g.groupby("material_class"):
            ax.scatter(gm.flow_initial_cm_s + rng.normal(0, 0.15, len(gm)), gm.o2_initial_pct,
                       marker=markers[mat], s=36, color=SERIES[i], edgecolor=SURFACE, linewidth=0.8, alpha=0.9)
    from matplotlib.lines import Line2D
    h = [Line2D([], [], ls="", marker="o", color=SERIES[i], label=oc) for i, oc in enumerate(sorted(d.outcome.unique()))]
    h += [Line2D([], [], ls="", marker=m, color=INK2, label=mat) for mat, m in markers.items()]
    ax.legend(handles=h, loc="upper left", bbox_to_anchor=(1.0, 1.0), fontsize=8)
    ax.set_xlabel("initial flow velocity (cm/s, 'Air display' column)")
    ax.set_ylabel("initial calibrated O₂ (% vol)")
    ax.set_title("G13 · BASS-II experimental conditions")
    cap = ("**G13.** Each point is one test (small horizontal jitter to avoid overlap). Colour = outcome noted by the "
           "crew; shape = material class. Shows the experimental coverage: where there is data to validate against "
           "and where a model would extrapolate. Extinctions cluster at low flow / low O₂, approaching the "
           "microgravity flammability limit. Note: many tests step the flow during the burn; only the initial value "
           "is shown, and a few O-test rows are known parser outliers (see docs/ROADMAP.md).")
    return fig, cap, d[["test_id", "material_class", "flow_initial_cm_s", "o2_initial_pct", "outcome"]]


# ------------------------------------------------------------------ G5 spread vs flow

def fig_spread_vs_flow(summary: pd.DataFrame, unit: str = "mm"):
    d = summary.dropna(subset=["rate", "flow_initial_cm_s"])
    fig, ax = plt.subplots(figsize=(6.2, 4.2))
    sc = ax.scatter(d.flow_initial_cm_s, d.rate, c=d.o2_initial_pct, cmap=CMAP_SEQ, s=40,
                    edgecolor=INK2, linewidth=0.5, vmin=15, vmax=23)
    ax.errorbar(d.flow_initial_cm_s, d.rate, yerr=[d.rate - d.lo, d.hi - d.rate], fmt="none",
                ecolor=INK2, elinewidth=0.8)
    for r in d.itertuples():
        ax.annotate(r.test_id, (r.flow_initial_cm_s, r.rate), fontsize=7, color=INK2,
                    xytext=(3, 3), textcoords="offset points")
    fig.colorbar(sc, ax=ax, label="initial O₂ (% vol)")
    ax.set_xlabel("air velocity during the steady window (cm/s, lag-corrected OSD AIR)")
    ax.set_ylabel(f"spread rate V_f ({unit}/s)")
    ax.set_yscale("log")
    ax.set_title("G5 · Spread rate vs. flow and oxygen (QC-trusted tests)")
    cap = ("**G5.** Steady spread rate (95 % CI, log scale) of the QC-trusted tests (configs/qc.yaml) against the air "
           "velocity measured during each steady window; colour = MCA-calibrated initial O₂. V_f is expected to "
           "increase with O₂; against flow, microgravity can show a maximum at low flow (radiative → thermal → "
           "kinetic regimes). Compare with published values (knowledge/literature/publications.md §2).")
    return fig, cap, d


# ------------------------------------------------------------------ G14 QC

def fig_qc(df: pd.DataFrame, test_id: str, cond: dict | None = None):
    panels = [("saturated_frac", "saturated fraction"), ("max_value", "max value (0–255)"),
              ("n_px_valid_bg", "mean background level")]
    panels = [p for p in panels if p[0] in df]
    fig, axes = plt.subplots(len(panels), 1, figsize=(6.4, 1.9 * len(panels)), sharex=True, squeeze=False)
    for ax, (c, lab), color in zip(axes[:, 0], panels, SERIES):
        ax.plot(df.time_s, df[c], color=color, lw=1)
        ax.set_ylabel(lab)
    axes[-1, 0].set_xlabel("time t (s)")
    axes[0, 0].set_title(f"G14 · Camera quality control — {_title(test_id, cond)}")
    cap = (f"**G14 — {test_id}.** Camera diagnostics: saturation, maximum and background level. Simultaneous jumps in "
           "the background and in the area (G7) point to an auto-exposure/gain artefact, not physics; those spans "
           "must be excluded from the V_f fit.")
    return fig, cap


# ------------------------------------------------------------------ G6 parity vs published

def fig_parity(v: pd.DataFrame):
    """Measured vs published spread rate (log-log parity) + Bland-Altman, coloured by validation set."""
    fig, (ax, ab) = plt.subplots(1, 2, figsize=(11.0, 4.8), gridspec_kw={"wspace": 0.32})
    v = v.copy()
    v["set"] = v.get("set", pd.Series("development", index=v.index)).fillna("other")
    excl = v.get("qc_excluded", pd.Series(False, index=v.index)).fillna(False).astype(bool)
    lo = min(v.vf_measured_mm_s.min(), v.vf_published_mm_s.min()) * 0.6
    hi = max(v.vf_measured_mm_s.max(), v.vf_published_mm_s.max()) * 1.6
    xx = np.geomspace(lo, hi, 50)
    ax.fill_between(xx, xx * 0.75, xx * 1.25, color=GRID, alpha=0.6, lw=0, label="±25 %")
    ax.fill_between(xx, xx * 0.9, xx * 1.1, color=SERIES[0], alpha=0.12, lw=0, label="±10 %")
    ax.plot(xx, xx, color=INK2, lw=1, ls="--", label="1:1")
    names = {"development": "development (in-sample)", "holdout": "hold-out (frozen settings)",
             "other": "other slab steps (diagnosed post hoc)"}
    colors = {"development": SERIES[0], "holdout": SERIES[1], "other": SERIES[2]}
    for st in ("development", "holdout", "other"):
        d = v[v.set == st]
        if d.empty:
            continue
        ok, bad = d[~excl.loc[d.index]], d[excl.loc[d.index]]
        ax.errorbar(ok.vf_published_mm_s, ok.vf_measured_mm_s, xerr=2 * ok.sigma_published, yerr=2 * ok.sigma_measured,
                    fmt="o", ms=6, color=colors[st], ecolor=colors[st], elinewidth=0.8, label=names[st])
        if len(bad):
            ax.errorbar(bad.vf_published_mm_s, bad.vf_measured_mm_s, xerr=2 * bad.sigma_published,
                        yerr=2 * bad.sigma_measured, fmt="o", ms=6, mfc="none", color=colors[st], ecolor=colors[st],
                        elinewidth=0.6, label=f"{names[st]} · excluded by physics QC")
        for r in d.itertuples():
            ax.annotate(r.test_id, (r.vf_published_mm_s, r.vf_measured_mm_s), fontsize=6.5, color=INK2,
                        xytext=(4, -9), textcoords="offset points")
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlim(lo, hi)
    ax.set_ylim(lo, hi)
    ax.set_xlabel("published V_f (mm/s)")
    ax.set_ylabel("measured V_f (mm/s, this pipeline)")
    ax.legend(loc="lower right", fontsize=7)
    ax.set_title("G6a · Parity with published spread rates")
    rel = 100 * (v.vf_measured_mm_s - v.vf_published_mm_s) / v.vf_published_mm_s
    mean = (v.vf_measured_mm_s + v.vf_published_mm_s) / 2
    for st in ("development", "holdout", "other"):
        m = v.set == st
        if m.any():
            ab.scatter(mean[m & ~excl], rel[m & ~excl], color=colors[st], s=34, edgecolor=SURFACE, linewidth=0.8,
                       label=names[st])
            ab.scatter(mean[m & excl], rel[m & excl], facecolor="none", edgecolor=colors[st], s=34, linewidth=1.1)
    short = {"development": "dev", "holdout": "hold-out", "other": "post hoc"}
    med_txt = ", ".join(f"{short[st]} {np.median(np.abs(rel[v.set == st])):.1f} % (n={int((v.set == st).sum())})"
                        for st in ("development", "holdout", "other") if (v.set == st).any())
    ab.axhline(0, color=INK2, lw=1)
    ab.axhspan(-10, 10, color=SERIES[0], alpha=0.08, lw=0, label="±10 %")
    ab.set_xscale("log")
    big = float(np.nanmax(np.abs(rel))) if len(rel) else 15.0
    if big > 40:  # wide range (hold-out outliers): symmetric-log axis with readable ticks
        ab.set_yscale("symlog", linthresh=20, linscale=1.5)
        ticks = [t for t in (-100, -50, -20, -10, 0, 10, 20, 50, 100, 200, 500, 1000) if abs(t) <= big * 1.5]
        ab.set_yticks(ticks, [f"{t:+d}" if t else "0" for t in ticks])
        ab.set_ylim(-max(30, -float(np.nanmin(rel)) * 1.5), big * 2.5)
    else:
        ab.set_ylim(-max(15.0, big * 1.15), max(15.0, big * 1.15) * 1.35)
    ab.set_xlabel("mean of measured and published V_f (mm/s)")
    ab.set_ylabel("relative difference (%)")
    ab.legend(loc="lower right", fontsize=7, title=f"median |diff|: {med_txt}", title_fontsize=7)
    ab.set_title("G6b · Relative difference (all comparisons)")
    cap = ("**G6 — validation against published spread rates.** Left: measured steady V_f (geometric ruler calibration) "
           "against published values (SDSU side view for B films, NASA TM-20210011385 Table 5.1 for M slabs); error bars "
           "are ±2σ on both axes (measured σ includes the 2 % scale uncertainty). Blue = development tests, used to choose "
           "the segmentation and regime settings (in-sample); orange = hold-out slab tests processed only after all "
           "settings were frozen; green = other slab steps examined while diagnosing regime selection (not independent). "
           "Hollow markers are comparisons rejected by the physics review, which was done with published values visible. "
           "Right: relative difference for every comparison; the legend gives the median absolute difference per set. "
           "The spatial calibration uses no published value.")
    return fig, cap


# ------------------------------------------------------------------ G19 thickness law (scale-free)

def fig_thickness_law(tl: dict):
    d = pd.DataFrame(tl["tests"])
    fig, ax = plt.subplots(figsize=(5.6, 4.2))
    ax.errorbar(d.thickness_mm * 1000, d.rate, yerr=[d.rate - d.lo, d.hi - d.rate], fmt="o", ms=6,
                color=SERIES[0], ecolor=SERIES[0], label="measured (this pipeline)")
    for r in d.itertuples():
        ax.annotate(r.test_id, (r.thickness_mm * 1000, r.rate), fontsize=7, color=INK2, xytext=(4, 3),
                    textcoords="offset points")
    th = np.geomspace(d.thickness_mm.min() * 0.85, d.thickness_mm.max() * 1.15, 30)
    c = np.exp(np.mean(np.log(d.rate) + np.log(d.thickness_mm)))
    ax.plot(th * 1000, c / th, color=INK2, ls="--", lw=1, label="de Ris thin-fuel law V_f ∝ 1/τ")
    b = np.exp(np.mean(np.log(d.rate) - tl["slope"] * np.log(d.thickness_mm)))
    ax.plot(th * 1000, b * th ** tl["slope"], color=SERIES[1], lw=1.6,
            label=f"fit: slope {tl['slope']:.2f} ± {tl['slope_se']:.2f}")
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("film thickness τ (µm)")
    ax.set_ylabel("steady spread rate V_f (mm/s)")
    ax.legend(loc="upper right", fontsize=8)
    ax.set_title("G19 · Thin-film thickness law (scale-free check)")
    cap = (f"**G19 — V_f vs. film thickness for PMMA films in opposed flow (O₂ > 19.5 %).** Log-log axes. The fitted slope "
           f"({tl['slope']:.2f} ± {tl['slope_se']:.2f}, R² = {tl['r2']:.2f}, n = {tl['n']}) does not depend on the spatial "
           "calibration, so it validates the edge tracking itself. The de Ris thin-fuel theory predicts −1; the published "
           f"SDSU values give {tl['published_slope']:.2f} ± {tl['published_slope_se']:.2f}. Scatter at equal thickness "
           "reflects different flow velocities and O₂.")
    return fig, cap, d


# ------------------------------------------------------------------ G10 forecast residuals

def fig_residuals(bt: pd.DataFrame):
    models = sorted(bt.model.unique())
    hs = sorted(bt.horizon_s.unique())
    fig, axes = plt.subplots(1, len(hs), figsize=(3.3 * len(hs), 3.6), sharey=True, squeeze=False)
    scale = bt.groupby(["test_id", "target"]).abs_err.transform("median").replace(0, np.nan)
    err = bt.assign(scaled=(bt.y_pred - bt.y_true) / scale)
    for ax, h in zip(axes[0], hs):
        data = [err[(err.model == m) & (err.horizon_s == h)].scaled.dropna().clip(-20, 20) for m in models]
        bp = ax.boxplot(data, patch_artist=True, showfliers=False, widths=0.6)
        for patch, color in zip(bp["boxes"], SERIES):
            patch.set_facecolor(color)
            patch.set_alpha(0.55)
            patch.set_edgecolor(INK2)
        for med in bp["medians"]:
            med.set_color(INK)
        ax.axhline(0, color=INK2, lw=0.8)
        ax.set_xticks(range(1, len(models) + 1), models, rotation=35, ha="right", fontsize=8)
        ax.set_title(f"h = {h:g} s", fontsize=9)
    axes[0, 0].set_ylabel("signed error / per-series median |error|")
    fig.suptitle("G10 · Forecast residuals by model and horizon", fontsize=10)
    cap = ("**G10.** Distribution of signed forecast errors (normalised per test and target so different units and scales "
           "are comparable) for each model and horizon, pooled over all tests and rolling origins. A box centred on zero = "
           "unbiased; a narrow box = precise. Boxes drifting below zero at long horizons reveal models that under-predict "
           "steady flame advance (e.g. persistence, damped trend).")
    return fig, cap


# ------------------------------------------------------------------ G15 threshold sensitivity

def fig_sensitivity(sens: pd.DataFrame, param: str = "k_low", default: float = 8):
    fig, ax = plt.subplots(figsize=(6.0, 3.9))
    sens = sens.groupby("test_id").filter(lambda g: (g.loc[g[param] == default, "rate"].notna()).any())
    for i, (t, g) in enumerate(sens.groupby("test_id")):
        g = g.sort_values(param)
        base = float(g.loc[g[param] == default, "rate"].iloc[0])
        y = 100 * (g.rate / base - 1)
        ax.plot(g[param], y, marker="o", ms=5, color=SERIES[i % len(SERIES)], label=t)
        if {"lo", "hi"} <= set(g.columns):
            ax.fill_between(g[param], 100 * (g.lo / base - 1), 100 * (g.hi / base - 1), color=SERIES[i % len(SERIES)],
                            alpha=0.10, lw=0)
    ax.axhline(0, color=INK2, lw=0.8)
    ax.axvline(default, color=GRID, lw=1)
    ax.set_xlabel("segmentation threshold k (multiples of background noise σ)")
    ax.set_ylabel("change in steady V_f vs. default (%)")
    ax.legend(loc="lower left", fontsize=8, ncol=3)
    ax.set_title("G15 · Sensitivity of V_f to the segmentation threshold")
    worst = (sens.assign(base=sens.groupby("test_id").rate.transform(
        lambda r: r[sens.loc[r.index, param] == default].iloc[0]))
        .assign(ch=lambda d: 100 * (d.rate / d.base - 1)).groupby("test_id").ch.apply(lambda c: c.abs().max()))
    robust = ", ".join(t for t, w in worst.items() if w < 5)
    fragile = ", ".join(f"{t} (up to {w:.0f} %)" for t, w in worst.items() if w >= 5)
    cap = ("**G15.** Relative change of the steady spread rate when the noise-relative threshold k varies from 4σ to 14σ "
           "around the default (8σ, vertical line; high threshold = 2k, floors scaled alike); shaded bands are the 95 % "
           f"CIs. Robust (< 5 % change): {robust or 'none'}. Threshold-dependent: {fragile or 'none'} — these faint flames "
           "carry a systematic uncertainty larger than their statistical CI. Tests whose default run gives no steady "
           "rate are omitted.")
    return fig, cap


# ------------------------------------------------------------------ G16 research-loop progress

def fig_loop_progress(res: pd.DataFrame):
    fig, ax = plt.subplots(figsize=(6.4, 3.6))
    run = res.run.astype(int)
    keep = res.status == "keep"
    ax.scatter(run[~keep], res.val_score[~keep], color="#a3a29c", s=22, label="discarded")
    ax.scatter(run[keep], res.val_score[keep], color=SERIES[2], s=34, edgecolor=SURFACE, linewidth=0.8, label="kept")
    best = res.val_score.where(np.isfinite(res.val_score)).cummin()
    ax.step(run, best, where="post", color=SERIES[0], lw=1.6, label="best so far")
    ax.set_xlabel("experiment #")
    ax.set_ylabel("val_score (lower is better)")
    ax.legend(loc="upper right")
    ax.set_title("G16 · Autonomous research loop progress")
    cap = ("**G16.** Every evaluation of research/experiment.py by the fixed harness (val_score combines segmentation, "
           "spread-rate accuracy and forecast skill, each normalised to the v0 baseline = 1). Green points were kept, grey "
           "ones reverted. The blue staircase is the best score so far; a long flat tail means the loop has converged on "
           "the current development set.")
    return fig, cap
