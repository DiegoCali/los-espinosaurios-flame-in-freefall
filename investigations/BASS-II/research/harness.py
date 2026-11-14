"""FIXED evaluation harness of the autoresearch loop (the agent must NOT edit it).

Computes val_score (knowledge/methods/evaluation_protocol.md §3) for the current experiment.py:
    D  segmentation    1 − Dice vs gold (data/gold/) or, without gold, a fixed synthetic set
    E  leading edge    (pending: needs gold edge tracks in data/gold/)
    R  spread rate     |ln(V̂/V_pub)| on calibrated tests (pending)
    C,M,P forecasting  on FROZEN REFERENCE series data/reference_series/ref_series_v*.parquet
D is divided by the v0 baseline stored in research/baseline.json; C and M are skill ratios vs. 'drift'.

Usage:
    python research/harness.py --freeze-ref   # (human) freeze reference series from data/processed
    python research/harness.py --init         # (human) measure v0 and store baseline.json
    python research/harness.py -m "change description"   # evaluate, log, decide keep/discard
No git: every evaluation is snapshotted in research/runs/NNN/ and the best one in research/best/.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import shutil
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "src"))

from bass2 import evaluation, forecast  # noqa: E402
from bass2.video import valid_mask  # noqa: E402

REF_DIR = ROOT / "data/reference_series"
GOLD_DIR = ROOT / "data/gold"
RESULTS = HERE / "results.tsv"
BASELINE = HERE / "baseline.json"
FORBIDDEN = [str((ROOT / p).resolve()).lower() for p in ("data/reference", "data/gold", "data/holdout")]
HORIZONS = [1, 2, 5, 10]
TARGET_WEIGHTS = {"leading_edge": 0.7, "log_area": 0.3}


# --------------------------------------------------------------------- utilities

def load_experiment(path: Path = HERE / "experiment.py"):
    spec = importlib.util.spec_from_file_location("experiment", path)
    mod = importlib.util.module_from_spec(spec)
    Guard.active = True  # top-level code of experiment.py must not read evaluation data either
    try:
        spec.loader.exec_module(mod)
    finally:
        Guard.active = False
    return mod


class Guard:
    """Forbid experiment.py from opening evaluation data (audit hook)."""
    active = False

    @classmethod
    def hook(cls, event, args):
        if cls.active and event == "open" and args and isinstance(args[0], (str, Path)):
            p = str(Path(args[0]).resolve()).lower()
            if any(p.startswith(f) for f in FORBIDDEN):
                raise PermissionError(f"experiment.py may not read {args[0]}")


sys.addaudithook(Guard.hook)


# --------------------------------------------------------------------- reference

def freeze_reference(version: int | None = None) -> Path:
    """(Human) Freeze leading edge and log(area) from the current pipeline as reference series."""
    REF_DIR.mkdir(parents=True, exist_ok=True)
    version = version or (len(list(REF_DIR.glob("ref_series_v*.parquet"))) + 1)
    parts = []
    for d in sorted((ROOT / "data/processed").iterdir()):
        f = d / "frames.parquet"
        st = d / "steady.json"
        if not f.exists():
            continue
        df = pd.read_parquet(f)
        unit = df["unit"].iloc[0]
        t0, t1 = (json.loads(st.read_text()).get(k) for k in ("t0", "t1")) if st.exists() else (None, None)
        if t0 is not None:
            df = df[(df.time_s >= t0) & (df.time_s <= t1)]
        area = "area_mm2" if unit == "mm" else "area_phys_px"
        df = df.assign(log_area=np.log1p(df[area]), leading_edge=df[f"leading_edge_{unit}"])
        parts.append(df[["time_s", "leading_edge", "log_area"]].assign(test_id=d.name, unit=unit))
    out = REF_DIR / f"ref_series_v{version}.parquet"
    pd.concat(parts, ignore_index=True).to_parquet(out, index=False)
    print(f"reference series frozen: {out} ({len(parts)} tests)")
    return out


def latest_ref() -> pd.DataFrame | None:
    files = sorted(REF_DIR.glob("ref_series_v*.parquet"))
    return pd.read_parquet(files[-1]) if files else None


# --------------------------------------------------------------------- components

def synthetic_gold(n: int = 24, seed: int = 1234):
    """Fixed synthetic set (faint/bright elliptical flames, noise, OSD) until a human gold set exists."""
    rng = np.random.default_rng(seed)
    for i in range(n):
        h, w = 480, 720
        img = rng.normal(6, 2 + 3 * rng.random(), (h, w, 3))
        yy, xx = np.mgrid[:h, :w]
        cx, cy = rng.uniform(150, 570), rng.uniform(150, 420)
        L, H = rng.uniform(30, 220), rng.uniform(8, 40)
        r2 = ((xx - cx) / (L / 2)) ** 2 + ((yy - cy) / (H / 2)) ** 2
        peak = rng.uniform(70, 255)
        prof = np.clip(1.2 - r2, 0, 1) ** 0.5  # soft edge like a real flame
        col = np.array([1.0, rng.uniform(0.2, 0.6), rng.uniform(0.4, 1.0)])  # blue/magenta
        img += prof[..., None] * peak * col
        img[30:80, 150:650] += 140 * (rng.random((50, 500, 1)) > 0.7)  # OSD text
        gold = r2 <= 1
        yield np.clip(img, 0, 255).astype(np.uint8), gold


def comp_D(exp) -> tuple[float, str]:
    gold_frames = sorted(GOLD_DIR.glob("*/*_mask.png")) if GOLD_DIR.exists() else []
    dices = []
    if gold_frames:
        import cv2
        for m in gold_frames:
            frame = cv2.imread(str(m).replace("_mask.png", "_frame.png"))
            g = cv2.imread(str(m), cv2.IMREAD_GRAYSCALE)
            ignore = g == 255 if (g == 255).any() and (g == 128).any() else None
            gold = g >= 128 if ignore is None else g == 128
            Guard.active = True
            try:
                pred = exp.segment(frame, valid_mask(frame.shape, {"y0": 0, "y1": 90}))
            finally:
                Guard.active = False
            dices.append(evaluation.dice(pred, gold, ignore))
        src = "gold"
    else:
        for frame, gold in synthetic_gold():
            Guard.active = True
            try:
                pred = exp.segment(frame, valid_mask(frame.shape, {"y0": 0, "y1": 90}))
            finally:
                Guard.active = False
            dices.append(evaluation.dice(pred, gold))
        src = "synthetic"
    return 1 - float(np.mean(dices)), src


def comp_forecast(exp, ref: pd.DataFrame) -> dict:
    rows = []
    hz = getattr(exp, "FORECAST_RESAMPLE_HZ", 2.0)

    class _Wrap(forecast.Forecaster):
        name = "candidate"

        def fit(self, t, y):
            self._m = exp.make_forecaster(0.9).fit(t, y)
            return self

        def predict(self, tf):
            return self._m.predict(tf)

    forecast.MODELS["candidate"] = _Wrap
    for (test_id, target) in [(t, c) for t in ref.test_id.unique() for c in TARGET_WEIGHTS]:
        s = forecast.resample(ref[ref.test_id == test_id], target, hz)
        Guard.active = True
        try:
            b = forecast.rolling_origin(s, target, ["candidate", "drift"], HORIZONS, 5.0, 12)
        finally:
            Guard.active = False
        if not b.empty:
            rows.append(b.assign(test_id=test_id, target=target))
    if not rows:
        return {"C": np.nan, "M": np.nan, "P": np.nan, "cov90": np.nan}
    bt = pd.concat(rows, ignore_index=True)
    if bt[["y_pred", "lo", "hi"]].isna().any().any() or (bt.lo > bt.hi).any():
        return {"gate_fail": "NaN or non-monotonic quantiles"}
    return evaluation.forecast_components(bt, "candidate", "drift", TARGET_WEIGHTS)


# --------------------------------------------------------------------- R: spread-rate accuracy

# Dev tests with a published side-view V_f, a downloaded video and a geometric calibration.
R_TESTS = ["B1", "B2", "B3", "B4", "B5", "B7", "B12", "M1"]
R_CACHE = HERE / ".r_cache.json"


def _r_worker(args):
    """Measure one test with the candidate segmenter (runs in a separate process)."""
    exp_path, test_id = args
    exp = load_experiment(Path(exp_path))
    from bass2.pipeline import measure_rate
    Guard.active = True  # the candidate segmenter runs in this child process: keep the audit hook armed
    vids = sorted([*(ROOT / "data/raw" / test_id).glob("*.mp4"), *(ROOT / "data/raw" / test_id).glob("*.ts")])
    if not vids:
        return test_id, np.nan
    r = measure_rate(test_id, vids[0], {"video": {"max_processed_frames": 1500}}, segment_fn=exp.segment)
    return test_id, (r.get("rate") if r.get("unit") == "mm/s" else np.nan)


def comp_R(exp, exp_path: Path) -> dict:
    """Mean |ln(V_measured / V_published)| over R_TESTS (published values read here, never by the experiment)."""
    import hashlib
    import inspect
    from concurrent.futures import ProcessPoolExecutor
    # cache key = whole experiment file (helper functions used by segment() also change R) + calibration table
    cal = ROOT / "data/catalog/spatial_calibration.csv"
    key = hashlib.sha1(Path(exp_path).read_bytes() + (cal.read_bytes() if cal.exists() else b"")).hexdigest()
    cache = json.loads(R_CACHE.read_text()) if R_CACHE.exists() else {}
    if key in cache:
        return cache[key]
    with ProcessPoolExecutor(min(5, len(R_TESTS))) as ex:
        rates = dict(ex.map(_r_worker, [(str(exp_path), t) for t in R_TESTS]))
    pub = pd.read_csv(ROOT / "data/reference/published_rates.csv")
    pub = pub[(pub.view == "side") & (pub.step == 1)].set_index("test_id")["vf_mm_s"]
    errs = {t: abs(np.log(v / pub[t])) for t, v in rates.items() if t in pub and v == v and v and v > 0}
    missing = [t for t in R_TESTS if t not in errs]
    # A test the candidate cannot measure counts as a factor-2 error (|ln 2|), like a missed edge in
    # evaluation_protocol.md §3.2, so a weak baseline still gets a finite score.
    all_errs = list(errs.values()) + [float(np.log(2.0))] * len(missing)
    res = {"R_err": float(np.mean(all_errs)) if all_errs else np.nan, "R_n": len(errs),
           "R_missing": missing, "R_rates": {t: rates[t] for t in rates}}
    cache[key] = res
    R_CACHE.write_text(json.dumps(cache, indent=1, default=float))
    return res


# --------------------------------------------------------------------- evaluation

def evaluate(exp_path: Path = HERE / "experiment.py") -> dict:
    t_start = time.time()
    exp = load_experiment(exp_path)
    raw = {}
    raw["D_err"], raw["D_source"] = comp_D(exp)
    raw.update(comp_R(exp, exp_path))
    if raw.get("R_n", 0) < len(R_TESTS) // 2:  # gate: the segmenter must measure at least half of the dev tests
        return {"val_score": np.inf, "status": "gate_fail", "reason": f"R failed on {raw.get('R_missing')}", "raw": raw}
    ref = latest_ref()
    if ref is not None:
        fc = comp_forecast(exp, ref)
        if "gate_fail" in fc:
            return {"val_score": np.inf, "status": "gate_fail", "reason": fc["gate_fail"]}
        raw.update(fc)
    base = json.loads(BASELINE.read_text()) if BASELINE.exists() else None
    comps = {"D": raw["D_err"] / base["D_err"] if base and base.get("D_err") else 1.0,
             "R": raw["R_err"] / base["R_err"] if base and base.get("R_err") else 1.0,
             "C": raw.get("C", np.nan), "M": raw.get("M", np.nan), "P": raw.get("P", np.nan)}
    res = evaluation.val_score(comps)
    res.update({"raw": raw, "runtime_s": round(time.time() - t_start, 1)})
    if res["runtime_s"] > 600:
        res.update(val_score=np.inf, status="gate_fail", reason="> 10 min")
    return res


def log_and_decide(res: dict, msg: str) -> str:
    runs = HERE / "runs"
    runs.mkdir(exist_ok=True)
    n = len(list(runs.iterdir())) + 1
    run_dir = runs / f"{n:03d}"
    run_dir.mkdir()
    shutil.copy(HERE / "experiment.py", run_dir / "experiment.py")
    (run_dir / "result.json").write_text(json.dumps(res, indent=2, default=float))
    best_file = HERE / "best" / "result.json"
    best = json.loads(best_file.read_text())["val_score"] if best_file.exists() else np.inf
    score = res["val_score"]
    status = res.get("status") or ("keep" if score < best - 0.005 else "discard")
    if status == "keep":
        (HERE / "best").mkdir(exist_ok=True)
        shutil.copy(HERE / "experiment.py", HERE / "best" / "experiment.py")
        best_file.write_text(json.dumps(res, indent=2, default=float))
    elif (HERE / "best" / "experiment.py").exists():
        shutil.copy(HERE / "best" / "experiment.py", HERE / "experiment.py")  # revert to the best snapshot
    header = not RESULTS.exists()
    with open(RESULTS, "a", encoding="utf-8") as fh:
        if header:
            fh.write("run\tval_score\tD\tR\tC\tM\tP\tR_err\tcov90\tD_source\truntime_s\tstatus\tdescription\n")
        r = res.get("raw", {})
        fh.write(f"{n:03d}\t{score:.6f}\t{res.get('D', np.nan):.4f}\t{res.get('R', np.nan):.4f}\t"
                 f"{res.get('C', np.nan):.4f}\t{res.get('M', np.nan):.4f}\t{res.get('P', np.nan):.4f}\t"
                 f"{r.get('R_err', np.nan):.4f}\t{r.get('cov90', np.nan):.3f}\t"
                 f"{r.get('D_source', '')}\t{res.get('runtime_s', 0)}\t{status}\t{msg}\n")
    return status


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--freeze-ref", action="store_true")
    ap.add_argument("--init", action="store_true")
    ap.add_argument("-m", "--message", default="")
    a = ap.parse_args()
    if a.freeze_ref:
        freeze_reference()
        return
    res = evaluate()
    if a.init:
        BASELINE.write_text(json.dumps(res["raw"], indent=2, default=float))
        print("baseline v0 stored:", json.dumps(res["raw"], default=float))
        res = evaluate()
    status = log_and_decide(res, a.message or ("baseline v0" if a.init else "no description"))
    print("---")
    print(f"val_score:  {res['val_score']:.6f}")
    for k in ("D", "R", "C", "M", "P"):
        if k in res:
            print(f"{k}:          {res[k]:.4f}")
    print(f"status:     {status}")
    print(f"runtime_s:  {res.get('runtime_s')}")


if __name__ == "__main__":
    main()
