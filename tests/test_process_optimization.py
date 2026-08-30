# -*- coding: utf-8 -*-
"""模块三：工艺追溯与参数优化单元测试。"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT))

from algorithms.process_optimization import ProcessAnalyzer


class TestProcessOptimization(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.an = ProcessAnalyzer()

    def test_context_loaded(self):
        self.assertEqual(len(self.an.df), 3000)

    def test_trace_by_workstation(self):
        recs = self.an.trace(workstation_id="WS-001")
        self.assertGreater(len(recs), 0)
        self.assertTrue((recs["workstation_id"] == "WS-001").all())

    def test_trace_by_label(self):
        recs = self.an.trace(label=1)
        self.assertTrue((recs["label"] == 1).all())

    def test_trace_by_spec_and_time(self):
        recs = self.an.trace(spec="M20", start_time="2026-08-01", end_time="2026-08-04")
        self.assertTrue((recs["spec"] == "M20").all())

    def test_summary(self):
        s = self.an.summary(self.an.df)
        self.assertEqual(s["n"], 3000)
        self.assertIn("pass_rate", s)

    def test_optimize(self):
        opt = self.an.optimize("M20")
        self.assertIn("recommended", opt)
        self.assertIn("pass_rate", opt["recommended"])
        self.assertIn("top_configs", opt)

    def test_correlation(self):
        corr = self.an.param_correlation()
        self.assertIn("param_vs_defect", corr)
        self.assertIn("param_vs_feature", corr)
        self.assertTrue(len(corr["param_vs_defect"]) >= 5)


if __name__ == "__main__":
    unittest.main()
