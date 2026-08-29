# -*- coding: utf-8 -*-
"""
螺栓拧紧力矩-转角时序数据生成脚本（自建模拟数据集）

生成两类数据：
  1. benchmark/ 标准工况基准集（1200 条）—— 5 类质量状态的标准拧紧曲线
  2. extended/  扩展工况集（1800 条）—— 不同螺栓等级、工具磨损、环境温度下的工况扩展

质量标签编码：
  0 = 合格, 1 = 欠拧, 2 = 过拧, 3 = 滑牙, 4 = 虚拧

物理模型说明：
  拧紧过程力矩-转角曲线分为空行程（run-down）、贴合（seating）、弹性段（elastic）、
  保持段（hold）四个阶段。不同质量状态对应不同的终态行为：
    - 合格：力矩升至目标扭矩后保持
    - 欠拧：力矩提前停止，终值明显低于目标扭矩
    - 过拧：力矩越过目标扭矩后停止，终值明显高于目标扭矩
    - 滑牙：力矩升至峰值后急剧跌落（螺纹滑丝）
    - 虚拧：力矩始终维持低位（错扣/未正确啮合）

用法：
    python data/generate_data.py
"""
from __future__ import annotations

import json
import os
from pathlib import Path

import numpy as np
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
RAW_DIR = BASE_DIR / "raw"

# 采样参数
DT = 0.01          # 采样间隔 0.01s（100 Hz）
SPEED_RANGE = (110.0, 190.0)   # 电动扭矩扳手转速 deg/s

# 螺栓规格基础参数（8.8 级通用紧固参考值，扭矩单位 N·m，角度单位 deg）
# stiffness 为弹性段斜率（N·m/deg）
BOLT_SPECS = {
    "M12": {"target_torque": 80.0, "stiffness": 1.70, "snug_angle": 35.0},
    "M16": {"target_torque": 180.0, "stiffness": 2.20, "snug_angle": 40.0},
    "M20": {"target_torque": 320.0, "stiffness": 2.80, "snug_angle": 45.0},
    "M24": {"target_torque": 520.0, "stiffness": 3.40, "snug_angle": 50.0},
}

# 扩展工况：螺栓性能等级、工具磨损状态、环境温度
GRADES = ["8.8", "10.9", "12.9"]     # 性能等级
WEARS = [0, 1, 2]                    # 0=新 1=中度磨损 2=重度磨损
TEMPS = [-10, 20, 50]                # 环境温度 ℃

LABELS = {0: "合格", 1: "欠拧", 2: "过拧", 3: "滑牙", 4: "虚拧"}


def simulate_tightening(
    spec: str,
    class_id: int,
    grade: str,
    wear: int,
    temp: float,
    rng: np.random.Generator,
) -> dict:
    """生成单条拧紧力矩-转角时序，返回 {angle, torque, ...}。"""
    p = BOLT_SPECS[spec]
    target = p["target_torque"]
    snug_angle = p["snug_angle"]

    # 等级、磨损、温度对物理参数的扰动
    grade_factor = 1.0 + (int(grade.split(".")[0]) - 8.8) * 0.03  # 等级越高刚度/强度略高
    wear_noise = 1.0 + wear * 0.5                                  # 磨损加大噪声
    temp_factor = 1.0 + (temp - 20) * 0.002                        # 温度对摩擦的微弱影响
    k = p["stiffness"] * grade_factor * temp_factor * rng.uniform(0.94, 1.06)
    snug_torque = (3.0 + rng.uniform(-0.5, 2.5)) * temp_factor

    speed = rng.uniform(*SPEED_RANGE) * rng.uniform(0.96, 1.04)

    # 依据质量状态确定各阶段角度
    if class_id == 0:  # 合格：升至目标扭矩并保持
        elastic_end = snug_angle + (target - snug_torque) / k
        hold_angle = rng.uniform(10.0, 20.0)
        final_angle = elastic_end + hold_angle
    elif class_id == 1:  # 欠拧：提前停止，终值约为目标 60%～82%
        ratio = rng.uniform(0.60, 0.82)
        elastic_end = snug_angle + (target * ratio - snug_torque) / k
        final_angle = elastic_end + rng.uniform(0.0, 8.0)
    elif class_id == 2:  # 过拧：越过目标，终值约为目标 115%～135%
        ratio = rng.uniform(1.15, 1.35)
        elastic_end = snug_angle + (target * ratio - snug_torque) / k
        final_angle = elastic_end + rng.uniform(5.0, 15.0)
    elif class_id == 3:  # 滑牙：升至峰值后跌落
        peak_ratio = rng.uniform(0.75, 0.95)
        peak_angle = snug_angle + (target * peak_ratio - snug_torque) / k
        final_angle = peak_angle + rng.uniform(8.0, 15.0)
    else:  # 虚拧：力矩始终低位，大量空转
        final_angle = snug_angle + rng.uniform(60.0, 100.0)

    # 生成角度序列
    n = max(int(final_angle / (speed * DT)) + 1, 20)
    angle = np.arange(n) * speed * DT
    angle[-1] = final_angle  # 精确对齐终止角度

    # 生成力矩序列
    torque = np.zeros(n)
    # 传感器噪声采用「读数相关」模型：约 1.5% 读数 + 0.05 N·m 底噪，
    # 避免绝对噪声淹没低扭矩工况（如虚拧）的真实信号

    for i, a in enumerate(angle):
        if class_id == 3:  # 滑牙：上升段 + 峰值后跌落
            if a <= peak_angle:
                if a <= snug_angle:
                    tau = snug_torque * (0.25 + 0.75 * a / snug_angle)
                else:
                    tau = snug_torque + k * (a - snug_angle)
            else:
                peak_torque = snug_torque + k * (peak_angle - snug_angle)
                drop_k = k * rng.uniform(4.0, 7.0)  # 跌落斜率更陡
                tau = max(peak_torque - drop_k * (a - peak_angle), 0.30 * peak_torque)
        elif class_id == 4:  # 虚拧：全程低位，未正确啮合
            tau = snug_torque * (0.30 + 0.15 * np.sin(a / 6.0)) + rng.uniform(0, 1.0)
        else:  # 合格/欠拧/过拧：空行程 + 弹性上升 + 保持
            if a <= snug_angle:
                tau = snug_torque * (0.25 + 0.75 * a / snug_angle)  # 空行程摩擦
            elif a <= elastic_end:
                tau = snug_torque + k * (a - snug_angle)             # 弹性段
            else:
                tau = snug_torque + k * (elastic_end - snug_angle)   # 保持段（稳定）
        torque[i] = tau

    torque += rng.normal(0.0, 0.015 * np.abs(torque) * wear_noise + 0.05, size=n)  # 叠加传感器噪声

    return {
        "angle": np.round(angle, 3).tolist(),
        "torque": np.round(torque, 3).tolist(),
        "speed": round(speed, 2),
    }


def build_dataset(n_per_class: dict, extended: bool, rng: np.random.Generator) -> list[dict]:
    """按类别数量生成数据集，返回记录列表。"""
    records: list[dict] = []
    spec_list = list(BOLT_SPECS.keys())
    seq = 0
    for class_id, count in n_per_class.items():
        for _ in range(count):
            spec = spec_list[seq % len(spec_list)]
            if extended:
                grade = GRADES[seq % len(GRADES)]
                wear = WEARS[seq % len(WEARS)]
                temp = TEMPS[seq % len(TEMPS)]
            else:
                grade = "8.8"
                wear = 0
                temp = 20.0
            seq += 1

            curve = simulate_tightening(spec, class_id, grade, wear, temp, rng)
            prefix = "E" if extended else "B"
            rec_id = f"{prefix}{seq:04d}"
            records.append({
                "id": rec_id,
                "spec": spec,
                "grade": grade,
                "wear": wear,
                "temp": temp,
                "target_torque": BOLT_SPECS[spec]["target_torque"],
                "speed": curve["speed"],
                "label": class_id,
                "label_name": LABELS[class_id],
                "angle": curve["angle"],
                "torque": curve["torque"],
            })
    return records


def write_records(records: list[dict], out_jsonl: Path, out_meta: Path) -> None:
    """写出 JSONL 时序文件与 metadata.csv 汇总文件。"""
    out_jsonl.parent.mkdir(parents=True, exist_ok=True)
    with open(out_jsonl, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    meta_rows = [
        {
            "id": r["id"], "spec": r["spec"], "grade": r["grade"],
            "wear": r["wear"], "temp": r["temp"],
            "target_torque": r["target_torque"], "speed": r["speed"],
            "label": r["label"], "label_name": r["label_name"],
            "length": len(r["angle"]),
        }
        for r in records
    ]
    pd.DataFrame(meta_rows).to_csv(out_meta, index=False, encoding="utf-8-sig")


def main() -> None:
    rng = np.random.default_rng(42)

    # 基准集：合格 700 + 缺陷 500（4 类各 125）
    benchmark = build_dataset(
        {0: 700, 1: 125, 2: 125, 3: 125, 4: 125},
        extended=False, rng=rng,
    )
    # 扩展集：扩充稀有缺陷样本
    extended = build_dataset(
        {0: 600, 1: 300, 2: 300, 3: 300, 4: 300},
        extended=True, rng=rng,
    )

    write_records(benchmark, RAW_DIR / "benchmark" / "records.jsonl",
                  RAW_DIR / "benchmark" / "metadata.csv")
    write_records(extended, RAW_DIR / "extended" / "records.jsonl",
                  RAW_DIR / "extended" / "metadata.csv")

    print(f"[OK] 基准集 {len(benchmark)} 条 -> {RAW_DIR / 'benchmark'}")
    print(f"[OK] 扩展集 {len(extended)} 条 -> {RAW_DIR / 'extended'}")
    print(f"[OK] 合计 {len(benchmark) + len(extended)} 条")


if __name__ == "__main__":
    main()
