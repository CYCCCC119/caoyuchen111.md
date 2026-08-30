# -*- coding: utf-8 -*-
"""后端 API 集成测试（FastAPI TestClient）。"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT))
sys.path.insert(0, str(PROJECT / "backend"))

from fastapi.testclient import TestClient  # noqa: E402

from main import app  # noqa: E402

client = TestClient(app)

CURVE = {"spec": "M20", "angle": [0, 10, 20, 30, 40, 50, 60],
         "torque": [3, 40, 120, 240, 300, 315, 320]}


class TestAPI(unittest.TestCase):
    def test_root(self):
        r = client.get("/")
        self.assertEqual(r.status_code, 200)
        self.assertIn("system", r.json())

    def test_detect(self):
        r = client.post("/api/detect", json=CURVE)
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertIn("label", body)
        self.assertIn("label_name", body)
        self.assertIn("confidence", body)

    def test_detect_batch(self):
        r = client.post("/api/detect/batch", json={"curves": [CURVE, CURVE]})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(r.json()["results"]), 2)

    def test_ingest_invalid_spec(self):
        r = client.post("/api/ingest", json={"spec": "M99", "angle": [0, 1, 2], "torque": [1, 2, 3]})
        self.assertEqual(r.status_code, 400)

    def test_ingest_length_mismatch(self):
        r = client.post("/api/ingest", json={"spec": "M20", "angle": [0, 1], "torque": [1, 2, 3]})
        self.assertEqual(r.status_code, 400)

    def test_trace(self):
        r = client.post("/api/trace", json={"workstation_id": "WS-001", "label": 1})
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertIn("summary", body)
        self.assertIn("records", body)

    def test_stats(self):
        r = client.get("/api/stats")
        self.assertEqual(r.status_code, 200)
        self.assertIn("pass_rate", r.json())

    def test_optimize(self):
        r = client.post("/api/optimize", json={"spec": "M20"})
        self.assertEqual(r.status_code, 200)
        self.assertIn("recommended", r.json())

    def test_correlation(self):
        r = client.get("/api/correlation")
        self.assertEqual(r.status_code, 200)
        self.assertIn("param_vs_defect", r.json())


if __name__ == "__main__":
    unittest.main()
