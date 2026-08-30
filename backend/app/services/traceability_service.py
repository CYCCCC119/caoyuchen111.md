# -*- coding: utf-8 -*-
"""工艺追溯服务：多条件组合检索与全局质量统计。"""
from __future__ import annotations

from .. import state
from ..schemas import TraceQuery

# 追溯结果返回字段（含业务实体与质量结果）
RECORD_COLS = [
    "id", "spec", "grade", "wear", "temp", "target_torque", "speed",
    "label", "label_name",
    "workstation_id", "workstation_name", "device_no", "operator", "workshop",
    "batch_id", "record_time",
]


def trace(query: TraceQuery) -> dict:
    """多条件组合追溯，返回汇总统计 + 记录列表。"""
    an = state.analyzer()
    records = an.trace(
        spec=query.spec,
        workstation_id=query.workstation_id,
        operator=query.operator,
        batch_id=query.batch_id,
        start_time=query.start_time,
        end_time=query.end_time,
        label=query.label,
    )
    summary = an.summary(records)
    data = records[RECORD_COLS].head(query.limit).copy()
    data["record_time"] = data["record_time"].astype(str)
    return {"summary": summary, "total_matched": len(records),
            "records": data.to_dict(orient="records")}


def stats() -> dict:
    """全局质量统计：整体合格率、缺陷分布、工位合格率。"""
    df = state.analyzer().df
    total = int(len(df))
    pass_rate = float((df["label"] == 0).mean())
    label_dist = df["label_name"].value_counts().to_dict()
    pass_rate_by_ws = (
        df.groupby("workstation_id")["label"]
        .apply(lambda g: round(float((g == 0).mean()), 4)).to_dict()
    )
    return {
        "total": total,
        "pass_rate": round(pass_rate, 4),
        "label_dist": label_dist,
        "pass_rate_by_workstation": pass_rate_by_ws,
    }
