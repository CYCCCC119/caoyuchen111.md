# -*- coding: utf-8 -*-
"""工艺追溯接口。"""
from __future__ import annotations

from fastapi import APIRouter

from ..schemas import TraceQuery
from ..services import traceability_service

router = APIRouter(prefix="/api", tags=["工艺追溯"])


@router.post("/trace", summary="多条件组合工艺追溯")
def trace(query: TraceQuery) -> dict:
    return traceability_service.trace(query)


@router.get("/stats", summary="全局质量统计")
def stats() -> dict:
    return traceability_service.stats()
