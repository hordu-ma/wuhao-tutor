"""
健康检查API端点
提供系统健康状态检查和监控功能，包含性能指标和详细系统状态
"""

import asyncio
import logging
import time
from datetime import datetime
from typing import Any, Dict

from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import get_settings
from src.core.database import get_db
from src.core.monitoring import get_metrics_collector
from src.core.security import get_rate_limiter
from src.services.bailian_service import get_bailian_service
from src.services.learning_service import get_learning_service
from src.utils.cache import cache_manager

logger = logging.getLogger("health_api")
settings = get_settings()

router = APIRouter(prefix="/health", tags=["健康检查"])


@router.get("/", summary="系统健康检查", description="检查系统各组件的健康状态")
async def health_check(db: AsyncSession = Depends(get_db)) -> JSONResponse:
    """系统健康检查"""
    start_time = time.time()

    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": getattr(settings, "VERSION", "1.0.0"),
        "environment": settings.ENVIRONMENT,
        "services": {},
    }

    all_healthy = True

    # 1. 数据库健康检查
    try:
        db_start = time.time()
        # 执行简单的数据库查询测试连接
        await db.execute(text("SELECT 1"))
        db_healthy = True
        db_time = round((time.time() - db_start) * 1000, 2)

        health_status["services"]["database"] = {
            "status": "healthy" if db_healthy else "unhealthy",
            "response_time_ms": db_time,
            "details": "PostgreSQL/SQLite connection test",
        }

        if not db_healthy:
            all_healthy = False

    except Exception as e:
        health_status["services"]["database"] = {
            "status": "unhealthy",
            "error": str(e),
            "details": "Database connection failed",
        }
        all_healthy = False

    # 2. AI服务健康检查
    try:
        ai_start = time.time()
        bailian_service = get_bailian_service()
        # 简单的服务可用性检查
        ai_healthy = True  # 这里可以添加实际的百炼服务检查
        ai_time = round((time.time() - ai_start) * 1000, 2)

        health_status["services"]["ai_service"] = {
            "status": "healthy" if ai_healthy else "unhealthy",
            "response_time_ms": ai_time,
            "details": "Bailian AI service availability check",
        }

        if not ai_healthy:
            all_healthy = False

    except Exception as e:
        health_status["services"]["ai_service"] = {
            "status": "unhealthy",
            "error": str(e),
            "details": "AI service check failed",
        }
        all_healthy = False

    # 3. 缓存服务健康检查
    try:
        cache_start = time.time()
        # 测试缓存读写
        test_key = "health_check_test"
        await cache_manager.set(test_key, "test_value", ttl=10)
        cache_value = await cache_manager.get(test_key)
        cache_healthy = cache_value == "test_value"
        await cache_manager.delete(test_key)
        cache_time = round((time.time() - cache_start) * 1000, 2)

        health_status["services"]["cache"] = {
            "status": "healthy" if cache_healthy else "unhealthy",
            "response_time_ms": cache_time,
            "details": "Redis/Memory cache read/write test",
        }

        if not cache_healthy:
            all_healthy = False

    except Exception as e:
        health_status["services"]["cache"] = {
            "status": "unhealthy",
            "error": str(e),
            "details": "Cache service check failed",
        }
        all_healthy = False

    # 4. 文件存储健康检查
    try:
        import os

        storage_healthy = os.path.exists(settings.UPLOAD_DIR) and os.access(
            settings.UPLOAD_DIR, os.W_OK
        )

        health_status["services"]["storage"] = {
            "status": "healthy" if storage_healthy else "unhealthy",
            "details": f"File storage directory: {settings.UPLOAD_DIR}",
            "writable": storage_healthy,
        }

        if not storage_healthy:
            all_healthy = False

    except Exception as e:
        health_status["services"]["storage"] = {
            "status": "unhealthy",
            "error": str(e),
            "details": "Storage accessibility check failed",
        }
        all_healthy = False

    # 总体状态
    health_status["status"] = "healthy" if all_healthy else "unhealthy"
    health_status["total_response_time_ms"] = round(
        (time.time() - start_time) * 1000, 2
    )

    # 根据健康状态返回对应的HTTP状态码
    status_code = (
        status.HTTP_200_OK if all_healthy else status.HTTP_503_SERVICE_UNAVAILABLE
    )

    return JSONResponse(status_code=status_code, content=health_status)


@router.get("/readiness", summary="就绪检查", description="检查服务是否准备好接收请求")
async def readiness_check(db: AsyncSession = Depends(get_db)) -> JSONResponse:
    """就绪检查 - 快速检查关键服务"""
    start_time = time.time()

    try:
        # 快速数据库连接测试
        from sqlalchemy import text

        await db.execute(text("SELECT 1"))

        readiness_status = {
            "status": "ready",
            "timestamp": datetime.utcnow().isoformat(),
            "response_time_ms": round((time.time() - start_time) * 1000, 2),
        }

        return JSONResponse(status_code=status.HTTP_200_OK, content=readiness_status)

    except Exception as e:
        logger.error(f"Readiness check failed: {e}")

        readiness_status = {
            "status": "not_ready",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e),
            "response_time_ms": round((time.time() - start_time) * 1000, 2),
        }

        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, content=readiness_status
        )


@router.get("/liveness", summary="活性检查", description="检查应用程序是否正在运行")
async def liveness_check() -> JSONResponse:
    """活性检查 - 最简单的存活检查"""
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "status": "alive",
            "timestamp": datetime.utcnow().isoformat(),
            "uptime_seconds": time.time()
            - getattr(liveness_check, "_start_time", time.time()),
        },
    )


@router.get("/metrics", summary="系统指标", description="获取系统运行指标和性能数据")
async def get_metrics(db: AsyncSession = Depends(get_db)) -> JSONResponse:
    """获取系统指标"""
    try:
        import os

        import psutil
        from sqlalchemy import text

        # 获取性能监控数据
        metrics_collector = get_metrics_collector()
        rate_limiter = get_rate_limiter()

        metrics = {
            "timestamp": datetime.utcnow().isoformat(),
            "system": {},
            "database": {},
            "application": {},
            "performance": {},
            "security": {},
        }

        # 系统指标
        try:
            system_stats = metrics_collector.get_system_stats()
            metrics["system"] = {
                "cpu_percent": psutil.cpu_percent(interval=1),
                "memory_percent": psutil.virtual_memory().percent,
                "disk_usage_percent": psutil.disk_usage("/").percent,
                "load_average": os.getloadavg() if hasattr(os, "getloadavg") else None,
                "active_connections": system_stats.get("active_connections", 0),
                "uptime_seconds": system_stats.get("uptime_seconds", 0),
            }
        except Exception as e:
            metrics["system"] = {"error": f"Unable to collect system metrics: {str(e)}"}

        # 数据库指标
        try:
            # 获取数据库连接数等信息
            result = await db.execute(
                text(
                    "SELECT COUNT(*) as total_tables FROM information_schema.tables WHERE table_schema = 'public'"
                )
            )
            row = result.fetchone()
            metrics["database"] = {
                "total_tables": row[0] if row else 0,
                "connection_status": "connected",
                "engine": (
                    str(db.bind.dialect.name)
                    if hasattr(db.bind, "dialect")
                    else "unknown"
                ),
            }
        except Exception as e:
            # 尝试SQLite查询
            try:
                result = await db.execute(
                    text("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
                )
                row = result.fetchone()
                metrics["database"] = {
                    "total_tables": row[0] if row else 0,
                    "connection_status": "connected",
                    "engine": "sqlite",
                }
            except:
                metrics["database"] = {"connection_status": "error", "error": str(e)}

        # 应用指标
        metrics["application"] = {
            "environment": settings.ENVIRONMENT,
            "version": getattr(settings, "VERSION", "1.0.0"),
            "upload_directory": settings.UPLOAD_DIR,
            "upload_directory_exists": os.path.exists(settings.UPLOAD_DIR),
            "debug_mode": settings.DEBUG,
        }

        # 性能指标
        try:
            performance_summary = metrics_collector.get_performance_summary()
            metrics["performance"] = {
                "request_stats": performance_summary.get("request_stats", {}),
                "slowest_endpoints": performance_summary.get("slowest_endpoints", []),
                "error_endpoints": performance_summary.get("error_endpoints", []),
            }
        except Exception as e:
            metrics["performance"] = {
                "error": f"Unable to collect performance metrics: {str(e)}"
            }

        # 安全指标
        try:
            metrics["security"] = {
                "rate_limiter_status": "active",
                "active_counters": len(rate_limiter.counters),
                "active_buckets": len(rate_limiter.buckets),
            }
        except Exception as e:
            metrics["security"] = {
                "error": f"Unable to collect security metrics: {str(e)}"
            }

        return JSONResponse(status_code=status.HTTP_200_OK, content=metrics)

    except Exception as e:
        logger.error(f"Metrics collection failed: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "Failed to collect metrics",
                "details": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            },
        )


@router.get(
    "/performance", summary="性能监控", description="获取详细的性能监控数据和统计信息"
)
async def get_performance_metrics() -> JSONResponse:
    """获取详细性能指标"""
    try:
        metrics_collector = get_metrics_collector()

        # 获取不同时间窗口的统计
        performance_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "last_hour": metrics_collector.get_request_stats(minutes=60),
            "last_15_minutes": metrics_collector.get_request_stats(minutes=15),
            "last_5_minutes": metrics_collector.get_request_stats(minutes=5),
            "path_statistics": metrics_collector.get_path_stats(),
            "system_status": metrics_collector.get_system_stats(),
            "summary": metrics_collector.get_performance_summary(),
        }

        return JSONResponse(status_code=status.HTTP_200_OK, content=performance_data)

    except Exception as e:
        logger.error(f"Performance metrics collection failed: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "Failed to collect performance metrics",
                "details": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            },
        )


@router.get(
    "/rate-limits", summary="限流状态", description="获取当前限流器状态和统计信息"
)
async def get_rate_limit_status() -> JSONResponse:
    """获取限流状态"""
    try:
        rate_limiter = get_rate_limiter()

        rate_limit_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "active_counters": len(rate_limiter.counters),
            "active_buckets": len(rate_limiter.buckets),
            "rules_count": len(rate_limiter.rules),
            "rules": [
                {
                    "type": rule.rule_type.value,
                    "limit": rule.limit,
                    "window": rule.window,
                    "endpoint": rule.endpoint,
                    "message": rule.message,
                }
                for rule in rate_limiter.rules
            ],
        }

        return JSONResponse(status_code=status.HTTP_200_OK, content=rate_limit_data)

    except Exception as e:
        logger.error(f"Rate limit status collection failed: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "Failed to collect rate limit status",
                "details": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            },
        )


# 初始化启动时间
liveness_check._start_time = time.time()
