# -*- coding: utf-8 -*-
"""质量检测接口。"""
from __future__ import annotations

from fastapi import APIRouter

from ..schemas import BatchDetectRequest, CurveInput, DetectResponse
from ..services import detection_service

router = APIRouter(prefix="/api", tags=["质量检测"])


@router.post("/detect", response_model=DetectResponse, summary="单条拧紧曲线质量检测")
def detect(curve: CurveInput) -> dict:
    return detection_service.detect(curve)


@router.post("/detect/batch", summary="批量拧紧曲线质量检测")
def detect_batch(req: BatchDetectRequest) -> dict:
    return {"results": detection_service.detect_batch(req.curves)}
