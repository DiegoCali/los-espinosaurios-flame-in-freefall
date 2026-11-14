#!/usr/bin/env python3
"""Modelo candidato de AutoResearch para NASA PSI-10 / Flame Design.

Único archivo editable durante la búsqueda. El evaluador (evaluate.py) fija
los datos, la separación por jornada y las métricas. No debe importarse
ningún conjunto de validación/holdout ni sus etiquetas desde aquí.

Interfaz obligatoria:
    fit_predict(X_train, y_train, X_eval, seed) -> np.ndarray

Orden de columnas, definido por evaluate.py:
    0  llama_inversa (1: Inverse, 0: Normal)
    1  burner_reactant_mole_fraction
    2  ambient_reactant_fraction_initial
    3  burner_reactant_flow_mg_s
    4  nitrogen_flow_mg_s
    5  total_flow_mg_s
    6  pressure_initial_atm
"""
from __future__ import annotations

import numpy as np

MODEL_NAME = "rbf_kernel_ridge_alpha_1"
RIDGE_ALPHA = 1.0


def fit_predict(
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_eval: np.ndarray,
    seed: int,
) -> np.ndarray:
    """Ajusta kernel Ridge gaussiano y predice Tad en K.

    Las medias y escalas se estiman exclusivamente con entrenamiento.
    La columna 0 es binaria; el resto representa entradas físicas.
    """
    del seed  # ajuste determinista; conservar argumento para otros modelos
    X_train = np.asarray(X_train, dtype=float)
    y_train = np.asarray(y_train, dtype=float).reshape(-1)
    X_eval = np.asarray(X_eval, dtype=float)

    if X_train.ndim != 2 or X_train.shape[1] != 7:
        raise ValueError("Se esperaban 7 características físicas en entrenamiento")
    if X_eval.ndim != 2 or X_eval.shape[1] != 7:
        raise ValueError("Se esperaban 7 características físicas en evaluación")
    if len(X_train) != len(y_train):
        raise ValueError("Longitudes X_train/y_train distintas")

    means = X_train[:, 1:].mean(axis=0)
    scales = X_train[:, 1:].std(axis=0)
    scales[scales < 1e-12] = 1.0
    z_train = np.column_stack((
        X_train[:, 0],
        (X_train[:, 1:] - means) / scales,
    ))
    z_eval = np.column_stack((
        X_eval[:, 0],
        (X_eval[:, 1:] - means) / scales,
    ))

    def squared_distances(left, right):
        return np.sum((left[:, None, :] - right[None, :, :])**2, axis=2)

    distances = squared_distances(z_train, z_train)
    positive = distances[distances > 0.0]
    width_squared = float(np.median(positive)) if positive.size else 1.0
    kernel = np.exp(-distances / (2.0 * width_squared))
    target_mean = y_train.mean()
    fitted = np.linalg.solve(
        kernel + RIDGE_ALPHA * np.eye(len(X_train)), y_train - target_mean,
    )
    evaluation_kernel = np.exp(
        -squared_distances(z_eval, z_train) / (2.0 * width_squared),
    )
    return target_mean + evaluation_kernel @ fitted
