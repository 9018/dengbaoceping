# 旧仓库资产迁移实施方案

## 1. 目标与边界

本方案用于把旧仓库遗留的运行时资产与知识资产平滑纳入当前新主链路，保证：

- 新主链路运行时目录以 `backend/` 下目录为唯一事实来源。
- 旧目录先盘点、再复制、后切换，不直接覆盖、不直接删除。
- 切换后保留 `legacy/` 归档区，支持审计、回看与回滚。
- 旧 `rules/`、`templates/` 只作为知识输入，不再作为运行时加载入口。

当前代码事实：

- `backend/app/core/config.py:21` 定义主链路运行时目录为 `backend/uploads`、`backend/exports`、`backend/snapshots`
- `backend/app/core/database.py:46` 在启动时自动创建以上目录
- `backend/app/services/rule_loader.py:12` 定义主链路规则目录为 `backend/app/rules`

## 2. 目录职责与调整建议

### 2.1 新主链路保留为唯一事实来源

以下目录继续作为主链路，不迁回旧结构：

- `backend/uploads/`
- `backend/exports/`
- `backend/snapshots/`
- `backend/app/rules/`
- `frontend/`
- `backend/app/`

### 2.2 旧目录处置建议

| 旧目录 | 处理方式 | 说明 |
|---|---|---|
| `uploads/` | 迁入 `legacy/runtime/uploads/`，根目录改为到 `backend/uploads/` 的兼容入口 | 旧历史文件保留，主写入切到 backend |
| `exports/` | 迁入 `legacy/runtime/exports/`，根目录改为到 `backend/exports/` 的兼容入口 | 避免旧脚本继续写 root exports |
| `snapshots/` | 迁入 `legacy/runtime/snapshots/`，根目录改为到 `backend/snapshots/` 的兼容入口 | 保留历史快照 |
| `rules/` | 迁入 `legacy/knowledge/rules/` | 只做规则设计参考，不再直连运行时 |
| `templates/` | 迁入 `legacy/knowledge/templates/` | 只做模板知识沉淀 |
| 旧 Docker 经验/脚本 | 迁入 `legacy/deploy/` | 只保留经验，不作为默认部署入口 |

## 3. 迁移原则

1. **复制优先，不覆盖**：从旧目录向新目录同步时，默认只补齐缺失文件。
2. **先验证，后切换**：在服务仍可正常读取旧数据前，先完成 inventory 与 dry-run。
3. **单一写入口**：切换完成后，所有新增运行时文件统一写入 `backend/`。
4. **旧知识与旧运行时分离**：`legacy/runtime/` 放历史数据，`legacy/knowledge/` 放规则与模板经验。
5. **保留回滚抓手**：切换脚本不删除历史目录，只移动并建立兼容链接。

## 4. 推荐迁移阶段

### Phase 0：盘点

执行：

```bash
python3 scripts/migration/01_inventory_legacy.py
```

目标：

- 盘清 root 旧目录是否存在、文件数、目录大小
- 盘清 `backend/` 当前主链路目录现状
- 输出到 `logs/migration_inventory_*.log`

### Phase 1：复制与补齐

执行：

```bash
python3 scripts/migration/02_sync_runtime_assets.py
```

策略：

- `uploads/` → `backend/uploads/`
- `exports/` → `backend/exports/`
- `snapshots/` → `backend/snapshots/`
- 默认使用 `cp -an`，只复制缺失文件，不覆盖现有主链路文件
- 同时将旧 `rules/`、`templates/` 归档到 `legacy/knowledge/`

### Phase 2：联调与验证

验证项：

1. 启动 backend，确认 `GET /health` 正常
2. 前端上传证据，确认新文件进入 `backend/uploads/`
3. 触发导出，确认结果进入 `backend/exports/`
4. 若有快照链路，确认新快照进入 `backend/snapshots/`
5. 校验旧目录内容尚未丢失

### Phase 3：切换兼容入口

执行：

```bash
python3 scripts/migration/03_cutover_mainline.py
```

策略：

- 将 root 级旧目录移入 `legacy/runtime/`
- 在 root 创建到 `backend/` 的软链接，兼容仍引用旧路径的人工操作或临时脚本
- 切换后仍以 `backend/` 为唯一写入口

### Phase 4：观察期

建议观察 1 个迭代周期：

- 持续观察新增文件是否都进入 `backend/` 对应目录
- 检查是否仍有脚本或人工习惯直接依赖 root 旧物理目录
- 若发现残留依赖，优先改脚本，不回退主链路定义

### Phase 5：必要时回滚

执行：

```bash
python3 scripts/migration/04_rollback_mainline.py
```

策略：

- 删除 root 兼容软链接
- 将 `legacy/runtime/` 中本次切换备份恢复回 root
- 不动 `backend/` 中已经复制出的数据，避免二次损伤

## 5. rules / templates 复用策略

旧 `rules/`、`templates/` 的价值在于经验，不在于路径。建议：

1. 先人工比对旧规则与 `backend/app/rules/*.json`
2. 仅把确认有效的业务规则迁入：
   - `field_rules.json`
   - `evaluation_items.json`
   - `templates.json`
3. 不直接让后端运行时加载 root `rules/` 或 root `templates/`
4. 每次吸收旧知识时，都以 PR 形式更新 `backend/app/rules/`，避免双写

## 6. 不再保留为主链路的旧代码/旧习惯

以下内容不应继续作为默认主链路：

- 任何直接读写 root `uploads/`、`exports/`、`snapshots/` 的新脚本
- 任何假设 root `rules/`、`templates/` 为运行时规则源的逻辑
- 任何绕过 `backend/app/core/config.py` 手写路径的长期方案
- 任何把 legacy 目录重新接入主业务服务的做法

## 7. 推荐目录结构

```text
backend/
  uploads/
  exports/
  snapshots/
  app/
    rules/

legacy/
  runtime/
    uploads/
    exports/
    snapshots/
  knowledge/
    rules/
    templates/
  deploy/
  cutover/
  rollback/

docs/
  migration/
    legacy-assets-migration.md

scripts/
  migration/
    _common.py
    01_inventory_legacy.py
    02_sync_runtime_assets.py
    03_cutover_mainline.py
    04_rollback_mainline.py
```

## 8. 操作 checklist

### 迁移前

- [ ] 确认当前分支工作区干净或已知变更可控
- [ ] 备份当前数据库与关键运行时目录
- [ ] 执行 `python3 scripts/migration/01_inventory_legacy.py`
- [ ] 阅读 inventory 日志，确认旧目录与新目录现状

### 迁移中

- [ ] 执行 `python3 scripts/migration/02_sync_runtime_assets.py`
- [ ] 核对 `backend/uploads/`、`backend/exports/`、`backend/snapshots/` 是否拿到旧数据
- [ ] 启动 backend 并验证健康检查
- [ ] 做一轮上传/OCR/导出链路验证
- [ ] 确认规则主链路仍从 `backend/app/rules/` 读取

### 切换时

- [ ] 执行 `python3 scripts/migration/03_cutover_mainline.py`
- [ ] 确认 root `uploads` / `exports` / `snapshots` 已变为指向 `backend/` 的软链接
- [ ] 确认 legacy 目录中保留了切换前目录

### 切换后观察

- [ ] 检查新增文件均落在 `backend/` 对应目录
- [ ] 检查是否仍有脚本引用旧 root 物理目录
- [ ] 将残留依赖整改为显式使用 `backend/` 目录或配置项

### 回滚时

- [ ] 执行 `python3 scripts/migration/04_rollback_mainline.py`
- [ ] 确认 root 目录实体恢复
- [ ] 重新验证关键链路
- [ ] 记录导致回滚的根因与后续整改项

## 9. 切换与回滚 SOP

### 切换 SOP

1. 停止会持续写入运行时目录的进程
2. 跑 inventory 与 sync
3. 验证 backend 主链路目录可正常服务
4. 执行 cutover 脚本建立兼容链接
5. 重启服务
6. 验证上传、导出、快照链路
7. 进入观察期

### 回滚 SOP

1. 停止服务写入
2. 执行 rollback 脚本恢复 root 目录实体
3. 重启服务或恢复旧操作方式
4. 验证关键业务链路
5. 保留 `backend/` 中同步出的数据用于事后分析，不直接删除
