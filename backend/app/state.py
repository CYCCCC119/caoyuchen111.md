# -*- coding: utf-8 -*-
"""共享服务实例（惰性单例）：模型检测器与工艺分析器。"""
from __future__ import annotations

from . import config  # noqa: F401  触发项目根目录 sys.path 注入

from algorithms.process_optimization import ProcessAnalyzer
from algorithms.quality_detection import QualityDetector

_detector: QualityDetector | None = None
_analyzer: ProcessAnalyzer | None = None


def detector() -> QualityDetector:
    global _detector
    if _detector is None:
        _detector = QualityDetector(config.PIPELINE_PATH)
    return _detector


def analyzer() -> ProcessAnalyzer:
    global _analyzer
    if _analyzer is None:
        _analyzer = ProcessAnalyzer(config.CONTEXT_PATH)
    return _analyzer
