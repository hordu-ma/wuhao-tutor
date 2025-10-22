# 五好伴学 Copilot 开发指令

## 项目概述

基于阿里云百炼智能体的 K12 智能学习平台，采用 FastAPI + Vue3 + 微信小程序架构，提供作业批改、学习问答、错题管理和学情分析服务。

**核心特性**：

- ✅ **AI 驱动问答**：集成阿里云百炼，支持多模态输入和流式响应
- ✅ **错题手册**：艾宾浩斯遗忘曲线复习、知识点关联分析（开发中）
- ✅ **学情分析**：多维度学习数据统计与可视化
- ✅ **企业级安全**：多层限流、JWT 双 Token、完整安全头配置

## 架构设计模式

### 四层分层架构 (src/)

```
api/ → services/ → repositories/ → models/
```

**分层原则**：

- ❌ **禁止跨层调用**（例如 API 直接调用 Repository）
- ✅ **必须使用类型注解**和 `async/await` 异步模式
- ✅ **Repository 层**：使用 `BaseRepository[Model]` 泛型实现 CRUD
- ✅ **Service 层**：处理业务逻辑、组合多个 Repository、管理事务
- ❌ **重要限定**: 若使用修复脚本进行修复工作，生成脚本前，先获得授权和确认；如果需要生成文档说明工作获得总结，也需要获得授权和确认。

### 核心基础设施 (src/core/)

| 模块             | 功能     | 关键特性                                         |
| ---------------- | -------- | ------------------------------------------------ |
| `config.py`      | 配置管理 | Pydantic Settings v2，环境变量验证，生产强制校验 |
| `database.py`    | 数据库   | Async SQLAlchemy 2.x，自动会话管理               |
| `security.py`    | 安全限流 | Token Bucket + Sliding Window 双算法             |
| `monitoring.py`  | 监控指标 | 自定义指标收集器，支持响应时间/错误率/系统资源   |
| `performance.py` | 性能优化 | N+1 查询检测，慢查询监听（>1s），自动缓存        |

### AI 服务集成

- **统一接口**：`BailianService` 在 `src/services/bailian_service.py`
- **错误处理**：使用具体异常类型（`src/core/exceptions.py`），禁止裸 `except:`
- **超时重试**：所有外部调用配置超时（默认 30s）和重试（最多 3 次）
- **流式响应**：支持 SSE（Server-Sent Events）实时流式输出

## 开发工作流

### 快速启动命令

```bash
# 环境设置和诊断
uv sync && uv run python scripts/diagnose.py

# 启动开发服务器（前端 + 后端）
./scripts/start-dev.sh

# 数据库操作
make db-init      # 执行 Alembic 迁移到最新版本
make db-migrate   # 创建新迁移（需手动输入描述）
make db-reset     # 开发环境重置（⚠️ 数据丢失）
make db-backup    # PostgreSQL 备份（生产环境）

# 代码质量
make test         # pytest 测试 + 覆盖率报告
make lint         # black 格式化 + flake8 检查
make type-check   # mypy 类型检查

# 文档生成
make schema       # 导出 OpenAPI JSON 到 docs/api/openapi.json
```

### 环境配置

| 环境            | 数据库        | 缓存       | 特性                         |
| --------------- | ------------- | ---------- | ---------------------------- |
| **Development** | SQLite        | 可选 Redis | 热重载，详细日志，允许跨域   |
| **Testing**     | SQLite (内存) | 无         | 快速测试，模拟依赖           |
| **Production**  | PostgreSQL    | Redis      | 完整监控，安全限流，日志脱敏 |

**环境变量**：

- `.env` 文件模板在 `config/templates/`
- 生产环境密钥必须以 `sk-` 开头（`BAILIAN_API_KEY`）
- ⚠️ **禁止提交** `secrets/` 目录和真实 `.env` 文件

### 多端前端架构

| 端             | 技术栈                   | 端口 | 说明                                        |
| -------------- | ------------------------ | ---- | ------------------------------------------- |
| **Web 前端**   | Vue3 + TypeScript + Vite | 5173 | Element Plus UI，Pinia 状态管理             |
| **微信小程序** | 原生 JS + TS 声明        | -    | 自定义网络层 `miniprogram/utils/request.js` |
| **共享 API**   | FastAPI                  | 8000 | 统一 RESTful 接口 `/api/v1/`                |

## 项目开发约定

### 数据模型设计

```python
# 所有模型继承自 src/models/base.py 的 BaseModel
class HomeworkModel(BaseModel):
    __tablename__ = "homework"
    # ✅ 统一使用 UUID 主键
    # ✅ 自动时间戳（created_at, updated_at）
    # ✅ 软删除支持（deleted_at 列）
```

**设计原则**：

- 主键使用 UUID，避免 ID 猜测攻击
- 所有表必须有 `created_at` 和 `updated_at`
- 敏感数据删除使用软删除（设置 `deleted_at`）
- 使用 SQLAlchemy 2.x 的 `Mapped[]` 类型注解

### Repository 模式

```python
# 继承 BaseRepository 获得类型安全的 CRUD 操作
class HomeworkRepository(BaseRepository[HomeworkModel]):
    async def find_by_student_id(self, student_id: UUID) -> List[HomeworkModel]:
        """复杂查询放在 Repository，不在 Service"""
        # 实现查询逻辑...
```

**职责划分**：

- ✅ Repository：数据访问、复杂查询、数据转换
- ✅ Service：业务逻辑、多 Repository 组合、事务管理
- ❌ 禁止在 Service 层编写 SQL 或 ORM 查询

### 错误处理

```python
# ✅ 使用具体异常类型（定义在 src/core/exceptions.py）
raise HomeworkNotFoundError(f"作业 {homework_id} 不存在")

```

**异常处理原则**：

- 使用领域特定异常（`*NotFoundError`, `*ValidationError`）
- 所有异常必须继承自 `AppException`
- 异常消息包含必要上下文（ID、用户、操作类型）
- API 层统一转换为 HTTP 状态码

### 性能监控

**自动监控**：

- ✅ 慢查询日志：查询超过 **1.0 秒**自动记录
- ✅ 限流保护：
  - IP 级别：**100 请求/分钟**
  - 用户级别：**50 请求/分钟**
  - AI 服务：**20 请求/分钟**
  - 登录端点：**10 请求/分钟**
- ✅ 指标收集：中间件自动追踪每个端点的响应时间

**N+1 查询检测**：

- `performance.py` 监听器自动检测并警告
- 使用 `joinedload()` 或 `selectinload()` 优化关联查询

### 前端集成

**API 客户端生成**：

```bash
# 从 OpenAPI 规范生成前端 SDK
make schema  # 生成 docs/api/openapi.json
```

**状态管理**：

- ✅ **Pinia Stores**：使用异步 actions，处理加载/错误状态
- ✅ **响应式更新**：确保数据变更触发 Vue 响应式系统
- ✅ **错误处理**：统一捕获 API 错误并显示用户友好消息

**微信小程序**：

- 网络请求封装在 `miniprogram/utils/request.js`
- 自动处理 Token 刷新和 401 重定向
- 支持文件上传（multipart/form-data）

## 文件组织结构

```
wuhao-tutor/
├── config/templates/       # 环境变量模板（.env.example）
├── alembic/versions/       # 数据库迁移文件（按时间排序）
├── scripts/                # 开发自动化脚本
│   ├── start-dev.sh       # 启动开发环境
│   ├── deploy_to_production.sh  # 生产部署
│   └── sql/               # SQL 初始化脚本
├── docs/                   # 项目文档
│   ├── api/               # API 文档和 OpenAPI 规范
│   └── architecture/      # 架构设计文档
├── src/                    # 后端源码
│   ├── api/               # FastAPI 路由
│   ├── services/          # 业务逻辑层
│   ├── repositories/      # 数据访问层
│   ├── models/            # SQLAlchemy 模型
│   └── core/              # 核心基础设施
├── frontend/               # Vue3 Web 前端
├── miniprogram/            # 微信小程序
├── tests/                  # 测试套件
└── monitoring/             # Prometheus 配置
```

## 常见陷阱与最佳实践

### ❌ 避免的错误

1. **不要在生产环境使用 `scripts/start-dev.sh`**

   - 生产部署必须使用 `./scripts/deploy_to_production.sh`
   - 生产服务通过 systemd 管理，不是直接运行脚本

2. **不要修改 `src/core/` 基础设施代码**

   - 除非你完全理解中间件堆栈的工作原理
   - 安全/限流/监控的变更可能影响整个系统

3. **不要绕过 Alembic 修改数据库**

   - 所有模型变更必须生成迁移：`make db-migrate`
   - 生产环境禁止使用 `create_all()`

4. **不要在代码中硬编码密钥**
   - 所有敏感信息放 `.env` 或 `secrets/` 目录
   - 生产密钥通过环境变量注入

### ✅ 推荐的实践

1. **AI 服务调用先用 Mock 数据测试**

   ```python
   # 开发环境可以使用 Mock
   if settings.ENVIRONMENT == "development":
       return MockBailianService()
   return BailianService()
   ```

2. **数据库变更工作流**

   ```bash
   # 1. 修改模型类
   # 2. 生成迁移
   make db-migrate
   # 3. 检查生成的迁移文件
   # 4. 应用迁移
   make db-init
   # 5. 测试回滚
   alembic downgrade -1
   alembic upgrade head
   ```

3. **测试策略**
   - **单元测试**：专注 Services 和 Repositories
   - **集成测试**：API 端点，使用测试数据库
   - **性能测试**：`tests/performance/` 负载测试脚本
   - **Mock 数据**：`scripts/init_database.py` 生成测试数据

## 技术集成点

### AI 服务（阿里云百炼）

**服务封装**：

- 入口：`src/services/bailian_service.py`
- 配置：`BAILIAN_API_KEY`, `BAILIAN_APPLICATION_ID`
- 特性：自动重试、流式响应、多模态支持

**最佳实践**：

```python
# ✅ 使用服务层调用
result = await bailian_service.chat(
    messages=messages,
    stream=True,  # 流式响应
    timeout=30    # 超时控制
)

# ❌ 不要直接调用 HTTP 客户端
# response = httpx.post(...)  # 跳过了重试和监控
```

### 文件存储

**开发环境**：

- 本地存储：`./uploads/` 目录
- URL 前缀：`http://localhost:8000/uploads/`

**生产环境**：

- 阿里云 OSS：`OSS_BUCKET_NAME` 配置
- CDN 加速：Nginx 反向代理优化

**限制**：

- 最大文件大小：**10MB**
- 允许格式：`.jpg`, `.jpeg`, `.png`, `.pdf`, `.webp`

### 数据库连接

**连接池配置**：

```python
# 开发环境（SQLite）
pool_size=5, max_overflow=10

# 生产环境（PostgreSQL）
pool_size=20, max_overflow=40
pool_pre_ping=True  # 连接健康检查
```

**事务管理**：

```python
async with get_db() as db:
    # 自动事务，异常时回滚
    await repository.create(db, obj)
    # 提交在上下文管理器退出时自动执行
```

### 缓存（Redis）

**用途**：

- 限流计数器（Token Bucket 和 Sliding Window）
- 会话存储（JWT Refresh Token）
- 数据缓存（用户信息、AI 响应缓存）

**配置**：

```python
CACHE_ENABLED: bool = True
CACHE_DEFAULT_TTL: int = 300  # 5 分钟
```

**降级策略**：

- Redis 不可用时，限流降级为内存计数（不跨进程）
- 缓存失败静默降级，直接查询数据库

### 前端构建

**开发环境**：

```bash
cd frontend
npm run dev  # Vite 开发服务器（热重载）
```

**生产构建**：

```bash
npm run build  # 构建到 frontend/dist/
# Nginx 托管静态文件
```

**API 代理**：

- 开发环境：Vite 代理 `/api` 到 `http://localhost:8000`
- 生产环境：Nginx 反向代理到后端服务

## 测试策略详解

### 单元测试

**覆盖目标**：Services 和 Repositories ≥ 80%

**示例**：

```python
@pytest.mark.asyncio
async def test_create_mistake(mistake_service):
    """测试创建错题记录"""
    result = await mistake_service.create_mistake(
        user_id=uuid4(),
        question_content="测试题目",
        subject=Subject.MATH
    )
    assert result.id is not None
    assert result.subject == Subject.MATH
```

### 集成测试

**覆盖目标**：所有 API 端点

**示例**：

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

### 性能测试

**工具**：JMeter, k6, locust

**基线指标**：

- 错题列表：P95 < 200ms
- 复习提交：P95 < 300ms
- AI 问答（非流式）：P95 < 3s

## 部署流程

### 生产环境配置

**⚠️ 重要：以下是阿里云生产环境的实际配置，修改代码时需要考虑这些约束**

| 配置项           | 值                   | 说明                       |
| ---------------- | -------------------- | -------------------------- |
| **服务器 IP**    | 121.199.173.244      | 阿里云 ECS                 |
| **域名**         | horsduroot.com       | 主域名（已配置 SSL）       |
| **SSH 用户**     | root@121.199.173.244 | 服务器访问                 |
| **后端部署路径** | /opt/wuhao-tutor     | FastAPI 应用目录           |
| **前端部署路径** | /var/www/html        | Nginx 静态文件目录         |
| **服务名称**     | wuhao-tutor.service  | systemd 服务               |
| **后端端口**     | 8000                 | 内部端口（Nginx 反向代理） |
| **数据库**       | PostgreSQL           | 生产数据库                 |
| **缓存**         | Redis                | 限流和会话存储             |
| **SSL 证书**     | Let's Encrypt        | www.horsduroot.com         |

**访问地址**：

- 前端：https://horsduroot.com
- 后端 API：https://horsduroot.com/api/v1/
- 健康检查：https://horsduroot.com/health

**部署命令**：

```bash
# 一键部署（推荐）
./scripts/deploy.sh

# 检查生产状态
./scripts/check-production.sh

# 查看服务日志
ssh root@121.199.173.244 'journalctl -u wuhao-tutor.service -f'
```

**注意事项**：

- 前端在本地构建后同步到服务器（避免 npm install 卡住）
- 微信小程序在本地开发工具中编译上传（不在服务器）
- `.env.production` 文件在服务器上，包含敏感配置
- 数据库迁移需要手动执行：`ssh root@121.199.173.244 'cd /opt/wuhao-tutor && source venv/bin/activate && alembic upgrade head'`

### 生产部署检查清单

```bash
# 1. 执行部署（已整合所有步骤）
./scripts/deploy.sh

# 2. 验证部署
curl https://horsduroot.com/health

# 3. 检查服务状态
./scripts/check-production.sh
```

### 部署步骤详解（自动执行）

`./scripts/deploy.sh` 会自动执行以下步骤：

1. **检查 SSH 连接**：验证服务器可访问
2. **同步后端代码**：rsync 到 /opt/wuhao-tutor
3. **重启后端服务**：systemctl restart wuhao-tutor.service
4. **构建前端**：本地执行 npm run build
5. **同步前端文件**：rsync 到 /var/www/html
6. **验证部署**：检查 API 健康端点和前端访问

**手动执行数据库迁移**：

```bash
ssh root@121.199.173.244 'cd /opt/wuhao-tutor && source venv/bin/activate && alembic upgrade head'
```

### 回滚流程

```bash
# 1. 回滚代码
git reset --hard <commit-hash>

# 2. 回滚数据库
alembic downgrade <revision>

# 3. 重启服务
systemctl restart wuhao-tutor

# 4. 验证
./scripts/verify_deployment.sh
```

## 故障排查指南

### 常见问题

**1. 数据库连接失败**

```bash
# 检查 PostgreSQL 状态
systemctl status postgresql

# 查看连接配置
env | grep POSTGRES

# 测试连接
psql -h localhost -U postgres -d wuhao_tutor
```

**2. AI 服务超时**

```python
# 检查配置
echo $BAILIAN_API_KEY
echo $BAILIAN_APPLICATION_ID

# 增加超时
BAILIAN_TIMEOUT=60  # 默认 30s
```

**3. 限流误拦截**

```bash
# 查看 Redis 限流键
redis-cli --scan --pattern "rate_limit:*"

# 清除特定 IP 限流
redis-cli DEL "rate_limit:ip:192.168.1.100"
```

**4. 慢查询分析**

```python
# 查看慢查询日志
tail -f logs/app.log | grep "Slow query"

# 分析 SQL
# 在 performance.py 中自动记录
```

### 日志查看

**开发环境**：

```bash
# 实时日志
tail -f logs/app.log

# 错误日志
grep ERROR logs/app.log
```

**生产环境**：

```bash
# systemd 日志
journalctl -u wuhao-tutor -f

# 应用日志
tail -f /var/log/wuhao-tutor/app.log
```

## 安全最佳实践

### 敏感数据处理

1. **密码**：使用 bcrypt 哈希，加盐轮次 ≥ 12
2. **Token**：JWT 短期有效（Access 8 天，Refresh 30 天）
3. **API 密钥**：环境变量注入，禁止硬编码
4. **用户数据**：日志脱敏，过滤 `Authorization`、`Cookie` 头

### 限流策略

| 维度    | 限制 | 窗口   | 说明       |
| ------- | ---- | ------ | ---------- |
| IP      | 100  | 1 分钟 | 防止 DDoS  |
| 用户    | 50   | 1 分钟 | 防止滥用   |
| AI 服务 | 20   | 1 分钟 | 控制成本   |
| 登录    | 10   | 1 分钟 | 防暴力破解 |

### HTTPS 配置

**生产环境必须启用 HTTPS**：

- 使用 Let's Encrypt 免费证书
- Nginx 强制 HTTPS 重定向
- HSTS 头启用（max-age=31536000）

## 监控与告警

### 关键指标

**应用指标**：

- 请求量（QPS）
- 响应时间（P50/P95/P99）
- 错误率
- AI 服务调用次数和成功率

**系统指标**：

- CPU 使用率
- 内存使用率
- 磁盘 I/O
- 数据库连接池状态

### Prometheus 集成

**端点**：`/api/v1/health/metrics`（JSON 格式）

**TODO**：转换为 Prometheus 格式

```python
# 未来支持
GET /metrics  # Prometheus 格式
```

## 开发技巧

### 调试技巧

**1. 使用 IPython 调试**

```python
# 在代码中插入断点
import IPython; IPython.embed()
```

**2. 查看 SQL 查询**

```python
# 启用 SQL 回显
engine = create_async_engine(
    database_url,
    echo=True  # 打印所有 SQL
)
```

**3. Mock AI 服务**

```python
# 测试时使用 Mock
@pytest.fixture
def mock_bailian_service(mocker):
    return mocker.patch('src.services.bailian_service.BailianService')
```

### 代码格式化

**自动格式化**：

```bash
make lint  # black + flake8
make type-check  # mypy
```

**VS Code 配置**：

```json
{
  "python.formatting.provider": "black",
  "python.linting.enabled": true,
  "python.linting.flake8Enabled": true,
  "editor.formatOnSave": true
}
```

### Git 工作流

**分支策略**：

- `main`：生产环境
- `develop`：开发环境
- `feature/*`：功能分支
- `hotfix/*`：紧急修复

**提交规范**：

```
feat: 添加错题手册列表功能
fix: 修复用户头像上传问题
docs: 更新 API 文档
chore: 升级依赖版本
```

---

**最后更新**：2025-10-16  
**维护者**：五好伴学开发团队  
**文档版本**：v2.0
