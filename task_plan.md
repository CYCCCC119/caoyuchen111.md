# 任务规划：前端开发与系统联调阶段

## 阶段目标

完成「重型机械装配车间螺栓拧紧质量智能检测与工艺追溯系统」的**前端开发与系统联调**，对应方案设计 3.4 节的五大页面，对接后端 8 个 RESTful 接口，实现全流程可视化闭环。

## 技术栈

Vue3 + Vue Router + Element Plus + ECharts + Axios，Vite 构建，开发环境经 `/api` 代理联通 FastAPI 后端（8000 端口）。

## 任务拆解

| # | 任务 | 产出物 | 状态 |
|---|------|--------|------|
| 1 | 工程骨架 | `frontend/`（package.json/vite.config/index.html/main/App/router/api） | ✅ 完成 |
| 2 | 依赖安装 | node_modules（npm install） | ✅ 完成 |
| 3 | 监控大屏 | `views/Dashboard.vue`（/api/stats） | ✅ 完成 |
| 4 | 质量检测分析 | `views/Detection.vue`（/api/detect、/api/detect/batch、/api/ingest/file） | ✅ 完成 |
| 5 | 工艺追溯查询 | `views/Traceability.vue`（/api/trace） | ✅ 完成 |
| 6 | 工艺参数优化 | `views/Optimization.vue`（/api/optimize、/api/correlation） | ✅ 完成 |
| 7 | 基础数据管理 | `views/DataManage.vue`（演示 CRUD，localStorage 持久化） | ✅ 完成 |
| 8 | 构建与联调 | `npm run build` 通过 + 前后端联通验证 | ✅ 完成 |
| 9 | 文档与追溯 | README / prompt 追溯 / 提交推送 | ✅ 完成 |
| 10 | 一键启动脚本 | `start.bat`（相对路径、纯英文、同目录启动，自动 npm install + 开浏览器） | ✅ 完成 |

## 关键决策

- **工程化**：Node 24 / npm 11 可用，采用标准 Vite + Vue3 单页应用（非 CDN 单文件），组件化、可扩展，贴近真实工业前端工程。
- **前后端联通**：开发环境用 Vite `/api` 代理到 `localhost:8000`（后端已开 CORS），生产可静态托管 `dist/` 或由 FastAPI 挂载。
- **图表**：封装通用 `ChartBox.vue`（ECharts 生命周期管理），各页面只关注 option 构造，减少样板代码。
- **基础数据管理**：后端阶段未提供基础数据写接口，本页采用前端 localStorage 演示 CRUD（预置数据对齐 init.sql 的工位/人员/螺栓/工艺基准），生产替换为 MySQL 基础数据服务。已在校验/文档中标注。
- **监控大屏**：独立深色工业风格，其余页面统一浅色 Element Plus 主题。
- **一键启动**：新增 `start.bat`，以 `%~dp0` 定位脚本自身目录（相对路径，无硬编码绝对路径），用 `start /D` 指定工作目录分别拉起后端 `python -m uvicorn:8000` 与前端 `npm run dev:5173`，首次运行自动 `npm install`，延时自动打开浏览器，方便整体打包迁移。

## 下一阶段

- 文档撰写与答辩准备（设计报告、演示视频、答辩 PPT）。
