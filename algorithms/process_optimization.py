# -*- coding: utf-8 -*-
"""
模块三：工艺追溯与参数优化（制造工艺追溯与参数优化）

两大能力：
  1. 工艺全链路追溯 —— 支持按螺栓规格 / 工位 / 人员 / 批次 / 时间 / 质量结果多条件组合检索，
     定位质量问题影响范围（正向追踪 + 反向定位）。
  2. 工艺参数优化 —— 基于历史数据的关联分析（Pearson 相关）挖掘参数对质量的影响规律，
     通过多目标网格搜索输出最优拧紧参数组合（合格率优先 + 效率 + 工具寿命）。

数据来源：data/business/tightening_context.csv（业务上下文）+ data/processed/*（特征集）。

用法：
    python algorithms/process_optimization.py   # 输出追溯示例与优化报告
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BASE_DIR.parent
CONTEXT_PATH = PROJECT_DIR / "data" / "business" / "tightening_context.csv"
PROCESSED_DIR = PROJECT_DIR / "data" / "processed"

# 参与关联分析的工艺参数（数值化）
PARAM_COLS = ["target_torque", "speed", "wear", "temp", "grade_ordinal"]
# 关键质量特征（来自特征集，反映质量状态的物理量）
QUALITY_FEATURE_COLS = ["final_torque", "hold_fluctuation", "angle_deviation",
                        "total_angle", "avg_rate", "rising_slope"]


def load_context(path: str | Path | None = None) -> pd.DataFrame:
    """加载业务追溯上下文（工艺参数 + 质量标签 + 业务实体）。"""
    p = Path(path) if path else CONTEXT_PATH
    df = pd.read_csv(p)
    df["record_time"] = pd.to_datetime(df["record_time"])
    df["is_defective"] = (df["label"] != 0).astype(int)
    # 性能等级可能被 pandas 读为 float（8.8/10.9/12.9），统一归一化为字符串后再映射
    df["grade"] = df["grade"].astype(str).str.strip()
    df["grade_ordinal"] = df["grade"].map({"8.8": 0, "10.9": 1, "12.9": 2})
    return df


def load_features() -> pd.DataFrame:
    """加载预处理特征集（train/val/test 合并），用于参数-质量特征关联分析。"""
    frames = [pd.read_csv(PROCESSED_DIR / f"{split}.csv")
              for split in ("train", "val", "test")]
    return pd.concat(frames, ignore_index=True)


def merge_context_features(context: pd.DataFrame) -> pd.DataFrame:
    """将业务上下文与质量特征按记录 ID 合并，供关联分析使用。"""
    feat = load_features()
    merged = context.merge(feat[["id"] + QUALITY_FEATURE_COLS + ["label"]],
                           on="id", how="left", suffixes=("", "_feat"))
    return merged


class ProcessAnalyzer:
    """工艺追溯与参数优化分析器。"""

    def __init__(self, context_path: str | Path | None = None):
        self.df = load_context(context_path)
        self.merged = merge_context_features(self.df)

    # ---------------- 追溯 ----------------
    def trace(self, spec: str | None = None, workstation_id: str | None = None,
              operator: str | None = None, batch_id: str | None = None,
              start_time: str | None = None, end_time: str | None = None,
              label: int | None = None) -> pd.DataFrame:
        """多条件组合追溯，返回满足条件的拧紧记录。"""
        df = self.df
        if spec:
            df = df[df["spec"] == spec]
        if workstation_id:
            df = df[df["workstation_id"] == workstation_id]
        if operator:
            df = df[df["operator"] == operator]
        if batch_id:
            df = df[df["batch_id"] == batch_id]
        if start_time:
            df = df[df["record_time"] >= pd.to_datetime(start_time)]
        if end_time:
            df = df[df["record_time"] <= pd.to_datetime(end_time)]
        if label is not None:
            df = df[df["label"] == label]
        return df.reset_index(drop=True)

    def summary(self, records: pd.DataFrame) -> dict:
        """对追溯结果做质量汇总统计。"""
        if records.empty:
            return {"n": 0, "pass_rate": None, "label_dist": {}}
        n = len(records)
        pass_rate = float((records["label"] == 0).mean())
        dist = records["label_name"].value_counts().to_dict()
        return {"n": int(n), "pass_rate": round(pass_rate, 4), "label_dist": dist}

    # ---------------- 关联分析 ----------------
    def param_correlation(self) -> dict:
        """工艺参数与质量结果的 Pearson 相关分析。"""
        defect_classes = {1: "欠拧", 2: "过拧", 3: "滑牙", 4: "虚拧"}
        corr_rows = []
        for param in PARAM_COLS:
            row = {"param": param,
                   "with_defect_rate": round(float(
                       self.merged[param].corr(self.merged["is_defective"])), 4)}
            for lb, name in defect_classes.items():
                ind = (self.merged["label"] == lb).astype(int)
                row[f"with_{name}"] = round(float(self.merged[param].corr(ind)), 4)
            corr_rows.append(row)

        # 参数与关键质量特征的相关系数（更具物理意义）
        param_feature = []
        for param in PARAM_COLS:
            for feat in QUALITY_FEATURE_COLS:
                c = self.merged[param].corr(self.merged[feat])
                if not np.isnan(c):
                    param_feature.append({"param": param, "feature": feat,
                                          "corr": round(float(c), 4)})
        return {"param_vs_defect": corr_rows, "param_vs_feature": param_feature}

    # ---------------- 参数优化 ----------------
    def optimize(self, spec: str, speed_bins: int = 3) -> dict:
        """多目标网格搜索：合格率优先 + 效率(转速) + 工具寿命(磨损)，输出最优参数组合。"""
        sub = self.df[self.df["spec"] == spec].copy()
        if sub.empty:
            return {"spec": spec, "error": "无该规格历史数据"}

        # 转速分箱（连续值离散化）
        q = pd.qcut(sub["speed"], speed_bins, labels=[0, 1, 2], duplicates="drop")
        sub["speed_bin"] = q.astype(int)

        # 网格聚合
        grouped = sub.groupby(["wear", "temp", "grade", "speed_bin"]).agg(
            n=("label", "size"),
            pass_rate=("label", lambda x: float((x == 0).mean())),
            mean_speed=("speed", "mean"),
        ).reset_index()

        # 多目标评分：合格率 60% + 效率 30% + 工具寿命(低磨损) 10%
        speed_max = grouped["mean_speed"].max() or 1.0
        grouped["score"] = (
            grouped["pass_rate"] * 0.60
            + (grouped["mean_speed"] / speed_max) * 0.30
            + (1 - grouped["wear"] / 2.0) * 0.10
        )
        grouped = grouped.sort_values(["score", "pass_rate"], ascending=False)

        top = grouped.head(5)
        best = top.iloc[0]
        pareto = self._pareto_frontier(grouped)

        return {
            "spec": spec,
            "n_samples": int(len(sub)),
            "recommended": {
                "wear": int(best["wear"]),
                "temp": float(best["temp"]),
                "grade": str(best["grade"]),
                "speed_range": self._speed_bin_range(sub, int(best["speed_bin"])),
                "pass_rate": round(float(best["pass_rate"]), 4),
                "mean_speed": round(float(best["mean_speed"]), 2),
                "score": round(float(best["score"]), 4),
            },
            "top_configs": [
                {"wear": int(r["wear"]), "temp": float(r["temp"]), "grade": str(r["grade"]),
                 "speed_range": self._speed_bin_range(sub, int(r["speed_bin"])),
                 "pass_rate": round(float(r["pass_rate"]), 4),
                 "mean_speed": round(float(r["mean_speed"]), 2),
                 "score": round(float(r["score"]), 4)}
                for _, r in top.iterrows()
            ],
            "pareto_frontier": pareto,
        }

    @staticmethod
    def _speed_bin_range(sub: pd.DataFrame, bin_id: int) -> str:
        rng = sub[sub["speed_bin"] == bin_id]["speed"]
        if rng.empty:
            return "N/A"
        return f"{rng.min():.0f}~{rng.max():.0f} deg/s"

    @staticmethod
    def _pareto_frontier(grouped: pd.DataFrame) -> list[dict]:
        """计算 (合格率, 平均转速) 的 Pareto 前沿（剔除被支配的配置）。"""
        pts = grouped[["pass_rate", "mean_speed", "wear"]].drop_duplicates().values
        frontier = []
        for pr, sp, wear in pts:
            dominated = any(o[0] >= pr and o[1] >= sp and (o[0] > pr or o[1] > sp)
                            for o in pts)
            if not dominated:
                frontier.append({"pass_rate": round(float(pr), 4),
                                 "mean_speed": round(float(sp), 2),
                                 "wear": int(wear)})
        frontier.sort(key=lambda x: (x["pass_rate"], x["mean_speed"]))
        return frontier


def main() -> None:
    analyzer = ProcessAnalyzer()

    # 追溯示例：追溯某工位欠拧记录
    trace_result = analyzer.trace(workstation_id="WS-001", label=1)
    print(f"[追溯] 工位 WS-001 欠拧记录 {len(trace_result)} 条，"
          f"合格率 {analyzer.summary(analyzer.trace(workstation_id='WS-001'))['pass_rate']}")

    # 关联分析
    corr = analyzer.param_correlation()
    print(f"[关联] 参数-缺陷相关系数: {corr['param_vs_defect']}")

    # 参数优化（以 M20 为例）
    opt = analyzer.optimize("M20")
    print(f"[优化] M20 推荐参数: {opt['recommended']}")

    # 输出报告
    report = {
        "param_vs_defect": corr["param_vs_defect"],
        "param_vs_feature_top": sorted(corr["param_vs_feature"],
                                       key=lambda x: abs(x["corr"]), reverse=True)[:10],
        "optimization": {spec: analyzer.optimize(spec)["recommended"]
                         for spec in ["M12", "M16", "M20", "M24"]},
    }
    out = BASE_DIR / "models" / "optimization_report.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"[OK] 优化报告已保存 -> {out}")


if __name__ == "__main__":
    main()
