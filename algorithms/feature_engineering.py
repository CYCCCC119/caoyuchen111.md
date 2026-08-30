# -*- coding: utf-8 -*-
"""
模块一：时序数据特征工程（工业大数据预处理与特征工程）

将非结构化的「力矩-转角」时序曲线转化为结构化特征向量，为质量检测模型提供标准输入。
本模块为特征提取的**唯一实现**，`data/preprocess.py` 与后端推理均复用此处的函数，避免逻辑漂移。

处理流程：
  1. 数据清洗   —— 去除空行程段、3σ 异常值剔除 + 线性插值
  2. 特征提取   —— 12 维时域特征
  3. 特征选择   —— Pearson 相关 + 共线性分析（结果固化在 feature_metadata.json）
  4. 特征标准化 —— Z-score（复用训练集统计量，避免数据泄露）
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

# 各规格名义最终拧紧角度（用于计算「转角偏差量」特征）
NOMINAL_ANGLE = {"M12": 95.0, "M16": 135.0, "M20": 175.0, "M24": 220.0}

# 12 维时域特征定义（名称 -> 物理含义）
FEATURE_NAMES = [
    "torque_max",         # 力矩最大值 (N·m)
    "torque_mean",        # 力矩平均值 (N·m)
    "torque_std",         # 力矩标准差 (N·m)
    "torque_peak_angle",  # 力矩峰值出现角度 (deg)
    "snug_torque",        # 贴合点扭矩 (N·m)
    "total_angle",        # 拧紧总转角 (deg)
    "avg_rate",           # 拧紧平均速率 (N·m/deg)
    "rising_slope",       # 力矩上升斜率 (N·m/deg)
    "torque_fluctuation", # 力矩波动率 (无量纲)
    "angle_deviation",    # 转角偏差量 (deg)
    "final_torque",       # 最终扭矩值 (N·m)
    "hold_fluctuation",   # 扭矩保持段波动率 (N·m)
]

# 质量标签编码
LABEL_NAMES = {0: "合格", 1: "欠拧", 2: "过拧", 3: "滑牙", 4: "虚拧"}


def clean_curve(angle: np.ndarray, torque: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """数据清洗：去除空行程段 + 3σ 异常值剔除并线性插值补全。"""
    angle = np.asarray(angle, dtype=float)
    torque = np.asarray(torque, dtype=float)

    # 1) 去除空行程段：截取从贴合点（力矩首次超过峰值 30%）到终止
    if len(torque) == 0:
        return angle, torque
    thresh = 0.3 * np.max(torque)
    snug_idx = int(np.argmax(torque >= thresh))
    angle, torque = angle[snug_idx:], torque[snug_idx:]
    if len(torque) < 3:
        return angle, torque

    # 2) 3σ 异常值剔除：基于一阶差分（跳变点）识别离群点，线性插值补全
    diff = np.abs(np.diff(torque, prepend=torque[0]))
    mu, sigma = diff.mean(), diff.std()
    if sigma > 1e-9:
        outliers = diff > (mu + 3 * sigma)
        if outliers.any():
            idx = np.where(outliers)[0]
            torque_clean = torque.copy()
            for i in idx:
                if 0 < i < len(torque) - 1:
                    torque_clean[i] = (torque[i - 1] + torque[i + 1]) / 2.0
            torque = torque_clean

    return angle, torque


def extract_features(angle: np.ndarray, torque: np.ndarray, spec: str) -> dict:
    """从力矩-转角时序提取 12 维时域特征。"""
    n = len(torque)
    torque_max = float(np.max(torque))
    peak_idx = int(np.argmax(torque))
    thresh = 0.3 * torque_max
    snug_idx = int(np.argmax(torque >= thresh)) if torque_max > 0 else 0

    grad = np.gradient(torque, angle)
    hold_start = int(n * 0.8)  # 保持段起点（末 20% 区间）

    snug_torque = float(torque[snug_idx])
    denom = float(angle[peak_idx] - angle[snug_idx]) if peak_idx > snug_idx else 1e-6

    return {
        "torque_max": torque_max,
        "torque_mean": float(np.mean(torque)),
        "torque_std": float(np.std(torque)),
        "torque_peak_angle": float(angle[peak_idx]),
        "snug_torque": snug_torque,
        "total_angle": float(angle[-1] - angle[0]),
        "avg_rate": float((torque_max - snug_torque) / denom),
        "rising_slope": float(np.max(grad[: peak_idx + 1])),
        "torque_fluctuation": float(np.std(torque) / (np.mean(torque) + 1e-6)),
        "angle_deviation": float(angle[-1] - NOMINAL_ANGLE.get(spec, np.nan)),
        "final_torque": float(torque[-1]),
        "hold_fluctuation": float(np.std(torque[hold_start:])),
    }


def standardize_features(features: dict, mean: dict, std: dict) -> dict:
    """对已选特征做 Z-score 标准化（复用训练集统计量）。"""
    out = {}
    for k, v in features.items():
        mu = mean.get(k, 0.0)
        sd = std.get(k, 1.0) or 1e-9
        out[k] = (v - mu) / sd
    return out


def load_pipeline_params(metadata_path: str | Path) -> dict:
    """从 feature_metadata.json 读取特征选择结果与标准化参数（训练阶段产出）。"""
    with open(metadata_path, encoding="utf-8") as f:
        meta = json.load(f)
    return {
        "selected_features": meta["selected_features"],
        "mean": meta["standardization"]["mean"],
        "std": meta["standardization"]["std"],
    }


def build_feature_vector(angle, torque, spec: str, params: dict) -> dict:
    """端到端：清洗 + 特征提取 + 选择 + 标准化，输出模型可用的特征向量。"""
    angle_c, torque_c = clean_curve(angle, torque)
    feats = extract_features(angle_c, torque_c, spec)
    selected = params["selected_features"]
    feats = {k: feats[k] for k in selected}
    return standardize_features(feats, params["mean"], params["std"])
