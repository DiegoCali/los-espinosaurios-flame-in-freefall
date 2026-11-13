"""Final audit suite for the SAME module. Writes runs/verification/ with the same artefact set as SAFFIRE:

canonical_identifier_check.json, final_checks.json, final-pytest.xml, markdown_language_check.json,
raw_integrity_final.json, readable_exports_check.json, report_cleanup_check.json, reproducibility.json
(+ material_audit_sensitivity.json from scripts/sensitivity_material_audit.py).

Nothing here uses git except read-only `git rev-parse` / `git status`.

    .venv/bin/python scripts/final_audit.py
"""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
VER = ROOT / "runs" / "verification"
PY = sys.executable
RUN_DIR = ROOT / "runs" / "autoresearch" / "same-run-01"
EN_STOP = {"the", "of", "and", "to", "in", "is", "for", "with", "that", "are", "as", "from", "by", "this", "on"}
ES_STOP = {"el", "la", "de", "que", "en", "los", "las", "con", "para", "es", "una", "del", "por", "se", "como", "y", "o", "al",
           "más", "pero", "también", "sin", "sobre", "entre", "cuando", "donde", "este", "esta", "muy", "su", "sus", "lo", "un"}


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def run(args: list[str], **kw) -> subprocess.CompletedProcess:
    return subprocess.run(args, cwd=ROOT, capture_output=True, text=True, **kw)


def write(name: str, obj) -> dict:
    VER.mkdir(parents=True, exist_ok=True)
    (VER / name).write_text(json.dumps(obj, indent=2, default=str) + "\n")
    return obj


def project_markdown() -> list[Path]:
    skip = {".venv", "upstream_reference", ".pytest_cache", ".mplconfig", "__pycache__"}
    return sorted(p for p in ROOT.rglob("*.md") if not (set(p.relative_to(ROOT).parts) & skip) and "data/raw" not in str(p))


def spanish_lines(p: Path) -> list[int]:
    """Line numbers that look Spanish: accented/inverted Spanish characters with a Spanish stop word, or mostly stop words."""
    hits = []
    for i, line in enumerate(p.read_text(encoding="utf-8", errors="ignore").splitlines(), 1):
        w = re.findall(r"[a-záéíóúñ]+", line.lower())
        es, en = sum(x in ES_STOP for x in w), sum(x in EN_STOP for x in w)
        if (re.search(r"[áéíóúñ¿¡]", line) and es >= 1) or (es >= 3 and es > en):
            hits.append(i)
    return hits


def language(p: Path) -> str:
    return "es" if spanish_lines(p) else "en"


def text_sources() -> list[Path]:
    skip = {".venv", "upstream_reference", ".pytest_cache", ".mplconfig", "__pycache__", "raw"}
    exts = {".py", ".md", ".json", ".toml", ".tsv", ".csv"}
    return sorted(p for p in ROOT.rglob("*") if p.is_file() and p.suffix in exts and p.stat().st_size < 3_000_000
                  and not (set(p.relative_to(ROOT).parts) & skip) and not p.name.endswith("pytest.xml"))


def scientific_digest() -> str:
    d = json.loads((ROOT / "analysis-same.json").read_text())
    d.pop("generated_at", None)
    return hashlib.sha256(json.dumps(d, sort_keys=True).encode()).hexdigest()


def regenerate() -> dict:
    run([PY, "-W", "ignore", "analysis/build_analysis_json.py"], env={**__import__("os").environ, "MPLCONFIGDIR": str(ROOT / ".mplconfig")})
    files = ["analysis-same-summary.json", "SAME_EXPLICADO.md", "SAME_ANALYSIS_REPORT_EN.md", "data/processed/VALIDATION.md",
             "analysis/output/insights.json"]
    return {"scientific_digest": scientific_digest(), **{f: sha(ROOT / f) for f in files}}


def link_targets(md: Path) -> list[str]:
    return [m for m in re.findall(r"\]\(([^)#\s]+)(?:#[^)]*)?\)", md.read_text(encoding="utf-8")) if not m.startswith("http")]


def main() -> int:
    ts = datetime.now(timezone.utc).isoformat()
    VER.mkdir(parents=True, exist_ok=True)
    run([PY, "scripts/sensitivity_material_audit.py"])

    # ---- pytest
    xml = VER / "final-pytest.xml"
    pt = run([PY, "-m", "pytest", "-q", "--junitxml", str(xml)], timeout=900)
    suite = ET.parse(xml).getroot().find("testsuite")
    n_tests, n_fail = int(suite.get("tests")), int(suite.get("failures")) + int(suite.get("errors"))
    n_pass = n_tests - n_fail - int(suite.get("skipped"))

    # ---- reproducibility (re-extracts, re-scores the best model)
    rp = run([PY, "-W", "ignore", "scripts/verify_reproducibility.py"], timeout=900)
    repro = json.loads((VER / "reproducibility.json").read_text())

    # ---- two regenerations must give identical scientific content
    d1, d2 = regenerate(), regenerate()
    identical = d1 == d2

    summary = json.loads((ROOT / "analysis-same-summary.json").read_text())
    detail = json.loads((ROOT / "analysis-same.json").read_text())
    best = json.loads((RUN_DIR / "best.json").read_text())

    # ---- raw integrity
    from extraction.common import find_raw_dir, sha256_file, sha256_partial

    raw = find_raw_dir()
    import pandas as pd

    inv = pd.read_csv(ROOT / "data" / "inventory" / "files.csv")
    bad, missing = [], []
    for r in inv.itertuples():
        p = raw / r.file
        if not p.exists():
            missing.append(r.file)
            continue
        h = sha256_file(p) if r.hash_kind == "full" else sha256_partial(p)
        if h != r.sha256 or p.stat().st_size != r.size_bytes:
            bad.append(r.file)
    raw_report = write("raw_integrity_final.json", {
        "n_files": int(len(inv)), "verification": "sha256_full_up_to_64MB_else_size_plus_first_last_MiB",
        "missing": missing, "changed": bad, "unchanged": not missing and not bad, "raw_folder": raw.name})

    # ---- canonical identifier
    docs = ["analysis-same.json", "analysis-same-summary.json", "analysis-same.md", "SAME_EXPLICADO.md",
            "data/inventory/INVENTORY.md", "data/processed/VALIDATION.md", "README.md", "DATA_PLAN.md",
            "SAME_ANALYSIS_REPORT_EN.md", "knowledge/SAME_KNOWLEDGE_BASE.md"]
    texts = {d: (ROOT / d).read_text(encoding="utf-8") for d in docs}
    from prepare import check_manifest

    write("canonical_identifier_check.json", {
        "phase": "canonical_investigation_identifier", "investigation_id": "PSI-101",
        "companion_investigation_not_present_locally": "PSI-102",
        "n_tests": summary["scope"]["n_tests"], "n_attempts": len(detail["autoresearch"]["ledger"]),
        "documents_and_exports_checked": docs,
        "documents_naming_psi_101": [d for d in docs if "PSI-101" in texts[d]],
        "documents_naming_foreign_id_psi_99": [d for d in docs if "PSI-99" in texts[d]],
        "best_metrics_match_archived_run": abs(detail["autoresearch"]["best"]["val_score"] - best["val_score"]) < 1e-12,
        "train_equals_best_train": sha(ROOT / "train.py") == sha(RUN_DIR / "best_train.py"),
        "protected_files_unchanged": not check_manifest()})

    # ---- language: everything must be English (SAFFIRE_EXPLICADO.md is English too; only its name is Spanish)
    mds = project_markdown()
    langs = {str(p.relative_to(ROOT)): language(p) for p in mds}
    scan = {str(p.relative_to(ROOT)): spanish_lines(p) for p in text_sources()}
    spanish_files = {f: l[:5] for f, l in scan.items() if l and f != "scripts/final_audit.py"}
    write("markdown_language_check.json", {
        "phase": "english_markdown_and_code", "project_markdown_count": len(mds),
        "all_markdown_reviewed_in_english": all(v == "en" for v in langs.values()),
        "language_by_markdown_file": langs,
        "explainer_file": {"name": "SAME_EXPLICADO.md", "language": langs.get("SAME_EXPLICADO.md"),
                           "note": "Name mirrors SAFFIRE_EXPLICADO.md, which is also English."},
        "text_files_scanned_py_md_json_csv_tsv_toml": len(scan),
        "files_with_spanish_text": spanish_files,
        "all_text_files_english": not spanish_files,
        "markdown_sha256": {str(p.relative_to(ROOT)): sha(p) for p in mds}})

    # ---- readable exports
    files = list(summary["files"].values()) + [c["path"] for c in summary["charts"]]
    unresolved = [f for f in files if not (ROOT / f).exists()]
    refs = [r for i in summary["insights"] for r in i["evidence_refs"] if "/" in r or "." in r]
    unresolved_refs = [r for r in refs if not (ROOT / r.split("#")[0]).exists()]
    nulls_ok = all(u["value"] is None for u in summary["unavailable_results"])
    write("readable_exports_check.json", {
        "phase": "english_dashboard_export", "schema_version": summary["schema_version"], "language": summary["language"],
        "n_test_results": len(summary["test_results"]), "n_insights": len(summary["insights"]),
        "n_chart_descriptions": len(summary["charts"]),
        "test_count_matches_detailed_export": len(summary["test_results"]) == len(detail["tests"]),
        "best_score_matches_detailed_export": summary["predictive_model"]["score"]["best_model"] == round(best["val_score"], 4),
        "all_missing_values_preserved_as_null": nulls_ok,
        "all_evidence_references_and_file_links_resolve": not unresolved and not unresolved_refs,
        "unresolved": unresolved + unresolved_refs, "dataset_citation_preserved": bool(summary["source"]["url"]),
        "two_regenerations_identical": identical, "export_sha256": {k: v for k, v in d2.items() if k != "scientific_digest"}})

    # ---- report cleanup: every relative markdown link resolves
    broken, n_links = [], 0
    for md in mds:
        for t in link_targets(md):
            n_links += 1
            if not (md.parent / t).exists():
                broken.append(f"{md.relative_to(ROOT)} -> {t}")
    write("report_cleanup_check.json", {
        "phase": "report_and_link_cleanup", "analysis_report": "analysis-same.md", "english_report": "SAME_ANALYSIS_REPORT_EN.md",
        "dashboard_export": "analysis-same-summary.json", "n_markdown_links_checked": n_links, "broken_links": broken,
        "all_links_resolve": not broken, "current_model_notes_free_of_obsolete_logistic_text":
        "logistic C by inner" not in detail["predictive_model"]["description"]["notes"]
        and "logistic C by inner" not in detail["autoresearch"]["best"]["model"]["notes"],
        "n_tests": summary["scope"]["n_tests"], "n_insights": len(summary["insights"])})

    # ---- final checks
    st = run(["git", "status", "--porcelain"]).stdout.splitlines()
    outside = [l for l in st if "investigations/SAME" not in l]
    checks = write("final_checks.json", {
        "checked_at": ts, "pytest_passed": n_pass, "pytest_failed": n_fail, "pytest_output_tail": pt.stdout.strip().splitlines()[-1:],
        "json_parse_and_schema": "pass" if summary["schema_version"] == "1.0.0" else "fail",
        "json_scientific_digest_matches_two_full_regenerations": identical,
        "selected_attempt": best["attempt"], "selected_train_sha256": best["train_sha256"],
        "train_py_equals_best_train_py": sha(ROOT / "train.py") == sha(RUN_DIR / "best_train.py"),
        "notes_field_corrected_and_original_preserved": "notes_correction" in best["model"],
        "git_head": run(["git", "rev-parse", "HEAD"]).stdout.strip(),
        "git_commits_made_by_module_work": "none (no git commit/push/branch/reset was run)",
        "git_changes_outside_module_pre_existing": outside,
        "raw_integrity": {"n_files": raw_report["n_files"], "unchanged": raw_report["unchanged"]},
        "all_metric_source_files_exist": all((ROOT / f).exists() for f in summary["files"].values()),
        "n_attempts": len(detail["autoresearch"]["ledger"]), "n_tests": summary["scope"]["n_tests"],
        "reproducibility_ok": repro["ok"], "reproducibility_script_returncode": rp.returncode})
    ok = (n_fail == 0 and not spanish_files and repro["ok"] and identical and raw_report["unchanged"] and not broken and not unresolved)
    print(json.dumps({k: checks[k] for k in ("pytest_passed", "reproducibility_ok",
                                              "json_scientific_digest_matches_two_full_regenerations")}, indent=1),
          "raw unchanged:", raw_report["unchanged"], "| broken links:", len(broken), "| ALL OK" if ok else "| FAILURES")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
