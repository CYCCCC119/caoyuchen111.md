# -*- coding: utf-8 -*-
"""数据接入接口：曲线校验 + 接入 + 实时检测。"""
from __future__ import annotations

import io
from datetime import datetime

import pandas as pd
from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from ..schemas import CurveInput, DetectResponse
from ..services import detection_service

router = APIRouter(prefix="/api", tags=["数据接入"])

VALID_SPECS = {"M12", "M16", "M20", "M24"}


def _validate(curve: CurveInput) -> None:
    if curve.spec not in VALID_SPECS:
        raise HTTPException(400, f"不支持的螺栓规格 {curve.spec}（应为 M12/M16/M20/M24）")
    if not curve.angle or not curve.torque:
        raise HTTPException(400, "转角/力矩序列不能为空")
    if len(curve.angle) != len(curve.torque):
        raise HTTPException(400, "转角与力矩序列长度不一致")
    if len(curve.angle) < 3:
        raise HTTPException(400, "采样点过少（至少 3 个点）")


def _gen_record_id() -> str:
    return f"R{datetime.now():%Y%m%d%H%M%S%f}"


@router.post("/ingest", response_model=DetectResponse, summary="单条曲线接入并实时检测")
def ingest(curve: CurveInput) -> dict:
    _validate(curve)
    if not curve.record_id:
        curve.record_id = _gen_record_id()
    return detection_service.detect(curve)


@router.post("/ingest/file", response_model=DetectResponse, summary="CSV 文件接入（angle,torque 两列）")
def ingest_file(spec: str = Form(..., description="螺栓规格 M12/M16/M20/M24"),
                file: UploadFile = File(...)) -> dict:
    if spec not in VALID_SPECS:
        raise HTTPException(400, f"不支持的螺栓规格 {spec}")
    try:
        content = file.file.read().decode("utf-8")
        df = pd.read_csv(io.StringIO(content))
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(400, f"CSV 解析失败：{exc}") from exc

    if "angle" not in df.columns or "torque" not in df.columns:
        raise HTTPException(400, "CSV 需包含 angle、torque 两列")
    curve = CurveInput(spec=spec, angle=df["angle"].tolist(), torque=df["torque"].tolist())
    _validate(curve)
    curve.record_id = _gen_record_id()
    return detection_service.detect(curve)
