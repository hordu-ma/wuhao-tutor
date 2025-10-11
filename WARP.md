# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

---

## 项目概述

**五好伴学 (Wuhao Tutor)** - 基于阿里云百炼智能体的 K12 智能学习支持平台

- **核心功能**：智能作业批改 + 个性化学习问答 + 全面学情分析
- **技术栈**：FastAPI + Vue3 + PostgreSQL/SQLite + 阿里云百炼 AI
- **当前版本**：0.4.x (Phase 4 - 智能上下文增强)
- **项目状态**：A- (优秀) - 核心功能完整，MCP+Analytics 全面上线

---

## 快速开始

### 环境要求

- Python 3.11+
- Node.js 18+
- `uv` (Python 包管理器) - **必需**

### 首次启动

```bash
# 1. 环境诊断（首次必运行）
uv run python scripts/diagnose.py

# 2. 安装依赖
uv sync                    # 后端依赖
cd frontend && npm install # 前端依赖

# 3. 配置环境变量
cp .env.dev .env
# 编辑 .env，配置：
# - BAILIAN_API_KEY: 阿里云百炼 API 密钥
# - BAILIAN_APPLICATION_ID: 百炼应用 ID
# - SECRET_KEY: JWT 密钥（可自动生成）

# 4. 初始化数据库
make db-reset
# 默认测试账号: 13800000001 / password123

# 5. 启动开发服务器（前后端同时启动）
./scripts/start-dev.sh

# 访问：
# - 前端: http://localhost:5173
# - 后端 API: http://localhost:8000
# - API 文档: http://localhost:8000/docs
```

---

## 常用开发命令

### 开发服务器

```bash
# 同时启动前后端（推荐）
./scripts/start-dev.sh

# 仅启动后端
make dev

# 分别启动
make dev                  # 后端 (端口 8000)
cd frontend && npm run dev # 前端 (端口 5173)
```

### 数据库管理

```bash
# 重置数据库 + 示例数据
make db-reset

# 生成迁移文件
make db-migrate
# 或: uv run alembic revision --autogenerate -m "描述"

# 应用迁移
make db-upgrade
# 或: uv run alembic upgrade head

# 回滚迁移
make db-downgrade
# 或: uv run alembic downgrade -1

# 备份数据库（PostgreSQL）
make db-backup
```

### 代码质量

```bash
# 运行所有检查（推荐）
make lint

# 格式化代码
make format
# 或: uv run black src/ tests/ --line-length 88

# 类型检查
make type-check
# 或: uv run mypy src/ --ignore-missing-imports
```

### 测试运行

```bash
# 运行所有测试
make test
# 或: uv run pytest tests/ -v

# 运行单元测试
make test-unit
# 或: uv run pytest tests/unit/ -v

# 运行集成测试
make test-integration
# 或: uv run pytest tests/integration/ -v

# 测试覆盖率报告
make test-coverage
# 或: uv run pytest tests/ --cov=src --cov-report=html --cov-report=term-missing

# 运行特定测试文件
uv run pytest tests/unit/test_user_service.py -v

# 运行特定测试用例
uv run pytest tests/unit/test_user_service.py::test_create_user -v

# 显示慢测试
uv run pytest --durations=10
```

### 其他工具

```bash
# 清理临时文件
make clean

# 查看所有可用命令
make help

# 项目状态检查
make status
```

---

## 四层架构设计

项目采用经典四层架构，**严格禁止跨层调用**：

```
┌─────────────────────────────────────────────┐
│  API Layer (api/v1/endpoints/)             │ → HTTP 请求处理
├─────────────────────────────────────────────┤
│  Service Layer (services/)                  │ → 业务逻辑编排
├─────────────────────────────────────────────┤
│  Repository Layer (repositories/)           │ → 数据访问封装
├─────────────────────────────────────────────┤
│  Model Layer (models/)                      │ → ORM 数据模型
└─────────────────────────────────────────────┘

核心基础设施 (core/):
├── config.py       # Pydantic Settings 配置管理
├── database.py     # 异步 SQLAlchemy 2.x
├── security.py     # JWT 认证 + 多维度限流
├── monitoring.py   # 性能监控（请求耗时、慢查询）
└── performance.py  # 查询优化和缓存
```

### 分层职责

| 层 | 目录 | 职责 | 不应做的事 |
|---|------|------|-----------|
| **API 层** | `src/api/v1/endpoints/` | 路由定义、请求验证、调用服务层 | 复杂业务判断、直接数据库操作 |
| **Service 层** | `src/services/` | 业务逻辑编排、事务协调、流程控制 | 直接拼接 SQL、返回 ORM 对象 |
| **Repository 层** | `src/repositories/` | 基于 `BaseRepository[Model]` 的 CRUD 封装 | 包含业务流程逻辑 |
| **Model 层** | `src/models/` | SQLAlchemy ORM 模型定义 | 包含业务逻辑 |

### 示例：正确的调用流程

```python
# ✅ 正确：API → Service → Repository → Model
@router.post("/homework/submit")
async def submit_homework(data: HomeworkSubmitRequest):
    # API 层：请求验证和服务调用
    result = await homework_service.submit_homework(data)
    return DataResponse(success=True, data=result)

# Service 层：业务逻辑编排
class HomeworkService:
    async def submit_homework(self, data):
        # 1. 数据验证和转换
        # 2. 调用 Repository
        homework = await self.homework_repo.create(data)
        # 3. 调用 AI 服务
        correction = await self.bailian_service.correct_homework(homework)
        # 4. 保存结果
        return await self.homework_repo.update(homework.id, correction)

# Repository 层：数据访问封装
class HomeworkRepository(BaseRepository[HomeworkModel]):
    async def create(self, data):
        # 使用泛型 BaseRepository 的 CRUD 方法
        return await super().create(data)

# ❌ 错误：API 直接调用 Repository（跨层调用）
@router.post("/homework/submit")
async def submit_homework(data):
    homework = await homework_repo.create(data)  # ❌ 错误
```

---

## AI 服务集成

### 百炼智能体配置

本项目使用阿里云百炼（Bailian）AI 服务，通过 `BailianService` 统一封装：

- **位置**：`src/services/bailian_service.py`
- **功能**：作业批改 + 学习问答
- **模型**：通义千问（qwen-max）

### 关键环境变量

```bash
# .env 文件配置
BAILIAN_APPLICATION_ID=<你的应用 ID>
BAILIAN_API_KEY=<你的 API 密钥>
BAILIAN_BASE_URL=https://dashscope.aliyuncs.com/api/v1
BAILIAN_TIMEOUT=30
```

### 上下文构建策略（MCP + RAG 混合）

**当前阶段（Phase 4-5）**：使用 **MCP（Model Context Protocol）** 精确查询

```python
# src/services/knowledge_context_builder.py
context = {
    "weak_points": await repo.get_weak_knowledge_points(user_id, top_k=5),
    "recent_errors": await repo.get_recent_errors(user_id, days=7),
    "mastery_scores": await repo.calculate_mastery_scores(user_id),
    "learning_preferences": await repo.analyze_learning_patterns(user_id),
}
```

**未来阶段（Phase 6）**：引入 **RAG（Retrieval-Augmented Generation）** 语义检索

- 集成 PGVector 扩展
- 通义千问 Embedding API
- 相似错题/历史问答语义检索

---

## 开发环境配置

### 数据库配置

- **开发环境**：SQLite (`wuhao_tutor_dev.db`)
- **生产环境**：PostgreSQL RDS

```python
# src/core/config.py
class DevelopmentSettings(Settings):
    SQLALCHEMY_DATABASE_URI = "sqlite+aiosqlite:///./wuhao_tutor_dev.db"

class Settings(BaseSettings):
    SQLALCHEMY_DATABASE_URI: Optional[Union[PostgresDsn, str]] = None
```

### 关键环境变量说明

| 变量名 | 说明 | 默认值 | 必需 |
|--------|------|--------|-----|
| `BAILIAN_API_KEY` | 阿里云百炼 API 密钥 | - | ✅ |
| `BAILIAN_APPLICATION_ID` | 百炼应用 ID | - | ✅ |
| `SECRET_KEY` | JWT 密钥 | 自动生成 | ✅ |
| `ENVIRONMENT` | 运行环境 | development | - |
| `DEBUG` | 调试模式 | false | - |
| `POSTGRES_*` | PostgreSQL 配置 | - | 生产必需 |
| `REDIS_*` | Redis 配置 | - | 可选 |

---

## 测试策略

### 测试分类

```
tests/
├── unit/                    # 单元测试（纯函数、Service、Repository）
│   ├── test_user_service.py
│   ├── test_bailian_service.py
│   └── repositories/
│       └── test_base_repository.py
├── integration/             # 集成测试（API 端点 + 真实 DB）
│   ├── test_api.py
│   └── test_miniprogram_api_integration.py
├── performance/             # 性能测试
│   └── test_load.py
└── conftest.py              # pytest fixtures
```

### 测试配置

```toml
# pyproject.toml
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py", "*_test.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
asyncio_mode = "auto"
markers = [
    "slow: marks tests as slow",
    "integration: marks tests as integration tests",
    "unit: marks tests as unit tests",
]
```

### Mock 策略

对于 AI 服务和外部依赖，使用 Mock 进行单元测试：

```python
# tests/unit/test_bailian_service.py
import pytest
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_correct_homework_success():
    with patch("src.services.bailian_service.httpx.AsyncClient.post") as mock_post:
        mock_post.return_value.json.return_value = {
            "output": {"text": "批改结果..."}
        }
        result = await bailian_service.correct_homework(homework_data)
        assert result["score"] > 0
```

### 测试覆盖率目标

| 模块 | 目标覆盖率 | 说明 |
|------|----------|------|
| `utils/` | ≥ 90% | 纯函数，易测试 |
| `services/` | ≥ 80% | 包括异常分支 |
| `repositories/` | ≥ 80% | CRUD + 错误路径 |
| `api/` | ≥ 75% | 关键端点全测 |
| `core/` | ≥ 70% | 监控、限流核心行为 |

---

## 代码规范

### 类型注解（必需）

```python
# ✅ 正确：完整类型注解
async def get_user(user_id: UUID, db: AsyncSession) -> Optional[UserModel]:
    return await db.get(UserModel, user_id)

# ❌ 错误：缺少类型注解
async def get_user(user_id, db):
    return await db.get(UserModel, user_id)
```

### 异常处理（具体异常类型）

```python
# ✅ 正确：具体异常类型
from src.core.exceptions import UserNotFoundError

async def get_user(user_id: UUID) -> UserModel:
    user = await repo.get(user_id)
    if not user:
        raise UserNotFoundError(f"User {user_id} not found")
    return user

# ❌ 错误：裸 except 或通用 Exception
try:
    user = await repo.get(user_id)
except:  # ❌ 错误
    pass
```

### 异步编程（async/await）

```python
# ✅ 正确：使用 async/await
async def create_homework(data: HomeworkCreate) -> HomeworkModel:
    async with get_db_session() as db:
        homework = await homework_repo.create(data)
        return homework

# ❌ 错误：在异步函数中使用同步调用
async def create_homework(data):
    homework = homework_repo.create_sync(data)  # ❌ 错误
```

### 代码格式化

- **Python**：Black (line-length=88) + isort
- **TypeScript**：Prettier (printWidth=100)

```bash
# 自动格式化
make format

# 或手动
uv run black src/ tests/ --line-length 88
uv run isort src/ tests/ --profile black
```

---

## 重要注意事项

### 1. PostgreSQL UUID 类型匹配

在 PostgreSQL 环境下，**必须严格匹配 UUID 类型**（开发 SQLite 环境下使用 String）：

```python
# ✅ 正确：PostgreSQL UUID 类型
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy import Column, String

class UserModel(BaseModel):
    # 开发环境（SQLite）使用 String，生产环境（PostgreSQL）使用 UUID
    id = Column(String(36), primary_key=True)  # SQLite
    # 或
    id = Column(PG_UUID(as_uuid=True), primary_key=True)  # PostgreSQL

# 外键必须匹配主键类型
user_id = Column(PG_UUID(as_uuid=True), ForeignKey('users.id'))

# ❌ 错误：类型不匹配
user_id = Column(String(36), ForeignKey('users.id'))  # 如果 users.id 是 UUID 类型
```

### 2. 性能监控阈值

```python
# src/core/config.py
SLOW_QUERY_THRESHOLD: float = 1.0  # 慢查询阈值（秒）
MAX_SLOW_QUERIES: int = 100        # 最大慢查询记录数
QUERY_CACHE_TTL: int = 300         # 查询缓存 TTL（秒）
```

### 3. 限流配置

```python
# 开发环境（宽松）
RATE_LIMIT_PER_IP: int = 1000      # 每 IP 每分钟
RATE_LIMIT_PER_USER: int = 500     # 每用户每分钟

# 生产环境（严格）
RATE_LIMIT_PER_IP: int = 100
RATE_LIMIT_PER_USER: int = 50
RATE_LIMIT_AI_SERVICE: int = 20    # AI 服务每分钟
```

### 4. 默认测试账号

```
手机号: 13800000001
密码: password123
```

### 5. 脚本执行

所有 Python 脚本必须使用 `uv run` 前缀：

```bash
# ✅ 正确
uv run python scripts/diagnose.py
uv run alembic upgrade head

# ❌ 错误
python scripts/diagnose.py  # 可能使用系统 Python
```

---

## 常见问题排查

### 后端启动失败

```bash
# 1. 运行环境诊断
uv run python scripts/diagnose.py

# 2. 查看详细错误
uv run uvicorn src.main:app --reload --log-level debug
```

### 数据库连接失败

```bash
# 重置数据库
make db-reset

# 检查配置
cat .env | grep SQLALCHEMY_DATABASE_URI
```

### 前端重复要求登录

```bash
# 清除浏览器缓存（浏览器控制台）
localStorage.clear()
sessionStorage.clear()

# 重新登录
```

### AI 服务调用失败

```bash
# 检查 API Key
cat .env | grep BAILIAN_API_KEY

# 查看日志
tail -f logs/app.log
# 或开发日志
tail -f .dev-pids/backend.log
```

---

## Git 提交规范

```bash
# 格式：类型(范围): 简洁描述
feat(api): 添加学习路径推荐接口
fix(auth): 修复 refresh_token 未保存问题
refactor(learning): 重构学习问答页面为通义千问风格
docs(readme): 更新项目状态和技术栈说明
test(homework): 添加作业批改单元测试
chore(deps): 更新依赖版本
```

**类型说明**：
- `feat`: 新功能
- `fix`: Bug 修复
- `refactor`: 代码重构（不改变功能）
- `docs`: 文档更新
- `test`: 测试相关
- `chore`: 构建/依赖/配置变更

---

## 关键文档

- **[README.md](README.md)** - 项目总览和快速开始
- **[全链条对齐开发补齐计划](docs/development/COMPREHENSIVE_TODO_PLAN.md)** ⭐ - 当前开发任务与路线图
- **[架构设计](docs/architecture/overview.md)** - 系统架构详解
- **[API 文档](docs/api/)** - RESTful API 接口文档
- **[测试指南](docs/guide/testing.md)** - 测试策略与质量保障
- **[开发指南](docs/guide/development.md)** - 开发规范和最佳实践
- **[AI 助手上下文](AI-CONTEXT.md)** - AI 协作必读信息

---

## 项目结构概览

```
wuhao-tutor/
├── src/                      # 后端源码
│   ├── api/v1/endpoints/    # API 路由（按功能分文件）
│   ├── services/            # 业务逻辑（单一职责）
│   ├── repositories/        # 数据访问（BaseRepository 泛型）
│   ├── models/              # ORM 模型（继承 BaseModel）
│   ├── core/                # 核心基础设施
│   │   ├── config.py        # 环境配置
│   │   ├── database.py      # 数据库连接
│   │   ├── security.py      # 认证和限流
│   │   ├── monitoring.py    # 性能监控
│   │   └── performance.py   # 查询优化
│   └── main.py              # FastAPI 应用入口
│
├── frontend/                 # Vue3 前端
│   ├── src/views/           # 页面组件
│   ├── src/stores/          # Pinia 状态管理
│   └── src/api/             # API 封装
│
├── tests/                   # 测试套件
│   ├── unit/                # 单元测试
│   ├── integration/         # 集成测试
│   ├── performance/         # 性能测试
│   └── conftest.py          # pytest fixtures
│
├── scripts/                 # 开发脚本
│   ├── diagnose.py          # 环境诊断
│   ├── start-dev.sh         # 开发服务器启动
│   └── deploy/              # 部署脚本
│
├── alembic/                 # 数据库迁移
│   └── versions/            # 迁移文件
│
├── docs/                    # 文档中心
│   ├── api/                 # API 文档
│   ├── architecture/        # 架构设计
│   ├── guide/               # 开发指南
│   └── operations/          # 运维文档
│
├── pyproject.toml           # 项目配置和依赖
├── Makefile                 # 开发任务自动化
├── .env                     # 环境变量（不提交）
└── WARP.md                  # 本文档
```

---

**最后更新**: 2025-10-11  
**项目版本**: 0.4.x  
**维护者**: Liguo Ma (maliguo@outlook.com)
