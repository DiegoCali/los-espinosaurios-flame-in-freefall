"""Check that the SAME results are reproducible, without touching git.

1. Hash every processed CSV, re-run the extraction, hash again: files must be byte-identical.
2. Re-evaluate runs/autoresearch/same-run-01/best_train.py: val_score must equal best.json.
3. Protected files (prepare.py, model tables, experiment script, gate test) must match the manifest.

Writes runs/verification/reproducibility.json.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import prepare  # noqa: E402
from extraction import run_all  # noqa: E402

PROCESSED = ROOT / "data" / "processed"
RUN_DIR = ROOT / "runs" / "autoresearch" / "same-run-01"


def hashes() -> dict[str, str]:
    return {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(PROCESSED.glob("*.csv*"))}


def main() -> int:
    before = hashes()
    run_all.main(["--no-hash"])
    after = hashes()
    changed = sorted(k for k in before if before[k] != after.get(k))

    spec = importlib.util.spec_from_file_location("best_train", RUN_DIR / "best_train.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    res = prepare.evaluate(mod, seed=0)
    best = json.loads((RUN_DIR / "best.json").read_text())
    score_ok = abs(res["val_score"] - best["val_score"]) < 1e-9
    protected = prepare.check_manifest()

    report = {
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "processed_files": len(before),
        "processed_files_changed_after_rerun": changed,
        "best_val_score_recorded": best["val_score"],
        "best_val_score_recomputed": res["val_score"],
        "best_score_reproduced": score_ok,
        "protected_files_changed": protected,
        "ok": not changed and score_ok and not protected,
    }
    out = ROOT / "runs" / "verification" / "reproducibility.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
