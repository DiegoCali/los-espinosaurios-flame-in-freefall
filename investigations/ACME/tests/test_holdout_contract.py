"""Pruebas exclusivamente sintéticas: NUNCA abren holdout real."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import evaluate_holdout as final  # noqa: E402


class TestHoldoutFinalContract(unittest.TestCase):
    def test_freeze_identifiers(self):
        self.assertEqual(len(final.FROZEN_COMMIT), 40)
        self.assertEqual(final.FROZEN_MODEL, "ridge_composition_quadratic_alpha_0_001")
        self.assertEqual(final.RUN_ID, "pilot-01")

    def test_reservation_is_exclusive(self):
        with tempfile.TemporaryDirectory() as d:
            receipt = Path(d) / "receipt.json"
            final.reserve_once(receipt, {"state": "reserved"})
            self.assertEqual(json.loads(receipt.read_text())["state"], "reserved")
            with self.assertRaises(FileExistsError):
                final.reserve_once(receipt, {"state": "second"})

    def test_grouped_metrics_use_synthetic_arrays(self):
        fake = [
            {"flame_type": "Normal", "group_id": "normal_day_FAKE"},
            {"flame_type": "Normal", "group_id": "normal_day_FAKE"},
            {"flame_type": "Inverse", "group_id": "inverse_day_FAKE"},
        ]
        y = np.array([2000, 2100, 2200], dtype=float)
        p = np.array([2010, 2090, 2230], dtype=float)
        out = final.metrics_by(fake, y, p, "flame_type")
        self.assertEqual(out["Normal"]["n"], 2)
        self.assertAlmostEqual(out["Normal"]["rmse_k"], 10.)
        self.assertAlmostEqual(out["Inverse"]["rmse_k"], 30.)

    def test_holdout_validation_rejects_wrong_size_without_reading_file(self):
        fake_audit = {
            "pilot_split_rows": {"holdout": 50},
            "pilot_split_groups": {"holdout": ["normal_day_FAKE"], "train": [], "validation": []},
        }
        with self.assertRaises(ValueError):
            final.validate_holdout_rows([], fake_audit)

    def test_report_creation_atomic_synthetic(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "output.json"
            final.write_json_atomic(path, {"global": {"rmse_k": 10.0}})
            self.assertEqual(json.loads(path.read_text())["global"]["rmse_k"], 10.0)


if __name__ == "__main__":
    unittest.main()
