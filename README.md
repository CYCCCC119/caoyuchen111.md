# 重型机械装配车间螺栓拧紧质量智能检测与工艺追溯系统

运用 Vibe Coding 开发方法，实现的一套 B/S 架构可运行 Demo 系统。系统面向重型机械装备制造的螺栓装配工序，围绕「质量管控 - 缺陷预警 - 工艺追溯 - 持续优化」全业务链条，验证制造智能技术在装配质量管控场景的落地应用。

## 项目概况

- **拟定题目**：重型机械装配车间螺栓拧紧质量智能检测与工艺追溯系统
- **技术方向**：工业大数据预处理与特征工程、制造过程质量智能检测与控制、制造工艺追溯与参数优化（覆盖《制造智能技术》课程 3 个核心专题）
- **架构**：前端展示层（Vue3 + Element Plus + ECharts）/ 后端服务层（FastAPI）/ 算法引擎层（scikit-learn）/ 数据存储层（MySQL + InfluxDB）
- **核心功能**：拧紧数据上传 → 质量实时检测（5 类状态：合格/欠拧/过拧/滑牙/虚拧）→ 缺陷自动预警 → 工艺全链追溯 → 参数优化推荐

## 项目结构

```
├── 选题说明.md          # 选题与目标
├── 方案设计.md          # 系统方案设计
├── 数据资源整理说明.md  # 数据资源规划（详细方案）
├── 学习笔记.md          # Vibe Coding / Git / AI 工具学习笔记
├── data/                # 数据集（原始数据 + 预处理特征 + 业务数据）
│   ├── raw/             #   原始拧紧时序数据（自建模拟）
│   ├── processed/       #   预处理后特征数据集（train/val/test）
│   ├── business/        #   业务数据库初始化脚本
│   ├── generate_data.py #   数据生成脚本
│   ├── preprocess.py    #   预处理 + 特征工程脚本
│   └── README.md        #   数据说明文档
├── algorithms/          # 核心算法模块（三模块 + 训练产物）
│   ├── feature_engineering.py   #   模块一：时序特征工程
│   ├── quality_detection.py     #   模块二：质量智能检测
│   ├── process_optimization.py  #   模块三：工艺追溯与参数优化
│   └── models/                  #   训练产物（模型 + 评估/优化报告）
├── backend/             # FastAPI 后端服务
│   ├── main.py          #   应用入口
│   ├── requirements.txt #   依赖清单
│   └── app/             #   配置 + 服务层 + 路由层
├── frontend/            # Vue3 前端（五大页面）
│   ├── package.json     #   依赖与脚本
│   ├── vite.config.js   #   构建 + /api 代理配置
│   └── src/
│       ├── views/       #   监控大屏 / 检测 / 追溯 / 优化 / 数据管理
│       ├── components/  #   通用图表组件
│       └── api/         #   后端接口封装
├── tests/               # 单元测试（unittest）
├── prompt/              # AI 交流提示词追溯记录
├── task_plan.md         # 任务规划
├── findings.md          # 调研发现
└── progress.md          # 进度记录
```

## 数据来源与预处理

数据采用**自建模拟数据集**：基于螺栓拧紧「力矩-转角」力学模型，模拟生成 3000 条覆盖 5 类质量状态的拧紧时序数据（采样频率 100 Hz）。

- **自建数据集开源地址**（Hugging Face）：https://huggingface.co/datasets/zerozero01/bolt-tightening-quality
- 数据集同时提交至本仓库 `data/` 目录；公开数据集参考链接见 [data/README.md](data/README.md)

预处理流程：数据清洗（去空行程 + 3σ 异常值剔除 + 线性插值）→ 12 维时域特征提取 → 特征选择（Pearson 相关 + 共线性分析）→ Z-score 标准化 → 7:2:1 分层划分。

详见 [data/README.md](data/README.md)。

### 数据快速复现

```bash
python data/generate_data.py   # 生成原始数据
python data/preprocess.py      # 预处理 + 特征工程 + 划分
```

## 核心算法与后端

对应课程三大技术方向，实现三个算法模块并封装为 FastAPI 后端服务（详见 [backend/README.md](backend/README.md)）。

### 三大算法模块

| 模块 | 对应课程技术 | 核心方法 | 效果 |
|------|------------|---------|------|
| 时序特征工程 | 工业大数据预处理与特征工程 | 清洗 → 12 维特征提取 → Pearson+共线性选择 → Z-score | 12 → 8 维 |
| 质量智能检测 | 质量智能检测与控制 | 随机森林（主，网格搜索）+ SVM/GBDT 对比 | 测试集准确率 99.67% |
| 工艺追溯与参数优化 | 工艺追溯与参数优化 | Pearson 关联分析 + 多目标网格搜索 | 输出最优参数组合 |

### 后端接口

```bash
cd backend && pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000   # 文档 /docs
```

主要接口：`POST /api/detect`（单条检测）、`POST /api/detect/batch`（批量检测）、`POST /api/ingest`（数据接入）、`POST /api/trace`（多条件追溯）、`GET /api/stats`（质量统计）、`POST /api/optimize`（参数优化）、`GET /api/correlation`（关联分析）。

### 测试

```bash
python -m unittest discover -s tests -p "test_*.py"
```

## 前端（Vue3 + Element Plus + ECharts）

五大页面，对接后端 8 个 RESTful 接口，实现全流程可视化闭环（详见 [frontend/README.md](frontend/README.md)）：

| 页面 | 对接接口 | 核心能力 |
|------|---------|---------|
| 拧紧质量监控大屏 | `/api/stats` `/api/trace` | 合格率/缺陷分布/工位排行 + 实时滚动 + 质量趋势 |
| 质量检测分析 | `/api/detect` `/api/detect/batch` `/api/ingest/file` | 单条/批量检测 + 力矩-转角曲线 + 概率分布 |
| 工艺追溯查询 | `/api/trace` | 多条件组合检索 + 反向定位详情 |
| 工艺参数优化 | `/api/optimize` `/api/correlation` | 关联热力图 + Pareto 前沿 + 优化前后对比 |
| 基础数据管理 | 前端 localStorage 演示 CRUD | 螺栓/工位/工艺参数/人员 增删改查 |

```bash
cd frontend && npm install
npm run dev            # 前端 5173，经 /api 代理到后端 8000
npm run build          # 生产构建输出 dist/
```

> 运行前需先启动后端（见上「后端接口」）。监控大屏为独立深色工业风格，其余页面为 Element Plus 浅色主题。

## 开发计划

| 阶段 | 内容 | 产出物 | 状态 |
|------|------|--------|------|
| 一 | 选题与需求设计 | 选题说明、方案设计 | ✅ 完成 |
| 二 | 数据准备与数据库设计 | 数据集、预处理脚本、数据库设计 | ✅ 完成 |
| 三 | 核心算法与后端开发 | 算法模块、后端接口 | ✅ 完成 |
| 四 | 前端开发与系统联调 | 前端代码、可运行 Demo | ✅ 完成 |
| 五 | 文档撰写与答辩准备 | 设计报告、演示视频、答辩 PPT | ⏳ 待开始 |

## 过程档案

全程使用 Git 管理版本，AI 交流提示词记录存放于 `prompt/` 目录，与代码提交对应，保证开发过程可追溯。
