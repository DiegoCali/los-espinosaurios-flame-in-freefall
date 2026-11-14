"""Lightweight preparation tests; no pandas or scikit-learn required."""
import csv
import sys
import unittest
from pathlib import Path

ACME_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ACME_ROOT))
import prepare  # noqa: E402


class TestAcmePreparation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.audit = prepare.prepare()
        cls.out = ACME_ROOT / "data" / "processed"

    @staticmethod
    def read_csv(path):
        with path.open(encoding="utf-8", newline="") as stream:
            return list(csv.DictReader(stream))

    def test_source_counts(self):
        self.assertEqual(self.audit["original_rows"], 327)
        self.assertEqual(self.audit["original_by_flame"], {"Inverse": 120, "Normal": 207})
        self.assertEqual(self.audit["tad_numeric_rows_all_fuels"], 256)

    def test_ramp_rows_and_propane_excluded_only_from_pilot(self):
        all_rows = self.read_csv(self.out / "acme_all.csv")
        pilot = self.read_csv(self.out / "acme_tad_pilot.csv")
        self.assertEqual(len(all_rows), 327)
        self.assertEqual(len(pilot), 236)
        self.assertTrue(all(row["fuel"] == "C2H4" for row in pilot))
        self.assertTrue(all(row["flow_status"] == "steady" for row in pilot))
        self.assertEqual(len({row["test_id"] for row in all_rows}), 327)
        self.assertEqual(sum(row["fuel"] == "C3H8" for row in all_rows), 20)

    def test_no_day_group_leakage(self):
        groups = {}
        for split in ("train", "validation", "holdout"):
            rows = self.read_csv(self.out / f"acme_tad_{split}.csv")
            groups[split] = {row["group_id"] for row in rows}
            self.assertTrue(rows)
            self.assertTrue(all(row["split"] == split for row in rows))
        self.assertFalse(groups["train"] & groups["validation"])
        self.assertFalse(groups["train"] & groups["holdout"])
        self.assertFalse(groups["validation"] & groups["holdout"])

    def test_feature_safety_contract(self):
        features = set(prepare.MODEL_FEATURES)
        self.assertFalse(features & {
            "zst_calculated", "tad_calculated_k", "pressure_final_atm",
            "pressure_mean_atm", "ambient_reactant_fraction_final",
            "test_id", "day", "group_id", "split",
        })


if __name__ == "__main__":
    unittest.main()
