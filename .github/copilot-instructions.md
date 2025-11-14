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

## 输出语言规范

- **用户交互**: 中文（简洁直接）
- **代码注释**: 中文（复杂逻辑必须注释）
- **文档编写**: 中文（README、开发文档等）
- **AGENTS.md**: 保持英文（供国际 AI 工具使用）
- **Git 提交**: 中文（遵循用户级指令的提交规范）

---

## 开发规范

**核心约束**:

- 类型注解 + 具体异常（禁止 `except:` 或 `except Exception:`）
  - ⚠️ **例外**: 最外层 API 入口可用 `Exception` 兜底（需详细日志）
- 函数 ≤ 60 行，单一职责
- Google 风格 docstring（复杂逻辑必须）
- 模型继承 `BaseModel`（UUID 主键 + `created_at` + `updated_at`）
- Repository 封装数据访问，Service 处理业务逻辑和事务
- 禁止跨层调用（如 API 直接调用 Repository）

```python
# 标准模式（参考 src/services/mistake_service.py）
async def create_mistake(
    self, db: AsyncSession, user_id: UUID
) -> MistakeDetailResponse:
    try:
        # 实现...
    except SpecificError as e:  # 具体异常
        raise ServiceError(f"错误: {e}")

# API层最外层兜底（例外情况）
@router.post("/mistakes")
async def create_mistake_endpoint(...):
    try:
        return await service.create_mistake(...)
    except ServiceError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:  # 兜底，避免500裸露
        logger.error(f"未预期错误: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="服务器内部错误")
```

---

## 快速命令

```bash
# 核心命令（完整命令列表见 AGENTS.md）
make dev                # 启动后端开发服务器
make db-migrate         # 创建数据库迁移
make test               # 运行测试
make lint               # 代码检查
./scripts/deploy.sh     # 生产部署
```

---

## 环境配置

**环境**: Dev (SQLite) | Test (内存 SQLite) | Prod (PostgreSQL + Redis)

**关键变量** (`.env`):

- `BAILIAN_API_KEY=sk-xxx` (生产必须 sk- 开头)
- `BAILIAN_APPLICATION_ID=xxx`
- `SQLALCHEMY_DATABASE_URI=xxx`
- `SECRET_KEY=xxx` (生产必须更改)
- `REDIS_HOST=localhost` (可选)

---

## 性能与安全

**限流**: IP 100/min | 用户 50/min | AI 20/min | 登录 10/min (Token Bucket + Sliding Window)  
**监控**: 慢查询 >1.0s | N+1 检测 | 中间件链（性能 → 安全头 → 限流 → CORS → 日志）

---

## AI 服务集成

**BailianService** (`src/services/bailian_service.py`):

- ✅ 使用 Service 层封装（支持重试、监控、流式响应）
- ❌ 禁止直接 HTTP 调用
- 配置: 超时 120s | 重试 3 次（指数退避）| SSE 流式

---

## 生产部署

**一键部署**: `./scripts/deploy.sh`（前端本地构建 + 后端热部署）  
**验证**: `curl https://horsduroot.com/health`  
**日志**: `journalctl -u wuhao-tutor.service -f`

**关键陷阱**:

- ❌ 生产用 `start-dev.sh` → 必须 `deploy.sh`
- ❌ 跳过 Alembic → 数据库变更必须 `make db-migrate`
- ❌ 硬编码密钥 → 环境变量
- ❌ 修改 `src/core/` 基础设施（除非完全理解）

**最佳实践**:

- 数据库变更: 修改模型 → `make db-migrate` → 检查迁移 → `make db-init` → 测试回滚
- 测试策略: 单元测试 (Services/Repositories) + 集成测试 (API) + 性能测试
- Mock AI: 开发环境可用 `MockBailianService`

---

## 项目结构

**后端**: `src/` (api/services/repositories/models/core) | 50+ API | 15+ 表  
**前端**: `frontend/` (Vue3 + TypeScript + Element Plus)  
**小程序**: `miniprogram/` (15+ 页面，连接生产环境)  
**其他**: `alembic/` (迁移) | `scripts/` (部署) | `tests/` (单元/集成/性能)

---

## 重要约束

1. **脚本授权**: 生成修复脚本或总结文档前，先获得授权确认
2. **分层严格**: API → Service → Repository → Model (禁止跨层)
3. **异步优先**: 所有 I/O 操作必须 `async/await`
4. **类型安全**: 全部类型注解 + mypy strict 检查
5. **配置外化**: 环境变量，禁止硬编码

---
