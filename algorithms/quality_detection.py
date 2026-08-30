# -*- coding: utf-8 -*-
"""
模块二：拧紧质量智能检测（制造过程质量智能检测与控制）

基于时序特征向量构建 5 类质量分类模型：
  - 主模型：随机森林（GridSearchCV 网格搜索调优）
  - 对比模型：SVM（RBF 核）、梯度提升树 GBDT
  - 评估指标：准确率、宏平均 F1、各类别 P/R/F1、混淆矩阵

产物（保存于 algorithms/models/）：
  - quality_pipeline.joblib  完整推理管线（模型 + 特征选择 + 标准化参数）
  - model_report.json        训练评估报告

用法：
  python algorithms/quality_detection.py   # 训练 + 评估 + 保存
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

# 使 `algorithms` 包在直接脚本运行时也可导入（项目根目录加入 sys.path）
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_recall_fscore_support,
)
from sklearn.model_selection import GridSearchCV
from sklearn.svm import SVC

from algorithms.feature_engineering import LABEL_NAMES, load_pipeline_params

BASE_DIR = Path(__file__).resolve().parent
PROCESSED_DIR = BASE_DIR.parent / "data" / "processed"
MODELS_DIR = BASE_DIR / "models"

# 缺陷等级映射：0=无（合格） 1=轻微 2=一般 3=严重
DEFECT_LEVEL = {0: 0, 1: 1, 2: 1, 3: 3, 4: 2}

# 标签顺序（与模型输出一致）
LABELS = list(LABEL_NAMES.keys())          # [0, 1, 2, 3, 4]
LABEL_NAMES_CN = [LABEL_NAMES[k] for k in LABELS]


def load_data() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, list[str]]:
    """加载训练/验证/测试特征集，返回 (train, val, test, feature_cols)。"""
    train = pd.read_csv(PROCESSED_DIR / "train.csv")
    val = pd.read_csv(PROCESSED_DIR / "val.csv")
    test = pd.read_csv(PROCESSED_DIR / "test.csv")
    feature_cols = load_pipeline_params(PROCESSED_DIR / "feature_metadata.json")["selected_features"]
    return train, val, test, feature_cols


def evaluate(model, X: pd.DataFrame, y: pd.Series) -> dict:
    """计算模型在给定数据集上的多指标评估结果。"""
    pred = model.predict(X)
    acc = accuracy_score(y, pred)
    macro_f1 = f1_score(y, pred, labels=LABELS, average="macro", zero_division=0)
    p, r, f1, _ = precision_recall_fscore_support(y, pred, labels=LABELS, zero_division=0)
    cm = confusion_matrix(y, pred, labels=LABELS)
    return {
        "accuracy": round(float(acc), 4),
        "macro_f1": round(float(macro_f1), 4),
        "per_class": [
            {"label": int(lb), "name": LABEL_NAMES[lb],
             "precision": round(float(p[i]), 4),
             "recall": round(float(r[i]), 4),
             "f1": round(float(f1[i]), 4)}
            for i, lb in enumerate(LABELS)
        ],
        "confusion_matrix": cm.tolist(),
        "n_samples": int(len(y)),
    }


def train_random_forest(X_train: pd.DataFrame, y_train: pd.Series) -> RandomForestClassifier:
    """网格搜索调优随机森林。"""
    param_grid = {
        "n_estimators": [100, 200, 300],
        "max_depth": [None, 10, 20],
        "min_samples_split": [2, 5],
    }
    base = RandomForestClassifier(random_state=42, class_weight="balanced", n_jobs=-1)
    gs = GridSearchCV(base, param_grid, cv=5, scoring="f1_macro", n_jobs=-1, verbose=0)
    gs.fit(X_train, y_train)
    print(f"[OK] 随机森林最优参数: {gs.best_params_}")
    print(f"     最佳交叉验证宏F1: {gs.best_score_:.4f}")
    return gs.best_estimator_


def compare_models(X_train, y_train, X_test, y_test) -> list[dict]:
    """对比随机森林 / SVM / 梯度提升树在测试集上的表现。"""
    models = {
        "RandomForest": RandomForestClassifier(random_state=42, class_weight="balanced", n_jobs=-1),
        "SVM(RBF)": SVC(kernel="rbf", C=1.0, gamma="scale", probability=True, random_state=42),
        "GradientBoosting": GradientBoostingClassifier(random_state=42),
    }
    rows = []
    for name, model in models.items():
        model.fit(X_train, y_train)
        acc = accuracy_score(y_test, model.predict(X_test))
        macro_f1 = f1_score(y_test, model.predict(X_test), labels=LABELS, average="macro", zero_division=0)
        rows.append({"model": name, "test_accuracy": round(float(acc), 4),
                     "test_macro_f1": round(float(macro_f1), 4)})
    return rows


def build_pipeline(model, feature_cols: list[str], meta_path: Path) -> dict:
    """打包完整推理管线：模型 + 特征选择 + 标准化参数。"""
    params = load_pipeline_params(meta_path)
    return {
        "model": model,
        "feature_cols": feature_cols,
        "selected_features": params["selected_features"],
        "mean": params["mean"],
        "std": params["std"],
        "label_names": LABEL_NAMES,
        "defect_level": DEFECT_LEVEL,
    }


def main() -> None:
    train, val, test, feature_cols = load_data()
    print(f"[OK] 加载数据集 -> train {len(train)} / val {len(val)} / test {len(test)}，特征 {len(feature_cols)} 维")

    X_train, y_train = train[feature_cols], train["label"]
    X_val, y_val = val[feature_cols], val["label"]
    X_test, y_test = test[feature_cols], test["label"]

    # 1) 主模型：随机森林（网格搜索）
    rf = train_random_forest(X_train, y_train)

    # 2) 各数据集评估
    report = {
        "task": "螺栓拧紧质量 5 类检测",
        "feature_cols": feature_cols,
        "best_params": rf.get_params(),
        "train": evaluate(rf, X_train, y_train),
        "val": evaluate(rf, X_val, y_val),
        "test": evaluate(rf, X_test, y_test),
        "model_comparison": compare_models(X_train, y_train, X_test, y_test),
    }
    report["classification_report"] = classification_report(
        y_test, rf.predict(X_test), labels=LABELS, target_names=LABEL_NAMES_CN,
        zero_division=0,
    )

    print(f"[OK] 随机森林 - 训练集准确率 {report['train']['accuracy']} / "
          f"验证集 {report['val']['accuracy']} / 测试集 {report['test']['accuracy']}")
    print(f"     测试集宏平均 F1 = {report['test']['macro_f1']}")
    print(f"[OK] 模型对比: {report['model_comparison']}")

    # 3) 保存管线与报告
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    pipeline = build_pipeline(rf, feature_cols, PROCESSED_DIR / "feature_metadata.json")
    joblib.dump(pipeline, MODELS_DIR / "quality_pipeline.joblib")
    with open(MODELS_DIR / "model_report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"[OK] 管线已保存 -> {MODELS_DIR / 'quality_pipeline.joblib'}")
    print(f"[OK] 报告已保存 -> {MODELS_DIR / 'model_report.json'}")


class QualityDetector:
    """质量检测推理器：加载训练好的管线，对单条/批量拧紧曲线进行判定。"""

    def __init__(self, pipeline_path: str | Path | None = None):
        path = Path(pipeline_path) if pipeline_path else MODELS_DIR / "quality_pipeline.joblib"
        pipe = joblib.load(path)
        self.model = pipe["model"]
        self.mean = pipe["mean"]
        self.std = pipe["std"]
        self.label_names = pipe["label_names"]
        self.defect_level = pipe["defect_level"]
        self.params = {"selected_features": pipe["selected_features"],
                       "mean": pipe["mean"], "std": pipe["std"]}

    def predict(self, angle, torque, spec: str) -> dict:
        """单条曲线检测，返回类别、置信度、各类概率与特征向量。"""
        from algorithms.feature_engineering import build_feature_vector

        feat = build_feature_vector(angle, torque, spec, self.params)
        cols = self.params["selected_features"]
        X = pd.DataFrame([[feat[f] for f in cols]], columns=cols)
        proba = self.model.predict_proba(X)[0]
        label = int(np.argmax(proba))
        confidence = float(proba[label])
        return {
            "label": label,
            "label_name": self.label_names[label],
            "confidence": round(confidence, 4),
            "defect_level": self.defect_level[label],
            "probabilities": {self.label_names[i]: round(float(proba[i]), 4)
                              for i in range(len(proba))},
            "features": {k: round(float(v), 4) for k, v in feat.items()},
        }

    def predict_batch(self, curves: list[dict]) -> list[dict]:
        """批量检测，curves 元素为 {spec, angle, torque}。"""
        return [self.predict(c["angle"], c["torque"], c["spec"]) for c in curves]


if __name__ == "__main__":
    main()
