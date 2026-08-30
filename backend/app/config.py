# -*- coding: utf-8 -*-
"""全局配置：路径常量与项目根目录注入。"""
from __future__ import annotations

import sys
from pathlib import Path

# backend/app/config.py -> 项目根目录 F:\CYC
APP_DIR = Path(__file__).resolve().parent      # backend/app
BACKEND_DIR = APP_DIR.parent                    # backend
PROJECT_DIR = BACKEND_DIR.parent                # 项目根

# 使后端可导入项目根的 algorithms 包
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

# 数据与模型路径
DATA_DIR = PROJECT_DIR / "data"
CONTEXT_PATH = DATA_DIR / "business" / "tightening_context.csv"
PIPELINE_PATH = PROJECT_DIR / "algorithms" / "models" / "quality_pipeline.joblib"

# 服务元信息
APP_TITLE = "重型机械装配车间螺栓拧紧质量智能检测与工艺追溯系统"
APP_VERSION = "1.0.0"
