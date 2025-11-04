# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

---

## 项目概览

**五好伴学 (Wuhao Tutor)** - 基于阿里云百炼智能体的 K12 智能学习平台

- **技术架构**: FastAPI + Vue3 + PostgreSQL + 阿里云百炼 AI
- **生产环境**: https://www.horsduroot.com
- **核心功能**: AI 驱动的作业问答 + 智能错题手册 + 学情分析

---

## 核心开发命令

### 环境管理

```bash
# 安装依赖（使用 uv 包管理器）
uv sync

# 安装开发依赖
uv sync --extra dev

# 更新依赖
uv sync --upgrade
```

### 开发服务器

```bash
# 启动后端开发服务器
uv run python src/main.py
# 或使用 Makefile
make dev

# 启动后端（自动重载）
make dev-reload

# 启动前端开发服务器（需在 frontend/ 目录）
cd frontend
npm run dev

# 使用一键启动脚本（同时启动前后端）
./scripts/start-dev.sh
```

### 数据库操作

```bash
# 初始化/升级数据库到最新版本
make db-init
# 或直接运行
uv run alembic upgrade head

# 生成新的数据库迁移（在修改模型后）
make db-migrate
# 会提示输入迁移描述

# 回滚一个迁移
make db-downgrade

# 重置数据库（⚠️ 危险操作，会删除所有数据）
make db-reset

# 生成测试数据
make seed-data
```

### 代码质量检查

```bash
# 代码格式化
make format
# 运行: black + isort

# 代码检查
make lint
# 运行: flake8 + black --check + isort --check

# 类型检查
make type-check
# 运行: mypy src/

# 运行所有检查
make check-all
```

### 测试

```bash
# 运行所有测试
make test
# 或直接运行
uv run pytest tests/ -v

# 运行单元测试
make test-unit
uv run pytest tests/unit/ -v

# 运行集成测试
make test-integration
uv run pytest tests/integration/ -v

# 运行测试并生成覆盖率报告
make test-coverage
# 覆盖率报告会生成在 htmlcov/index.html
```

### 前端命令（在 frontend/ 目录下）

```bash
# 开发服务器
npm run dev

# 构建生产版本
npm run build

# 类型检查
npm run type-check

# 代码检查和修复
npm run lint

# 代码格式化
npm run format

# 运行测试
npm run test
```

### 其他有用命令

```bash
# 导出 OpenAPI Schema
make schema

# 查看项目状态
make status

# 清理临时文件和缓存
make clean

# 进入 Python shell
make shell

# 快速开始（安装依赖 + 初始化数据库 + 生成测试数据）
make quick-start
```

---

## 架构设计

### 四层分层架构

项目采用严格的四层架构设计，**必须遵循单向依赖原则**：

```
┌─────────────────────────────────────────────┐
│  API Layer (api/v1/endpoints/)             │ → HTTP 请求处理、参数验证
├─────────────────────────────────────────────┤
│  Service Layer (services/)                  │ → 业务逻辑、事务管理
├─────────────────────────────────────────────┤
│  Repository Layer (repositories/)           │ → 数据访问、复杂查询
├─────────────────────────────────────────────┤
│  Model Layer (models/)                      │ → ORM 数据模型
└─────────────────────────────────────────────┘
```

**关键原则**：
- ❌ **禁止跨层调用**（例如 API 直接调用 Repository）
- ✅ **必须使用类型注解**和 `async/await` 异步模式
- ✅ **Repository 层**：使用 `BaseRepository[Model]` 泛型实现 CRUD
- ✅ **Service 层**：处理业务逻辑、组合多个 Repository、管理事务

### 核心基础设施 (src/core/)

| 模块 | 功能 | 关键特性 |
|------|------|----------|
| `config.py` | 配置管理 | Pydantic Settings v2，环境变量验证，支持多环境配置 |
| `database.py` | 数据库连接 | Async SQLAlchemy 2.x，异步连接池，自动会话管理 |
| `security.py` | 安全限流 | JWT 认证，Token Bucket + Sliding Window 双算法限流 |
| `monitoring.py` | 监控指标 | 自定义指标收集器，支持响应时间/错误率/系统资源 |
| `performance.py` | 性能优化 | N+1 查询检测，慢查询监听（>1s），自动缓存 |
| `exceptions.py` | 异常定义 | 统一异常体系，领域特定异常类型 |
| `logging.py` | 日志管理 | 结构化日志（JSON 格式），便于问题排查 |

### 目录结构

```
wuhao-tutor/
├── src/                    # 后端源码
│   ├── main.py            # FastAPI 应用入口
│   ├── api/               # API 路由
│   │   └── v1/            # API v1 版本
│   │       ├── api.py     # 路由集合
│   │       └── endpoints/ # 端点实现（auth, user, learning, mistakes 等）
│   ├── services/          # 业务逻辑层
│   │   ├── auth_service.py
│   │   ├── bailian_service.py      # 阿里云百炼 AI 集成
│   │   ├── learning_service.py
│   │   ├── mistake_service.py
│   │   ├── analytics_service.py
│   │   ├── knowledge_graph_service.py
│   │   └── algorithms/             # 算法实现（如艾宾浩斯）
│   ├── repositories/      # 数据访问层
│   │   ├── base_repository.py      # 泛型基础 Repository
│   │   ├── learning_repository.py
│   │   ├── mistake_repository.py
│   │   └── analytics_repository.py
│   ├── models/            # SQLAlchemy ORM 模型
│   │   ├── base.py        # 基础模型（UUID 主键，时间戳，软删除）
│   │   ├── user.py
│   │   ├── homework.py
│   │   ├── learning.py
│   │   ├── study.py       # 错题记录
│   │   └── knowledge.py
│   ├── schemas/           # Pydantic 数据验证模型
│   ├── core/              # 核心基础设施（见上文）
│   └── utils/             # 工具函数
│
├── frontend/              # Vue3 Web 前端
│   ├── src/
│   │   ├── views/         # 页面组件
│   │   ├── components/    # 可复用组件
│   │   ├── stores/        # Pinia 状态管理
│   │   ├── router/        # Vue Router
│   │   └── api/           # API 客户端
│   ├── package.json
│   └── vite.config.ts
│
├── miniprogram/           # 微信小程序
│   ├── pages/
│   ├── utils/
│   │   └── request.js     # 网络请求封装
│   └── package.json
│
├── tests/                 # 测试套件
│   ├── unit/              # 单元测试
│   ├── integration/       # 集成测试
│   ├── conftest.py        # pytest 配置和 fixtures
│   └── factories.py       # 测试数据工厂
│
├── scripts/               # 开发自动化脚本
│   ├── start-dev.sh       # 启动开发环境
│   ├── deploy.sh          # 生产部署脚本
│   └── sql/               # SQL 初始化脚本
│
├── alembic/               # 数据库迁移
│   └── versions/          # 迁移文件（按时间排序）
│
├── config/templates/      # 环境变量模板
├── docs/                  # 项目文档
├── pyproject.toml         # Python 项目配置
├── Makefile              # 自动化任务
└── .env                  # 环境变量（不提交到 Git）
```

---

## 关键技术栈和工具

### 后端

- **框架**: FastAPI 0.104+（异步高性能）
- **Python**: 3.11+（要求类型注解）
- **ORM**: SQLAlchemy 2.x（Async）
- **验证**: Pydantic v2
- **数据库**: PostgreSQL 14+（生产）/ SQLite（开发）
- **缓存**: Redis 6+（可选）
- **包管理**: **uv**（快速包管理器，类似 pip 但更快）

### 前端

- **框架**: Vue 3.4+（Composition API）
- **语言**: TypeScript 5.6+
- **UI 库**: Element Plus 2.5+
- **构建工具**: Vite 5+
- **状态管理**: Pinia 2.1+
- **路由**: Vue Router 4.x
- **公式渲染**: KaTeX + Marked

### AI 服务

- **提供商**: 阿里云百炼智能体
- **模型**: 通义千问
- **功能**: 学习问答 + 作业批改
- **特性**: 流式响应、多模态支持（文字+图片）

### 开发工具

- **代码格式化**: Black（line-length=88）
- **代码检查**: Flake8
- **类型检查**: mypy（strict 模式）
- **测试框架**: pytest + pytest-asyncio
- **数据库迁移**: Alembic

---

## 开发约定和最佳实践

### 数据模型设计

所有模型必须继承 `src/models/base.py` 的 `BaseModel`：

```python
from src.models.base import BaseModel

class HomeworkModel(BaseModel):
    __tablename__ = "homework"
    # 自动包含:
    # - UUID 主键 (id)
    # - 时间戳 (created_at, updated_at)
    # - 软删除支持 (deleted_at)
```

**设计原则**：
- 主键统一使用 UUID（避免 ID 猜测攻击）
- 所有表必须有 `created_at` 和 `updated_at`
- 敏感数据删除使用软删除（设置 `deleted_at`）
- 使用 SQLAlchemy 2.x 的 `Mapped[]` 类型注解

### Repository 模式

Repository 层继承 `BaseRepository[Model]` 获得类型安全的 CRUD 操作：

```python
from src.repositories.base_repository import BaseRepository
from src.models.homework import HomeworkModel

class HomeworkRepository(BaseRepository[HomeworkModel]):
    """作业 Repository"""
    
    async def find_by_student_id(
        self, 
        db: AsyncSession, 
        student_id: UUID
    ) -> List[HomeworkModel]:
        """复杂查询放在 Repository，不在 Service"""
        stmt = select(HomeworkModel).where(
            HomeworkModel.student_id == student_id,
            HomeworkModel.deleted_at.is_(None)
        )
        result = await db.execute(stmt)
        return result.scalars().all()
```

**职责划分**：
- ✅ **Repository**: 数据访问、复杂查询、数据转换
- ✅ **Service**: 业务逻辑、多 Repository 组合、事务管理
- ❌ 禁止在 Service 层编写 SQL 或 ORM 查询

### 错误处理

使用具体的异常类型（定义在 `src/core/exceptions.py`）：

```python
from src.core.exceptions import HomeworkNotFoundError

# ✅ 使用领域特定异常
raise HomeworkNotFoundError(f"作业 {homework_id} 不存在")

# ❌ 不要使用通用异常
raise Exception("作业不存在")  # 错误！
```

**异常处理原则**：
- 使用领域特定异常（`*NotFoundError`, `*ValidationError`）
- 所有异常必须继承自 `AppException`
- 异常消息包含必要上下文（ID、用户、操作类型）
- API 层统一转换为 HTTP 状态码

### 异步编程

项目采用**全异步架构**，所有 I/O 操作必须使用 `async/await`：

```python
# ✅ 正确：异步数据库查询
async def get_user(db: AsyncSession, user_id: UUID) -> UserModel:
    result = await db.execute(select(UserModel).where(UserModel.id == user_id))
    return result.scalar_one_or_none()

# ❌ 错误：同步调用会阻塞事件循环
def get_user_sync(db: Session, user_id: UUID) -> UserModel:
    return db.query(UserModel).filter(UserModel.id == user_id).first()
```

### 类型注解

**必须使用完整的类型注解**（mypy strict 模式）：

```python
# ✅ 正确
async def create_mistake(
    self,
    user_id: UUID,
    question_content: str,
    subject: Subject
) -> MistakeModel:
    ...

# ❌ 错误：缺少类型注解
async def create_mistake(self, user_id, question_content, subject):
    ...
```

### 依赖注入

使用 FastAPI 的 `Depends` 机制进行依赖注入：

```python
from fastapi import Depends
from src.core.database import get_db
from src.api.dependencies.auth import get_current_user

@router.post("/mistakes")
async def create_mistake(
    data: MistakeCreate,
    db: AsyncSession = Depends(get_db),           # 数据库会话
    current_user: User = Depends(get_current_user) # 当前用户
):
    ...
```

---

## 数据库操作工作流

### 修改数据模型后的标准流程

1. **修改模型类**（在 `src/models/` 中）
2. **生成迁移文件**：
   ```bash
   make db-migrate
   # 或手动：uv run alembic revision --autogenerate -m "描述"
   ```
3. **检查生成的迁移文件**（在 `alembic/versions/` 中）
4. **应用迁移**：
   ```bash
   make db-init
   # 或手动：uv run alembic upgrade head
   ```
5. **测试回滚**（可选但推荐）：
   ```bash
   uv run alembic downgrade -1
   uv run alembic upgrade head
   ```

### 数据库环境

| 环境 | 数据库 | 连接字符串 |
|------|--------|-----------|
| **Development** | SQLite | `sqlite+aiosqlite:///./wuhao_tutor_dev.db` |
| **Production** | PostgreSQL | 通过环境变量配置 |
| **Testing** | SQLite (内存) | `sqlite+aiosqlite:///:memory:` |

---

## 环境配置

### 环境变量模板

环境变量模板在 `config/templates/` 目录：
- `.env.development` - 开发环境模板
- `.env.production` - 生产环境模板

**关键环境变量**：

```bash
# 应用配置
ENVIRONMENT=development  # development | production | testing
DEBUG=true
SECRET_KEY=your-secret-key-here

# 数据库配置
SQLALCHEMY_DATABASE_URI=sqlite+aiosqlite:///./wuhao_tutor_dev.db
# 生产环境使用 PostgreSQL:
# SQLALCHEMY_DATABASE_URI=postgresql+asyncpg://user:pass@host/db

# 阿里云百炼 AI 配置（必需）
BAILIAN_API_KEY=sk-xxx
BAILIAN_APPLICATION_ID=xxx

# Redis 配置（可选）
REDIS_HOST=localhost
REDIS_PORT=6379

# 文件上传配置
UPLOAD_DIR=./uploads
UPLOAD_MAX_SIZE=10485760  # 10MB
```

### 初始化开发环境

```bash
# 1. 克隆项目
git clone <repository-url>
cd wuhao-tutor

# 2. 复制环境变量模板
cp config/templates/.env.development .env

# 3. 编辑 .env 配置必要的环境变量
# - BAILIAN_API_KEY（阿里云百炼 API Key）
# - SECRET_KEY（JWT 密钥）

# 4. 使用快速开始命令（安装依赖 + 初始化数据库 + 生成测试数据）
make quick-start

# 5. 启动开发服务器
make dev

# 6. （可选）在另一个终端启动前端
cd frontend
npm install
npm run dev
```

---

## 测试策略

### 测试覆盖目标

- **核心模块**: ≥ 80%
- **Service 层**: ≥ 85%
- **Repository 层**: ≥ 90%

### 单元测试

测试位置：`tests/unit/`

```python
import pytest
from uuid import uuid4

@pytest.mark.asyncio
async def test_create_mistake(mistake_service, db_session):
    """测试创建错题记录"""
    result = await mistake_service.create_mistake(
        db=db_session,
        user_id=uuid4(),
        question_content="测试题目",
        subject="math"
    )
    assert result.id is not None
    assert result.subject == "math"
```

### 集成测试

测试位置：`tests/integration/`

```python
async def test_get_mistakes_list(client, auth_headers):
    """测试错题列表接口"""
    response = await client.get(
        "/api/v1/mistakes",
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
```

### 运行特定测试

```bash
# 运行单个测试文件
uv run pytest tests/unit/test_user_service.py -v

# 运行单个测试函数
uv run pytest tests/unit/test_user_service.py::test_create_user -v

# 使用标记运行测试
uv run pytest -m unit  # 只运行单元测试
uv run pytest -m integration  # 只运行集成测试
```

---

## 性能监控和限流

### 自动性能监控

- ✅ **慢查询日志**: 查询超过 **1.0 秒**自动记录
- ✅ **N+1 查询检测**: `performance.py` 监听器自动检测并警告
- ✅ **指标收集**: 中间件自动追踪每个端点的响应时间
- ✅ **系统监控**: CPU、内存、磁盘使用率实时采集

### 限流配置

| 维度 | 限制 | 窗口 | 说明 |
|------|------|------|------|
| IP | 100 请求 | 1 分钟 | 防止 DDoS |
| 用户 | 50 请求 | 1 分钟 | 防止滥用 |
| AI 服务 | 20 请求 | 1 分钟 | 控制成本 |
| 登录端点 | 10 请求 | 1 分钟 | 防暴力破解 |

限流使用 **Token Bucket + Sliding Window** 双算法实现。

### 优化查询性能

使用 `joinedload()` 或 `selectinload()` 避免 N+1 查询：

```python
from sqlalchemy.orm import selectinload

# ✅ 正确：预加载关联数据
stmt = select(HomeworkModel).options(
    selectinload(HomeworkModel.student),
    selectinload(HomeworkModel.mistakes)
).where(HomeworkModel.id == homework_id)

# ❌ 错误：会导致 N+1 查询
homework = await db.get(HomeworkModel, homework_id)
# 后续访问 homework.student 和 homework.mistakes 会触发额外查询
```

---

## AI 服务集成

### 阿里云百炼服务封装

服务入口：`src/services/bailian_service.py`

```python
from src.services.bailian_service import BailianService

# 初始化服务
bailian_service = BailianService()

# 调用 AI 问答（支持流式响应）
async for chunk in bailian_service.chat_stream(
    messages=[
        {"role": "user", "content": "解释一元二次方程"}
    ],
    user_id=user_id
):
    # 处理流式响应
    print(chunk)
```

**最佳实践**：
- ✅ 使用 Service 层封装，不直接调用 HTTP 客户端
- ✅ 配置超时时间（默认 120s）
- ✅ 使用自动重试机制（最多 3 次）
- ✅ 支持流式和非流式两种模式
- ✅ 自动处理多模态输入（文字+图片）

---

## 文件上传和存储

### 本地开发

- **存储路径**: `./uploads/` 目录
- **URL 前缀**: `http://localhost:8000/uploads/`
- **最大文件大小**: 10MB
- **允许格式**: `.jpg`, `.jpeg`, `.png`, `.pdf`, `.webp`

### 生产环境

- **存储**: 阿里云 OSS
- **CDN 加速**: Nginx 反向代理优化
- **环境变量**: `OSS_BUCKET_NAME`, `OSS_ENDPOINT`, `OSS_ACCESS_KEY_ID`, `OSS_ACCESS_KEY_SECRET`

---

## 生产部署

### 一键部署脚本

```bash
# 部署到生产环境（阿里云 ECS）
./scripts/deploy.sh

# 检查生产环境状态
./scripts/check-production.sh

# 查看服务日志
ssh root@121.199.173.244 'journalctl -u wuhao-tutor.service -f'
```

### 生产环境配置

- **服务器**: 阿里云 ECS (121.199.173.244)
- **域名**: horsduroot.com（已配置 SSL）
- **后端部署路径**: `/opt/wuhao-tutor`
- **前端部署路径**: `/var/www/html`
- **服务管理**: systemd (`wuhao-tutor.service`)
- **Web 服务器**: Nginx（反向代理 + 静态文件托管）

**注意事项**：
- 前端在本地构建后同步到服务器
- 微信小程序在本地开发工具中编译上传
- `.env.production` 文件在服务器上，包含敏感配置
- 数据库迁移需要手动执行

---

## 常见陷阱和注意事项

### ❌ 避免的错误

1. **不要跨层调用**
   - 错误：API 直接调用 Repository
   - 正确：API → Service → Repository

2. **不要在生产环境使用 `scripts/start-dev.sh`**
   - 开发脚本仅用于本地开发
   - 生产环境使用 `./scripts/deploy.sh`

3. **不要绕过 Alembic 修改数据库**
   - 所有模型变更必须生成迁移：`make db-migrate`
   - 生产环境禁止使用 `create_all()`

4. **不要在代码中硬编码密钥**
   - 所有敏感信息放 `.env` 文件
   - 生产密钥通过环境变量注入

5. **不要使用裸 `except:`**
   - 使用具体的异常类型
   - 所有异常继承自 `AppException`

### ✅ 推荐的实践

1. **使用 Mock 数据测试 AI 服务**
   ```python
   if settings.ENVIRONMENT == "development":
       return MockBailianService()
   return BailianService()
   ```

2. **提交前运行完整检查**
   ```bash
   make pre-commit  # 格式化 + 检查 + 类型检查 + 测试
   ```

3. **使用依赖注入**
   ```python
   # ✅ 正确
   async def endpoint(db: AsyncSession = Depends(get_db)):
       ...
   
   # ❌ 错误：直接创建连接
   async def endpoint():
       db = create_session()
       ...
   ```

---

## 重要文档引用

项目包含完整的文档体系，详见以下文件：

- **[开发进度](DEVELOPMENT_STATUS.md)** - 当前开发状态、已完成功能、下阶段计划
- **[更新日志](CHANGELOG.md)** - 版本更新和功能变更记录
- **[开发路线图](DEVELOPMENT_ROADMAP.md)** - 长期开发规划（12 个月路线图）
- **[Copilot 指令](.github/copilot-instructions.md)** - AI 辅助开发规范和详细架构说明
- **[部署指南](scripts/DEPLOY-README.md)** - 一键部署脚本使用说明
- **[文档中心](docs/DOCS-README.md)** - 完整的项目文档导航

---

## Git 提交规范

```
类型(范围): 简洁描述

类型：
- feat: 新功能
- fix: 修复 bug
- docs: 文档更新
- refactor: 重构
- test: 测试相关
- chore: 构建/工具链更新

示例：
feat(learning): 添加数学公式渲染支持
fix(avatar): 修复头像上传 Pinia 响应式问题
docs(readme): 更新项目现状和核心功能说明
refactor(mistake): 重构错题服务使用 Repository 模式
test(analytics): 添加学情分析单元测试
```

---

**最后更新**: 2025-11-04  
**项目版本**: 0.1.0  
**维护者**: hordu-ma
