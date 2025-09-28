"""
五好伴学 - FastAPI 主应用
基于AI的初高中学情管理系统
"""

from contextlib import asynccontextmanager
from typing import Dict, Any

import uvicorn
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from src.core.config import settings
from src.core.logging import configure_logging, get_logger, LoggingMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    logger = get_logger("app.lifespan")

    # 启动时
    logger.info("🚀 应用启动中...")
    yield

    # 关闭时
    logger.info("🛑 应用关闭中...")


def create_app() -> FastAPI:
    """创建 FastAPI 应用实例"""

    # 配置日志
    configure_logging()
    logger = get_logger("app.factory")

    # 创建应用实例
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        description="基于AI的初高中学情管理系统，帮助学生构建个人知识图谱",
        openapi_url=f"{settings.API_V1_STR}/openapi.json" if settings.DEBUG else None,
        docs_url="/docs" if settings.DEBUG else None,
        redoc_url="/redoc" if settings.DEBUG else None,
        lifespan=lifespan,
    )

    # 添加中间件
    setup_middleware(app)

    # 添加异常处理器
    setup_exception_handlers(app)

    # 注册路由
    setup_routes(app)

    logger.info("✅ FastAPI 应用创建完成", project=settings.PROJECT_NAME, version=settings.VERSION)
    return app


def setup_middleware(app: FastAPI) -> None:
    """配置中间件"""

    # CORS 中间件
    if settings.BACKEND_CORS_ORIGINS:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    # 安全中间件
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["localhost", "127.0.0.1", settings.HOST] if settings.DEBUG else ["*"]
    )

    # 日志中间件
    app.add_middleware(LoggingMiddleware)


def setup_exception_handlers(app: FastAPI) -> None:
    """配置异常处理器"""

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        """请求验证异常处理"""
        logger = get_logger("app.exception")
        logger.warning("请求验证失败",
                      path=request.url.path,
                      errors=exc.errors())

        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "code": "VALIDATION_ERROR",
                "message": "请求参数验证失败",
                "details": exc.errors(),
            },
        )

    @app.exception_handler(500)
    async def internal_server_error_handler(request: Request, exc: Exception):
        """内部服务器错误处理"""
        logger = get_logger("app.exception")
        logger.error("内部服务器错误",
                    path=request.url.path,
                    error=str(exc),
                    exc_info=True)

        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "code": "INTERNAL_ERROR",
                "message": "服务器内部错误，请稍后重试",
            },
        )


def setup_routes(app: FastAPI) -> None:
    """设置路由"""

    @app.get("/")
    async def root() -> Dict[str, Any]:
        """根路径"""
        return {
            "project": settings.PROJECT_NAME,
            "version": settings.VERSION,
            "status": "running",
            "message": "欢迎使用五好伴学！"
        }

    @app.get("/health")
    async def health_check() -> Dict[str, Any]:
        """健康检查端点"""
        return {
            "status": "healthy",
            "project": settings.PROJECT_NAME,
            "version": settings.VERSION,
            "environment": "development" if settings.DEBUG else "production",
        }

    # 注册 API 路由
    from src.api.v1.api import api_router
    app.include_router(api_router, prefix=settings.API_V1_STR)


# 创建应用实例
app = create_app()


if __name__ == "__main__":
    """开发服务器启动"""
    uvicorn.run(
        "src.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
    )
