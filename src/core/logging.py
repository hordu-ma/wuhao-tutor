"""
结构化日志配置模块
基于 structlog 的日志系统
"""

import logging
import sys
import time
from typing import Any, List, Optional

import structlog

from .config import settings


def configure_logging() -> None:
    """配置结构化日志"""

    # 基础处理器
    processors: List[Any] = [
        # 添加日志级别和名称
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        # 添加时间戳
        structlog.processors.TimeStamper(fmt="iso"),
        # 添加调用信息（仅在调试模式下）
        (
            structlog.processors.CallsiteParameterAdder(
                parameters=[
                    structlog.processors.CallsiteParameter.FILENAME,
                    structlog.processors.CallsiteParameter.LINENO,
                ]
            )
            if settings.DEBUG
            else structlog.processors.CallsiteParameterAdder()
        ),
    ]

    # 根据配置选择输出格式
    if settings.LOG_FORMAT == "json":
        processors.extend(
            [structlog.processors.dict_tracebacks, structlog.processors.JSONRenderer()]
        )
    else:
        processors.extend(
            [
                structlog.processors.add_log_level,
                structlog.dev.ConsoleRenderer(colors=True),
            ]
        )

    # 配置 structlog
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # 配置标准库 logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, settings.LOG_LEVEL.upper()),
    )

    # 配置第三方库日志级别
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)


def get_logger(name: Optional[str] = None) -> structlog.BoundLogger:
    """获取结构化日志器"""
    return structlog.get_logger(name or __name__)


class LoggingMiddleware:
    """日志中间件，记录请求信息"""

    def __init__(self, app):
        self.app = app
        self.logger = get_logger("middleware.logging")

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)

        start_time = None
        request_body = b""

        async def receive_wrapper():
            nonlocal request_body
            message = await receive()
            if message["type"] == "http.request":
                request_body += message.get("body", b"")
            return message

        async def send_wrapper(message):
            nonlocal start_time
            if message["type"] == "http.response.start":
                start_time = time.time()
                status_code = message["status"]

                # 记录请求开始
                self.logger.info(
                    "Request started",
                    method=scope["method"],
                    path=scope["path"],
                    query_string=scope["query_string"].decode(),
                    client=scope["client"],
                    status_code=status_code,
                )
            elif message["type"] == "http.response.body":
                if start_time:
                    duration = time.time() - start_time
                    self.logger.info(
                        "Request completed",
                        duration=duration,
                    )
            return await send(message)

        return await self.app(scope, receive_wrapper, send_wrapper)
