# 公共雕塑投影路径干扰簇

河岬公共艺术照明组在试投后用邻接观测划分灯影分区，并交接公共艺术雕塑保护观察位。

## 现场工作与联系人

河岬公共艺术照明组有三个灯组和一名展陈复核员。团队过去在纸质平面上标串光、用群聊交接站位。纸图不易看出成片串光，复测后各灯组容易使用旧图，保护位的聊天回执也难与原班次对应。现场遮挡和串光读数进入本系统，分区图和双签回单由负责晚间试投的灯组使用。

- 雕塑投影带 `sculpture_bands`，字段为 `title`（虚构展品）、`cols`（网格列数）、`rows`（网格行数）、`revision`（观测版本）、`scope`（造型种类）。模型约束位于 `backend/domain/sculpture_bands_model.py`，规则位于 `sculpture_bands_service.py`。
- 遮挡观测格 `sight_cells`，字段为 `band`（投影带）、`x`（列坐标）、`y`（行坐标）、`shade`（遮挡面积比）、`spill`（串光面积比）、`owner`（当前责任灯组）、`protected`（雕塑保护观察位）。模型约束位于 `backend/domain/sight_cells_model.py`，规则位于 `sight_cells_service.py`。
- 遮挡图谱 `shadow_plans`，字段为 `band`（投影带）、`revision`（底图版本）、`clusters`（簇数）、`layout`（簇及网格坐标）、`evidence`（谱聚类统计）、`token`（任务凭证）。模型约束位于 `backend/domain/shadow_plans_model.py`，规则位于 `shadow_plans_service.py`。
- 观察位灯组责任 `light_handoffs`，字段为 `plan`（谱图）、`cell`（观察格）、`cluster`（关联簇）、`source`（交出灯组）、`target`（接收灯组）、`status`（移交状态）、`first_sign`（领班签署人）、`second_sign`（复核签署人）。模型约束位于 `backend/domain/light_handoffs_model.py`，规则位于 `light_handoffs_service.py`。

### 一天的业务操作

1. 17:20 展陈复核员核对 BANK-01 披风者前方的 6×4 观测网格。
2. 17:40 领班录入第 2 列第 1 行，记录遮挡 46%、串光 50%。
3. 18:00 试投后再测该格为 47%，原底图版本失效。
4. 18:20 对 24 个观测格划分 3 组，复核员归档 MAP-BANK-01。
5. 18:40 普通观察格 BANK-01-1-0 直接移交南侧灯组。
6. 18:50 BANK-01-0-0 保护观察位先由领班签署 LX-024，北侧组继续负责。
7. 19:10 展陈复核员签收 LX-024，观察位责任转到南侧组。

## 启动

```sh
cp .env.example .env
docker compose up -d --build --wait
docker compose exec -T backend python -m scripts.seed_demo
```

打开 `http://127.0.0.1:18320`。FastAPI OpenAPI 在 `http://127.0.0.1:19320/docs`。
Compose 运行 Nginx、Python FastAPI、独立 Redis 消费进程、PostgreSQL 16 和 Redis，SQL 与 Redis 使用命名卷。
本地开发可在 Python 3.11 环境安装 `backend/requirements.txt` 后从 backend 目录运行 `uvicorn core.app:app`。须提供 `DATABASE_URL`、`REDIS_URL`、`JWT_SECRET`，`SEED_DEMO` 控制演示初始化。

| 演示账号 | 权限 |
|---|---|
| operator@demo.test | 记录试投方格、测算灯影分区、以领班身份签发移交 |
| reviewer@demo.test | 登记底图和保护位、归档分区图、以独立身份复核保护位移交 |
| viewer@demo.test | 浏览网格、分区平面和灯组责任记录 |

三个本地演示账号均使用 `DemoC0de!2026`。角色在 `backend/core/roles.py` 和 `frontend/src/store.js` 中声明。计算状态在 worker、queueing、API 和前端交互模块中使用。

## 页面与接口

| 业务任务 | FastAPI 路由 | 页面 |
|---|---|---|
| 雕塑投影带 | `/sculpture_bands` /sculpture_bands/book-band | `frontend/src/pages/sculpture_bands.js` |
| 遮挡观测格 | `/sight_cells` /sight_cells/record-beam，/sight_cells/protect-station | `frontend/src/pages/sight_cells.js` |
| 遮挡图谱 | `/shadow_plans` /shadow_plans/segment-bank，/shadow_plans/pin-map | `frontend/src/pages/shadow_plans.js` |
| 观察位灯组责任 | `/light_handoffs` /light_handoffs/offer-station，/light_handoffs/check-station | `frontend/src/pages/light_handoffs.js` |

SQL 实体与约束在 `backend/domain` 下维护。前端使用原生 ES modules。核心算子为 SpectralClustering。以四邻格构图，按遮挡率和串光率差的平方和设定指数权重。谱分组按格序重新编号，输出边切分数量、权重占比和底图哈希。

观测和展品为虚构，本应用用于灯影分区草案与责任记录。现场灯具独立控制。

[MIT](LICENSE)
