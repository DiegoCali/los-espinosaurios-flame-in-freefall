"""Synthetic recovery/export checks; never load real holdout data."""
from __future__ import annotations

import csv
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import recover_validation_predictions as recovery  # noqa: E402
from export_predictions import evidence, verify_acme_validation  # noqa: E402


class TestValidationPredictions(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        processed = self.root / "data/processed"
        processed.mkdir(parents=True)
        (self.root / "train.py").write_text("# Synthetic hash fixture, never imported.\n")
        (processed / "acme_tad_train.csv").write_text("synthetic training hash fixture\n")
        fields = ("test_id", "flame_type", "group_id", "split", "tad_calculated_k")
        rows = [{"test_id": f"synthetic-{i}", "flame_type": "Normal", "group_id": "synthetic-day",
                 "split": "validation", "tad_calculated_k": 2000 + i} for i in range(52)]
        with (processed / "acme_tad_validation.csv").open("w", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)
        digest = evidence(self.root, "train.py")["sha256"]
        self.selected = {"model_name": "synthetic", "seed": 1, "features": ["synthetic"],
                         "train_sha256": digest, "val_rmse_k": 2., "val_mae_k": 2., "val_max_abs_error_k": 2.}
        self.report = {"model_name": "synthetic", "train_sha256": digest}
        self.saved = {"model": "synthetic", "split": "validation", "seed": 1, "feature_order": ["synthetic"],
            "train_sha256": digest, "n_train": 134, "n_validation": 52, "unit": "K",
            "residual_definition": "actual_minus_predicted",
            "source_files": [evidence(self.root, p) for p in (
                "train.py", "data/processed/acme_tad_train.csv", "data/processed/acme_tad_validation.csv")],
            "metrics": {"rmse_k": 2., "mae_k": 2., "max_abs_error_k": 2.},
            "predictions": [{**{k: row[k] for k in fields[:-1]},
                "actual": {"tad_calculated_k": row["tad_calculated_k"]},
                "predicted": {"tad_calculated_k": row["tad_calculated_k"] + 2},
                "residual": {"tad_calculated_k": -2},
                "source_file": "data/processed/acme_tad_validation.csv", "source_row": i + 1}
                for i, row in enumerate(rows)]}

    def verify(self):
        verify_acme_validation(self.root, self.saved, self.selected, self.report)

    def test_accepts_matching_predictions_and_rounding_tolerance(self):
        self.saved["metrics"]["rmse_k"] += 1e-8
        self.verify()

    def test_recomputes_metrics_from_predictions(self):
        row = self.saved["predictions"][0]
        row["predicted"]["tad_calculated_k"] += 3
        row["residual"]["tad_calculated_k"] -= 3
        with self.assertRaisesRegex(ValueError, "metrics mismatch.*export stopped"):
            self.verify()

    def test_rejects_wrong_split_and_residual(self):
        row = self.saved["predictions"][0]
        row["split"] = "holdout"
        with self.assertRaisesRegex(ValueError, "identifiers"):
            self.verify()
        row["split"] = "validation"
        row["residual"]["tad_calculated_k"] = 2
        with self.assertRaisesRegex(ValueError, "residual"):
            self.verify()

    def test_rejects_missing_rows_and_non_finite_values(self):
        row = self.saved["predictions"].pop()
        with self.assertRaisesRegex(ValueError, "52 distinct"):
            self.verify()
        self.saved["predictions"].append(row)
        row["predicted"]["tad_calculated_k"] = float("nan")
        with self.assertRaisesRegex(ValueError, "value or residual"):
            self.verify()

    def test_rejects_changed_source_hash(self):
        (self.root / "data/processed/acme_tad_train.csv").write_text("changed\n")
        with self.assertRaisesRegex(ValueError, "source changed"):
            self.verify()

    def test_frozen_hash_is_checked_before_model_call(self):
        for name, value in (("runs/holdout-final-v1/final_holdout_metrics.json", self.report),
                            ("runs/pilot-01/latest_validation.json", self.selected)):
            path = self.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(value))
        (self.root / "train.py").write_text("# Modified synthetic model\n")
        with mock.patch.object(recovery, "ROOT", self.root), mock.patch.object(recovery.evaluate, "load_and_verify") as loader:
            with self.assertRaisesRegex(ValueError, "frozen model SHA-256"):
                recovery.recover()
            loader.assert_not_called()

    def test_failed_recovery_does_not_overwrite_saved_predictions(self):
        path = self.root / recovery.OUTPUT
        path.parent.mkdir(parents=True)
        path.write_text("previous result\n")
        with mock.patch.object(recovery, "ROOT", self.root), mock.patch.object(
                recovery, "recover", side_effect=ValueError("metric mismatch")):
            with self.assertRaisesRegex(ValueError, "metric mismatch"):
                recovery.main()
        self.assertEqual(path.read_text(), "previous result\n")


if __name__ == "__main__":
    unittest.main()
