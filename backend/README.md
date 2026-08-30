# 后端服务说明

「重型机械装配车间螺栓拧紧质量智能检测与工艺追溯系统」后端服务，基于 **FastAPI** 构建，对接 `algorithms/` 三大算法模块，对外提供 RESTful API。

## 一、技术栈

- **Web 框架**：FastAPI + Uvicorn
- **数据校验**：Pydantic v2
- **算法引擎**：scikit-learn（复用 `algorithms/` 模块）
- **数据层**：CSV 文件仓库（`data/business/tightening_context.csv` + 预处理特征集），零外部数据库依赖，开箱即用；生产环境可无缝替换为 MySQL + InfluxDB（表结构见 `data/business/init.sql`）

## 二、目录结构

```
backend/
├── main.py                      # 应用入口 + CORS + 路由注册
├── requirements.txt             # 依赖清单
├── README.md                    # 本文档
└── app/
    ├── config.py                # 路径常量 + 项目根目录注入
    ├── state.py                 # 共享服务实例（惰性单例）
    ├── schemas.py               # Pydantic 请求/响应契约
    ├── services/                # 业务服务层
    │   ├── detection_service.py     # 质量检测
    │   ├── traceability_service.py  # 工艺追溯
    │   └── optimization_service.py  # 参数优化
    └── routers/                 # API 路由层
        ├── detection.py         # 检测接口
        ├── ingest.py            # 数据接入接口
        ├── traceability.py      # 追溯接口
        └── optimization.py      # 优化接口
```

## 三、启动

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

启动后访问：
- 交互式接口文档：http://127.0.0.1:8000/docs
- 系统信息：http://127.0.0.1:8000/

## 四、接口概览

| 分类 | 方法 | 路径 | 说明 |
|------|------|------|------|
| 质量检测 | POST | `/api/detect` | 单条曲线质量检测 |
| 质量检测 | POST | `/api/detect/batch` | 批量曲线质量检测 |
| 数据接入 | POST | `/api/ingest` | 单条曲线接入并检测 |
| 数据接入 | POST | `/api/ingest/file` | CSV 文件接入（angle,torque 两列） |
| 工艺追溯 | POST | `/api/trace` | 多条件组合追溯 |
| 工艺追溯 | GET  | `/api/stats` | 全局质量统计 |
| 参数优化 | POST | `/api/optimize` | 最优工艺参数推荐 |
| 参数优化 | GET  | `/api/correlation` | 参数-质量关联分析 |

## 五、调用示例

单条检测：

```bash
curl -X POST http://127.0.0.1:8000/api/detect \
  -H "Content-Type: application/json" \
  -d '{"spec":"M20","angle":[0,10,20,30,40,50,60],"torque":[3,40,120,240,300,315,320]}'
```

工艺追溯（工位 WS-001 的欠拧记录）：

```bash
curl -X POST http://127.0.0.1:8000/api/trace \
  -H "Content-Type: application/json" \
  -d '{"workstation_id":"WS-001","label":1}'
```

参数优化（M20）：

```bash
curl -X POST http://127.0.0.1:8000/api/optimize \
  -H "Content-Type: application/json" \
  -d '{"spec":"M20"}'
```
