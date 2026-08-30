# 调研发现

## 环境

- Python 3.9.13
- numpy 1.26.4 / pandas 2.3.3 / scikit-learn 1.6.1 均可用

## 数据来源调研结果（2026-08-28 网络检索）

检索到与「螺栓/螺钉拧紧 力矩-转角 + 质量检测」相关的公开数据集：

1. **pyscrew Screw Driving Dataset**（GitHub，公开）：`https://github.com/nikolaiwest/pyscrew`
   - 约 12,500 个 JSON 文件，含 torque/angle/time/class 通道，标签为 OK/NOK 及多种异常工况（断丝、孔位偏移、表面摩擦变化等）。
   - 最接近「拧紧质量检测」场景的公开数据。
2. **AURSAD**（Universal Robot Screwdriving Anomaly Detection Dataset，Leporowski 等 2021，公开）。
3. **国家基础学科公共科学数据中心——螺栓紧固实验测试数据**：`https://nbsdc.cn/general/dataDetail?id=6988b31b195d2616afb01c17&type=1`（68.39MB，2007 个文件，偏实验测试与力矩-转角关系建模）。
4. **M2/M3 螺钉力矩-角度曲线数据集**（MDPI Data 2024，DOI: 10.3390/data9100115），关注滑牙/螺纹失效。
5. **dataset_unfastening**（GitHub，2022），方向为螺钉拆卸状态识别。

## 关键结论

- **不存在同时标注「合格、欠拧、过拧、滑牙、虚拧」5 类的单一公开数据集**。本项目拟定的 5 类质量分类方案属于自建设计，核心训练数据需基于拧紧力矩-转角力学模型**模拟生成**。
- 原 `数据资源整理说明.md` 中「国内高校公开 5 类基准数据集（1200 条）」的描述与事实不符，需在文档中更正为「自建模拟数据集 + 公开数据集参考」。
- 公开数据集可作为参考来源（给出有效链接），不直接作为本项目 5 类检测的训练数据。

## 环境补充（2026-08-30 后端开发前核查）

- 可用：fastapi 0.128.8 / uvicorn 0.39.0 / pydantic 2.13.4 / joblib 1.5.3 / python-multipart 0.0.20 / httpx 0.28.1。
- 未安装：xgboost、sqlalchemy、pymysql、influxdb、pytest。
- 决策：模型对比用 sklearn `GradientBoostingClassifier` 替代 xgboost；后端数据层采用 CSV 文件仓库（零外部数据库依赖，开箱即用），生产环境可替换为 MySQL（表结构见 `data/business/init.sql`）；测试用 stdlib `unittest` 替代 pytest。

## 前端开发补充（2026-08-30）

- Node v24.14.1 / npm 11.11.0 可用，采用标准 Vite + Vue3 工程（非 CDN 单文件）。
- 后端检测接口 `probabilities` 字段的键为**中文类别名**（合格/欠拧/过拧/滑牙/虚拧），非数字索引，前端需按名称映射。
- 检测接口响应只含特征向量，不含原始 angle/torque 序列；力矩-转角曲线需在前端缓存输入曲线用于绘图。
- Vite dev server 默认绑定 IPv6 `::1`（`localhost`），`127.0.0.1` 直连为空；curl 需用 `localhost`。
- `v-model` 不能绑定 `!!detail` 这类非成员表达式，需用独立 ref 控制 dialog 显隐。
- 构建产物 chunk 偏大（ECharts + Element Plus 约 1MB gzip 后 340KB），属正常，课程设计场景可接受；如需优化可用 manualChunks 分包。
- 基础数据管理页后端阶段未提供写接口，采用前端 localStorage 演示 CRUD，预置数据对齐 init.sql。
