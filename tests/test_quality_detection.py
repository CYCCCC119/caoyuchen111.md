# -*- coding: utf-8 -*-
"""模块二：质量检测模型单元测试。"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT))

import numpy as np
import pandas as pd

from algorithms.quality_detection import LABELS, QualityDetector


class TestQualityDetector(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.detector = QualityDetector()
        cls.test = pd.read_csv(PROJECT / "data" / "processed" / "test.csv")

    def test_model_loaded(self):
        self.assertIsNotNone(self.detector.model)

    def test_selected_features_match(self):
        self.assertEqual(len(self.detector.params["selected_features"]), 8)

    def test_test_set_accuracy(self):
        cols = self.detector.params["selected_features"]
        X = self.test[cols]
        y = self.test["label"].values
        acc = float((self.detector.model.predict(X) == y).mean())
        self.assertGreaterEqual(acc, 0.95)

    def test_predict_structure(self):
        result = self.detector.predict(
            [0, 10, 20, 30, 40, 50, 60],
            [3, 40, 120, 240, 300, 315, 320],
            "M20",
        )
        self.assertIn(result["label"], LABELS)
        self.assertIn("label_name", result)
        self.assertIn("confidence", result)
        self.assertIn("defect_level", result)
        self.assertAlmostEqual(sum(result["probabilities"].values()), 1.0, places=3)

    def test_predict_batch(self):
        curves = [
            {"spec": "M20", "angle": [0, 10, 20, 30, 40], "torque": [3, 40, 120, 240, 300]},
            {"spec": "M12", "angle": [0, 8, 16, 24, 32], "torque": [2, 10, 30, 60, 70]},
        ]
        results = self.detector.predict_batch(curves)
        self.assertEqual(len(results), 2)
        self.assertTrue(all(r["label"] in LABELS for r in results))


if __name__ == "__main__":
    unittest.main()
