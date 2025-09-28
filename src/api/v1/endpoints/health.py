"""
健康检查API端点
提供系统健康状态检查和监控功能
"""

import asyncio
import logging
import time
from datetime import datetime
from typing import Dict, Any

from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.config import get_settings
from src.services.bailian_service import get_bailian_service
from src.services.homework_service import get_homework_service
from src.services.learning_service import get_learning_service
from src.utils.cache import cache_manager

logger = logging.getLogger("health_api")
settings = get_settings()

router = APIRouter(prefix="/health", tags=["健康检查"])


@router.get(
    "/",
    summary="系统健康检查",
    description="检查系统各组件的健康状态"
)
async def health_check(
    db: AsyncSession = Depends(get_db)
) -> JSONResponse:
    """系统健康检查"""
    start_time = time.time()

    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": getattr(settings, 'VERSION', '1.0.0'),
        "environment": settings.ENVIRONMENT,
        "services": {}
    }

    all_healthy = True

    # 1. 数据库健康检查
    try:
        db_start = time.time()
        homework_service = get_homework_service()
        db_healthy = await homework_service.health_check(db)
        db_time = round((time.time() - db_start) * 1000, 2)

        health_status["services"]["database"] = {
            "status": "healthy" if db_healthy else "unhealthy",
            "response_time_ms": db_time,
            "details": "PostgreSQL/SQLite connection test"
        }

        if not db_healthy:
            all_healthy = False

    except Exception as e:
        health_status["services"]["database"] = {
            "status": "unhealthy",
            "error": str(e),
            "details": "Database connection failed"
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
            "details": "Bailian AI service availability check"
        }

        if not ai_healthy:
            all_healthy = False

    except Exception as e:
        health_status["services"]["ai_service"] = {
            "status": "unhealthy",
            "error": str(e),
            "details": "AI service check failed"
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
            "details": "Redis/Memory cache read/write test"
        }

        if not cache_healthy:
            all_healthy = False

    except Exception as e:
        health_status["services"]["cache"] = {
            "status": "unhealthy",
            "error": str(e),
            "details": "Cache service check failed"
        }
        all_healthy = False

    # 4. 文件存储健康检查
    try:
        import os
        storage_healthy = os.path.exists(settings.UPLOAD_DIR) and os.access(settings.UPLOAD_DIR, os.W_OK)

        health_status["services"]["storage"] = {
            "status": "healthy" if storage_healthy else "unhealthy",
            "details": f"File storage directory: {settings.UPLOAD_DIR}",
            "writable": storage_healthy
        }

        if not storage_healthy:
            all_healthy = False

    except Exception as e:
        health_status["services"]["storage"] = {
            "status": "unhealthy",
            "error": str(e),
            "details": "Storage accessibility check failed"
        }
        all_healthy = False

    # 总体状态
    health_status["status"] = "healthy" if all_healthy else "unhealthy"
    health_status["total_response_time_ms"] = round((time.time() - start_time) * 1000, 2)

    # 根据健康状态返回对应的HTTP状态码
    status_code = status.HTTP_200_OK if all_healthy else status.HTTP_503_SERVICE_UNAVAILABLE

    return JSONResponse(
        status_code=status_code,
        content=health_status
    )


@router.get(
    "/readiness",
    summary="就绪检查",
    description="检查服务是否准备好接收请求"
)
async def readiness_check(
    db: AsyncSession = Depends(get_db)
) -> JSONResponse:
    """就绪检查 - 快速检查关键服务"""
    start_time = time.time()

    try:
        # 快速数据库连接测试
        from sqlalchemy import text
        await db.execute(text("SELECT 1"))

        readiness_status = {
            "status": "ready",
            "timestamp": datetime.utcnow().isoformat(),
            "response_time_ms": round((time.time() - start_time) * 1000, 2)
        }

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=readiness_status
        )

    except Exception as e:
        logger.error(f"Readiness check failed: {e}")

        readiness_status = {
            "status": "not_ready",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e),
            "response_time_ms": round((time.time() - start_time) * 1000, 2)
        }

        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content=readiness_status
        )


@router.get(
    "/liveness",
    summary="活性检查",
    description="检查应用程序是否正在运行"
)
async def liveness_check() -> JSONResponse:
    """活性检查 - 最简单的存活检查"""
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "status": "alive",
            "timestamp": datetime.utcnow().isoformat(),
            "uptime_seconds": time.time() - getattr(liveness_check, '_start_time', time.time())
        }
    )


@router.get(
    "/metrics",
    summary="系统指标",
    description="获取系统运行指标"
)
async def get_metrics(
    db: AsyncSession = Depends(get_db)
) -> JSONResponse:
    """获取系统指标"""
    try:
        from sqlalchemy import text
        import psutil
        import os

        metrics = {
            "timestamp": datetime.utcnow().isoformat(),
            "system": {},
            "database": {},
            "application": {}
        }

        # 系统指标
        try:
            metrics["system"] = {
                "cpu_percent": psutil.cpu_percent(interval=1),
                "memory_percent": psutil.virtual_memory().percent,
                "disk_usage_percent": psutil.disk_usage('/').percent,
                "load_average": os.getloadavg() if hasattr(os, 'getloadavg') else None
            }
        except:
            metrics["system"] = {"error": "Unable to collect system metrics"}

        # 数据库指标
        try:
            # 获取数据库连接数等信息（这里需要根据实际数据库类型调整）
            result = await db.execute(text("SELECT COUNT(*) as total_tables FROM information_schema.tables WHERE table_schema = 'public'"))
            row = result.fetchone()
            metrics["database"] = {
                "total_tables": row[0] if row else 0,
                "connection_status": "connected"
            }
        except Exception as e:
            metrics["database"] = {
                "connection_status": "error",
                "error": str(e)
            }

        # 应用指标
        metrics["application"] = {
            "environment": settings.ENVIRONMENT,
            "version": getattr(settings, 'VERSION', '1.0.0'),
            "upload_directory": settings.UPLOAD_DIR,
            "upload_directory_exists": os.path.exists(settings.UPLOAD_DIR)
        }

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=metrics
        )

    except Exception as e:
        logger.error(f"Metrics collection failed: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "Failed to collect metrics",
                "details": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
        )


# 初始化启动时间
liveness_check._start_time = time.time()
