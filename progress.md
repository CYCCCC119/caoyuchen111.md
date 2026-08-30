# 进度记录

## 2026-08-28 数据准备阶段（已完成）

- [x] 分析项目现状：读取 README.md、选题说明.md、方案设计.md、数据资源整理说明.md、学习笔记.md
- [x] 确认运行环境（Python 3.9.13 + numpy/pandas/sklearn）
- [x] 数据来源调研（网络检索公开螺栓拧紧数据集）
- [x] 数据生成脚本 `data/generate_data.py`（力学模型模拟 5 类质量状态，3000 条）
- [x] 预处理与特征工程脚本 `data/preprocess.py`（清洗→12维特征→8维选择→标准化→7:2:1划分）
- [x] 生成原始数据 `data/raw/`（benchmark 1200 + extended 1800）
- [x] 生成预处理特征数据 `data/processed/`（train/val/test + feature_metadata.json）
- [x] 业务数据初始化脚本 `data/business/init.sql`（6 表 + 基础数据）
- [x] 数据说明文档 `data/README.md`
- [x] 更新项目 `README.md`
- [x] AI 提示词追溯 `prompt/`（README 规范 + 本阶段 JSON 记录）
- [x] 更正 `数据资源整理说明.md` 中「公开 5 类基准数据集」的不实描述与无效链接

## 验证结果

- 随机森林验证：验证集 / 测试集准确率均为 100%，数据生成、标注、特征提取链路正确。
- 特征选择 12 → 8 维（剔除 1 弱相关 + 合并 3 共线性），保留特征见 feature_metadata.json。

## 2026-08-29 上传 GitHub 与压缩前备份

- [x] 上传到 GitHub 仓库 `CYCCCC119/caoyuchen111.md`（公开），提交 `40767e0`，21 个文件
- [x] 解决推送认证：本机 git 凭据原绑 `2670242589zero-star`，改用 PAT 绑定 `CYCCCC119` 后推送成功
- [x] 上下文压缩前补记 prompt 记录（第 9-13 条），并同步提交备份

## 2026-08-30 核心算法与后端开发阶段（已完成）

- [x] 抽取特征工程模块 `algorithms/feature_engineering.py` 并重构 `preprocess.py` 复用（重跑无回归）
- [x] 质量检测模块 `algorithms/quality_detection.py`（RF 网格搜索 + SVM/GBDT 对比）
- [x] 训练模型产物 `algorithms/models/quality_pipeline.joblib` + `model_report.json`
- [x] 业务追溯上下文 `data/build_business_context.py` → `data/business/tightening_context.csv`（3000 条）
- [x] 工艺追溯与参数优化模块 `algorithms/process_optimization.py` + `optimization_report.json`
- [x] FastAPI 后端 `backend/`（8 个 RESTful 接口，CSV 仓库零 DB 依赖）
- [x] 单元测试 `tests/`（21 用例，unittest）
- [x] 更新 README / data README，标记开发计划第三阶段完成

## 验证结果

- 随机森林：交叉验证宏F1 0.9977，测试集准确率 99.67% / 宏F1 0.9968（优于 SVM 96.67%、GBDT 99.33%）
- 参数-特征关联物理意义正确：target_torque↔final_torque 0.70、wear↔angle_deviation -0.26
- 21 个单元测试全部通过；uvicorn 冒烟测试 4 接口均 200 OK
- 修复两个 bug：grade 列 float 导致 grade_ordinal 全 NaN；测试方法 cls/self 误用

## 2026-08-30 前端开发与系统联调阶段（已完成）

- [x] 前端工程骨架 `frontend/`（Vite + Vue3 + Element Plus + ECharts + Axios，标准 npm 工程）
- [x] 五大页面：监控大屏 Dashboard / 质量检测分析 Detection / 工艺追溯查询 Traceability / 参数优化 Optimization / 基础数据管理 DataManage
- [x] 通用图表组件 ChartBox（ECharts 生命周期封装）、axios 接口封装、共享常量
- [x] 提取真实样本曲线 `sampleCurves.js`（自 records.jsonl，每类一条，供示例检测）
- [x] `npm run build` 通过；前后端联调验证（Vite /api 代理 → FastAPI 8000，8 接口全部连通）
- [x] 更新 README.md / frontend/README.md，标记开发计划第四阶段完成

## 验证结果

- `npm run build` 成功（2240 模块，14s）；chunk 偏大为 ECharts/Element Plus 正常体积，不影响运行
- 联调验证：经 Vite 代理访问后端 /api/stats、/api/correlation、/api/optimize、/api/detect、/api/detect/batch、/api/trace 均返回正确数据
- 批量检测 5 类样本：模型正确判定 合格/欠拧/过拧/滑牙/虚拧 五类
- 修复前端两处：`v-model="!!detail"` 非法表达式（改用独立 detailVisible）；检测接口 probabilities 键为中文类别名（前端改按名称映射）；曲线绘图改读输入曲线（后端仅返回特征不返回原始序列）

## 下一阶段

- 文档撰写与答辩准备（设计报告、演示视频、答辩 PPT）。

## 备注

- 发现并修复两个实现 bug：噪声模型淹没低扭矩信号、hold_fluctuation 恒为 0。
- PDF 任务书加密无法读取，不影响本阶段（其余文档信息充分）。
- 后续推送：凭据已绑定 CYCCCC119，直接 `git push origin main` 即可。
