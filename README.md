# CPGJ Tool

CPGJ Tool 是一个面向等级保护测评场景的工具项目，提供项目管理、证据上传、OCR、字段抽取与复核、测评记录生成与复核、项目级 TXT 导出等能力。仓库内包含 FastAPI 后端与 Vue 3 工具前端，可用于本地联调和 Docker 交付。

## 技术栈

- Backend: FastAPI, SQLAlchemy, Alembic, Pydantic, SQLite/PostgreSQL
- Frontend: Vue 3, TypeScript, Vite, Element Plus, Pinia, Axios
- Testing: pytest, FastAPI TestClient
- Delivery: Docker, Docker Compose, Nginx

## 目录结构

```text
backend/                 后端服务与 Alembic 迁移
  app/
    api/
    core/
    models/
    repositories/
    rules/
    schemas/
    services/
  tests/                 后端测试
frontend/                Vue 3 工具前端
  src/
  public/
docs/                    项目补充文档
scripts/                 迁移与辅助脚本
legacy/                  旧资产归档区
backend.Dockerfile       后端镜像定义
frontend.Dockerfile      前端镜像定义
compose.yml              开发/交付环境启动编排
README.md                仓库启动与交付说明
```

## 项目介绍

核心业务链路如下：

1. 创建项目
2. 上传证据
3. 触发 OCR
4. 执行字段抽取
5. 在复核页修正字段
6. 生成测评记录
7. 复核 / 审批记录
8. 发起项目导出并下载 TXT 结果

## 本地启动方式

### 1. 后端启动

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

后端启动后可访问：

- API 根路径：`http://127.0.0.1:8000/api/v1`
- 健康检查：`http://127.0.0.1:8000/health`

### 2. 前端启动

```bash
cd frontend
cp .env.example .env
npm install
npm run dev
```

前端默认运行在：

- `http://127.0.0.1:5173`

`frontend/.env.example` 默认将 `VITE_API_BASE_URL` 指向 `http://127.0.0.1:8000/api/v1`。如果通过 Nginx / Docker 反代运行，可改为 `/api/v1`。

前端容器默认通过 Nginx `/api/` 反向代理访问后端，因此 Docker 构建默认使用相对地址 `/api/v1`。`frontend/.env.example` 主要用于本地 Vite 开发，如需容器自定义 API 地址，可在构建时覆盖 `VITE_API_BASE_URL`。

## 数据库初始化

后端在 `backend/main.py` 的 lifespan 中调用 `backend/app/core/database.py:init_db()`：

- 自动创建 `uploads/`、`exports/`、`snapshots/` 运行时目录
- 自动执行 Alembic `upgrade head`

因此本地首次启动时不需要手动建表。只需准备好 `.env` 后直接启动后端即可。

## 环境变量说明

后端样例文件：`backend/.env.example`

关键变量：

- `DATABASE_URL`：数据库连接串，默认 SQLite
- `CORS_ORIGINS`：允许的前端来源
- `UPLOAD_DIR`：上传文件目录
- `EXPORT_DIR`：导出文件目录
- `SNAPSHOT_DIR`：快照目录
- `OCR_PROVIDER`：`mock` 或 `real`
- `OCR_TIMEOUT_SECONDS`：OCR 超时时间

前端样例文件：`frontend/.env.example`

- `VITE_API_BASE_URL`：前端访问后端 API 的基础地址

## 规则文件说明

规则文件位于：`backend/app/rules/`

主要包括：

- `field_rules.json`：字段抽取规则
- `evaluation_items.json`：测评项匹配规则
- `templates.json`：记录模板与 fallback 规则

后端通过 `backend/app/services/rule_loader.py` 读取这些规则文件。需要调整抽取、匹配或记录渲染逻辑时，应优先更新这些 JSON 文件，而不是写死到代码里。

## 导出说明

项目级导出由以下接口提供：

- `POST /api/v1/projects/{project_id}/export`
- `GET /api/v1/projects/{project_id}/export-jobs`
- `GET /api/v1/exports/{export_id}/download`

当前仅支持 TXT 导出。导出文件默认写入 `EXPORT_DIR`，内容按“项目 → 设备 → 记录”分组输出。只有状态为 `approved` 或 `exported` 的记录允许参与导出。

## 测试

在后端目录执行：

```bash
cd backend
source .venv/bin/activate
pytest -q
```

测试至少覆盖：

- 项目管理
- 证据上传
- 字段抽取
- 记录生成
- 导出

前端构建验证：

```bash
cd frontend
npm run build
```

## 验证记录

当前仓库已完成以下交付验证：

1. 后端自动化测试通过
2. 前端生产构建通过
3. `docker compose up --build` 可正常启动
4. `http://127.0.0.1:18000/health` 可访问
5. `http://127.0.0.1:18080` 可访问
6. 已完成浏览器端黄金路径实操闭环：
   - 创建项目
   - 上传证据
   - 执行 OCR
   - 字段抽取与字段复核
   - 生成记录并审批
   - 发起项目导出并成功下载 TXT

在这轮浏览器实操中，已额外修复两个仅靠单测和 curl 不易发现的交付问题：

- `frontend/src/api/exports.ts` 不再写死导出下载地址，而是复用 `apiBaseUrl`
- `frontend.Dockerfile` 默认使用相对地址 `/api/v1`，避免前端容器错误继承本地开发 API 地址

## Docker 启动说明

### 1. 准备环境文件

```bash
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
```

### 2. 启动容器

```bash
docker compose up --build
```

如需覆盖默认宿主机端口，可在命令前设置环境变量，例如：

```bash
BACKEND_PORT=18000 FRONTEND_PORT=18080 docker compose up --build
```

启动后访问：

- Frontend: `http://127.0.0.1:18080`
- Backend health: `http://127.0.0.1:18000/health`

Compose 默认使用：

- backend: FastAPI + uvicorn
- frontend: 静态构建产物 + Nginx

前端容器会通过 `/api/` 反向代理到 backend，因此浏览器侧不需要直连容器内部地址。

## 从零启动步骤

1. 克隆仓库
2. 准备后端环境
   - `cd backend`
   - `python3 -m venv .venv`
   - `source .venv/bin/activate`
   - `pip install -r requirements.txt`
   - `cp .env.example .env`
3. 启动后端
   - `uvicorn main:app --host 0.0.0.0 --port 8000 --reload`
4. 准备前端环境
   - `cd ../frontend`
   - `cp .env.example .env`
   - `npm install`
5. 启动前端
   - `npm run dev`
6. 打开前端并联调
   - 进入项目列表
   - 创建项目
   - 上传证据
   - OCR → 字段抽取 → 字段复核 → 生成记录 → 审批 → 导出
7. 如需容器化启动
   - 回到仓库根目录
   - `docker compose up --build`
   - 默认访问 `http://127.0.0.1:18080`，后端健康检查为 `http://127.0.0.1:18000/health`

## 修改文件时建议关注

- 后端入口：`backend/main.py`
- 配置：`backend/app/core/config.py`
- 数据库初始化：`backend/app/core/database.py`
- 前端 API 层：`frontend/src/api/http.ts`
- Vite 配置：`frontend/vite.config.ts`
