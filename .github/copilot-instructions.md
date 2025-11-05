# 五好伴学 Copilot 开发指令

## 项目概览

K12 智能学习平台 | FastAPI + Vue3 + 微信小程序 + PostgreSQL + 阿里云百炼 AI

**生产环境**: https://www.horsduroot.com (121.199.173.244)  
**版本**: v0.1.0 | **更新**: 2025-11-05

### 核心模块

- ✅ AI 问答 (25+ API): 多模态输入、流式响应、公式渲染
- ✅ 错题手册 (10+ API): 艾宾浩斯算法、知识点关联
- ✅ 知识图谱 (3+ API): 可视化、薄弱点分析
- ✅ 学习分析 (8+ API): 多维统计、趋势分析
- ✅ 微信小程序: 已上线，连接生产环境

---

## 架构原则

### 四层严格分层

```
API → Service → Repository → Model
```

**规则**:

- ❌ 禁止跨层调用 (如 API → Repository)
- ✅ 全异步 `async/await`
- ✅ 类型注解必须 (mypy strict)
- ✅ Repository 使用 `BaseRepository[Model]` 泛型
- ✅ Service 处理业务逻辑和事务

### 核心基础设施 (src/core/)

| 模块           | 功能                                    |
| -------------- | --------------------------------------- |
| config.py      | Pydantic Settings v2 环境配置           |
| database.py    | SQLAlchemy 2.x 异步连接池               |
| security.py    | JWT + 多层限流 (Token Bucket + Sliding) |
| monitoring.py  | 性能指标收集 (响应时间/错误率)          |
| performance.py | 慢查询监听 (>1s) + N+1 检测             |
| exceptions.py  | 统一异常 (20+ 类型)                     |

---

## 开发规范

### 代码质量 (强制)

```python
# 1. 类型注解 + 具体异常
async def create_mistake(
    self, db: AsyncSession, user_id: UUID
) -> MistakeDetailResponse:
    try:
        # 实现...
    except SpecificError:  # ✅ 具体异常
        raise ServiceError("描述")
    # ❌ 禁止: except: 或 except Exception:

# 2. 函数 ≤ 60 行，单一职责
# 3. Google 风格 docstring (复杂逻辑必须)
```

### 数据模型

```python
# 所有模型继承 BaseModel (src/models/base.py)
class MyModel(BaseModel):
    __tablename__ = "my_table"
    # ✅ UUID 主键 + created_at + updated_at
    # ✅ 软删除: deleted_at (可选)
```

### Repository 模式

```python
class MyRepository(BaseRepository[MyModel]):
    async def custom_query(self, ...):
        """复杂查询在 Repository，不在 Service"""
        pass

# ✅ Repository: 数据访问 + 复杂查询
# ✅ Service: 业务逻辑 + 多 Repository 组合 + 事务
# ❌ 禁止: Service 层写 SQL/ORM 查询
```

---

## 快速命令

```bash
# 环境
uv sync && uv run python

# 开发
./scripts/start-dev.sh  # 前后端一键启动
make dev                # 仅后端

# 数据库
make db-init            # Alembic 迁移
make db-migrate         # 创建新迁移
make db-reset           # ⚠️ 重置 (开发)

# 质量
make test               # pytest + 覆盖率
make lint               # black + flake8
make type-check         # mypy strict

# 部署
./scripts/deploy.sh     # 生产一键部署
```

---

## 环境配置

| 环境       | 数据库        | 缓存  | 特性                 |
| ---------- | ------------- | ----- | -------------------- |
| Dev        | SQLite        | 可选  | 热重载、详细日志     |
| Test       | SQLite (内存) | 无    | 快速测试、Mock 依赖  |
| Production | PostgreSQL    | Redis | 监控、限流、日志脱敏 |

**关键环境变量** (`.env`):

```bash
BAILIAN_API_KEY=sk-xxx            # 生产必须 sk- 开头
BAILIAN_APPLICATION_ID=xxx
SQLALCHEMY_DATABASE_URI=xxx       # SQLite/PostgreSQL
SECRET_KEY=xxx                    # 生产必须更改
REDIS_HOST=localhost              # 可选
```

---

## 性能与安全

### 限流策略

| 维度    | 限制          | 算法           |
| ------- | ------------- | -------------- |
| IP      | 100 请求/分钟 | Token Bucket   |
| 用户    | 50 请求/分钟  | Token Bucket   |
| AI 服务 | 20 请求/分钟  | Sliding Window |
| 登录    | 10 请求/分钟  | Token Bucket   |

### 监控指标

- ✅ 慢查询: >1.0 秒自动记录
- ✅ N+1 检测: `performance.py` 自动警告
- ✅ 中间件: 性能监控 → 安全头 → 限流 → CORS → 日志

---

## AI 服务集成

### BailianService (src/services/bailian_service.py)

```python
# ✅ 推荐: 使用 Service 层封装
result = await bailian_service.chat(
    messages=messages,
    stream=True,      # 流式响应
    timeout=120       # 支持图片 OCR
)

# ❌ 禁止: 直接 HTTP 调用 (跳过重试/监控)
```

**配置**:

- 超时: 120s (图片 OCR)
- 重试: 最多 3 次 (指数退避)
- 流式: SSE (Server-Sent Events)

---

## 生产部署

**服务器**: 121.199.173.244 (horsduroot.com)  
**路径**: /opt/wuhao-tutor (后端) + /var/www/html (前端)  
**服务**: systemd (wuhao-tutor.service)

```bash
# 一键部署
./scripts/deploy.sh

# 验证
curl https://horsduroot.com/health

# 日志
ssh root@121.199.173.244 'journalctl -u wuhao-tutor.service -f'
```

**注意**:

- 前端本地构建后同步 (避免 npm install 卡住)
- 小程序本地编译上传 (不在服务器)
- 数据库迁移需手动执行
- `.env.production` 在服务器上

---

## 常见陷阱

### ❌ 避免

1. 生产用 `scripts/start-dev.sh` (必须用 `deploy.sh`)
2. 修改 `src/core/` 基础设施 (除非完全理解)
3. 绕过 Alembic 改数据库 (必须 `make db-migrate`)
4. 硬编码密钥 (必须环境变量)

### ✅ 推荐

1. **数据库变更**: 修改模型 → `make db-migrate` → 检查迁移 → `make db-init` → 测试回滚
2. **测试策略**: 单元测试 (Services/Repositories) + 集成测试 (API) + 性能测试
3. **Mock AI**: 开发环境可用 `MockBailianService`

---

## 项目结构 (简化)

```
wuhao-tutor/
├── src/
│   ├── api/v1/endpoints/    # API 路由 (50+ 端点)
│   ├── services/            # 业务逻辑 (BailianService, LearningService 等)
│   ├── repositories/        # 数据访问 (BaseRepository 泛型)
│   ├── models/              # ORM 模型 (15+ 表)
│   ├── schemas/             # Pydantic 模型
│   ├── core/                # 基础设施 (config, security, monitoring)
│   └── main.py              # FastAPI 入口
├── frontend/                # Vue3 + TypeScript + Element Plus
├── miniprogram/             # 微信小程序 (15+ 页面)
├── alembic/                 # 数据库迁移
├── scripts/                 # 开发脚本 (deploy.sh, diagnose.py)
├── tests/                   # 测试 (单元/集成/性能)
└── docs/                    # 文档 (api, architecture, guide)
```

---

## 重要约束

1. **脚本授权**: 生成修复脚本或总结文档前，先获得授权确认
2. **分层严格**: API → Service → Repository → Model (禁止跨层)
3. **异步优先**: 所有 I/O 操作必须 `async/await`
4. **类型安全**: 全部类型注解 + mypy strict 检查
5. **配置外化**: 环境变量，禁止硬编码

---

**文档版本**: v3.0 (精简版)  
**最后更新**: 2025-11-05  
**Token 优化**: 从 ~3000 token 精简至 ~1200 token
