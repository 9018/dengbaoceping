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
- `OCR_PROVIDER`：`mock`、`paddle` 或 `real`
- `OCR_TIMEOUT_SECONDS`：OCR 超时时间
- `PADDLE_OCR_LANG`：PaddleOCR 语言配置，默认 `ch`
- `PADDLE_OCR_USE_ANGLE_CLS`：是否启用方向分类器
- `PADDLE_OCR_USE_GPU`：是否启用 GPU

前端样例文件：`frontend/.env.example`

- `VITE_API_BASE_URL`：前端访问后端 API 的基础地址

## OCR provider 说明

- 默认 `OCR_PROVIDER=mock`，适合本地开发和 CI。
- `OCR_PROVIDER=paddle` 时，会读取真实上传文件并执行 PaddleOCR。
- `OCR_PROVIDER=real` 仍保留为占位 provider，当前会返回 `REAL_OCR_NOT_CONFIGURED`。
- PaddleOCR 结果统一至少包含：`provider`、`status`、`full_text`、`lines`、`processed_at`。
- `lines` 中每项结构为：`{ text, confidence, bbox }`。
- `full_text` 由 `lines[].text` 拼接得到，下游字段抽取继续依赖 `text_content/full_text` 即可工作。
- Paddle 运行期失败会返回结构化失败结果并持久化到 `ocr_result_json`，不会因为识别异常直接把接口打崩。

### Paddle 安装提示

`backend/requirements.txt` 已补充 Paddle 依赖，但 Paddle 版本兼容性受平台影响较大。首次在新环境安装时，建议优先在后端虚拟环境中单独验证：

```bash
cd backend
source .venv/bin/activate
python -c "from paddleocr import PaddleOCR; print('paddle ready')"
```

首次 OCR 调用会触发 PaddleOCR 引擎初始化，耗时通常显著高于热启动；当前实现已在进程内缓存引擎，后续调用不会重复初始化。

## 规则文件说明

规则文件位于：`backend/app/rules/`

主要包括：

- `field_rules.json`：字段抽取规则
- `evaluation_items.json`：测评项匹配规则
- `templates.json`：记录模板与 fallback 规则

后端通过 `backend/app/services/rule_loader.py` 读取这些规则文件。需要调整抽取、匹配或记录渲染逻辑时，应优先更新这些 JSON 文件，而不是写死到代码里。

## 指导书知识库说明

第一阶段已接入固定路径指导书文件：`md/指导书.md`

注意事项：

- 只读取 `md/指导书.md`
- 不读取 `docs/指导书.md`
- 如果 `md/指导书.md` 不存在，导入接口会返回明确错误
- 如果 `md/指导书.md` 为空，页面会显示“指导书.md 当前为空，请先补充内容”

### Markdown 推荐格式

建议优先使用标准 Markdown 标题组织章节，例如：

```md
# 安全物理环境
## 安全通用要求
### 物理访问控制

| 测评项 | 操作步骤 | 预期结果 |
| --- | --- | --- |
| 物理访问控制 | 应核查门禁配置并查看门禁日志 | 应提供门禁记录和现场截图 |
```

当前导入逻辑会：

- 按 `#` / `##` / `###` 标题切分章节
- 生成 `section_path`
- 生成稳定 `guidance_code`
- 保存 `raw_markdown` 和 `plain_text`
- 规则提取 `keywords_json`、`check_points_json`、`evidence_requirements_json`
- 初步生成 `record_suggestion`

### 导入方式

后端 API：

- `POST /api/v1/guidance/import-md`：导入 `md/指导书.md`
- `GET /api/v1/guidance/items`：获取指导书状态和章节列表
- `GET /api/v1/guidance/items/{guidance_id}`：获取章节详情
- `GET /api/v1/guidance/search?keyword=门禁`：按关键词搜索章节

前端页面：

- 进入“指导书管理”页面
- 查看固定路径 `md/指导书.md`
- 执行“一键导入”
- 使用关键词搜索章节并查看详情

### 查询方式

支持以下维度的规则查询：

- 章节标题
- 章节路径
- 关键词
- 核查要点
- 证据要求
- 章节正文纯文本

当前实现不引入 Elasticsearch、向量库或大模型，先使用规则和关键词完成第一版。

### 后续与 evaluation_items 的关联方向

当前阶段只完成指导书入库和查询，不改动记录生成主链路。

后续可在不破坏现有 OCR、字段抽取、记录生成、导出流程的前提下，逐步接入：

1. 用 `keywords_json` / `plain_text` 参与测评项匹配排序
2. 用 `check_points_json` 和 `evidence_requirements_json` 增强复核展示
3. 用 `record_suggestion` 辅助记录生成草稿
4. 将 `guidance_code` 与 `evaluation_items` 建立显式映射关系

## 历史人工测评记录库说明

第一阶段新增“历史人工测评记录库”，用于把真实人工三级测评 Excel 导入系统，沉淀为可查询、可搜索、可统计、可相似匹配的样本库。

当前阶段能力边界：

- 仅支持 `.xlsx` 文件导入
- 不引入 Elasticsearch、向量库或大模型
- 不改动现有 OCR、字段抽取、记录生成、复核、导出主链路

### Excel 推荐格式

建议每个工作表对应一个设备、区域或管理对象，至少包含以下列：

- `扩展标准`
- `控制点`
- `测评项`
- `结果记录`
- `符合情况`
- `分值`
- `编号`

当前导入逻辑会：

- 遍历所有工作表并自动识别表头
- 一行生成一条历史记录
- 默认使用 `sheet_name` 作为 `asset_name`
- 按工作表名称推断 `asset_type`（如防火墙/交换机/服务器/数据库/安全管理）
- 从控制点、测评项、结果记录中提取 `keywords_json`
- 返回导入统计、跳过数量和符合情况分布

### 导入与查询方式

后端 API：

- `POST /api/v1/history/import-excel`：导入历史测评记录 Excel
- `GET /api/v1/history/records`：按 sheet/control_point/compliance_status/asset_type 筛选记录
- `GET /api/v1/history/records/{record_id}`：获取单条历史记录详情
- `GET /api/v1/history/search?keyword=日志审计`：按关键词搜索历史记录
- `GET /api/v1/history/stats`：获取工作表数量、记录总数、符合情况统计、资产类型统计
- `GET /api/v1/history/similar?control_point=xxx&evaluation_item=xxx&asset_type=xxx`：获取相似历史记录 Top N
- `GET /api/v1/history/phrases`：统计常见句式（经现场核查 / 查看 / 未提供 / 当前 / 已配置 / 不适用）

前端页面：

- 进入“历史记录库”页面
- 上传 `.xlsx` 文件
- 查看导入统计卡片
- 按 sheet / 控制点 / 符合情况 / 资产类型筛选
- 执行关键词搜索
- 查看详情抽屉、相似样本和句式统计

### 后续与指导书 / 记录生成的结合方向

当前阶段只完成历史样本入库与查询，不自动写回现有测评记录生成主链路。

后续可以在不破坏当前流程的前提下逐步接入：

1. 用历史样本辅助记录写法参考
2. 用相似记录结果辅助复核判断
3. 与指导书知识库做联合检索与推荐

## 指导书与历史人工记录关联说明

当前阶段新增了 Guidance ↔ History 的独立关联层，用于把指导书章节与历史人工测评记录建立可重算、可持久化的规则链接，为后续生成更接近人工风格的测评记录提供样本参考。

当前阶段能力边界：

- 不引入 Elasticsearch、向量库或大模型
- 不改动现有 OCR、字段抽取、记录生成、复核、导出主链路
- 仅基于规则和文本重合度做第一版关联

### 关联规则

当前匹配逻辑会综合以下因素计算 `match_score` 并产出结构化 `match_reason`：

- `control_point` 与指导书章节标题 / 路径 / 核查要点 / 正文的命中或部分重合
- `evaluation_item` / `record_text` 与指导书记录建议 / 证据要求 / 正文的命中或部分重合
- `keywords_json` 的重合
- `asset_type` 的命中

关联结果会持久化到 `guidance_history_links`，因此前端查看详情时可以直接读取已有样本，而不是每次重新全量计算。

### 查询方式

后端 API：

- `POST /api/v1/guidance/{guidance_id}/link-history`：重算某个指导书章节的历史记录关联并持久化结果
- `GET /api/v1/guidance/{guidance_id}/history-records`：获取某个指导书章节已关联的历史记录，支持 `compliance_status` 筛选
- `GET /api/v1/history/{history_id}/guidance-items`：从某条历史记录反查关联到的指导书章节

前端页面：

- 进入“指导书管理”页面
- 打开某个章节详情抽屉
- 查看“相似历史记录”表格
- 按“符合情况”筛选关联结果
- 点击“刷新关联”重新计算该章节的样本链接

### 后续与记录生成的结合方向

当前阶段只完成“指导书章节 ↔ 历史人工样本”的关联沉淀，不直接改写现有生成链路。

后续可以在不破坏当前流程的前提下逐步接入：

1. 在记录生成时按 `guidance_id` 读取高分历史样本
2. 用历史人工写法样本增强记录文风参考
3. 在复核阶段展示章节依据与历史写法的联合参考

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

如果只验证 OCR 链路，可执行：

```bash
cd backend
source .venv/bin/activate
pytest -q tests/test_evidences_api.py tests/services/test_paddle_adapter.py
```

测试至少覆盖：

- 项目管理
- 证据上传
- OCR
- 字段抽取
- 记录生成
- 导出
- 指导书入库与查询
- 历史人工测评记录入库与查询
- 指导书与历史人工记录关联

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
7. 已完成指导书知识库第一阶段闭环：
   - 固定读取 `md/指导书.md`
   - 支持空文件检测与友好提示
   - 支持章节导入、列表查询、关键词搜索与章节详情展示
8. 已完成历史人工测评记录库第一阶段闭环：
   - 支持 `.xlsx` 导入、筛选、搜索、相似记录与句式统计
   - 支持详情抽屉查看结构化历史样本
9. 已完成指导书与历史人工记录关联第一阶段闭环：
   - 支持 guidance 章节触发 link-history 重算
   - 支持 guidance 详情查看相似历史记录并按符合情况筛选
   - 支持 history 记录反查 guidance 章节

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
   - 进入“指导书管理”页面
   - 检查 `md/指导书.md` 路径状态
   - 执行一键导入、关键词搜索和章节详情查看
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
