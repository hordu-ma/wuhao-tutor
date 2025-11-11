# AGENTS_zh.md

本文件为 Qoder (qoder.com) 在处理此代码库时提供指导。

## 项目概述

**五好伴学 (Wuhao Tutor)** - K12 AI 驱动的学习平台，具有作业问答、错题本、知识图谱和学习分析功能。

- **技术栈**: FastAPI + Vue3 + 微信小程序 + PostgreSQL + Redis + 阿里云百炼 AI
- **生产环境**: https://www.horsduroot.com (121.199.173.244)
- **版本**: v0.1.0
- **Python**: 3.11+
- **多平台**: Web 前端 + 微信小程序（均已上线）

## 常用命令

### 开发

```bash
# 后端开发
make dev                    # 启动后端服务器 (端口 8000)
uv run python src/main.py   # 后端启动替代方案
./scripts/start-dev.sh      # 同时启动前端和后端

# 前端开发
cd frontend && npm run dev  # 启动前端 (端口 5173)

# 数据库迁移
make db-init                # 应用所有迁移
make db-migrate             # 创建新迁移 (提示输入描述)
make db-upgrade             # 应用迁移
make db-downgrade           # 回滚一次迁移
make db-reset               # 危险操作: 重置整个数据库
```

### 代码质量

```bash
# 代码检查和格式化
make lint                   # 运行 flake8 + black + isort 检查
make format                 # 使用 black + isort 格式化代码
make type-check             # 运行 mypy 类型检查
make check-all              # 运行所有检查 (lint + type-check)

# 前端质量
cd frontend && npm run lint        # ESLint
cd frontend && npm run type-check  # vue-tsc
cd frontend && npm run format      # Prettier
```

### 测试

```bash
# 后端测试
make test                   # 运行所有测试
make test-unit              # 仅单元测试
make test-integration       # 仅集成测试
make test-coverage          # 生成覆盖率报告 (查看 htmlcov/)

# 前端测试
cd frontend && npm run test          # 运行 vitest
cd frontend && npm run test:coverage # 带覆盖率
```

### 部署

```bash
./scripts/deploy.sh         # 生产环境部署 (构建前端 + 部署后端)
journalctl -u wuhao-tutor.service -f  # 查看生产环境日志
```

## 架构

### 四层严格分离

后端遵循严格的四层架构。**切勿跳过层级** (例如，API → Repository)。

```
API 层 → Service 层 → Repository 层 → Model 层
```

**规则**:

- **API 层** (`src/api/v1/endpoints/`): HTTP 请求处理、参数验证、响应格式化 (19 个文件，50+ 个端点)
- **Service 层** (`src/services/`): 业务逻辑、事务管理、多 Repository 协调
  - `BailianService` (1000+ 行): AI 服务集成
  - `LearningService` (2400+ 行): 问答业务逻辑
  - `MistakeService` (1260+ 行): 错题本
  - `KnowledgeGraphService`, `AnalyticsService`, `AuthService` 等
- **Repository 层** (`src/repositories/`): 数据访问、复杂查询、数据转换
  - 所有 Repository 扩展 `BaseRepository[ModelType]` 泛型
- **Model 层** (`src/models/`): 数据库模型 (11 个模型)，全部继承自带有 UUID 和时间戳的 `BaseModel`

### 核心基础设施 (`src/core/`)

- `config.py`: Pydantic Settings v2 环境配置
- `database.py`: SQLAlchemy 2.x 异步引擎 + 连接池
- `security.py`: JWT 认证 + 多层限流 (令牌桶 + 滑动窗口)
- `monitoring.py`: 性能指标收集 (响应时间、错误率)
- `performance.py`: 慢查询监听 (>1.0s) + N+1 检测
- `exceptions.py`: 统一异常层次结构 (20+ 种类型)

**除非完全理解影响，否则不要修改核心基础设施。**

### 数据库

- **开发环境**: SQLite (本地文件)
- **生产环境**: PostgreSQL 14+ (阿里云 RDS)
- **ORM**: SQLAlchemy 2.x 支持异步 (`asyncpg` 用于 PostgreSQL, `aiosqlite` 用于 SQLite)
- **迁移**: Alembic (~15 个迁移文件在 `alembic/versions/`)
- **缓存**: Redis 6+ 用于限流、刷新令牌、会话缓存

**迁移工作流程**:

1. 修改 `src/models/` 中的模型
2. 运行 `make db-migrate` (生成迁移并提示输入描述)
3. 检查 `alembic/versions/` 中生成的迁移
4. 运行 `make db-init` 应用
5. 使用 `make db-downgrade` 测试回滚

### AI 服务集成

**阿里云百炼**:

- **服务**: `BailianService` (`src/services/bailian_service.py`)
- **模型**: Qwen (通义千问) 大语言模型
- **功能**: 学习问答、作业批改、知识点提取
- **超时**: 120s (支持图像 OCR)
- **重试**: 3 次尝试，指数退避
- **流式传输**: 服务器发送事件 (SSE) 实现实时响应

**环境变量** (`.env`):

- `BAILIAN_API_KEY=sk-xxx` (生产环境必须以 `sk-` 开头)
- `BAILIAN_APPLICATION_ID=xxx`

**禁止**:

- 直接向 AI 服务发出 HTTP 调用 (始终使用 `BailianService`)
- 跳过重试逻辑或超时配置

### 前端架构

**Web 前端** (`frontend/`):

- **框架**: Vue 3.4+ (Composition API) + TypeScript 5.6+
- **UI 库**: Element Plus 2.5+
- **构建工具**: Vite 5+
- **状态管理**: Pinia 2.1+
- **路由**: Vue Router 4.x
- **HTTP 客户端**: Axios 1.6+
- **数学渲染**: KaTeX 0.16+ (LaTeX 公式)
- **Markdown**: marked 16.x + highlight.js
- **图表**: ECharts 6.0 + vue-echarts

**微信小程序** (`miniprogram/`):

- **语言**: 原生 JavaScript + TypeScript 声明
- **框架**: 微信小程序原生 API
- **UI**: 微信原生组件 + 自定义组件
- **网络**: 自定义请求封装 (`utils/request.js`)
- **API**: 连接生产环境 (horsduroot.com)
- **页面**: 15+ 个页面 (学习、错题、个人资料、分析)

## 开发最佳实践

### 代码风格

- **类型注解**: 所有函数必需 (mypy 严格模式)
- **异常处理**: 使用特定异常 (切勿使用 `except:` 或 `except Exception:`)
- **函数长度**: ≤ 60 行，单一职责
- **文档字符串**: 复杂逻辑使用 Google 风格
- **异步**: 所有 I/O 操作必须使用 `async/await`

**示例** (参考 `src/services/mistake_service.py`):

```python
async def create_mistake(
    self, db: AsyncSession, user_id: UUID
) -> MistakeDetailResponse:
    """
    创建新的错题记录。

    Args:
        db: 数据库会话
        user_id: 用户 UUID

    Returns:
        创建的错题详情

    Raises:
        ServiceError: 如果创建失败
    """
    try:
        # 实现...
    except SpecificError as e:  # 特定异常
        raise ServiceError(f"创建错题失败: {e}")
```

### Repository 模式

所有 Repository 必须:

- 扩展 `BaseRepository[ModelType]` 泛型
- 封装数据访问逻辑
- 使用 SQLAlchemy 异步 API (`select()`, `update()`, `delete()`)
- 适当处理数据库错误

### Service 层事务

Service 处理事务和业务逻辑:

- 使用 `async with db.begin()` 进行显式事务
- 协调多个 Repository
- 实现业务规则和验证

### 模型标准

所有模型必须:

- 继承自 `BaseModel` (提供 UUID `id`、`created_at`、`updated_at`)
- 使用 SQLAlchemy 2.x 声明式风格
- 包含适当的关系和懒加载
- 为频繁查询的列定义索引

## 安全与性能

### 限流 (多层)

- **IP 级别**: 100 请求/分钟 (令牌桶) - DDoS 防护
- **用户级别**: 50 请求/分钟 (令牌桶) - 防滥用
- **AI 服务**: 20 请求/分钟 (滑动窗口) - 成本控制
- **登录端点**: 10 请求/分钟 (令牌桶) - 防暴力破解

### 认证

- **JWT**: 访问令牌 (8 天) + 刷新令牌 (30 天)
- **密码**: bcrypt 12 轮
- **令牌存储**: 刷新令牌存储在 Redis 中
- **自动续期**: 访问令牌刷新机制

### 中间件栈 (执行顺序)

1. `PerformanceMonitoringMiddleware` - 指标收集
2. `SecurityHeadersMiddleware` - CSP, HSTS, X-Frame-Options
3. `RateLimitMiddleware` - 限流
4. `CORSMiddleware` - CORS 处理
5. `TrustedHostMiddleware` - 主机验证
6. `LoggingMiddleware` - 请求/响应日志

### 性能监控

- **慢查询**: 自动记录 >1.0s 的查询
- **N+1 检测**: 警告 N+1 查询模式
- **指标收集**: 响应时间、错误率、系统资源
- **系统监控**: CPU、内存、磁盘使用情况

## 环境配置

**环境**:

- **开发**: SQLite 本地数据库
- **测试**: 内存 SQLite
- **生产**: PostgreSQL + Redis

**关键环境变量** (`.env`):

```bash
# 生产环境必需
BAILIAN_API_KEY=sk-xxx              # 必须以 sk- 开头
BAILIAN_APPLICATION_ID=xxx
SQLALCHEMY_DATABASE_URI=xxx
SECRET_KEY=xxx                      # 生产环境必须更改
REDIS_HOST=localhost                # 开发环境可选

# 数据库
DATABASE_URL=postgresql+asyncpg://user:pass@host/db  # 生产环境

# 安全
ACCESS_TOKEN_EXPIRE_DAYS=8
REFRESH_TOKEN_EXPIRE_DAYS=30
```

## 生产环境部署

**部署流程**:

1. 运行 `./scripts/deploy.sh` (本地构建前端，部署到服务器)
2. 验证: `curl https://horsduroot.com/health`
3. 检查日志: `journalctl -u wuhao-tutor.service -f`

**部署结构**:

- 后端: `/opt/wuhao-tutor`
- 前端: `/var/www/html`
- 日志: `/var/log/wuhao-tutor`
- 配置: `/opt/wuhao-tutor/.env.production`

**关键部署规则**:

- ❌ **切勿** 在生产环境使用 `start-dev.sh` → 使用 `deploy.sh`
- ❌ **切勿** 跳过 Alembic 迁移 → 运行 `make db-migrate` + `make db-init`
- ❌ **切勿** 硬编码密钥 → 使用环境变量
- ✅ **始终** 在部署前本地测试迁移
- ✅ **始终** 在部署前运行 lint + type-check

## 测试策略

**单元测试**: Service 和 Repository

- 模拟外部依赖 (AI 服务、Redis)
- 隔离测试业务逻辑
- 使用 `MockBailianService` 进行 AI 服务测试

**集成测试**: API 端点

- 测试完整的请求/响应周期
- 使用测试数据库 (内存 SQLite)
- 验证认证和授权

**性能测试**: 负载测试

- 可通过 `make test-performance` 使用
- 监控响应时间和资源使用情况

## 重要约束

1. **严格分层**: API → Service → Repository → Model (不可跳过层级)
2. **全面异步**: 所有 I/O 操作必须使用 `async/await`
3. **类型安全**: 完整的类型注解 + mypy 严格检查
4. **配置外化**: 仅使用环境变量，不使用硬编码值
5. **数据库变更**: 始终使用 Alembic 迁移 (切勿直接更改模式)

## 常见陷阱

❌ **API 直接调用 Repository** → 必须通过 Service 层
❌ **异步上下文中的同步代码** → 对所有 I/O 使用 `async/await`
❌ **通用异常处理** → 使用特定异常类型
❌ **跳过迁移** → 始终生成和检查迁移
❌ **硬编码 API 密钥** → 使用环境变量
❌ **缺少类型注解** → mypy 将失败
❌ **长函数 (>60 行)** → 拆分为更小的函数

## 关键文件参考

- 架构: 阅读 `.github/copilot-instructions.md` 获取详细指南
- 开发状态: `DEVELOPMENT_STATUS.md`
- 变更日志: `CHANGELOG.md`
- API 文档: `docs/api/` 目录
- 数据库模式: `docs/database/` 目录
