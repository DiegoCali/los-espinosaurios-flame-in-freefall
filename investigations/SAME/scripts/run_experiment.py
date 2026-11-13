"""Evaluate the current train.py as one AutoResearch attempt and log it WITHOUT touching git.

Replaces the upstream `git commit` / `git reset` loop: every attempt is archived as files in
runs/autoresearch/same-run-01/:

    attempt-XX.json       metrics, model description, held-out predictions, gate results
    attempt-XX.train.py   exact snapshot of the candidate that was evaluated
    results.tsv           ledger (one line per attempt)
    best.json             metrics of the best kept attempt
    best_train.py         backup of the best candidate (restore with --restore-best)

Usage:
    .venv/bin/python scripts/run_experiment.py --description "what changed"
    .venv/bin/python scripts/run_experiment.py --restore-best
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import re
import shutil
import subprocess
import sys
import traceback
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import prepare  # noqa: E402

RUN_DIR = ROOT / "runs" / "autoresearch" / "same-run-01"
TRAIN = ROOT / "train.py"
MAX_ATTEMPTS = 15
MIN_REL_IMPROVEMENT = 0.001  # 0.1 %: smaller gains are discarded (simplicity rule)
FORBIDDEN = [r"\bopen\s*\(", r"read_csv", r"read_excel", r"np\.load", r"\bPath\s*\(", r"__file__",
             r"size_dataset", r"detection_dataset", r"import\s+prepare", r"from\s+prepare", r"\bsubprocess\b",
             r"\bos\.", r"\bjson\b", r"\[\s*['\"](test|run|source_row)['\"]\s*\]"]
TSV_HEADER = "attempt\ttrain_sha256\tmodel_name\tval_score\tsize_nrmse\tdetection_brier_ratio\tnum_params\tstatus\tdescription\n"


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def static_gate(src: str) -> list[str]:
    return [pat for pat in FORBIDDEN if re.search(pat, src)]


def load_candidate():
    spec = importlib.util.spec_from_file_location("train_candidate", TRAIN)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def next_attempt() -> int:
    return len(list(RUN_DIR.glob("attempt-[0-9][0-9].json"))) + 1


def best_record() -> dict | None:
    p = RUN_DIR / "best.json"
    return json.loads(p.read_text()) if p.exists() else None


def run_pytest(attempt: int) -> dict:
    xml = RUN_DIR / f"attempt-{attempt:02d}-pytest.xml"
    r = subprocess.run([sys.executable, "-m", "pytest", "-q", "tests/test_experiment_gate.py", f"--junitxml={xml}"],
                       cwd=ROOT, capture_output=True, text=True, timeout=600)
    return {"returncode": r.returncode, "tail": r.stdout.strip().splitlines()[-1:] if r.stdout else []}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--description", default="")
    ap.add_argument("--restore-best", action="store_true")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--skip-pytest", action="store_true")
    a = ap.parse_args(argv)
    RUN_DIR.mkdir(parents=True, exist_ok=True)

    if a.restore_best:
        src = RUN_DIR / "best_train.py"
        if not src.exists():
            print("no best_train.py yet")
            return 1
        shutil.copyfile(src, TRAIN)
        print(f"train.py restored from {src.relative_to(ROOT)}")
        return 0

    attempt = next_attempt()
    if attempt > MAX_ATTEMPTS:
        print(f"budget exhausted: {MAX_ATTEMPTS} attempts already recorded")
        return 2
    if not a.description:
        print("--description is required")
        return 2

    src = TRAIN.read_text()
    shutil.copyfile(TRAIN, RUN_DIR / f"attempt-{attempt:02d}.train.py")
    record = {"attempt": attempt, "description": a.description,
              "timestamp_utc": datetime.now(timezone.utc).isoformat(), "train_sha256": _sha(TRAIN),
              "validation": "leave_one_run_out (size) / leave_one_test_out (detection)"}

    gate = {"protected_files_changed": prepare.check_manifest(), "forbidden_patterns": static_gate(src)}
    if attempt == 1 and gate["protected_files_changed"] == ["protected_manifest.json missing (run: prepare.py --init-manifest)"]:
        prepare.write_manifest()
        gate["protected_files_changed"] = []
        gate["manifest_initialised"] = True
    record["gate"] = gate
    if not a.skip_pytest:
        record["pytest"] = run_pytest(attempt)

    status, metrics = "crash", None
    if gate["protected_files_changed"] or gate["forbidden_patterns"]:
        record["error"] = "gate failed"
    elif record.get("pytest", {}).get("returncode", 0) != 0:
        record["error"] = "pytest failed"
    else:
        try:
            mod = load_candidate()
            res = prepare.evaluate(mod, seed=a.seed)
            record["model"] = mod.describe_model()
            record["cv_predictions"] = prepare.cv_prediction_records(res)
            metrics = {k: v for k, v in res.items() if not k.startswith("_")}
            record.update(metrics)
            best = best_record()
            if best is None or res["val_score"] < best["val_score"] * (1 - MIN_REL_IMPROVEMENT):
                status = "keep"
            else:
                status = "discard"
        except Exception:  # noqa: BLE001 - every failure is logged as a crash
            record["error"] = traceback.format_exc()
    record["status"] = status
    prepare_json = json.dumps(record, indent=2, default=float)
    (RUN_DIR / f"attempt-{attempt:02d}.json").write_text(prepare_json + "\n")

    tsv = RUN_DIR / "results.tsv"
    if not tsv.exists():
        tsv.write_text(TSV_HEADER)
    m = record.get("model", {})
    with tsv.open("a") as f:
        f.write("\t".join([
            str(attempt), record["train_sha256"][:12], str(m.get("model_name", "")),
            f"{metrics['val_score']:.6f}" if metrics else "nan",
            f"{metrics['size_nrmse']:.6f}" if metrics else "nan",
            f"{metrics['detection_brier_ratio']:.6f}" if metrics else "nan",
            str(m.get("num_params", "")), status, a.description.replace("\t", " "),
        ]) + "\n")

    if status == "keep":
        shutil.copyfile(TRAIN, RUN_DIR / "best_train.py")
        best = {k: record[k] for k in ("attempt", "description", "train_sha256", "model", "val_score",
                                       "size_nrmse", "detection_brier_ratio", "size_rmse", "size_nrmse_by_target",
                                       "size_factor_error", "detection_brier", "detection_brier_ratio_by_target",
                                       "detection_accuracy_at_0p5", "n_size_rows", "n_size_groups",
                                       "n_detection_rows", "n_detection_groups", "seed")}
        (RUN_DIR / "best.json").write_text(json.dumps(best, indent=2, default=float) + "\n")
    elif status in ("discard", "crash") and (RUN_DIR / "best_train.py").exists():
        shutil.copyfile(RUN_DIR / "best_train.py", TRAIN)  # revert, like `git reset` upstream

    summary = f"attempt {attempt:02d} {status}"
    if metrics:
        summary += (f" val_score={metrics['val_score']:.4f} size_nrmse={metrics['size_nrmse']:.4f} "
                    f"det_brier_ratio={metrics['detection_brier_ratio']:.4f}")
    else:
        summary += f" error={record.get('error', '')[-300:]}"
    print(summary)
    return 0 if status != "crash" else 1


if __name__ == "__main__":
    sys.exit(main())
