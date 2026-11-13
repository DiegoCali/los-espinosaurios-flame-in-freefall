"""BASS-II scientific visualisation interface.

Run from investigations/BASS-II:
    .venv/Scripts/streamlit run app/streamlit_app.py
Reads already-processed results only (data/processed, reports/figures); it does not process video.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from bass2.viz import SERIES  # noqa: E402

PROC, FIGS, CAT = ROOT / "data/processed", ROOT / "reports/figures", ROOT / "data/catalog"

st.set_page_config(page_title="BASS-II · flame spread", layout="wide")
st.title("BASS-II — Flame-spread detection and measurement in microgravity")
st.caption("NASA PSI-25 · Burning and Suppression of Solids II (ISS, 2012–2014) · CC0")

tests = sorted(d.name for d in PROC.iterdir() if (d / "frames.parquet").exists()) if PROC.exists() else []
tab_test, tab_set, tab_data = st.tabs(["Single test", "Test ensemble", "NASA catalog"])

with tab_test:
    if not tests:
        st.info("No processed tests yet. Run `bass2 analyze B1`.")
    else:
        test = st.selectbox("Test", tests)
        df = pd.read_parquet(PROC / test / "frames.parquet")
        steady = json.loads((PROC / test / "steady.json").read_text())
        unit = df["unit"].iloc[0]
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Steady V_f", f"{steady['rate']:.3g} {steady['unit']}",
                  help="Theil-Sen over the steady window, 95 % CI")
        c2.metric("95 % CI", f"[{steady['lo']:.3g}, {steady['hi']:.3g}]")
        c3.metric("Steady window", f"{steady.get('t0', np.nan):.1f}–{steady.get('t1', np.nan):.1f} s")
        c4.metric("Direction", steady.get("direction", "?"))

        fig = make_subplots(rows=4, cols=1, shared_xaxes=True, vertical_spacing=0.03,
                            subplot_titles=(f"Front position ({unit})", f"Local V_f ({unit}/s)",
                                            "Luminous area", "OSD telemetry: FAN (10×V) and RAD"))
        fig.add_scatter(x=df.time_s, y=df[f"leading_edge_{unit}"], mode="markers", marker_size=3,
                        marker_color=SERIES[1], name="leading edge", row=1, col=1)
        tt = np.array([steady.get("t0", 0), steady.get("t1", 0)])
        fig.add_scatter(x=tt, y=steady["rate"] * tt + steady.get("intercept", 0), mode="lines",
                        line_color="#0b0b0b", name="Theil-Sen fit", row=1, col=1)
        fig.add_scatter(x=df.time_s, y=df[f"spread_rate_roll_{unit}_s"], line_color=SERIES[1],
                        name="V_f local regression", row=2, col=1)
        area = "area_mm2" if unit == "mm" else "area_phys_px"
        fig.add_scatter(x=df.time_s, y=df[area], line_color=SERIES[3], name="area", row=3, col=1)
        if "osd_fan" in df:
            fig.add_scatter(x=df.time_s, y=df.osd_fan / df.osd_fan.max(), line_color=SERIES[0],
                            name="FAN (normalised)", row=4, col=1)
            fig.add_scatter(x=df.time_s, y=df.osd_rad / df.osd_rad.max(), line_color=SERIES[2],
                            name="RAD (normalised)", row=4, col=1)
        fig.update_layout(height=900, hovermode="x unified", template="plotly_white")
        fig.update_xaxes(title_text="time (s)", row=4, col=1)
        st.plotly_chart(fig, use_container_width=True)

        kymo_p = PROC / test / "kymograph.npy"
        if kymo_p.exists():
            k = np.load(kymo_p)
            kf = go.Figure(go.Heatmap(z=np.log1p(k / (np.percentile(k, 99.5) + 1e-9) * 50), y=df.time_s,
                                      colorscale="Blues", showscale=False))
            kf.update_layout(title="Space-time diagram (kymograph)", xaxis_title="x (px)",
                             yaxis_title="time (s)", height=450, template="plotly_white")
            st.plotly_chart(kf, use_container_width=True)
            st.caption("Slanted band = spread; visual slope = 1/V_f; fading = extinction.")

        st.subheader("Explained figures")
        for png in sorted((FIGS / test).glob("G*.png")):
            md = png.with_suffix(".md")
            with st.expander(png.stem, expanded=png.stem.startswith(("G1", "G3"))):
                st.image(str(png))
                if md.exists():
                    st.markdown(md.read_text(encoding="utf-8"))

with tab_set:
    agg = FIGS / "_ensemble"
    if not agg.exists():
        st.info("Run `bass2 aggregate` after processing several tests.")
    else:
        if (agg / "steady_rates.csv").exists():
            st.dataframe(pd.read_csv(agg / "steady_rates.csv")[["test_id", "rate", "lo", "hi", "unit",
                                                                "material_raw", "o2_initial_pct",
                                                                "flow_initial_cm_s"]])
        for png in sorted(agg.glob("G*.png")):
            with st.expander(png.stem, expanded=True):
                st.image(str(png))
                md = png.with_suffix(".md")
                if md.exists():
                    st.markdown(md.read_text(encoding="utf-8"))
        res = ROOT / "research/results.tsv"
        if res.exists():
            st.subheader("Autoresearch loop progress")
            r = pd.read_csv(res, sep="\t")
            pf = go.Figure()
            for status, color in (("keep", SERIES[2]), ("discard", "#a3a29c")):
                s = r[r.status == status]
                pf.add_scatter(x=s.run, y=s.val_score, mode="markers", marker_color=color, name=status)
            pf.add_scatter(x=r.run, y=r.val_score.cummin(), mode="lines", line_color=SERIES[0], name="best")
            pf.update_layout(xaxis_title="experiment", yaxis_title="val_score (lower is better)",
                             template="plotly_white", height=380)
            st.plotly_chart(pf, use_container_width=True)

with tab_data:
    tbl = CAT / "experimental_table_clean.csv"
    if tbl.exists():
        st.dataframe(pd.read_csv(tbl), use_container_width=True)
    inv = CAT / "files_inventory.csv"
    if inv.exists():
        d = pd.read_csv(inv)
        st.write(f"{len(d)} files · {d.size_bytes.sum() / 1e9:.1f} GB")
        st.dataframe(d.groupby("kind").size_bytes.agg(["count", "sum"]).assign(GB=lambda x: x["sum"] / 1e9))
