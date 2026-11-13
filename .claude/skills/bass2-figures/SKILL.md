---
name: bass2-figures
description: Standards and recipe for adding or changing BASS-II scientific figures (G1–G18) with explanatory captions. Use when creating a new chart, editing src/bass2/viz.py, or writing figure captions for the report.
---

# BASS-II figure standards

Load the general `dataviz` skill first; this skill adds the project-specific rules.

## Rules
1. Implement figures in `src/bass2/viz.py` as `fig_<name>(...) -> (fig, caption[, data])`; call them from
   `src/bass2/pipeline.py` (per test) or `aggregate()` (ensemble) and persist with `viz.save(fig, caption, dir, "G<n>_<name>", data)`.
2. Colours: `viz.SERIES` in fixed order (never cycled), `viz.CMAP_SEQ` for magnitudes, `viz.CMAP_DIV` for residuals.
   Leading edge = `viz.LE_COLOR` (orange), trailing edge = `viz.TE_COLOR` (aqua).
3. No dual y-axis: stacked panels with `sharex=True`. Units on every axis. Legend when ≥ 2 series.
4. Always show uncertainty (CI band, error bars, prediction interval).
5. Title: `G<n> · <what> — <test · material · O2 · flow>` via `viz._title(test_id, cond)`.
6. Caption (2–4 sentences, Markdown, starts with `**G<n> — <test>.**`): what is shown, how to read it, what to conclude,
   and the main caveat. Do not claim conclusions the data do not support.
7. Save the plotted data as CSV (third return value) so the figure is reproducible.
8. Open the PNG and look at it before finishing (overlaps, clipping, empty panels).

## Catalog
G1 overlay · G2 kymograph · G3 edge + Theil-Sen fit · G4 rate(t) · G5 V_f vs flow/O2 · G6 parity vs published ·
G7 size(t) · G8 standoff · G9 forecast vs observed · G10 residuals · G11 skill vs horizon · G12 calibration ·
G13 conditions map · G14 camera QC · G15 threshold sensitivity · G16 research-loop progress · G17 segmenter comparison ·
G18 OSD telemetry. Reading guide: `knowledge/methods/evaluation_protocol.md` §6.
Implemented today: G1, G2, G3, G4, G5, G7, G9, G11, G12, G13, G14, G18. Pending: G6, G8, G10, G15, G16 (Streamlit has a live version), G17.
