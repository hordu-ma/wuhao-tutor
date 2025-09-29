# 五好伴学 (Wuhao Tutor) - 开发者上下文指南

> **📋 上下文文档说明**
> 本文档作为新对话窗口的核心上下文参考，包含项目架构、开发环境、工具链使用和约定规范。

---

## 🎯 项目概览

**五好伴学** - 基于阿里云百炼智能体的 K12 学情与智能学习支持平台

### 核心功能闭环

1. **智能作业批改** (Homework Correction)
2. **学习问答互动** (Learning Q&A)
3. **学情分析反馈** (Learning Analytics)

### 当前状态

- 版本：`0.1.0` (后端核心完成度 ~90%)
- 环境：开发阶段，学情分析/监控增强迭代中
- 维护者：Liguo Ma <maliguo@outlook.com>

---

## 🧱 技术栈架构

| 层级          | 技术选型                                                 | 版本要求  |
| ------------- | -------------------------------------------------------- | --------- |
| **后端**      | Python 3.11+, FastAPI, SQLAlchemy 2 (Async), Pydantic v2 | >=3.11    |
| **数据库**    | PostgreSQL 14+ (生产) / SQLite (开发)                    | 14+       |
| **缓存/限流** | Redis 6+ (限流/缓存)                                     | 6+        |
| **AI服务**    | 阿里云百炼智能体统一封装                                 | -         |
| **前端**      | Vue 3 + TypeScript + Vite + Element Plus + Tailwind      | Node 18+  |
| **依赖管理**  | uv (Python), npm/pnpm (Node.js)                          | uv latest |
| **运维**      | Docker, docker-compose, Nginx                            | -         |
| **代码质量**  | Black, isort, mypy, pytest                               | -         |

---

## 🚀 快速启动 (开发环境)

### 环境准备

```bash
# 克隆项目
git clone <repo-url>
cd wuhao-tutor

# Python依赖管理 (使用uv)
uv sync

# 环境变量配置
cp .env.example .env
# 编辑 .env 配置必要参数

# 环境诊断
uv run python scripts/diagnose.py
```

### 启动开发服务

```bash
# 方式1: 使用开发脚本 (推荐)
./scripts/start-dev.sh        # 同时启动前后端
./scripts/status-dev.sh       # 检查服务状态
./scripts/stop-dev.sh         # 停止服务

# 方式2: 使用Makefile
make quick-start              # 完整环境初始化
make dev                      # 启动后端开发服务器
make status                   # 查看项目状态

# 方式3: 直接启动后端
uv run uvicorn src.main:app --reload
```

### 核心端点

- **API文档**: http://localhost:8000/docs (Swagger)
- **健康检查**: http://localhost:8000/health
- **性能指标**: http://localhost:8000/api/v1/health/performance
- **前端**: http://localhost:5173 (如果启
  动)

---

## 📂 项目结构导航

```
wuhao-tutor/
├── src/                    # 🔥 核心应用代码
│   ├── api/               # FastAPI 路由与端点
│   ├── core/              # 配置/安全/监控/性能
│   ├── models/            # SQLAlchemy ORM 模型
│   ├── repositories/      # 数据访问层抽象
│   ├── schemas/           # Pydantic 数据模型
│   ├── services/          # 业务逻辑与AI封装
│   └── utils/             # 工具函数
├── scripts/               # 🛠️ 开发运维脚本
│   ├── start-dev.sh       # 启动开发环境
│   ├── stop-dev.sh        # 停止开发环境
│   ├── status-dev.sh      # 状态检查
│   ├── diagnose.py        # 环境诊断
│   ├── manage_db.py       # 数据库管理
│   └── performance_monitor.py # 性能监控
├── docs/                  # 📚 结构化文档
├── tests/                 # 🧪 测试代码
├── frontend/              # 🎨 前端项目
├── alembic/               # 🗄️ 数据库迁移
├── Makefile              # 📋 任务自动化
└── pyproject.toml        # 📦 项目配置
```

---

## 🛠️ 开发工具链使用

### 依赖管理 (uv)

```bash
uv sync                   # 安装依赖
uv add <package>          # 添加新依赖
uv remove <package>       # 移除依赖
uv run <command>          # 在虚拟环境中执行
```

### 代码质量工具

```bash
# 格式化与检查
make format               # 代码格式化 (Black + isort)
make lint                 # 代码检查 (flake8)
make type-check           # 类型检查 (mypy)
make check-all           # 运行所有检查

# 测试
make test                # 运行所有测试
make test-unit           # 单元测试
make test-coverage       # 测试覆盖率
```

### 数据库管理

```bash
# Alembic 迁移
make db-migrate          # 生成迁移文件
make db-upgrade          # 应用迁移
make db-init             # 初始化数据库

# 脚本管理
uv run python scripts/manage_db.py --help
uv run python scripts/init_database.py
```

---

## 📋 开发约定与规范

### 代码规范

- **函数长度**: ≤60行，超出需拆分
- **类型注解**: 全量类型注解，mypy通过
- **异常处理**: 精确捕获，禁用裸except
- **命名规范**: snake_case变量/函数，PascalCase类，UPPER_CASE常量

### Git提交规范

```
<type>: <简述>

类型: feat|fix|docs|style|refactor|test|chore
示例:
  feat: 增加作业批改评分细则扩展点
  fix: 修复限流中间件对测试环境误触发
  docs: 更新API文档结构
```

### API设计约定

- **前缀**: `/api/v1`
- **响应格式**:
    ```json
    {
      "success": true,
      "data": {...},
      "message": "OK"
    }
    ```
- **错误格式**:
    ```json
    {
        "success": false,
        "error": {
            "code": "RESOURCE_NOT_FOUND",
            "message": "资源不存在"
        }
    }
    ```

---

## ⚙️ 环境配置

### 最小环境变量 (开发)

```env
ENVIRONMENT=development
DEBUG=true
SQLALCHEMY_DATABASE_URI=sqlite+aiosqlite:///./wuhao_tutor_dev.db
```

### AI功能配置 (可选)

```env
BAILIAN_API_KEY=sk-your-key
BAILIAN_APPLICATION_ID=app-your-id
```

### 配置管理脚本

```bash
python scripts/env_manager.py init          # 初始化环境模板
python scripts/env_manager.py create development  # 创建开发配置
```

---

## 🔧 常用开发脚本

| 脚本                                           | 功能             | 使用场景   |
| ---------------------------------------------- | ---------------- | ---------- |
| `./scripts/start-dev.sh`                       | 启动完整开发环境 | 开始开发   |
| `./scripts/stop-dev.sh`                        | 停止开发服务     | 结束工作   |
| `./scripts/status-dev.sh`                      | 检查服务状态     | 状态诊断   |
| `./scripts/restart-dev.sh`                     | 重启开发环境     | 配置更新后 |
| `uv run python scripts/diagnose.py`            | 环境诊断         | 排查问题   |
| `uv run python scripts/manage_db.py`           | 数据库管理       | DB操作     |
| `uv run python scripts/performance_monitor.py` | 性能监控         | 性能分析   |

### 脚本使用示例

```bash
# 完整开发流程
./scripts/start-dev.sh                    # 启动服务
./scripts/status-dev.sh --verbose        # 检查状态
./scripts/stop-dev.sh --clean-logs       # 停止并清理日志

# 数据库操作
uv run python scripts/manage_db.py migrate    # 数据库迁移
uv run python scripts/manage_db.py backup     # 数据库备份
```

---

## 🏗️ 架构分层说明

### 请求流转

```
API Layer (路由)
  ↓
Service Layer (业务逻辑)
  ↓
Repository Layer (数据访问)
  ↓
Model Layer (ORM模型)
```

### 核心模块职责

- **API层** (`src/api/`): HTTP路由、请求验证、响应封装
- **Service层** (`src/services/`): 业务组合逻辑、AI服务封装
- **Repository层** (`src/repositories/`): 数据访问抽象、查询封装
- **Core层** (`src/core/`): 配置管理、安全策略、监控性能

---

## 🔐 安全与限流

### 安全特性

- **多维限流**: IP/用户/AI服务/登录尝试
- **安全头**: CSP, HSTS(生产), X-Frame-Options
- **输入验证**: Pydantic严格校验
- **错误处理**: 统一异常处理，避免信息泄露

### 监控端点

- `/health` - 基础健康检查
- `/api/v1/health/performance` - 性能指标
- `/api/v1/health/rate-limits` - 限流状态
- `/api/v1/health/metrics` - 系统指标

---

## 🧪 测试策略

### 测试命令

```bash
# 快速测试
uv run pytest -q

# 详细测试
uv run pytest tests/ -v

# 覆盖率测试
uv run pytest --cov=src --cov-report=html

# 性能测试
uv run pytest tests/performance -k basic
```

### 测试分类

- **单元测试**: `tests/unit/` - 独立函数/类测试
- **集成测试**: `tests/integration/` - API端到端测试
- **性能测试**: `tests/performance/` - 基准性能测试

---

## 📚 文档导航

| 主题         | 文档路径                | 说明               |
| ------------ | ----------------------- | ------------------ |
| 架构设计     | `docs/ARCHITECTURE.md`  | 系统分层与模块设计 |
| 开发工作流   | `docs/DEVELOPMENT.md`   | 详细开发指南       |
| API文档      | `docs/api/`             | 接口规范与示例     |
| 数据访问     | `docs/DATA-ACCESS.md`   | 数据层设计模式     |
| 安全策略     | `docs/SECURITY.md`      | 安                 |
| 全基线与实践 |
| 性能监控     | `docs/OBSERVABILITY.md` | 监控与指标体系     |
| 部署运维     | `docs/DEPLOYMENT.md`    | 部署策略与流程     |
| 项目状态     | `docs/STATUS.md`        | 版本规划与里程碑   |

---

## 🚨 故障排除快速指南

### 常见问题

| 问题                        | 解决方案                                   |
| --------------------------- | ------------------------------------------ |
| 服务启动失败                | `./scripts/diagnose.py` → 检查环境         |
| 端口被占用                  | `./scripts/stop-dev.sh --force` → 强制清理 |
| 依赖问题                    | `uv sync` → 重新同步依赖                   |
| 数据库连接失败              | 检查 `.env` 中的 `SQLALCHEMY_DATABASE_URI` |
| AI功能异常                  |
| 验证 `BAILIAN_API_KEY` 配置 |
| 类型检查错误                | `uv run mypy src/` → 检查具体错误          |

### 调试工具

```bash
# 查看服务日志
tail -f .dev-pids/backend.log
tail -f .dev-pids/frontend.log

# 检查端口占用
lsof -i :8000
lsof -i :5173

# 性能监控
uv run python scripts/performance_monitor.py status
```

---

## 🎯 提交前检查清单

```bash
# 自动化检查
make pre-commit              # 格式化+检查+测试

# 手动步骤
uv run python scripts/diagnose.py    # 环境诊断
alembic upgrade head                  # 数据库迁移
```

**提交前必须通过**:

- ✅ 代码格式化 (Black + isort)
- ✅ 类型检查 (mypy 0 errors)
- ✅ 基础测试通过
- ✅ 环境诊断无错误

---

## 🔄 版本路线图

| 版本  | 重点                          | 状态      |
| ----- | ----------------------------- | --------- |
| 0.1.x | 功能骨架 + 文档重构           | 🔄 进行中 |
| 0.2.x | 学情分析初版 + 测试覆盖率基线 | 📋 规划   |
| 0.3.x | 监控闭环 (Prometheus/Trace)   | 📋 规划   |
| 0.4.x | 缓存与性能优化                | 📋 规划   |
| 1.0.0 | 稳定发布 (API冻结/完整基线)   | 🎯 目标   |

---

## 🤝 贡献流程

1. **创建分支**: `feature/<name>` / `fix/<name>`
2. **开发实现**: 包含必要测试
3. **本地验证**: 通过提交前检查清单
4. **提交PR**: 描述变更与影响范围
5. **代码评审**: 响应反馈并调整
6. **合并代码**: 保持清晰的提交历史

---

## 📞 支持与联系

- **维护者**: Liguo Ma
- **邮箱**: maliguo@outlook.com
- **文档问题**: 创建 GitHub Issue (标签: `docs`)
- **功能建议**: 提交 Pull Request

---

## 🏷️ 标签与元信息

- **项目类型**: K12教育AI平台
- **开发阶段**: Alpha (0.1.x)
- **技术栈**: Python/FastAPI + Vue3/TypeScript
- **更新时间**: 2024-12-19
- **许可证**: MIT

---

## 💡 快速参考卡片

**新手上手三步骤**:

1. `uv sync` → `cp .env.example .env` → `./scripts/start-dev.sh`
2. 访问 http://localhost:8000/docs 查看API文档
3. 阅读 `docs/DEVELOPMENT.md` 了解详细开发流程

**日常开发循环**:

1. `./scripts/start-dev.sh` (启动)
2. 编码 → 测试 → `make pre-commit` (检查)
3. `./scripts/stop-dev.sh` (结束)

**紧急问题处理**:

1. `./scripts/status-dev.sh --verbose` (诊断)
2. `./scripts/restart-dev.sh` (重启)
3. 查看 `docs/` 相关文档或联系维护者

---

_本README作为上下文指南，详细信息请参见 `docs/` 目录相关文档。_
