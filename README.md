# 等级保护测评工作台

这是一个面向等级保护测评流程的全栈工作台，覆盖项目建档、证据采集、OCR、字段复核、测评记录生成、结果导出，以及模板库 / 历史记录库 / 指导书依据库三条全局知识链路。

仓库当前由 FastAPI 后端、Vue 3 前端和 Docker 交付配置组成，适合本地开发联调，也适合直接用 Compose 启动演示环境。

## 当前能力范围

- 项目管理：创建、查看、维护测评项目
- 证据中心：上传证据、查看证据、进入证据处理向导
- OCR：调用 PaddleOCR 识别截图文本
- 字段抽取与复核：从 OCR 结果提取结构化字段并人工修正
- 测评记录生成：结合模板、指导书依据、历史样例生成记录草稿
- 记录复核与导出：审批记录并导出项目结果
- 全局知识库：
  - 测评记录模板库 `/assessment-templates`
  - 历史测评记录库 `/history-records`
  - 指导书依据库 `/guidance`

## 技术栈

### Backend
- FastAPI
- SQLAlchemy
- Alembic
- Pydantic Settings
- SQLite（默认）

### Frontend
- Vue 3
- TypeScript
- Vite
- Element Plus
- Pinia
- Vue Router
- Axios

### Delivery
- Docker
- Docker Compose
- Nginx

## 仓库结构

```text
backend/                     后端服务、领域模型、API、测试
  app/
    api/
    core/
    models/
    repositories/
    schemas/
    services/
  alembic/
  tests/
frontend/                    Vue 3 前端
  src/
md/                          指导书 Markdown 文件目录
compose.yml                  Docker Compose 启动入口
backend.Dockerfile           后端镜像定义
frontend.Dockerfile          前端镜像定义
README.md                    仓库说明
```

## 核心流程

项目工作区主链路：

1. 创建项目
2. 上传证据
3. 执行 OCR
4. 抽取字段
5. 人工复核字段
6. 生成测评记录
7. 复核记录
8. 导出项目结果

全局知识链路：

1. 导入测评记录模板库
2. 导入指导书依据库
3. 导入历史测评记录库
4. 为模板项建立指导书与历史样例关联
5. 在证据向导和记录生成阶段消费这些结构化知识

## 本地开发启动

### 1. 启动后端

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

后端入口：
- 根路径：`http://127.0.0.1:8000/`
- 健康检查：`http://127.0.0.1:8000/health`
- API 前缀：`http://127.0.0.1:8000/api/v1`

### 2. 启动前端

```bash
cd frontend
npm install
npm run dev
```

前端默认地址：
- `http://127.0.0.1:5173`

本地 Vite 开发时，前端通常通过 `VITE_API_BASE_URL` 直连后端 `http://127.0.0.1:8000/api/v1`。

## Docker 启动

仓库根目录直接启动：

```bash
docker compose up -d --build
```

默认端口：
- 后端：`http://127.0.0.1:18000`
- 后端健康检查：`http://127.0.0.1:18000/health`
- 前端：`http://127.0.0.1:18080`

### Compose 说明

`compose.yml` 当前包含两个服务：

- `backend`
  - 使用 `backend.Dockerfile`
  - 对外暴露 `18000 -> 8000`
- `frontend`
  - 使用 `frontend.Dockerfile`
  - 对外暴露 `18080 -> 80`

前端容器中的 Nginx 会把 `/api/` 反向代理到后端容器，因此 Docker 场景下前端默认通过相对路径访问后端。

## 环境变量

后端示例文件：`backend/.env.example`

关键项：
- `APP_NAME`
- `APP_VERSION`
- `API_V1_PREFIX`
- `DATABASE_URL`
- `CORS_ORIGINS`
- `UPLOAD_DIR`
- `EXPORT_DIR`
- `SNAPSHOT_DIR`
- `GUIDANCE_FILE_PATH`
- `OCR_PROVIDER`
- `OCR_TIMEOUT_SECONDS`
- `PADDLE_OCR_LANG`
- `PADDLE_OCR_USE_ANGLE_CLS`
- `PADDLE_OCR_USE_GPU`

默认后端 API 前缀为：

```env
API_V1_PREFIX=/api/v1
```

## 数据初始化

后端在启动时会执行 `init_db()`，并自动完成以下动作：

- 初始化运行时目录
- 执行 Alembic `upgrade head`

因此默认情况下，不需要手工执行建表命令；只要 `.env` 可用，直接启动后端即可。

## 全局页面入口

前端当前主要全局导航为：

- `/dashboard` 工作台
- `/projects` 项目列表
- `/assessment-templates` 测评记录模板库
- `/history-records` 历史测评记录库
- `/guidance` 指导书依据库

项目级工作区入口为：

- `/projects/:projectId`
- `/projects/:projectId/evidence-wizard`
- `/projects/:projectId/evidences`
- `/projects/:projectId/records`
- `/projects/:projectId/exports`

## 测试与构建

### 后端测试

```bash
cd backend
source .venv/bin/activate
pytest -q
```

### 前端构建

```bash
cd frontend
npm run build
```

## 交付与维护建议

- 不要把 `__pycache__`、`.pyc`、运行时 `exports/`、`snapshots/`、索引数据目录等产物提交到源码 commit
- 文档、接口、模板链路变更后，优先同步更新本 README
- 如果 README 中的端口、路由或启动命令与仓库状态不一致，应以实际代码和 `compose.yml` 为准并立即修正文档
