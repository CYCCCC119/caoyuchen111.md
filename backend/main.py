# -*- coding: utf-8 -*-
"""FastAPI 应用入口。

启动方式（在 backend/ 目录下）：
    uvicorn main:app --reload --host 0.0.0.0 --port 8000
"""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import config
from app.routers import detection, ingest, optimization, traceability

app = FastAPI(title=config.APP_TITLE, version=config.APP_VERSION)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

for r in (detection.router, ingest.router, traceability.router, optimization.router):
    app.include_router(r)


@app.get("/", tags=["系统"], summary="系统信息与接口导航")
def root() -> dict:
    return {
        "system": config.APP_TITLE,
        "version": config.APP_VERSION,
        "endpoints": {
            "质量检测": ["POST /api/detect", "POST /api/detect/batch"],
            "数据接入": ["POST /api/ingest", "POST /api/ingest/file"],
            "工艺追溯": ["POST /api/trace", "GET /api/stats"],
            "参数优化": ["POST /api/optimize", "GET /api/correlation"],
        },
        "docs": "/docs",
    }
