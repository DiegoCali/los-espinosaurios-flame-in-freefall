#!/usr/bin/env python3
"""Auditoría final única del piloto NASA PSI-10 / ACME Tad.

--check: verificación de código, fuentes, historial y partición de entrenamiento;
         NO abre ni inspecciona holdout.
--final: crea un recibo exclusivo ANTES de leer holdout, comprueba su
         correspondencia con los CSV originales y produce solo métricas
         agregadas. No permite una segunda ejecución del mismo cierre.

No modifica train.py, prepare.py ni evaluate.py. Ejecutar desde ACME con uv.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

import evaluate
import prepare

ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[1]
BRANCH = "feature/psi-10-acme-autoresearch"
FROZEN_COMMIT = "6d4dbe72c660dff475bfee09804ac275382300b6"
FROZEN_MODEL = "ridge_composition_quadratic_alpha_0_001"
RUN_ID = "pilot-01"
TRAIN_REPO_PATH = "investigations/ACME/train.py"
RESULT_DIR = ROOT / "runs" / "holdout-final-v1"
RECEIPT = RESULT_DIR / "execution_receipt.json"
REPORT = RESULT_DIR / "final_holdout_metrics.json"
PROTECTED_PATHS = [
    "investigations/ACME/prepare.py",
    "investigations/ACME/evaluate.py",
    "investigations/ACME/protocol.md",
    "investigations/ACME/data/metadata/acme_inventory.json",
    "investigations/ACME/pyproject.toml",
    "investigations/ACME/uv.lock",
]


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def command(*args: str, check: bool = True) -> bytes:
    result = subprocess.run(
        ["git", "-C", str(REPO_ROOT), *args], capture_output=True,
        check=False, timeout=10,
    )
    if check and result.returncode != 0:
        raise RuntimeError(f"Git {' '.join(args)}: {result.stderr.decode(errors='replace').strip()}")
    return result.stdout


def ensure_clean_tracked_files() -> None:
    for args in (("diff", "--quiet"), ("diff", "--cached", "--quiet")):
        result = subprocess.run(
            ["git", "-C", str(REPO_ROOT), *args], capture_output=True, timeout=10,
        )
        if result.returncode:
            raise RuntimeError("Existen cambios rastreados sin confirmar; congelar antes de la auditoría")
    # El evaluador debe haberse añadido mediante un commit a la rama.
    command("ls-files", "--error-unmatch", "investigations/ACME/evaluate_holdout.py")


def validate_history(train_digest: str) -> dict:
    ledger = ROOT / "runs" / RUN_ID / "results.tsv"
    if not ledger.is_file():
        raise FileNotFoundError(f"Falta el historial original: {ledger}")
    entries = evaluate.read_ledger(ledger)
    if len(entries) != 12:
        raise ValueError(f"Se esperaban 12 intentos en {RUN_ID}; hay {len(entries)}")
    if any(row["run_id"] != RUN_ID or int(row["seed"]) != prepare.SEED for row in entries):
        raise ValueError("run-id o semillas inconsistentes en el historial")
    best_candidates = [
        row for row in entries if row["status"] in {"baseline", "keep"}
    ]
    if not best_candidates:
        raise ValueError("No hay resultados aceptados en el historial")
    best = min(best_candidates, key=lambda row: float(row["val_rmse_k"]))
    last = entries[-1]
    if best is not last or last["status"] != "keep":
        raise ValueError("El intento 12 no es el mejor modelo aceptado")
    if last["model_name"] != FROZEN_MODEL:
        raise ValueError("El nombre de modelo del intento 12 no coincide")
    if last["train_sha256"] != train_digest:
        raise ValueError("El SHA-256 de train.py difiere del historial del intento 12")
    if not FROZEN_COMMIT.startswith(last["commit"]):
        raise ValueError("El commit del intento 12 no coincide con el congelado")
    return {
        "attempts": len(entries),
        "best_attempt": int(last["attempt"]),
        "best_validation_rmse_k": float(last["val_rmse_k"]),
        "best_validation_mae_k": float(last["val_mae_k"]),
        "ledger_sha256": sha256(ledger.read_bytes()),
    }


def preflight() -> tuple[dict, dict, str]:
    if command("branch", "--show-current").decode().strip() != BRANCH:
        raise RuntimeError(f"Utilizar la rama {BRANCH}")
    ensure_clean_tracked_files()
    subprocess.run(
        ["git", "-C", str(REPO_ROOT), "merge-base", "--is-ancestor", FROZEN_COMMIT, "HEAD"],
        check=True, capture_output=True, timeout=10,
    )
    difference = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "diff", "--quiet", FROZEN_COMMIT,
         "HEAD", "--", *PROTECTED_PATHS],
        check=False, capture_output=True, timeout=10,
    )
    if difference.returncode:
        raise RuntimeError("Se modificaron archivos protegidos tras congelar el modelo")

    frozen_content = command("show", f"{FROZEN_COMMIT}:{TRAIN_REPO_PATH}")
    model_content = (ROOT / "train.py").read_bytes()
    if model_content != frozen_content:
        raise RuntimeError("train.py no coincide byte a byte con el commit congelado")
    train_digest = sha256(model_content)

    import train
    if train.MODEL_NAME != FROZEN_MODEL:
        raise ValueError("El nombre del modelo no coincide con la versión congelada")

    audit_path = ROOT / "data" / "metadata" / "acme_inventory.json"
    audit = json.loads(audit_path.read_text(encoding="utf-8"))
    if audit["fixed_seed"] != prepare.SEED:
        raise ValueError("La semilla de los datos no coincide")
    if audit["permitted_input_features"] != prepare.MODEL_FEATURES:
        raise ValueError("Cambió el contrato de entradas físicas")
    for filename, expected_digest in audit["source_sha256"].items():
        if prepare.file_hash(ROOT / "data" / "raw" / filename) != expected_digest:
            raise ValueError(f"Cambió el archivo original NASA: {filename}")

    # Solo lee la partición de ENTRENAMIENTO. No lee validación ni holdout.
    x_train, y_train, groups, count = evaluate.load_split("train")
    if count != audit["pilot_split_rows"]["train"] or count != 134:
        raise ValueError("La cantidad de filas de entrenamiento no coincide")
    if groups != set(audit["pilot_split_groups"]["train"]):
        raise ValueError("Las jornadas de entrenamiento no coinciden")
    if x_train.shape != (134, len(evaluate.FEATURE_ORDER)):
        raise ValueError("Dimensión de entrenamiento inesperada")
    if not np.isfinite(y_train).all():
        raise ValueError("Etiquetas de entrenamiento no finitas")

    history = validate_history(train_digest)
    if RECEIPT.exists() or REPORT.exists():
        raise FileExistsError(
            "Ya existe un recibo/informe de evaluación final. No ejecutar de nuevo."
        )
    return audit, history, train_digest


def reserve_once(path: Path, info: dict) -> None:
    """Reserva exclusiva en disco ANTES de acceder al conjunto holdout."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as output:
        json.dump(info, output, indent=2, ensure_ascii=False)
        output.write("\n")
        output.flush()
        os.fsync(output.fileno())


def write_json_atomic(path: Path, value: dict) -> None:
    temporary = path.with_name(path.name + f".tmp-{os.getpid()}")
    try:
        with temporary.open("x", encoding="utf-8") as output:
            json.dump(value, output, indent=2, ensure_ascii=False)
            output.write("\n")
            output.flush()
            os.fsync(output.fileno())
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def validate_holdout_rows(rows: list[dict[str, str]], audit: dict):
    expected_count = audit["pilot_split_rows"]["holdout"]
    expected_groups = set(audit["pilot_split_groups"]["holdout"])
    training_groups = set(audit["pilot_split_groups"]["train"])
    validation_groups = set(audit["pilot_split_groups"]["validation"])
    if len(rows) != expected_count or expected_count != 50:
        raise ValueError("Número de filas holdout incorrecto")
    groups = {row["group_id"] for row in rows}
    if groups != expected_groups or groups & (training_groups | validation_groups):
        raise ValueError("Jornadas holdout incorrectas o solapadas")
    if len({row["test_id"] for row in rows}) != len(rows):
        raise ValueError("Identificadores duplicados en holdout")
    if not all(
        row["split"] == "holdout"
        and row["fuel"] == "C2H4"
        and row["flow_status"] == "steady"
        and row["flame_type"] in {"Normal", "Inverse"}
        for row in rows
    ):
        raise ValueError("Holdout contiene registros fuera del contrato")
    x = np.asarray([
        [float(row["flame_type"] == "Inverse")]
        + [float(row[k]) for k in evaluate.NUMERIC_FEATURES]
        for row in rows
    ], dtype=float)
    y = np.asarray([float(row["tad_calculated_k"]) for row in rows], dtype=float)
    if x.shape != (50, 7) or y.shape != (50,):
        raise ValueError("Forma inesperada en holdout")
    if not (np.isfinite(x).all() and np.isfinite(y).all()):
        raise ValueError("Valores no finitos en holdout")
    return x, y


def metrics_by(rows: list[dict[str, str]], y: np.ndarray,
               prediction: np.ndarray, field: str) -> dict:
    keys = sorted({row[field] for row in rows})
    result = {}
    for key in keys:
        indices = [i for i, row in enumerate(rows) if row[field] == key]
        values = evaluate.errors(y[indices], prediction[indices])
        result[key] = {"n": len(indices), **{f"{k}": round(v, 6) for k, v in values.items()}}
    return result


def read_final_data(audit: dict):
    """Solo invocar DESPUÉS de crear el recibo exclusivo."""
    path = ROOT / "data" / "processed" / "acme_tad_holdout.csv"
    with path.open(newline="", encoding="utf-8") as stream:
        reader = csv.DictReader(stream)
        if not set(prepare.PILOT_COLUMNS).issubset(set(reader.fieldnames or [])):
            raise ValueError("Columnas holdout no coinciden con el protocolo")
        rows = list(reader)
    x, y = validate_holdout_rows(rows, audit)

    # Verificación independiente de integridad contra los CSV NASA originales.
    # Esta reconstrucción se realiza exclusivamente en el modo FINAL.
    source_rows, hashes = prepare.read_sources(ROOT / "data" / "raw")
    if hashes != audit["source_sha256"]:
        raise ValueError("Los CSV de origen cambiaron durante la auditoría")
    pilot = [row for row in source_rows if prepare.eligible_for_tad(row)]
    assigned = prepare.group_splits(pilot)
    expected = []
    for row in pilot:
        if assigned[row["group_id"]] == "holdout":
            expected.append({**row, "split": "holdout"})
    if len(expected) != len(rows):
        raise ValueError("La partición calculada desde NASA tiene longitud distinta")
    for source, processed in zip(expected, rows):
        if any(source[k] != processed.get(k) for k in prepare.PILOT_COLUMNS):
            raise ValueError("El archivo holdout difiere de la fuente NASA normalizada")
    return rows, x, y, sha256(path.read_bytes())


def final_once(audit: dict, history: dict, train_digest: str) -> dict:
    receipt = {
        "state": "reserved_before_holdout_access",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "frozen_model_commit": FROZEN_COMMIT,
        "frozen_train_sha256": train_digest,
        "run_id": RUN_ID,
        "purpose": "single_independent_holdout_audit",
    }
    reserve_once(RECEIPT, receipt)
    started = time.perf_counter()
    try:
        # Las etiquetas holdout solo se abren después de reservar la ejecución.
        rows, x_test, y_test, holdout_digest = read_final_data(audit)
        x_train, y_train, _groups, _count = evaluate.load_split("train")
        import train
        prediction = np.asarray(
            train.fit_predict(x_train.copy(), y_train.copy(), x_test.copy(), prepare.SEED),
            dtype=float,
        )
        global_metrics = evaluate.errors(y_test, prediction)
        report = {
            "investigation": "NASA PSI-10 / ACME Flame Design",
            "objective": "Tad calculated (K), NOT measured temperature or soot",
            "status": "final_holdout_audit_completed",
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "model_name": train.MODEL_NAME,
            "frozen_model_commit": FROZEN_COMMIT,
            "train_sha256": train_digest,
            "ledger_sha256": history["ledger_sha256"],
            "source_sha256": audit["source_sha256"],
            "holdout_csv_sha256": holdout_digest,
            "python_version": sys.version.split()[0],
            "numpy_version": np.__version__,
            "n_train": len(y_train),
            "n_holdout": len(y_test),
            "validation_rmse_k_reference": round(history["best_validation_rmse_k"], 6),
            "global": {k: round(v, 6) for k, v in global_metrics.items()},
            "by_flame_type": metrics_by(rows, y_test, prediction, "flame_type"),
            "by_day_group": metrics_by(rows, y_test, prediction, "group_id"),
            "elapsed_seconds": round(time.perf_counter() - started, 6),
            "limitations": [
                "Single holdout audit after 11 validation-guided comparisons.",
                "Grouped observations from only four reserved experimental days.",
                "No direct soot, real-temperature or extinction labels.",
                "This audit must not be used for additional model selection.",
            ],
        }
        write_json_atomic(REPORT, report)
        receipt["state"] = "completed_do_not_repeat"
        receipt["completed_at_utc"] = report["timestamp_utc"]
        receipt["report_sha256"] = sha256(REPORT.read_bytes())
        write_json_atomic(RECEIPT, receipt)
        return report
    except BaseException as exc:
        receipt["state"] = "failed_or_interrupted_do_not_auto_repeat"
        receipt["failure"] = f"{type(exc).__name__}: {exc}"[:500]
        receipt["failed_at_utc"] = datetime.now(timezone.utc).isoformat()
        write_json_atomic(RECEIPT, receipt)
        raise


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true", help="preflight SIN abrir holdout")
    mode.add_argument("--final", action="store_true", help="única evaluación final holdout")
    args = parser.parse_args()
    audit, history, digest = preflight()
    if args.check:
        print("PREFLIGHT OK: ninguna lectura de holdout; modelo e historial congelados")
        print(f"rama: {BRANCH}")
        print(f"modelo: {FROZEN_MODEL} / {FROZEN_COMMIT[:7]}")
        print(f"SHA-256 train.py: {digest}")
        print(f"intentos: {history['attempts']}; mejor validación: {history['best_validation_rmse_k']:.6f} K")
        print("estado holdout: intacto; para la única evaluación ejecutar --final")
        return
    report = final_once(audit, history, digest)
    print("AUDITORÍA HOLDOUT FINAL COMPLETADA — NO VOLVER A EJECUTAR")
    print(f"modelo: {report['model_name']}")
    print(f"filas: {report['n_holdout']}")
    for key, value in report["global"].items():
        print(f"{key}: {value:.6f}")
    print("resultados por configuración:")
    for key, values in report["by_flame_type"].items():
        print(f"  {key}: n={values['n']}, RMSE={values['rmse_k']:.6f} K, MAE={values['mae_k']:.6f} K")
    print(f"reporte: {REPORT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
