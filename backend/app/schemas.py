# -*- coding: utf-8 -*-
"""Pydantic 请求/响应模型定义（接口契约）。"""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class CurveInput(BaseModel):
    """单条拧紧力矩-转角曲线输入。"""
    spec: str = Field(..., description="螺栓规格 M12/M16/M20/M24")
    angle: list[float] = Field(..., description="转角序列 deg")
    torque: list[float] = Field(..., description="力矩序列 N·m")
    record_id: Optional[str] = Field(None, description="记录 ID（可选）")


class BatchDetectRequest(BaseModel):
    curves: list[CurveInput] = Field(..., description="待检测曲线列表")


class DetectResponse(BaseModel):
    record_id: Optional[str] = None
    label: int
    label_name: str
    confidence: float
    defect_level: int
    probabilities: dict[str, float]
    features: dict[str, float]


class TraceQuery(BaseModel):
    """多条件工艺追溯查询参数。"""
    spec: Optional[str] = None
    workstation_id: Optional[str] = None
    operator: Optional[str] = None
    batch_id: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    label: Optional[int] = Field(None, ge=0, le=4, description="质量标签 0-4")
    limit: int = Field(100, ge=1, le=1000, description="返回条数上限")


class OptimizeRequest(BaseModel):
    spec: str = Field("M20", description="螺栓规格 M12/M16/M20/M24")
