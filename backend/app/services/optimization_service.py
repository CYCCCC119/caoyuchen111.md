# -*- coding: utf-8 -*-
"""参数优化服务：工艺参数关联分析与最优参数推荐。"""
from __future__ import annotations

from .. import state


def optimize(spec: str) -> dict:
    """针对某螺栓规格输出最优工艺参数组合。"""
    return state.analyzer().optimize(spec)


def correlation() -> dict:
    """工艺参数与质量结果的关联分析。"""
    return state.analyzer().param_correlation()
