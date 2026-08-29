# -*- coding: utf-8 -*-
"""
螺栓拧紧数据预处理与特征工程脚本

处理流程（对应「工业大数据预处理与特征工程」技术方向）：
  1. 数据清洗    —— 去除空行程段、3σ 异常值剔除 + 线性插值、缺失值处理
  2. 特征提取    —— 从力矩-转角时序提取 12 维时域特征
  3. 特征选择    —— Pearson 相关 + 共线性分析，降维至 10 维核心特征
  4. 特征标准化  —— Z-score（仅基于训练集统计量，避免数据泄露）
  5. 数据集划分  —— 7:2:1 分层随机抽样（按质量标签）

输入：data/raw/{benchmark,extended}/records.jsonl
输出：
  data/processed/train.csv / val.csv / test.csv   —— 标准化后特征集
  data/processed/feature_metadata.json            —— 特征元信息

用法：
    python data/preprocess.py
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
RAW_DIR = BASE_DIR / "raw"
PROCESSED_DIR = BASE_DIR / "processed"

# 各规格名义最终拧紧角度（用于计算「转角偏差量」特征）
NOMINAL_ANGLE = {"M12": 95.0, "M16": 135.0, "M20": 175.0, "M24": 220.0}

# 12 维时域特征定义
FEATURE_NAMES = [
    "torque_max",        # 力矩最大值 (N·m)
    "torque_mean",       # 力矩平均值 (N·m)
    "torque_std",        # 力矩标准差 (N·m)
    "torque_peak_angle", # 力矩峰值出现角度 (deg)
    "snug_torque",       # 贴合点扭矩 (N·m)
    "total_angle",       # 拧紧总转角 (deg)
    "avg_rate",          # 拧紧平均速率 (N·m/deg)
    "rising_slope",      # 力矩上升斜率 (N·m/deg)
    "torque_fluctuation",# 力矩波动率 (无量纲)
    "angle_deviation",   # 转角偏差量 (deg)
    "final_torque",      # 最终扭矩值 (N·m)
    "hold_fluctuation",  # 扭矩保持段波动率 (N·m)
]


def load_raw() -> pd.DataFrame:
    """加载原始数据（基准集 + 扩展集合并）。"""
    frames = []
    for sub in ("benchmark", "extended"):
        path = RAW_DIR / sub / "records.jsonl"
        with open(path, encoding="utf-8") as f:
            recs = [json.loads(line) for line in f if line.strip()]
        df = pd.DataFrame(recs)
        df["source"] = sub
        frames.append(df)
    return pd.concat(frames, ignore_index=True)


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
            valid = ~outliers
            # 仅当两端存在有效点时进行插值，否则保留原值
            torque_clean = torque.copy()
            for i in idx:
                if 0 < i < len(torque) - 1:
                    torque_clean[i] = (torque[i - 1] + torque[i + 1]) / 2.0
            torque = torque_clean

    return angle, torque


def extract_features(angle: np.ndarray, torque: np.ndarray, spec: str) -> dict:
    """提取 12 维时域特征。"""
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


def select_features(feat_df: pd.DataFrame, y: pd.Series, threshold_corr: float = 0.1,
                    threshold_collinear: float = 0.97) -> tuple[list[str], dict]:
    """特征选择：剔除弱相关特征，合并共线性特征（连通分量聚类，保留每组代表）。"""
    corr_with_label = {f: float(np.corrcoef(feat_df[f], y)[0, 1]) for f in FEATURE_NAMES}
    abs_corr = {f: abs(c) for f, c in corr_with_label.items()}

    # 弱相关剔除
    kept = [f for f in FEATURE_NAMES if abs_corr[f] >= threshold_corr]
    dropped_weak = [f for f in FEATURE_NAMES if abs_corr[f] < threshold_corr]

    # 共线性合并：|corr| 高于阈值的特征对构成连通分量，每组保留与标签相关性最强的一个
    parent = {f: f for f in kept}

    def find(x: str) -> str:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a: str, b: str) -> None:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[rb] = ra

    collinear_pairs = []
    for i in range(len(kept)):
        for j in range(i + 1, len(kept)):
            f_i, f_j = kept[i], kept[j]
            c = float(np.corrcoef(feat_df[f_i], feat_df[f_j])[0, 1])
            if abs(c) > threshold_collinear:
                collinear_pairs.append((f_i, f_j, round(c, 3)))
                union(f_i, f_j)

    clusters: dict[str, list[str]] = {}
    for f in kept:
        clusters.setdefault(find(f), []).append(f)

    selected, dropped_collinear = [], []
    for members in clusters.values():
        best = max(members, key=lambda f: abs_corr[f])
        selected.append(best)
        for m in members:
            if m != best:
                dropped_collinear.append({"kept": best, "dropped": m,
                                          "corr": next(c for a, b, c in collinear_pairs
                                                        if {a, b} == {best, m})})
    selected.sort()

    meta = {
        "pearson_with_label": {f: round(v, 4) for f, v in corr_with_label.items()},
        "dropped_weak": dropped_weak,
        "dropped_collinear": dropped_collinear,
        "selected_features": selected,
    }
    return selected, meta


def main() -> None:
    raw = load_raw()
    print(f"[OK] 加载原始数据 {len(raw)} 条")

    # 1) 清洗 + 2) 特征提取
    feature_rows = []
    for _, row in raw.iterrows():
        angle, torque = clean_curve(row["angle"], row["torque"])
        if len(torque) < 3:
            continue
        feats = extract_features(angle, torque, row["spec"])
        feats.update({"id": row["id"], "spec": row["spec"], "source": row["source"],
                      "label": row["label"], "label_name": row["label_name"]})
        feature_rows.append(feats)

    feat_df = pd.DataFrame(feature_rows)
    print(f"[OK] 特征提取完成，有效样本 {len(feat_df)} 条")

    # 3) 特征选择
    selected, meta = select_features(feat_df, feat_df["label"])
    print(f"[OK] 特征选择：{len(FEATURE_NAMES)} -> {len(selected)} 维")
    print(f"      剔除弱相关: {meta['dropped_weak']}")
    print(f"      合并共线性: {meta['dropped_collinear']}")

    # 4) 数据集划分（7:2:1 分层）
    from sklearn.model_selection import train_test_split
    train, temp = train_test_split(feat_df, test_size=0.3, stratify=feat_df["label"],
                                   random_state=42)
    val, test = train_test_split(temp, test_size=1 / 3, stratify=temp["label"],
                                 random_state=42)

    # 5) 特征标准化：仅基于训练集统计量
    mean = train[selected].mean()
    std = train[selected].std().replace(0, 1e-9)

    def standardize(df: pd.DataFrame) -> pd.DataFrame:
        out = df.copy()
        out[selected] = (out[selected] - mean) / std
        return out

    train_s, val_s, test_s = standardize(train), standardize(val), standardize(test)

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    cols = ["id", "spec", "source", "label", "label_name"] + selected
    train_s[cols].to_csv(PROCESSED_DIR / "train.csv", index=False, encoding="utf-8-sig")
    val_s[cols].to_csv(PROCESSED_DIR / "val.csv", index=False, encoding="utf-8-sig")
    test_s[cols].to_csv(PROCESSED_DIR / "test.csv", index=False, encoding="utf-8-sig")

    meta["n_samples"] = {"train": int(len(train)), "val": int(len(val)),
                         "test": int(len(test))}
    meta["standardization"] = {"mean": mean.round(6).to_dict(), "std": std.round(6).to_dict()}
    with open(PROCESSED_DIR / "feature_metadata.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    print(f"[OK] 数据集划分 -> train {len(train)} / val {len(val)} / test {len(test)}")
    print(f"[OK] 输出目录 {PROCESSED_DIR}")


if __name__ == "__main__":
    main()
