# 五好伴学 (Wuhao Tutor)

基于阿里云百炼智能体的 K12 学情与智能学习支持平台

## 🎯 核心定位

聚焦三个闭环功能：

1. 智能作业批改 (Homework Correction)
2. 学习问答互动 (Learning Q&A)
3. 学情分析反馈 (Learning Analytics)

## 🧱 技术栈

| 层   | 主要技术                                                  |
| ---- | --------------------------------------------------------- |
| 后端 | Python 3.11, FastAPI, SQLAlchemy 2 (Async), Pydantic v2   |
| 数据 | PostgreSQL (生产) / SQLite (开发), Redis(限流/缓存规划)   |
| AI   | 阿里云百炼智能体统一封装                                  |
| 前端 | Vue 3 + TypeScript + Vite + Element Plus + Tailwind       |
| 运维 | Docker, docker-compose, Nginx, Prometheus(规划), uv(依赖) |
| 质量 | Pytest, mypy, Black, isort                                |

## 🚀 快速开始（后端）

```bash
git clone <your-repo-url>
cd wuhao-tutor
uv sync
cp .env.example .env
uv run python scripts/diagnose.py
uv run uvicorn src.main:app --reload
# 浏览 http://localhost:8000/docs
```

最小必需环境变量（开发）：

```bash
ENVIRONMENT=development
DEBUG=true
SQLALCHEMY_DATABASE_URI=sqlite+aiosqlite:///./wuhao_tutor_dev.db
```

启用 AI 功能（可选）：

```bash
BAILIAN_API_KEY=sk-your-key
BAILIAN_APPLICATION_ID=app-your-id
```

## 📂 目录速览

```
wuhao-tutor/
├── src/                # 应用源代码
│   ├── api/            # 路由与端点
│   ├── core/           # 配置 / 安全 / 监控 / 性能
│   ├── models/         # ORM 模型
│   ├── repositories/   # 数据访问层 (Base + 业务仓储)
│   ├── schemas/        # Pydantic 数据模型
│   ├── services/       # 业务组合 & AI 封装
│   └── utils/          # 工具函数
├── frontend/           # 前端项目
├── scripts/            # 初始化 / 迁移 / 运维脚本
├── docs/               # 重构后的结构化文档
├── tests/              # 测试代码
└── alembic/            # 数据库迁移
```

更多详见：`docs/ARCHITECTURE.md`

## 🔐 安全与限流（摘要）

- 多维限流：IP / 用户 / AI 服务 / 登录尝试
- 安全头：CSP, HSTS(生产), X-Frame-Options, Permissions-Policy
- 统一错误结构：`{ success, data?, error? }`
- 不在日志输出敏感凭证

详情：`docs/SECURITY.md`

## 📊 可观测性（摘要）

可用端点：

- `/health` / `/health/live` / `/health/ready`
- `/api/v1/health/performance`
- `/api/v1/health/rate-limits`
- `/api/v1/health/metrics`

规划：Prometheus `/metrics`、Trace-ID、AI tokens 成本统计
详情：`docs/OBSERVABILITY.md`

## 🧪 测试

```bash
# 单元 & 集成
uv run pytest -q

# 类型检查
uv run mypy src/

# 格式化
uv run black src/ && uv run isort src/
```

测试策略：`docs/TESTING.md`

## 📚 API

运行后访问：

- 文档：`/docs` (Swagger)
- ReDoc：`/redoc`

文档拆分：

- 总览：`docs/api/overview.md`
- 端点：`docs/api/endpoints.md`
- 数据模型：`docs/api/models.md`
- 错误码：`docs/api/errors.md`
- SDK 示例：`docs/api/sdk-python.md` / `docs/api/sdk-js.md`

### 响应示例

```json
{
    "success": true,
    "data": { "id": "abc123", "name": "example" },
    "message": "OK"
}
```

失败：

```json
{
    "success": false,
    "error": { "code": "RESOURCE_NOT_FOUND", "message": "资源不存在" }
}
```

## 🗂 文档导航

| 主题             | 文件                         |
| ---------------- | ---------------------------- |
| 项目状态与里程碑 | docs/STATUS.md               |
| 架构分层说明     | docs/ARCHITECTURE.md         |
| 开发工作流       | docs/DEVELOPMENT.md          |
| 数据访问与仓储   | docs/DATA-ACCESS.md          |
| 部署与运维       | docs/DEPLOYMENT.md (待补)    |
| 监控与指标       | docs/OBSERVABILITY.md        |
| 安全基线         | docs/SECURITY.md             |
| 数据迁移         | docs/MIGRATION.md            |
| 前后端协作       | docs/FRONTEND-INTEGRATION.md |
| 术语表           | docs/GLOSSARY.md             |

## 🛠 常用脚本

| 目的                   | 命令 (示例)                                           |
| ---------------------- | ----------------------------------------------------- |
| 诊断环境               | `uv run python scripts/diagnose.py`                   |
| 初始化数据库           | `uv run python scripts/init_database.py`              |
| 统一管理 (迁移/备份等) | `uv run python scripts/manage_db.py --help`           |
| 性能监控工具           | `uv run python scripts/performance_monitor.py status` |
| 环境变量模板管理       | `python scripts/env_manager.py`                       |
| 部署管理               | `python scripts/deploy.py`                            |

## 🧭 路线图（摘录）

| 版本阶段 | 重点                            |
| -------- | ------------------------------- |
| 0.1.x    | 功能骨架 + 文档重构             |
| 0.2.x    | 学情分析初版 + 覆盖率基线       |
| 0.3.x    | 监控闭环（Prometheus / Trace）  |
| 0.4.x    | 缓存与性能优化                  |
| 1.0.0    | 稳定发布（冻结 API / 完整基线） |

详情：`docs/STATUS.md`

## 🤝 贡献

1. Fork / Clone
2. 新建分支：`feature/<name>` / `fix/<name>`
3. 提交信息前缀：`feat|fix|docs|refactor|test|chore`
4. 确保：类型检查 0 错误，测试通过，格式化完成
5. 更新相关文档（必要时）
6. 发起 PR（描述变更、影响、回滚方式）

## 🔒 许可证

MIT (见 `LICENSE`)

## 📬 联系

- 维护者: Liguo Ma
- 邮箱: maliguo@outlook.com
- （规划）GitHub Issues：用于反馈与跟踪

## 🗓 元信息

Last Updated: 2025-09-29
当前状态：后端核心完成度 ~90%，学情分析/监控增强迭代中

---

_本 README 精简说明，深度信息请参见 docs 目录。_
