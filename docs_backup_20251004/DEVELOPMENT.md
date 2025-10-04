# 五好伴学开发工作流指南 (DEVELOPMENT)

Last Updated: 2025-09-29
适用范围：后端 0.1.x 开发分支

---

## 1. 文档定位

本文件面向“日常参与开发/维护”的工程师，聚焦：
- 环境安装与运行
- 代码与分支规范
- 依赖、配置、脚本、测试、发布前检查
- 与其它文档的引用关系

不包含系统分层/架构原理（详见 `ARCHITECTURE.md`），不展开测试细节（详见 `TESTING.md`），不描述部署策略（详见 `DEPLOYMENT.md`）。

---

## 2. 开发目标与原则

| 维度 | 原则 | 说明 |
|------|------|------|
| 可读性 | 单一职责 + 清晰命名 | 函数不超过 60 行；复杂逻辑拆分 |
| 类型安全 | 全量类型注解 | mypy 通过视为门槛 |
| 可维护 | 明确模块边界 | Service 不直接操作 ORM 模型字段写入 |
| 一致性 | 统一响应与错误模型 | 避免端点各自发明格式 |
| 可诊断 | 结构化日志与错误上下文 | 避免吞异常 |
| 渐进迭代 | 小步提交，可回滚 | 禁止超大跨域 PR |
| 安全意识 | 不泄露敏感信息 | 控制日志 / 配置加载顺序 |
| 性能意识 | 先正确→再优化 | 有指标支撑才做重构 |

---

## 3. 环境要求

| 类别 | 要求 | 备注 |
|------|------|------|
| 操作系统 | macOS / Linux (推荐) | Windows 需适配脚本 |
| Python | ≥ 3.11 | 使用 `uv` 管理虚拟环境与依赖 |
| Node.js | ≥ 18（如需前端联调） | 使用 nvm 管理 |
| 数据库 | PostgreSQL 14+（生产） / SQLite（开发） | 通过配置切换 |
| Redis | 6+（限流 / 预留缓存） | 可选（某些功能可降级） |
| 包管理 | uv (Python) / npm 或 pnpm | 推荐统一 npm |
| 监控工具 | 可选：Docker + Prometheus | 规划阶段 |

---

## 4. 初次克隆与快速启动

```bash
git clone <repo>
cd wuhao-tutor

# 安装 Python 依赖
uv sync

# 准备环境变量
cp .env.example .env
# 或使用脚本（将来）
# python scripts/env_manager.py init
# python scripts/env_manager.py create development

# 运行诊断（模块导入/数据库/配置）
uv run python scripts/diagnose.py

# 启动应用
uv run uvicorn src.main:app --reload

# 访问 Swagger
open http://localhost:8000/docs
```

---

## 5. 目录快速参考（精简版）

| 目录 | 内容 |
|------|------|
| `src/api/` | 路由与端点 |
| `src/schemas/` | Pydantic Schema |
| `src/services/` | 业务组合逻辑 |
| `src/repositories/` | 数据访问抽象 |
| `src/core/` | 配置 / 数据库 / 监控 / 性能 / 安全 |
| `scripts/` | 环境、部署、数据库、监控等脚本 |
| `tests/` | 测试代码 |
| `frontend/` | 前端项目 |
| `docs/` | 文档体系 |

详见：`ARCHITECTURE.md`

---

## 6. 环境变量与配置

- 基础配置：`.env`（开发） / `.env.prod`（生产）等
- 管理脚本（规划/已部分实现）：`scripts/env_manager.py`

最小化示例：
```
ENVIRONMENT=development
DEBUG=true
SQLALCHEMY_DATABASE_URI=sqlite+aiosqlite:///./wuhao_tutor_dev.db
```

AI 功能需：
```
BAILIAN_API_KEY=sk-xxx
BAILIAN_APPLICATION_ID=app-xxx
```

加载策略：
1. `ENVIRONMENT=testing` 时可绕过部分外部依赖
2. 不在代码中使用 `os.getenv` 直接散布，统一通过 `get_settings()`
3. 生产禁用 DEBUG/自适应跨域

---

## 7. 依赖管理

| 操作 | 命令 | 说明 |
|------|------|------|
| 安装 | `uv sync` | 基于 `pyproject.toml` 及锁文件 |
| 添加依赖 | `uv add <package>` | 自动更新锁 |
| 移除依赖 | `uv remove <package>` | 清理引用后执行 |
| 查看 | `uv pip list` | |
| 升级锁 | `uv lock` | 锁文件重建（需审阅差异） |

约束：
- 优先使用标准库
- 引入新三方包需在 PR 描述说明：用途 / 替代方案 / 安全性
- 严禁加入未使用依赖（定期回收）

---

## 8. 运行模式

| 模式 | 命令 | 用途 |
|------|------|------|
| 开发（热重载） | `uv run uvicorn src.main:app --reload` | 普通开发 |
| 诊断 | `uv run python scripts/diagnose.py` | 排查依赖/结构问题 |
| 数据库初始化 | `uv run python scripts/init_database.py` | PostgreSQL 场景 |
| 数据库管理统一入口 | `uv run python scripts/manage_db.py --help` | 初始化 / 备份 / 迁移 |
| 性能监控脚本 | `uv run python scripts/performance_monitor.py status` | 指标查看 |
| 部署预检 | `uv run python scripts/deploy.py check` | 生产前 |

---

## 9. 常用开发任务

| 任务 | 命令 | 备注 |
|------|------|------|
| 格式化 | `uv run black src/` | 自动 88 宽度 |
| import 排序 | `uv run isort src/` | 与 Black 兼容配置 |
| 类型检查 | `uv run mypy src/` | 必须 0 error |
| 单元测试 | `uv run pytest -q` | 快速验证 |
| 全量测试 | `uv run pytest --maxfail=1 --disable-warnings -q` | CI 模式 |
| 覆盖率（规划） | `uv run pytest --cov=src` | 需添加插件 |
| 性能基准（轻量） | `uv run pytest tests/performance -k basic` | 控制时间 |
| API 集成测试 | `uv run pytest tests/integration` | 需本地服务 |
| 运行单文件调试 | `uv run python -m src.some.module` | 避免全局副作用 |

---

## 10. Git 分支与提交规范

| 类型 | 用途示例 |
|------|----------|
| `main` | 稳定分支（CI 通过 / 可部署） |
| `develop` (可选) | 若存在多人协同，则引入 |
| `feature/<name>` | 新功能 |
| `fix/<name>` | 缺陷修复 |
| `refactor/<name>` | 重构（无新功能） |
| `docs/<name>` | 文档相关 |
| `chore/<name>` | 构建/脚本/依赖调整 |
| `test/<name>` | 测试用例增强 |

提交信息格式：
```
<type>: <简述>  (英文或中文；保持一致)
```
示例：
```
feat: 增加作业批改评分细则扩展点
fix: 修复限流中间件对测试环境误触发
refactor: 拆分 monitoring 收集器结构
docs: 拆分 API 文档为模块化结构
```

---

## 11. 代码风格与结构约定

| 约束 | 说明 |
|------|------|
| 函数长度 | 控制 ≤ 60 行；超出必须拆分或标明合理性 |
| 类职责 | 单一上下文；不混入非核心职责方法 |
| 异常处理 | 精确捕获（不要裸 except） |
| 数据流 | API → Service → Repository；避免跨层绕行 |
| 日志 | 使用封装 logger（后续统一 logger 工具） |
| 返回值 | API 层统一包装响应模型（避免裸 dict） |
| Schema | 输入/输出分离：`Create` / `Update` / `Out` |
| 命名 | `snake_case` / 类 PascalCase / 常量 UPPER_CASE |
| 兼容临时代码 | 标注 `# TODO(date|owner): 描述` 并创建 Issue |
| 废弃 | 标注 `# DEPRECATED(日期): 替代方案` 并计划移除 |

---

## 12. 异常与错误处理规范（缩略）

| 场景 | 做法 | 禁止 |
|------|------|------|
| 输入校验失败 | 依赖 Pydantic，返回 422 | 手工拼接不一致结构 |
| 业务错误 | 自定义异常 → 统一异常处理器转换 | 在深层打印+吞掉 |
| 授权失败 | 返回 401/403 | 返回 200 + error message |
| 限流 | 标准 429 + Retry-After | 自定义非标准状态码 |
| 系统内部错误 | 500 + 通用提示 | 暴露堆栈到响应 |

错误结构：
```
{
  "success": false,
  "error": {
    "code": "RESOURCE_NOT_FOUND",
    "message": "资源不存在",
    "details": { ... 可选 ... }
  }
}
```
成功结构：
```
{ "success": true, "data": {...}, "message": "OK" }
```
详见：`api/overview.md`（迁移后）

---

## 13. 日志策略（初版）

| 类别 | 内容 | 级别建议 |
|------|------|----------|
| 启动信息 | 配置概要（脱敏） | INFO |
| 请求处理（可选） | 路径/耗时/状态码 | INFO/DEBUG |
| 性能告警 | 慢查询 / p95 超阈值 | WARNING |
| 业务预警 | 外部服务超时 / 降级 | WARNING |
| 异常 | 堆栈 + 上下文 | ERROR |
| 安全相关 | 认证失败次数（聚合） | INFO（后续可分类） |

后续计划：
- 结构化 JSON 日志
- 关联请求 ID
- 可选分发到集中日志（ELK / Loki）

---

## 14. 数据库与迁移

| 操作 | 命令 | 说明 |
|------|------|------|
| 初始化（PostgreSQL） | `uv run python scripts/init_database.py` | 存在即跳过创建 |
| 创建迁移 | `alembic revision --autogenerate -m "desc"` | 确认 diff 再提交 |
| 应用迁移 | `alembic upgrade head` | |
| 回滚 | `alembic downgrade -1` | 谨慎操作 |
| 统一管理 | `uv run python scripts/manage_db.py migrate` | 脚本封装 |
| 备份 | `uv run python scripts/db_backup.py create` | 生产使用 cron/调度 |
| 恢复 | `uv run python scripts/db_backup.py restore <file>` | 需确认环境 |

迁移合规：
- 不直接手写危险 DDL（谨慎 DROP）
- 复杂变更分多步（添加列 → 回填 → 约束）
- 指定默认值而不是写入层处理模拟

---

## 15. 数据访问层与缓存（规划）

目前：
- `BaseRepository`：通用 CRUD（异步）
- `LearningRepository`：复杂统计查询
- 查询缓存结构预留：`core/performance.py`

规划：
- 添加可装饰缓存（语义：读繁 / 写少）
- 热点维度：用户最近会话、题目统计
- 缓存一致性策略文档化

避免：
- 在 Service 层自行写复杂 SQL，可迁移到 Repository
- 直接通过 Session 在 Service 内执行散乱查询

---

## 16. 性能与监控（开发期关注）

| 项 | 检查点 |
|----|--------|
| 请求耗时 | 查看 `/api/v1/health/performance` |
| 限流状态 | `/api/v1/health/rate-limits` |
| 指标聚合 | `/api/v1/health/metrics` |
| 慢查询 | 日志 or 性能模块内部缓存 |
| 端点分位 | p95/p99 需监控 |
| 调优节奏 | 优先选热点端点（调用次数高 + 延迟高） |

---

## 17. 安全实践（开发态最小要求）

| 类别 | 事项 |
|------|------|
| 配置 | 不提交真实密钥；使用示例/模板 |
| 调试 | 禁止在日志中打印 token / 密钥 |
| CORS | 除非调试，不放开 `*`（生产严格白名单） |
| 依赖 | 新增前查已有功能是否覆盖 |
| AI 调用 | 加超时 / 失败重试上限 |
| 限流 | 开发可放宽；生产按策略表执行 |
| 文件上传 | 验证后缀/大小（后续加 MIME 深检） |

---

## 18. API 设计约束

| 规则 | 说明 |
|------|------|
| 前缀 | `/api/v1` |
| 命名 | 资源名复数（/homework /sessions） |
| 动作 | 纯查询 GET；副作用 POST；更新 PUT/PATCH；删除 DELETE |
| 状态码 | 遵循 HTTP 语义；错误不滥用 200 |
| 分页 | 查询参数：`?limit=20&offset=0`（后续可扩展 cursor） |
| 幂等 | PUT/PATCH 需保证语义幂等 |
| 文件上传 | Multipart；返回存储 ID 与访问路径 |
| AI 交互 | 封装于 Service；端点不直连外部 |

---

## 19. PR / Code Review 关注点清单

| 检查项 | 说明 |
|--------|------|
| 逻辑清晰 | 单一职责是否满足 |
| 命名语义 | 避免缩写/误导 |
| Schema 严格 | 输入输出明确，不暴露内部字段 |
| 异常处理 | 是否丢失上下文 / 误用裸 except |
| 日志 | 是否过量 / 是否泄露隐私 |
| 性能隐患 | 循环中数据库调用、N+1 查询 |
| 安全 | 没有调试代码残留 / 未开放危险端点 |
| 测试 | 是否有最小用例，核心分支覆盖 |
| 文档 | 是否需要更新相关文档链接 |
| 依赖 | 新增是否必要且描述充分 |

---

## 20. 提交前本地检查 (Pre-flight Checklist)

```bash
uv run black src/
uv run isort src/
uv run mypy src/
uv run pytest -q
uv run python scripts/diagnose.py
# 若涉及 DB：
alembic upgrade head
# 若新增端点：
# - 更新 api/endpoints.md (迁移后)
```

失败项请在本地解决后再发起 PR。

---

## 21. 贡献流程（标准化）

| 步骤 | 行为 | 输出 |
|------|------|------|
| 1 | 创建分支 | `feature/<feature-name>` |
| 2 | 设计评估 | 必要时附简要说明/草图/Issue 引用 |
| 3 | 开发实现 | 包含必要测试 |
| 4 | 本地验证 | 通过 Pre-flight Checklist |
| 5 | 提交 PR | 标题分类 + 描述变更与影响范围 |
| 6 | 代码评审 | 补充说明 / 调整 |
| 7 | 合并 | squash 或保持清晰提交历史 |
| 8 | 文档更新 | 对应文档补充 |
| 9 | 回归测试 | 集成测试通过 |
| 10 | 标记版本（必要时） | 更新 CHANGELOG |

---

## 22. 常见问题 (FAQ 简版)

| 问题 | 解决路径 |
|------|----------|
| 模块导入失败 | 运行诊断脚本，检查 `PYTHONPATH` |
| 配置不生效 | 确认 `.env` 是否加载；调试打印 settings |
| 数据库连接失败 | 检查 DSN / 权限 / 服务是否启动 |
| 限流误触发 | 测试环境是否关闭限流校验路径 |
| 性能指标不更新 | 检查监控中间件是否注册、路径是否匹配 |
| Pydantic 报字段错误 | 确认字段别名 / 校验器 / schema 是否同步 |
| Alembic 没检测到变更 | 确保模型导入发生（未被懒加载优化掉） |
| 循环导入 | 把类型注解转到 `if TYPE_CHECKING` 块 |

更深入参见 `TROUBLESHOOTING.md`

---

## 23. 后续待补充（Roadmap for This Document）

| 项 | 状态 |
|----|------|
| 覆盖率工具集成示例 | 待添加 |
| 缓存策略调用示例 | 规划 |
| 生成型任务脚手架示例 | 规划 |
| pre-commit 钩子配置 | 规划 |
| API Mock/契约测试指引 | 规划 |
| CLI 小工具清单 | 规划 |

---

## 24. 相关文档引用导航

| 主题 | 去向 |
|------|------|
| 架构与分层 | `ARCHITECTURE.md` |
| API 模型与错误码 | `api/overview.md` / `api/errors.md` |
| 数据访问策略 | `DATA-ACCESS.md` |
| 学情指标规划 | （后续）`LEARNING-ANALYTICS.md` (规划) |
| 部署与回滚 | `DEPLOYMENT.md` |
| 性能与指标 | `OBSERVABILITY.md` |
| 安全策略 | `SECURITY.md` |
| 术语与统一词表 | `GLOSSARY.md` |
| 版本与状态 | `STATUS.md` / `CHANGELOG.md` |

---

## 25. 反馈

如发现：
- 本指南过时
- 某章节缺实际可执行价值
- 存在与其他文档重复/冲突

请：
1. 创建 Issue（标签：`docs` + `development`）
2. 或提交 PR（附上：变更原因 / 影响范围 / 是否需团队同步）

---

_（END）_
