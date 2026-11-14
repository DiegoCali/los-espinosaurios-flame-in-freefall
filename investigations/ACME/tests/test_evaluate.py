"""Pruebas del evaluador protegido, sin usar la partición final holdout."""
from __future__ import annotations

import csv
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import evaluate  # noqa: E402
import prepare  # noqa: E402
import train  # noqa: E402


class TestEvaluationContract(unittest.TestCase):
    def test_sizes_and_split_groups(self):
        xtr, ytr, xval, yval = evaluate.load_and_verify()
        self.assertEqual(xtr.shape, (134, 7))
        self.assertEqual(xval.shape, (52, 7))
        self.assertEqual(ytr.shape, (134,))
        self.assertEqual(yval.shape, (52,))

    def test_permitted_features_match_preparation(self):
        self.assertEqual(evaluate.FEATURE_ORDER[0], "flame_type_inverse")
        self.assertEqual(evaluate.NUMERIC_FEATURES,
                         [f for f in prepare.MODEL_FEATURES if f != "flame_type"])
        self.assertFalse(set(evaluate.FEATURE_ORDER) & {
            "zst_calculated", "tad_calculated_k", "pressure_final_atm",
            "pressure_mean_atm", "day", "test_id", "group_id", "split"
        })

    def test_candidate_produces_finite_predictions(self):
        xtr, ytr, xval, yval = evaluate.load_and_verify()
        predictions = train.fit_predict(xtr, ytr, xval, evaluate.SEED)
        metrics = evaluate.errors(yval, predictions)
        self.assertTrue(np.isfinite(metrics["rmse_k"]))
        self.assertGreaterEqual(metrics["mae_k"], 0)
        self.assertEqual(len(predictions), 52)

    def test_holdout_is_not_a_supported_split(self):
        with self.assertRaises(ValueError):
            evaluate.load_split("holdout")

    def test_invalid_predictions_rejected(self):
        with self.assertRaises(ValueError):
            evaluate.errors(np.zeros(4), np.zeros(3))
        with self.assertRaises(ValueError):
            evaluate.errors(np.zeros(4), np.array([0, 0, 0, float("nan")]))

    def test_ledger_is_append_only_and_numbered(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "results.tsv"
            self.assertEqual(evaluate.read_ledger(path), [])
            evaluate.append_ledger(path, {"attempt": 1, "status": "baseline"})
            evaluate.append_ledger(path, {"attempt": 2, "status": "keep"})
            self.assertEqual([r["status"] for r in evaluate.read_ledger(path)],
                             ["baseline", "keep"])
            with path.open(encoding="utf-8", newline="") as f:
                self.assertEqual(len(list(csv.DictReader(f, delimiter="\t"))), 2)


if __name__ == "__main__":
    unittest.main()
