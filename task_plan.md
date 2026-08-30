# 任务规划：核心算法与后端开发阶段

## 阶段目标

完成「重型机械装配车间螺栓拧紧质量智能检测与工艺追溯系统」的**核心算法与后端开发**，对应方案设计 3.6 节的三大算法模块与 3.5 节的后端服务，实现质量检测、工艺追溯、参数优化三大能力的离线验证与接口化封装。

## 任务拆解

| # | 任务 | 产出物 | 状态 |
|---|------|--------|------|
| 1 | 抽取特征工程模块 | `algorithms/feature_engineering.py` | ✅ 完成 |
| 2 | 重构 preprocess.py 复用 | `data/preprocess.py`（import 复用，无回归） | ✅ 完成 |
| 3 | 质量检测模块 | `algorithms/quality_detection.py` | ✅ 完成 |
| 4 | 训练模型 + 产物 | `algorithms/models/quality_pipeline.joblib` + `model_report.json` | ✅ 完成 |
| 5 | 业务追溯上下文数据 | `data/build_business_context.py` + `tightening_context.csv` | ✅ 完成 |
| 6 | 工艺追溯与参数优化模块 | `algorithms/process_optimization.py` + `optimization_report.json` | ✅ 完成 |
| 7 | FastAPI 后端 | `backend/`（config/state/schemas/services/routers/main） | ✅ 完成 |
| 8 | 单元测试 | `tests/`（21 用例） | ✅ 完成 |
| 9 | 测试与冒烟验证 | 21 tests OK + uvicorn 4 接口 200 | ✅ 完成 |
| 10 | 文档与规划更新 | README / data README / prompt 追溯 | ✅ 完成 |

## 关键决策

- **模型选型**：随机森林为主模型（鲁棒、可解释、免调参友好），SVM/GBDT 作对比基线；因 xgboost 未安装，用 sklearn GradientBoosting 替代，效果已满足要求（测试集 99.67%）。
- **后端数据层**：采用 CSV 文件仓库（零外部数据库依赖，开箱即跑 Demo），生产可无缝替换 MySQL（表结构见 `data/business/init.sql`）。
- **特征工程复用**：`clean_curve`/`extract_features` 收敛到 `algorithms/feature_engineering.py` 唯一实现，预处理与推理共用，避免逻辑漂移。
- **测试栈**：stdlib `unittest`（pytest 未装），API 集成测试用 FastAPI TestClient（httpx 已装）。

## 下一阶段

- 前端开发与系统联调：Vue3 + Element Plus + ECharts 实现五大页面，对接后端 8 接口，完成全流程联调测试。
