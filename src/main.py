"""
五好伴学 - FastAPI 主应用
基于AI的初高中学情管理系统
"""

from contextlib import asynccontextmanager
from typing import Dict, Any
import asyncio

import uvicorn
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from src.core.config import settings
from src.core.logging import configure_logging, get_logger, LoggingMiddleware
from src.core.monitoring import (
    get_metrics_collector,
    get_system_collector,
    PerformanceMonitoringMiddleware,
    cleanup_old_metrics
)
from src.core.security import (
    get_rate_limiter,
    RateLimitMiddleware,
    SecurityHeadersMiddleware,
    cleanup_rate_limiters
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    logger = get_logger("app.lifespan")

    # 初始化变量
    system_collector = None
    cleanup_task = None
    rate_limit_cleanup_task = None

    # 启动时
    logger.info("🚀 应用启动中...")

    # 启动性能监控
    if settings.ENABLE_METRICS:
        system_collector = get_system_collector()
        await system_collector.start()
        logger.info("✅ 性能监控已启动")

        # 启动清理任务
        cleanup_task = asyncio.create_task(cleanup_old_metrics())
        rate_limit_cleanup_task = asyncio.create_task(cleanup_rate_limiters())

    yield

    # 关闭时
    logger.info("🛑 应用关闭中...")

    # 停止监控服务
    if settings.ENABLE_METRICS and system_collector:
        await system_collector.stop()
        if cleanup_task:
            cleanup_task.cancel()
        if rate_limit_cleanup_task:
            rate_limit_cleanup_task.cancel()
        logger.info("✅ 性能监控已停止")


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

    # 性能监控中间件（最外层，最先执行）
    if settings.ENABLE_METRICS:
        metrics_collector = get_metrics_collector()
        app.add_middleware(PerformanceMonitoringMiddleware, collector=metrics_collector)

    # 安全头中间件
    app.add_middleware(SecurityHeadersMiddleware)

    # 限流中间件
    rate_limiter = get_rate_limiter()
    app.add_middleware(RateLimitMiddleware, rate_limiter=rate_limiter)

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
    import os
    if os.getenv("TESTING") != "1":  # 测试时跳过主机验证
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=["localhost", "127.0.0.1", "testserver", settings.HOST] if settings.DEBUG else ["*"]
        )

    # 日志中间件（最内层，最后执行）
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
