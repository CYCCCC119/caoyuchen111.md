# 前端（Vue3 + Element Plus + ECharts）

「重型机械装配车间螺栓拧紧质量智能检测与工艺追溯系统」前端展示层，采用工业管控系统经典布局（左侧导航 + 顶部标题 + 主内容区），共 5 个核心页面，对接后端 8 个 RESTful 接口。

## 技术栈

- **Vue3**（Composition API + `<script setup>`）
- **Vue Router 4**（单页路由，5 页面）
- **Element Plus**（组件库，中文语言包）
- **ECharts 5**（可视化，封装通用 `ChartBox` 组件管理生命周期）
- **Axios**（HTTP 封装，统一错误处理）
- **Vite 6**（构建，开发环境 `/api` 代理到后端 8000）

## 快速开始

```bash
# 1. 先启动后端（项目根 backend/ 目录）
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000

# 2. 另开终端，启动前端（项目根 frontend/ 目录）
cd frontend
npm install        # 首次运行安装依赖
npm run dev        # 启动开发服务器，访问 http://localhost:5173
```

开发环境前端请求 `/api/*` 由 Vite 代理转发至 `http://localhost:8000`（配置见 `vite.config.js`），后端已开启 CORS。

生产构建：`npm run build` 输出静态文件至 `dist/`，可托管于 Nginx 或由 FastAPI 挂载。

## 目录结构

```
frontend/
├── index.html
├── vite.config.js         # 构建 + /api 代理
├── package.json
└── src/
    ├── main.js            # 应用入口（Element Plus + 图标 + 路由）
    ├── App.vue            # 整体布局（侧边导航 + 顶栏 + 主内容）
    ├── router/index.js    # 5 页面路由
    ├── api/index.js       # 后端接口封装（axios）
    ├── utils/
    │   ├── constants.js   # 标签/等级/规格等共享常量
    │   └── sampleCurves.js# 真实样本曲线（自 data/raw 提取，供示例检测）
    ├── components/
    │   └── ChartBox.vue   # ECharts 通用封装（init/resize/dispose）
    └── views/
        ├── Dashboard.vue      # 拧紧质量监控大屏
        ├── Detection.vue      # 质量检测分析
        ├── Traceability.vue   # 工艺追溯查询
        ├── Optimization.vue   # 工艺参数优化
        └── DataManage.vue     # 基础数据管理
```

## 五大页面说明

### 1. 拧紧质量监控大屏（Dashboard）
- 对接 `GET /api/stats`、`POST /api/trace`
- 四张统计卡（总记录/合格率/缺陷数/覆盖工位）+ 缺陷类型分布饼图 + 工位合格率柱状图 + 按小时质量趋势折线图
- 实时滚动拧紧记录，缺陷行高亮预警（定时轮播最近 40 条）
- 独立深色工业风格

### 2. 质量检测分析（Detection）
- 对接 `POST /api/detect`、`POST /api/detect/batch`、`POST /api/ingest/file`
- 单条检测三种输入方式：**示例曲线**（真实样本，五类各一）、**上传 CSV**（angle,torque 两列）、**手动输入**
- 结果展示：判定标签 + 置信度 + 缺陷等级 + 力矩-转角曲线 + 各类别概率条
- 批量检测：一键加载 5 类样本批量检测，输出报告并统计与已知标签的一致性

### 3. 工艺追溯查询（Traceability）
- 对接 `POST /api/trace`
- 多条件组合检索（规格/工位/操作人员/物料批次/质量结果/时间范围）
- 汇总统计 + 结果列表（缺陷行高亮），点击行弹出**反向定位详情**（工艺参数/设备/人员/批次）

### 4. 工艺参数优化（Optimization）
- 对接 `POST /api/optimize`、`GET /api/correlation`、`POST /api/trace`
- 按规格生成推荐工况（性能等级/磨损/转速区间/温度）+ 优化前后合格率对比
- 参数 × 质量特征相关热力图、参数 × 缺陷类型相关系数图、Pareto 前沿散点、Top 5 候选配置表

### 5. 基础数据管理（DataManage）
- 螺栓基础信息 / 工位信息 / 工艺参数基准 / 人员信息 四类实体的增删改查
- 预置数据对齐 `data/business/init.sql`
- **演示模式**：数据持久化于浏览器 localStorage；生产环境替换为 MySQL 基础数据服务（表结构见 init.sql）

## 说明

- `sampleCurves.js` 由 `data/raw/benchmark/records.jsonl` 提取真实样本曲线（M20，每类一条），数据来源可追溯，非前端伪造，用于「示例检测」即时演示。
- 后端检测接口返回的 `probabilities` 键为中文类别名（合格/欠拧/过拧/滑牙/虚拧），前端据此映射显示。
