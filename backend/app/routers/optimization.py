# -*- coding: utf-8 -*-
"""参数优化接口。"""
from __future__ import annotations

from fastapi import APIRouter

from ..schemas import OptimizeRequest
from ..services import optimization_service

router = APIRouter(prefix="/api", tags=["参数优化"])


@router.post("/optimize", summary="最优工艺参数推荐")
def optimize(req: OptimizeRequest) -> dict:
    return optimization_service.optimize(req.spec)


@router.get("/correlation", summary="工艺参数-质量关联分析")
def correlation() -> dict:
    return optimization_service.correlation()
