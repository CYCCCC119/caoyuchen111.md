# -*- coding: utf-8 -*-
"""质量检测服务：调用算法模型完成单条/批量拧紧质量判定。"""
from __future__ import annotations

from .. import state
from ..schemas import CurveInput


def detect(curve: CurveInput) -> dict:
    """单条曲线质量检测。"""
    result = state.detector().predict(curve.angle, curve.torque, curve.spec)
    result["record_id"] = curve.record_id
    return result


def detect_batch(curves: list[CurveInput]) -> list[dict]:
    """批量曲线质量检测。"""
    det = state.detector()
    out = []
    for c in curves:
        r = det.predict(c.angle, c.torque, c.spec)
        r["record_id"] = c.record_id
        out.append(r)
    return out
