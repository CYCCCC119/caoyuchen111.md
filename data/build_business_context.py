# -*- coding: utf-8 -*-
"""
业务追溯上下文数据生成脚本

将原始拧紧记录（raw/*/metadata.csv）关联到车间业务实体（工位/设备/人员/批次/时间），
生成 `data/business/tightening_context.csv`，支撑工艺全链路追溯与参数优化分析。

关联规则（确定性，seed=42 可复现）：
  - 工位：按记录顺序轮询分配 WS-001~WS-004，操作人员取对应工位负责人
  - 批次：按螺栓规格 + 批次序号生成（同规格同批次聚合，便于追溯）
  - 时间：2026-08-01 起 3 天内随机分布（贴合生产时序）

用法：
    python data/build_business_context.py
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
RAW_DIR = BASE_DIR / "raw"
BUSINESS_DIR = BASE_DIR / "business"

# 与 init.sql 中的工位/人员保持一致
WORKSTATIONS = [
    {"workstation_id": "WS-001", "workstation_name": "一号装配工位",
     "device_no": "WS-001", "operator": "张伟", "workshop": "总装一车间"},
    {"workstation_id": "WS-002", "workstation_name": "二号装配工位",
     "device_no": "WS-002", "operator": "李强", "workshop": "总装一车间"},
    {"workstation_id": "WS-003", "workstation_name": "三号装配工位",
     "device_no": "WS-003", "operator": "王芳", "workshop": "总装二车间"},
    {"workstation_id": "WS-004", "workstation_name": "四号装配工位",
     "device_no": "WS-004", "operator": "刘洋", "workshop": "总装二车间"},
]


def main() -> None:
    frames = []
    for sub in ("benchmark", "extended"):
        meta = pd.read_csv(RAW_DIR / sub / "metadata.csv")
        meta["source"] = sub
        frames.append(meta)
    df = pd.concat(frames, ignore_index=True).sort_values("id").reset_index(drop=True)

    rng = np.random.default_rng(42)
    n = len(df)

    # 工位轮询分配
    ws = [WORKSTATIONS[i % len(WORKSTATIONS)] for i in range(n)]
    df["workstation_id"] = [w["workstation_id"] for w in ws]
    df["workstation_name"] = [w["workstation_name"] for w in ws]
    df["device_no"] = [w["device_no"] for w in ws]
    df["operator"] = [w["operator"] for w in ws]
    df["workshop"] = [w["workshop"] for w in ws]

    # 批次：同规格 + 批次序号
    df["batch_id"] = df["spec"] + "-" + (df.groupby("spec").cumcount() % 6 + 1).astype(str).str.zfill(2)

    # 时间：2026-08-01 08:00 起 3 天内随机分布
    start = pd.Timestamp("2026-08-01 08:00:00")
    offsets = rng.integers(0, 3 * 24 * 3600, size=n)
    df["record_time"] = [start + pd.Timedelta(seconds=int(s)) for s in offsets]
    df = df.sort_values("record_time").reset_index(drop=True)

    BUSINESS_DIR.mkdir(parents=True, exist_ok=True)
    cols = ["id", "spec", "grade", "wear", "temp", "target_torque", "speed",
            "label", "label_name", "source",
            "workstation_id", "workstation_name", "device_no", "operator", "workshop",
            "batch_id", "record_time"]
    df[cols].to_csv(BUSINESS_DIR / "tightening_context.csv", index=False, encoding="utf-8-sig")
    print(f"[OK] 生成业务追溯上下文 {n} 条 -> {BUSINESS_DIR / 'tightening_context.csv'}")
    print(f"     工位分布: {df['workstation_id'].value_counts().to_dict()}")


if __name__ == "__main__":
    main()
