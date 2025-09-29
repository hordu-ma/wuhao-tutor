# 五好伴学文档索引 (Documentation Hub)

本目录提供项目的结构化文档入口，聚焦“清晰、可维护、单一职责”。所有文档均为中文版本。
若需英文版，可在未来添加 `docs/en/` 结构。

---

## 🗂 文档结构总览

| 分类             | 文件                      | 说明                             |
| ---------------- | ------------------------- | -------------------------------- |
| 项目总览         | `README.md` (项目根)      | 对外首要入口（被精简）           |
| 状态与版本       | `STATUS.md`               | 项目阶段、完成度、里程碑         |
| 变更记录         | `CHANGELOG.md`            | 语义化版本历史（待初始化）       |
| 架构             | `ARCHITECTURE.md`         | 系统分层、技术栈、关键流程       |
| 开发工作流       | `DEVELOPMENT.md`          | 环境、依赖、运行、提交流程、规范 |
| 测试策略         | `TESTING.md`              | 单元 / 集成 / 性能 / 验收策略    |
| 部署与运维       | `DEPLOYMENT.md`           | 多环境、Docker、启动、回滚       |
| 安全与合规       | `SECURITY.md`             | 安全头、限流、密钥、风险控制     |
| 监控与观测       | `OBSERVABILITY.md`        | 指标、限流状态、慢查询、缓存命中 |
| 数据访问         | `DATA-ACCESS.md`          | 仓储层抽象、与缓存/监控协同      |
| 术语表           | `GLOSSARY.md`             | 统一业务与技术术语               |
| 前后端协作       | `FRONTEND-INTEGRATION.md` | 接口契约、错误约定、节流策略     |
| 数据迁移         | `MIGRATION.md`            | Alembic / 版本迁移 / 回滚        |
| API 文档（分拆） | `api/overview.md` 等      | 认证、端点、模型、错误、SDK      |
| 历史归档         | `history/`                | 旧阶段总结、废弃设计说明         |

> 说明：原 `docs/task-5.x-summary.md` 系列已归档，不再直接暴露于主导航。仅保留用于回溯。具体归档路径：`docs/history/`，原文件名（如 `task-5.2-summary.md`）保持不变，用于历史追踪与审计。

---

## 🔧 使用建议

1. 新成员阅读顺序：`ARCHITECTURE` → `DEVELOPMENT` → `API/overview` → `DATA-ACCESS` → `TESTING`
2. 运维/部署相关：重点阅读 `DEPLOYMENT`、`SECURITY`、`OBSERVABILITY`
3. 快速定位问题：
    - 启动/环境问题 → 根目录 `TROUBLESHOOTING.md`
    - 性能异常 → `OBSERVABILITY.md`
    - 数据结构或查询策略 → `DATA-ACCESS.md`
4. 增量功能开发：
    - 新增 API → 同步更新 `api/endpoints.md` 与 `api/models.md`
    - 新增领域术语 → 更新 `GLOSSARY.md`
    - 发布版本 → 更新 `CHANGELOG.md` + `STATUS.md`

---

## 📌 统一约定（全局）

| 维度         | 约定                                                               |
| ------------ | ------------------------------------------------------------------ |
| 时间格式     | `YYYY-MM-DD`                                                       |
| 版本格式     | 语义化版本：`MAJOR.MINOR.PATCH`；开发中使用 `0.x`                  |
| 接口前缀     | `/api/v1`                                                          |
| 响应结构     | `{ success: bool, data?: T, error?: { code, message, details? } }` |
| 限流分类     | `per_ip` / `per_user` / `ai_service` / `login`                     |
| 指标命名     | `snake_case`（如：`request_count`, `p95_latency_ms`）              |
| 术语规范     | 统一参见 `GLOSSARY.md`                                             |
| 代码风格     | Python: Black(88)；TS: Prettier(printWidth=100)                    |
| Git 提交前缀 | feat / fix / docs / style / refactor / test / chore                |
| 异常处理     | 不使用裸 `except:`；分类捕获并记录上下文                           |

---

## 🧭 导航索引

### 1. 核心理解

- 系统分层与边界 → `ARCHITECTURE.md`
- 术语、业务域 → `GLOSSARY.md`

### 2. 开发生命周期

- 环境搭建与依赖 → `DEVELOPMENT.md`
- 数据迁移、数据库策略 → `MIGRATION.md`
- 数据访问抽象 → `DATA-ACCESS.md`

### 3. API

- 总览与认证 → `api/overview.md`
- 端点与调用示例 → `api/endpoints.md`
- 数据模型与模式 → `api/models.md`
- 错误与错误码 → `api/errors.md`
- SDK 示例（Python/JS）→ `api/sdk-python.md` / `api/sdk-js.md`

### 4. 质量保障

- 测试矩阵与运行方式 → `TESTING.md`
- 性能与观测指标 → `OBSERVABILITY.md`
- 安全策略与合规基线 → `SECURITY.md`

### 5. 交付与运维

- 部署矩阵、分环境策略 → `DEPLOYMENT.md`
- 监控与巡检 → `OBSERVABILITY.md`
- 发布与版本迭代 → `CHANGELOG.md`
- 里程碑进度 → `STATUS.md`

### 6. 协作与前后端

- 接口契约与错误处理规范 → `FRONTEND-INTEGRATION.md`

---

## 🛡 安全最小清单（快速参考）

| 项       | 要求                                              |
| -------- | ------------------------------------------------- |
| 环境变量 | 不提交敏感值；使用模板管理                        |
| 密钥管理 | 通过脚本生成与轮换（详见 `SECURITY.md`）          |
| CORS     | 白名单配置（生产）                                |
| 安全头   | 强 CSP、HSTS、X-Frame-Options、Permissions-Policy |
| 限流     | 多维：IP / 用户 / 登录 / AI 服务                  |
| 日志     | 不记录敏感明文（token、密码、密钥）               |

---

## 📈 指标与监控入口

| 类别     | 说明             | 入口                                     |
| -------- | ---------------- | ---------------------------------------- |
| 健康检查 | 存活 / 就绪      | `/health` `/health/live` `/health/ready` |
| 性能监控 | 延迟/吞吐/慢端点 | `/api/v1/health/performance`             |
| 限流状态 | 当前策略与计数   | `/api/v1/health/rate-limits`             |
| 聚合指标 | 综合统计         | `/api/v1/health/metrics`                 |
| 数据查询 | 慢查询、缓存命中 | 详见 `OBSERVABILITY.md`                  |

---

## 📜 文档维护策略

| 场景         | 要求                                               |
| ------------ | -------------------------------------------------- |
| 新增模块     | 更新架构图 & `ARCHITECTURE.md`                     |
| 新增 API     | 同步 `api/endpoints.md` + 模型                     |
| 性能调优     | 更新 `OBSERVABILITY.md` → 增加指标说明             |
| 发布版本     | 更新 `CHANGELOG.md` + `STATUS.md`                  |
| 安全策略变更 | 优先更新 `SECURITY.md` 再引用到其他文档            |
| 废弃功能     | 标注 `[DEPRECATED: <日期>]` 并迁移到附录或 history |

---

## 🧪 新成员 30 分钟上手脚本建议

| 步骤 | 操作                                              | 目标             |
| ---- | ------------------------------------------------- | ---------------- |
| 1    | 阅读 `ARCHITECTURE.md`                            | 建立系统心智模型 |
| 2    | `uv sync && uv run uvicorn src.main:app --reload` | 启动后端         |
| 3    | 浏览 Swagger (`/docs`)                            | 熟悉 API 分区    |
| 4    | 运行 `uv run pytest -q`                           | 确认测试通过     |
| 5    | 查看 `/api/v1/health/performance`                 | 校验监控工作     |
| 6    | 阅读 `DATA-ACCESS.md`                             | 理解数据访问约定 |
| 7    | 若做前端：查 `FRONTEND-INTEGRATION.md`            | 建立接口契约共识 |

---

## 🔄 与归档（history）策略

历史阶段任务总结、实验性设计、一次性评估类文档迁入：
`docs/history/`
仅做回溯参考，不再更新，不出现在主导航。引用时加注释：

> （来源：history/…，仅供历史追溯）

---

## 🧩 常见改动标签（建议）

| 标签        | 用途示例            |
| ----------- | ------------------- |
| [ADD]       | 新增文件或大段内容  |
| [UPDATE]    | 更新现有内容        |
| [REVISE]    | 调整结构/表达更清晰 |
| [FIX]       | 修正文档错误        |
| [DEPRECATE] | 标记废弃            |
| [MOVE]      | 文件迁移或重命名    |

---

## ✅ 当前文档重构状态（第一轮完成）

| 文件             | 状态    | 说明                  |
| ---------------- | ------- | --------------------- |
| 本索引           | ✅      | 已完成                |
| DEPLOYMENT.md    | ✅      | Docker 配置已迁移     |
| ARCHITECTURE.md  | ✅      | 包含百炼集成详细信息  |
| DEVELOPMENT.md   | ✅      | 开发环境配置完善      |
| API 拆分         | ✅      | 已拆分为模块化文件    |
| 旧文件清理       | ✅      | dev-guide.md 等已删除 |
| 原 task-5.x 系列 | ✅ 归档 | 已排除主导航          |
| 规范化核对       | ⏳      | 术语与模型统一进行中  |

---

## 📬 反馈与改进

若发现：

- 内容过时
- 链接失效
- 结构不佳
- 术语不一致

请：

1. 新建 Issue（分类：`docs`）
2. 或直接提交 PR（附 `[docs]` 前缀说明范围）

---

_Last Updated: 2025-09-29 (文档骨架初始版本)_
_维护责任人：项目开发团队_
