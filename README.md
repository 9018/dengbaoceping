# 等级保护测评工作台

这是一个围绕等级保护测评交付闭环构建的全栈工作台。系统把“模板、指导书、历史记录、项目资产、截图证据、OCR、事实识别、草稿生成、人工确认”拉通成统一流程，而不是把能力分散在孤立页面里。

当前仓库由 FastAPI 后端、Vue 3 前端和 Docker 交付配置组成，既支持本地开发联调，也支持直接用 Docker Compose 启动演示环境。

## 当前产品主线

系统现在分成两条主线：

### 1. 全局初始化主线

用于沉淀可复用的知识库能力：

1. 导入结果记录参考模板
2. 生成全局测评项模板库
3. 导入指导书
4. 给模板项补充依据、操作步骤、判断标准、预期结果
5. 导入历史人工测评记录
6. 给模板项补充写法样本和符合情况样本

### 2. 项目测评主线

用于完成单个项目的实际交付：

1. 创建项目资产
2. 根据资产类型生成项目测评表
3. 上传截图证据
4. 执行 OCR
5. 识别页面类型和证据事实
6. 匹配项目测评表行 / 模板行
7. 结合模板、指导书、历史记录生成 D/E 列草稿
8. 人工确认后写回项目测评表

合并后的业务闭环可理解为完整十步：

1. 导入结果记录参考模板
2. 导入指导书
3. 导入历史人工测评记录
4. 创建项目资产
5. 生成项目测评表
6. 上传截图并 OCR
7. 识别页面类型和证据事实
8. 匹配项目测评表行
9. 生成 D/E 列草稿
10. 人工确认写回

## 核心领域对象

### 全局知识库

- `AssessmentTemplateWorkbook / AssessmentTemplateSheet / AssessmentTemplateItem`
  - 全局测评模板主来源
- `GuidanceItem`
  - 指导书依据条目
- `HistoricalAssessmentRecord`
  - 历史人工记录样本
- `TemplateGuidebookLink`
  - 模板项与指导书条目关联
- `TemplateHistoryLink`
  - 模板项与历史记录关联

### 项目工作流主脊柱

- `ProjectAssessmentTable`
  - 项目内按资产生成的测评表
- `ProjectAssessmentItem`
  - 项目测评表中的具体待填写行
- `EvidenceFact`
  - OCR 后持久化的页面类型与归一化事实

## 关键能力说明

- 模板优先：`AssessmentTemplateItem` 是全局模板唯一主来源
- 指导书补强：指导书用于补充依据、检查步骤和判断标准，不替代模板主骨架
- 历史记录补强：历史人工记录只用于写法增强，不应覆盖当前截图事实
- 事实优先于旧样本：当前证据识别出的账号、策略、配置、版本、时间等事实优先级高于历史写法
- 人工确认为最终真值：系统生成的是草稿，最终结果以人工确认写回为准
- 项目独立：每个项目有独立资产、独立项目测评表、独立证据与草稿状态

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

## 主要页面与路由

### 全局页面

- `/dashboard` 工作台
- `/setup-wizard` 初始化向导
- `/assessment-templates` 模板库
- `/guidance` 指导书库
- `/history-records` 历史记录库
- `/projects` 项目列表

### 项目页面

- `/projects/:projectId` 项目详情
- `/projects/:projectId/assessment-wizard` 项目测评向导
- `/projects/:projectId/assets` 项目资产
- `/projects/:projectId/evidences` 证据中心
- `/projects/:projectId/records` 项目测评表
- `/projects/:projectId/exports` 导出中心

### 兼容入口

以下旧链路仍保留，用于兼容过渡期：

- `/projects/:projectId/evidence-wizard`
- 旧 `/evidences/*` 处理接口
- 旧 `/records/*` 记录接口
- 旧 `Template / EvaluationItem / rules/*.json` 相关链路

新前端主路径优先使用 workflow API 和新的向导视图。

## Workflow API

### 全局流程接口

- `GET /api/v1/workflow/global-status`
- `POST /api/v1/workflow/import-template`
- `POST /api/v1/workflow/import-guidance`
- `POST /api/v1/workflow/import-history`

### 项目流程接口

- `GET /api/v1/projects/{project_id}/workflow/status`
- `POST /api/v1/projects/{project_id}/assets/{asset_id}/generate-assessment-table`
- `GET /api/v1/projects/{project_id}/assessment-tables`
- `GET /api/v1/assessment-tables/{table_id}/items`
- `POST /api/v1/evidences/{evidence_id}/extract-facts`
- `POST /api/v1/evidences/{evidence_id}/match-project-assessment-item`
- `POST /api/v1/project-assessment-items/{item_id}/generate-draft`
- `POST /api/v1/project-assessment-items/{item_id}/confirm`

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
  - SQLite 数据库存放在容器内 `/app/runtime/app.db`
  - 挂载 `./backend/runtime`、`./backend/uploads`、`./backend/exports`、`./backend/snapshots`
  - 内置 `/health` 健康检查
- `frontend`
  - 使用 `frontend.Dockerfile`
  - 对外暴露 `18080 -> 80`
  - 依赖后端健康后再启动

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

默认情况下，只要 `.env` 可用，直接启动后端即可，无需手工建表。

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

### Docker 健康检查

```bash
docker compose up -d --build
curl http://127.0.0.1:18000/health
```

## 运行与维护约束

- 不要提交 `__pycache__`、`.pyc`、`node_modules`、`dist`、数据库文件和运行时导出目录
- `.gitignore` 已覆盖 `uploads/`、`exports/`、`snapshots/`、`*.db`、`*.sqlite*`、前端构建产物等常见运行时垃圾
- 若文档、路由、接口与当前实现不一致，应以代码为准并立即修正文档
- 旧链路当前保留是为了兼容迁移，不代表后续主开发方向
