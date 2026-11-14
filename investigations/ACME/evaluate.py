#!/usr/bin/env python3
"""Evaluador FIJO para el piloto NASA PSI-10 / ACME.

No consulta el archivo holdout. Lee solo train/validation y entrega a train.py
X_train, y_train y X_validation (nunca y_validation). Registra un intento por
llamada, con máximo 12 intentos (baseline incluida).

  python evaluate.py --baseline --run-id pilot-01
  python evaluate.py --candidate --run-id pilot-01 --description "Ridge inicial"
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import resource
import signal
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

import prepare

ROOT = Path(__file__).resolve().parent
NUMERIC_FEATURES = [f for f in prepare.MODEL_FEATURES if f != "flame_type"]
FEATURE_ORDER = ["flame_type_inverse"] + NUMERIC_FEATURES
SEED = prepare.SEED
MAX_ATTEMPTS = 12
MAX_CANDIDATE_SECONDS = 120
MIN_IMPROVEMENT_K = 0.001
FIELDNAMES = [
    "attempt", "run_id", "commit", "train_sha256", "seed", "model_name",
    "val_rmse_k", "val_mae_k", "val_max_abs_error_k", "elapsed_seconds",
    "peak_memory_mb", "status", "description",
]


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_split(name: str) -> tuple[np.ndarray, np.ndarray, set[str], int]:
    if name not in {"train", "validation"}:
        raise ValueError("Solo se permiten train y validation; holdout está protegido")
    path = ROOT / "data" / "processed" / f"acme_tad_{name}.csv"
    with path.open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    if not rows:
        raise ValueError(f"Partición vacía: {path}")
    X, y, groups = [], [], set()
    for row in rows:
        if (row["split"] != name or row["fuel"] != "C2H4"
                or row["flow_status"] != "steady"):
            raise ValueError(f"Registro fuera del contrato de {name}: {row['test_id']}")
        if row["flame_type"] not in {"Normal", "Inverse"}:
            raise ValueError("Tipo de llama desconocido")
        # El agente recibe la bandera de orientación y SOLO características
        # iniciales autorizadas. El identificador y la jornada se excluyen.
        X.append([float(row["flame_type"] == "Inverse")]
                 + [float(row[f]) for f in NUMERIC_FEATURES])
        y.append(float(row["tad_calculated_k"]))
        groups.add(row["group_id"])
    x_array = np.asarray(X, dtype=float)
    y_array = np.asarray(y, dtype=float)
    if not (np.isfinite(x_array).all() and np.isfinite(y_array).all()):
        raise ValueError("Los datos procesados contienen valores no finitos")
    return x_array, y_array, groups, len(rows)


def load_and_verify() -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    with (ROOT / "data" / "metadata" / "acme_inventory.json").open(encoding="utf-8") as f:
        audit = json.load(f)
    if audit["fixed_seed"] != SEED:
        raise ValueError("La semilla no coincide con la auditoría congelada")
    raw_dir = ROOT / "data" / "raw"
    actual = {name: prepare.file_hash(raw_dir / name) for name in prepare.FILES.values()}
    if audit["source_sha256"] != actual:
        raise ValueError("Cambió un archivo CSV de NASA")
    if audit["permitted_input_features"] != prepare.MODEL_FEATURES:
        raise ValueError("Cambió el contrato de características")
    xtr, ytr, tr_groups, ntr = load_split("train")
    xval, yval, val_groups, nval = load_split("validation")
    if tr_groups & val_groups:
        raise ValueError("Fuga: hay jornadas en ambas particiones")
    expected = audit["pilot_split_rows"]
    if (ntr, nval) != (expected["train"], expected["validation"]):
        raise ValueError("Las filas de entrenamiento/validación no coinciden con inventario")
    expected_groups = audit["pilot_split_groups"]
    if (tr_groups != set(expected_groups["train"])
            or val_groups != set(expected_groups["validation"])):
        raise ValueError("Cambió la asignación de jornadas")
    return xtr, ytr, xval, yval


def errors(y_true: np.ndarray, y_pred: np.ndarray) -> dict[str, float]:
    y_pred = np.asarray(y_pred, dtype=float)
    if y_pred.shape != y_true.shape or not np.isfinite(y_pred).all():
        raise ValueError("Predicción inválida: forma incorrecta o números no finitos")
    delta = y_pred - y_true
    return {
        "rmse_k": float(np.sqrt(np.mean(delta**2))),
        "mae_k": float(np.mean(np.abs(delta))),
        "max_abs_error_k": float(np.max(np.abs(delta))),
    }


def git_head() -> str:
    try:
        return subprocess.check_output(
            ["git", "-C", str(ROOT), "rev-parse", "--short", "HEAD"],
            stderr=subprocess.DEVNULL, text=True, timeout=3,
        ).strip()
    except (OSError, subprocess.SubprocessError):
        return "unavailable"


def read_ledger(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as file:
        rows = list(csv.DictReader(file, delimiter="\t"))
    if any(int(row["attempt"]) != i for i, row in enumerate(rows, 1)):
        raise ValueError("El historial contiene intentos faltantes o desordenados")
    return rows


def append_ledger(path: Path, record: dict) -> None:
    exists = path.exists()
    with path.open("a", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDNAMES, delimiter="\t")
        if not exists:
            writer.writeheader()
        writer.writerow({field: record.get(field, "") for field in FIELDNAMES})


def peak_mb() -> float:
    rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    # Linux usa KiB; macOS usa bytes.
    return round(rss / 1024 if sys.platform != "darwin" else rss / (1024**2), 3)


def predict_with_timeout(xtr: np.ndarray, ytr: np.ndarray,
                         xval: np.ndarray) -> tuple[np.ndarray, str]:
    """Linux: acota la evaluación del candidato a 120 s en tiempo real.

    Para cargas bloqueantes fuera de Python puede utilizarse adicionalmente
    `timeout 125s python ...` desde la terminal; ese corte externo no podrá
    quedar registrado automáticamente en results.tsv.
    """
    import train

    def alarm_handler(signum, frame):
        del signum, frame
        raise TimeoutError(f"El candidato excedió {MAX_CANDIDATE_SECONDS} segundos")

    old_handler = signal.getsignal(signal.SIGALRM)
    signal.signal(signal.SIGALRM, alarm_handler)
    signal.setitimer(signal.ITIMER_REAL, MAX_CANDIDATE_SECONDS)
    try:
        predicted = train.fit_predict(xtr.copy(), ytr.copy(), xval.copy(), SEED)
        return predicted, str(train.MODEL_NAME)[:100]
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0.0)
        signal.signal(signal.SIGALRM, old_handler)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    choices = parser.add_mutually_exclusive_group(required=True)
    choices.add_argument("--baseline", action="store_true")
    choices.add_argument("--candidate", action="store_true")
    parser.add_argument("--run-id", default="pilot-01")
    parser.add_argument("--description", default="")
    args = parser.parse_args()

    if not args.run_id.replace("-", "").replace("_", "").isalnum():
        parser.error("run-id solo admite letras, números, - y _")
    if len(args.description) > 240 or "\n" in args.description or "\t" in args.description:
        parser.error("descripción demasiado larga o con saltos/tabulaciones")

    out = ROOT / "runs" / args.run_id
    out.mkdir(parents=True, exist_ok=True)
    ledger_path = out / "results.tsv"
    history = read_ledger(ledger_path)
    if len(history) >= MAX_ATTEMPTS:
        parser.error(f"se alcanzaron {MAX_ATTEMPTS} intentos; use un run-id nuevo")
    if args.baseline and history:
        parser.error("la línea base debe ejecutarse una vez en un run-id nuevo")
    if args.candidate and not history:
        parser.error("primero ejecute --baseline en este run-id")

    xtr, ytr, xval, yval = load_and_verify()
    attempt = len(history) + 1
    started = time.perf_counter()
    candidate_hash = file_hash(ROOT / "train.py") if args.candidate else "-"
    model_name = "training_mean" if args.baseline else "unknown"
    status = "crash"
    metrics = None
    problem = None

    try:
        if args.baseline:
            predictions = np.full_like(yval, ytr.mean())
        else:
            # El objetivo de validación yval NUNCA se pasa al modelo editable.
            predictions, model_name = predict_with_timeout(xtr, ytr, xval)
        if args.candidate and time.perf_counter() - started > MAX_CANDIDATE_SECONDS:
            raise TimeoutError(f"El candidato excedió {MAX_CANDIDATE_SECONDS} segundos")
        metrics = errors(yval, predictions)
        if args.baseline:
            status = "baseline"
        else:
            best = min(
                float(r["val_rmse_k"])
                for r in history if r["status"] in {"baseline", "keep"}
            )
            status = "keep" if metrics["rmse_k"] < best - MIN_IMPROVEMENT_K else "discard"
    except Exception as exc:
        problem = f"{type(exc).__name__}: {exc}"[:220]

    elapsed = round(time.perf_counter() - started, 6)
    record = {
        "attempt": attempt, "run_id": args.run_id, "commit": git_head(),
        "train_sha256": candidate_hash, "seed": SEED, "model_name": model_name,
        "elapsed_seconds": elapsed, "peak_memory_mb": peak_mb(), "status": status,
        "description": (args.description or ("Línea base: media de entrenamiento" if args.baseline else "candidato"))
                       + (f" | {problem}" if problem else ""),
    }
    if metrics:
        record.update({
            "val_rmse_k": metrics["rmse_k"],
            "val_mae_k": metrics["mae_k"],
            "val_max_abs_error_k": metrics["max_abs_error_k"],
        })
    append_ledger(ledger_path, record)
    (out / "latest_validation.json").write_text(
        json.dumps({**record, "features": FEATURE_ORDER, "n_train": len(ytr),
                    "n_validation": len(yval), "objective": "calculated_Tad_not_soot"},
                   ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print("---")
    print("experiment: NASA PSI-10 / Tad surrogate; NOT soot detection")
    print(f"model_name: {model_name}")
    for key in ("val_rmse_k", "val_mae_k", "val_max_abs_error_k"):
        if key in record:
            print(f"{key}: {record[key]:.6f}")
    print(f"elapsed_seconds: {elapsed:.6f}")
    print(f"peak_memory_mb: {record['peak_memory_mb']:.3f}")
    print(f"attempt: {attempt}/{MAX_ATTEMPTS}")
    print(f"status: {status}")
    print(f"ledger: {ledger_path.relative_to(ROOT)}")
    if problem:
        print(f"error: {problem}", file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
