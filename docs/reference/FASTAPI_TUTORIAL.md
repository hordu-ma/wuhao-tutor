# FastAPI 学习教程（基于五好伴学 Wuhao Tutor 实战）

面向已有一定 Python 基础的同学，带你用本项目的真实代码快速上手 FastAPI：从应用工厂、路由与依赖注入、配置管理，到数据库会话、分层架构、中间件与异常处理，并给出可运行的“试一试”步骤与扩展练习。

---

## 你将学到什么

- 如何创建一个可扩展的 FastAPI 应用（应用工厂 + lifespan）
- 路由分组与版本化（APIRouter、include_router）
- 依赖注入（Depends）与异步数据库会话（AsyncSession, SQLAlchemy 2.x）
- 配置管理（pydantic-settings）与环境切换
- 分层架构：API → Services → Repositories → Models 的职责边界
- 中间件与统一异常处理、规范化日志与性能监控
- 用本项目现有模块快速扩展新功能

示例代码均取自本仓库：

- 应用入口：`src/main.py`
- 路由聚合：`src/api/v1/api.py`
- 健康检查端点：`src/api/v1/endpoints/health.py`
- 配置管理：`src/core/config.py`
- 数据库会话与依赖：`src/core/database.py`
- 通用仓储：`src/repositories/base_repository.py`
- 业务服务示例：`src/services/homework_service.py`

---

## 快速运行（Development）

以下命令在 macOS + zsh 下测试通过，默认使用 SQLite（Development 环境）。

```bash
# 1) 安装依赖（推荐 uv）
uv sync

# 2) 启动开发服务（后端）
# 若你在根目录，FastAPI app 模块为 "src.main:app"
ENVIRONMENT=development uv run uvicorn src.main:app --host 127.0.0.1 --port 8000 --reload

# 3) 打开浏览器
open http://127.0.0.1:8000/
open http://127.0.0.1:8000/docs
```

可选：本仓库还提供脚本与 Make 任务（见根目录 `Makefile` 与 `scripts/`）。若你使用 PostgreSQL/Redis，请先正确配置 `.env`。

---

## 从一个最小可用的应用开始

本项目采用“应用工厂 + lifespan”的推荐模式。精简自 `src/main.py`：

- 应用工厂：集中配置标题、版本、OpenAPI/Docs 等，并挂载中间件与异常处理
- lifespan：在启动/关闭阶段进行监控器启停、清理任务等

示例（节选）：

```python
# src/main.py（节选）
from fastapi import FastAPI
from contextlib import asynccontextmanager
from src.core.config import settings

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动阶段
    # ...启动性能监控、后台清理任务等
    yield
    # 关闭阶段
    # ...停止监控、取消任务


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        description="AI 助力的学情管理系统",
        openapi_url=f"{settings.API_V1_STR}/openapi.json" if settings.DEBUG else None,
        docs_url="/docs" if settings.DEBUG else None,
        redoc_url="/redoc" if settings.DEBUG else None,
        lifespan=lifespan,
    )
    # 中间件、异常处理、路由
    setup_middleware(app)
    setup_exception_handlers(app)
    setup_routes(app)
    return app

app = create_app()
```

运行后可直接访问：

- GET `/` 返回项目名称与版本
- GET `/health` 返回应用与环境状态

---

## 路由与版本化：APIRouter + include_router

统一在 `src/api/v1/api.py` 聚合所有 v1 路由：

```python
# src/api/v1/api.py（节选）
from fastapi import APIRouter
from src.api.v1.endpoints import auth, user, learning, homework, homework_compatibility, analytics, mistakes, goals, file, health

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["认证"])
api_router.include_router(user.router, prefix="/user", tags=["用户管理"])
api_router.include_router(learning.router, prefix="/learning", tags=["学习问答"])
api_router.include_router(homework.router, tags=["作业批改"])  # 某些模块自身定义了 prefix
api_router.include_router(health.router, tags=["健康检查"])      # 健康检查
```

在应用层通过 `include_router` 挂载：

```python
# src/main.py（节选）
from src.api.v1.api import api_router
app.include_router(api_router, prefix=settings.API_V1_STR)
```

“试一试”：

```bash
curl -s http://127.0.0.1:8000/api/v1/health/ | jq
```

---

## 依赖注入（Depends）与数据库会话（AsyncSession）

`src/core/database.py` 提供 FastAPI 可直接注入的异步会话：

```python
# src/core/database.py（节选）
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from typing import AsyncGenerator
from src.core.config import settings

engine = create_async_engine(str(settings.SQLALCHEMY_DATABASE_URI), echo=settings.DEBUG)
AsyncSessionLocal = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
```

在端点中使用依赖：

```python
# src/api/v1/endpoints/health.py（节选）
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.database import get_db

router = APIRouter(prefix="/health", tags=["健康检查"])

@router.get("/")
async def health_check(db: AsyncSession = Depends(get_db)):
    # 使用 db 执行快速检查或查询
    return {"status": "healthy"}
```

---

## 配置管理与环境切换（pydantic-settings）

`src/core/config.py` 使用 `BaseSettings` 统一管理配置，并按 `ENVIRONMENT` 变量切换不同子类：

```python
# src/core/config.py（节选）
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "五好伴学"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"
    DEBUG: bool = False
    SQLALCHEMY_DATABASE_URI: str | None = None
    # ... 省略若干配置项（Redis/日志/AI 服务等）

class DevelopmentSettings(Settings):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = "sqlite+aiosqlite:///./wuhao_tutor_dev.db"

class TestingSettings(Settings):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = "sqlite+aiosqlite:///:memory:"

class ProductionSettings(Settings):
    DEBUG = False
    # 对关键项增加严格校验（如 SECRET_KEY、BAILIAN_API_KEY 等）

def get_settings() -> Settings:
    import os
    env = os.getenv("ENVIRONMENT", "development").lower()
    return {"production": ProductionSettings, "testing": TestingSettings}.get(env, DevelopmentSettings)()

settings = get_settings()
```

要切换环境，只需调整启动前的环境变量：

```bash
ENVIRONMENT=testing uv run pytest -q
ENVIRONMENT=production uv run uvicorn src.main:app --host 0.0.0.0 --port 8000
```

---

## 分层架构：API → Services → Repositories → Models

项目约定：

- API 层仅处理请求/响应与授权校验，不直接访问数据库
- Service 层承载业务逻辑，协调多个仓储、第三方服务（如百炼、OSS、OCR）
- Repository 层封装 CRUD 与复杂查询（SQLAlchemy 2.x）
- Models 层定义 ORM 模型（`src/models/*`），Schemas 层用于请求/响应数据（`src/schemas/*`）

通用仓储基类（节选自 `src/repositories/base_repository.py`）：

```python
from typing import Generic, TypeVar, Type, Optional, Any, Dict, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func, and_
from sqlalchemy.orm import DeclarativeBase

ModelType = TypeVar("ModelType", bound=DeclarativeBase)

class BaseRepository(Generic[ModelType]):
    def __init__(self, model: Type[ModelType], db: AsyncSession):
        self.model = model
        self.db = db

    async def get_by_id(self, record_id: str) -> Optional[ModelType]:
        stmt = select(self.model).where(getattr(self.model, 'id') == record_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create(self, data: Dict[str, Any]) -> ModelType:
        instance = self.model(**data)
        self.db.add(instance)
        await self.db.commit()
        await self.db.refresh(instance)
        return instance
```

服务层示例（节选自 `src/services/homework_service.py`）：

```python
class HomeworkService:
    async def get_homework(self, session: AsyncSession, homework_id: uuid.UUID):
        stmt = select(Homework).where(Homework.id == homework_id)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()
```

把它们连起来（API → Service → DB）：

```python
# 假设我们在某个 endpoints 模块中
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.database import get_db
from src.services.homework_service import HomeworkService

router = APIRouter(prefix="/example")
service = HomeworkService()

@router.get("/homeworks/{hid}")
async def get_hw(hid: str, db: AsyncSession = Depends(get_db)):
    hw = await service.get_homework(db, uuid.UUID(hid))
    if not hw:
        raise HTTPException(status_code=404, detail="Homework not found")
    return hw
```

---

## 中间件与统一异常处理

中间件在 `src/main.py` 的 `setup_middleware` 中注册：

- 性能监控：`PerformanceMonitoringMiddleware`
- 安全响应头：`SecurityHeadersMiddleware`
- 限流：`RateLimitMiddleware`
- CORS：`CORSMiddleware`
- 日志：`LoggingMiddleware`

统一异常处理（节选自 `setup_exception_handlers`）：

```python
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi import status

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"code": "VALIDATION_ERROR", "message": "请求参数校验失败", "details": exc.errors()},
    )
```

项目还定义了丰富的业务异常（见 `src/core/exceptions.py`），如 `DatabaseError`、`AIServiceError`、`UserNotFoundError`、`RateLimitError` 等，建议在 Service 层抛出具体异常，在 API 层转换为标准化响应。

---

## 数据校验与响应模型（Pydantic v2）

- 请求体/查询参数的校验：在 `src/schemas/*` 定义数据模型
- 响应模型：可通过 `response_model=XXX` 限定输出结构
- 复杂分页响应：项目提供 `PaginatedResponse` 与 `PaginationInfo`（见 `src/schemas/common.py`）

示例：

```python
from fastapi import APIRouter
from pydantic import BaseModel

class Item(BaseModel):
    id: int
    name: str

router = APIRouter(prefix="/items")

@router.get("/{item_id}", response_model=Item)
async def get_item(item_id: int) -> Item:
    return Item(id=item_id, name="demo")
```

---

## 一起动手：新增一个“Ping”端点（完整流程）

目标：新增路由 `/api/v1/example/ping`，返回应用版本与数据库连通性。

1. 新建文件：`src/api/v1/endpoints/example.py`

```python
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from src.core.database import get_db
from src.core.config import settings

router = APIRouter(prefix="/example", tags=["示例"])

@router.get("/ping")
async def ping(db: AsyncSession = Depends(get_db)):
    await db.execute(text("SELECT 1"))
    return {"pong": True, "version": settings.VERSION}
```

2. 在 `src/api/v1/api.py` 注册：

```python
from src.api.v1.endpoints import example  # 新增导入
api_router.include_router(example.router)
```

3. 试一试：

```bash
curl -s http://127.0.0.1:8000/api/v1/example/ping | jq
```

---

## 测试与质量

项目已配置 pytest、mypy、flake8 与 coverage：

```bash
# 运行测试（自动选择 asyncio 模式）
uv run pytest -q

# 静态检查 & 格式化
uv run mypy src
uv run flake8
uv run python -m black --check .
```

示例单元测试（端点级，使用 TestClient 或 httpx.AsyncClient）：

```python
import pytest
from httpx import AsyncClient
from src.main import app

@pytest.mark.asyncio
async def test_root():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        resp = await ac.get("/")
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("status") == "running"
```

---

## 常见坑与实践建议

- 异步优先：端点、Service、Repository 全链路 async/await，避免同步阻塞
- 依赖注入：数据库会话通过 `Depends(get_db)` 注入，务必不要在全局持有 `AsyncSession`
- 严禁裸 `except:`：抛出具体异常类型（见 `src/core/exceptions.py`），在 API 层统一转换
- 配置与密钥：一律使用环境变量或 `.env`，禁止硬编码凭证
- 分层边界：API 不直接访问数据库；复杂查询应放在 Repository 层；事务性业务放在 Service 层
- 性能监控：关注慢查询阈值、限流与缓存配置（`src/core/performance.py`、`src/core/security.py`、`src/utils/cache.py`）

---

## 参考与进阶

- FastAPI 官方文档：https://fastapi.tiangolo.com/
- SQLAlchemy 2.0（Async）：https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html
- Pydantic v2 / Settings：https://docs.pydantic.dev/
- 本项目：
  - 架构与约定见 `docs/` 与 `src/core/*`
  - AI 与文件服务封装：`src/services/bailian_service.py`、`src/utils/file_upload.py`、`src/utils/ocr.py`
  - 示例端点：`src/api/v1/endpoints/health.py`

---

祝学习顺利！如果你已经跑通“Ping”端点，可以尝试：

- 为 `homework` 新增一个只读查询端点（调用 `HomeworkService.list_homeworks`）
- 在 Service 层抛出自定义异常，并在 API 层转换为 400/404/503 等标准响应
- 编写 2~3 个异步单元测试（正常路径 + 1 个异常路径）

> 小贴士：遵循“函数单一职责”（≤ 60 行）、“强类型注解（mypy strict）”、“具体异常类型”这三条铁律，代码会更健壮、更易维护。
