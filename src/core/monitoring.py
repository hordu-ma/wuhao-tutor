"""
性能监控核心模块
提供API响应时间监控、系统指标收集和性能分析功能
"""

import asyncio
import logging
import threading
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Deque, Dict, List, Optional

import psutil
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


@dataclass
class RequestMetrics:
    """请求指标数据类"""

    path: str
    method: str
    status_code: int
    response_time: float
    timestamp: datetime
    user_id: Optional[str] = None
    ip_address: str = ""
    user_agent: str = ""


@dataclass
class SystemMetrics:
    """系统指标数据类"""

    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    disk_usage_percent: float
    active_connections: int = 0
    request_count: int = 0


class MetricsCollector:
    """指标收集器"""

    def __init__(self, max_records: int = 10000):
        self.max_records = max_records
        self._request_metrics: Deque[RequestMetrics] = deque(maxlen=max_records)
        self._system_metrics: Deque[SystemMetrics] = deque(maxlen=max_records // 10)
        self._path_stats: Dict[str, Dict] = defaultdict(
            lambda: {
                "count": 0,
                "total_time": 0.0,
                "min_time": float("inf"),
                "max_time": 0.0,
                "error_count": 0,
            }
        )
        self._active_requests = 0
        self._lock = threading.RLock()
        self._start_time = time.time()

    def record_request(self, metrics: RequestMetrics) -> None:
        """记录请求指标"""
        with self._lock:
            self._request_metrics.append(metrics)

            # 更新路径统计
            path_key = f"{metrics.method} {metrics.path}"
            stats = self._path_stats[path_key]
            stats["count"] += 1
            stats["total_time"] += metrics.response_time
            stats["min_time"] = min(stats["min_time"], metrics.response_time)
            stats["max_time"] = max(stats["max_time"], metrics.response_time)

            if metrics.status_code >= 400:
                stats["error_count"] += 1

    def record_system_metrics(self) -> None:
        """记录系统指标"""
        try:
            with self._lock:
                metrics = SystemMetrics(
                    timestamp=datetime.utcnow(),
                    cpu_percent=psutil.cpu_percent(interval=None),
                    memory_percent=psutil.virtual_memory().percent,
                    disk_usage_percent=psutil.disk_usage("/").percent,
                    active_connections=self._active_requests,
                    request_count=len(self._request_metrics),
                )
                self._system_metrics.append(metrics)
        except Exception as e:
            logger.warning(f"Failed to collect system metrics: {e}")

    def increment_active_requests(self) -> None:
        """增加活跃请求数"""
        with self._lock:
            self._active_requests += 1

    def decrement_active_requests(self) -> None:
        """减少活跃请求数"""
        with self._lock:
            self._active_requests = max(0, self._active_requests - 1)

    def get_request_stats(self, minutes: int = 60) -> Dict[str, Any]:
        """获取请求统计信息"""
        cutoff_time = datetime.utcnow() - timedelta(minutes=minutes)

        with self._lock:
            recent_requests = [
                m for m in self._request_metrics if m.timestamp > cutoff_time
            ]

            if not recent_requests:
                return {
                    "total_requests": 0,
                    "avg_response_time": 0.0,
                    "min_response_time": 0.0,
                    "max_response_time": 0.0,
                    "error_rate": 0.0,
                    "requests_per_minute": 0.0,
                }

            response_times = [m.response_time for m in recent_requests]
            error_count = sum(1 for m in recent_requests if m.status_code >= 400)

            return {
                "total_requests": len(recent_requests),
                "avg_response_time": round(
                    sum(response_times) / len(response_times), 3
                ),
                "min_response_time": round(min(response_times), 3),
                "max_response_time": round(max(response_times), 3),
                "error_rate": round((error_count / len(recent_requests)) * 100, 2),
                "requests_per_minute": round(len(recent_requests) / minutes, 2),
            }

    def get_path_stats(self) -> Dict[str, Dict]:
        """获取路径统计信息"""
        with self._lock:
            stats = {}
            for path, data in self._path_stats.items():
                if data["count"] > 0:
                    stats[path] = {
                        "count": data["count"],
                        "avg_response_time": round(
                            data["total_time"] / data["count"], 3
                        ),
                        "min_response_time": round(data["min_time"], 3),
                        "max_response_time": round(data["max_time"], 3),
                        "error_count": data["error_count"],
                        "error_rate": round(
                            (data["error_count"] / data["count"]) * 100, 2
                        ),
                    }
            return stats

    def get_system_stats(self) -> Dict[str, Any]:
        """获取系统统计信息"""
        with self._lock:
            if not self._system_metrics:
                return {
                    "cpu_percent": 0.0,
                    "memory_percent": 0.0,
                    "disk_usage_percent": 0.0,
                    "active_connections": self._active_requests,
                    "uptime_seconds": round(time.time() - self._start_time, 2),
                }

            latest = self._system_metrics[-1]
            return {
                "cpu_percent": latest.cpu_percent,
                "memory_percent": latest.memory_percent,
                "disk_usage_percent": latest.disk_usage_percent,
                "active_connections": latest.active_connections,
                "uptime_seconds": round(time.time() - self._start_time, 2),
                "total_requests": latest.request_count,
            }

    def get_performance_summary(self) -> Dict[str, Any]:
        """获取性能总结"""
        request_stats = self.get_request_stats()
        path_stats = self.get_path_stats()
        system_stats = self.get_system_stats()

        # 找出最慢的端点
        slowest_endpoints = sorted(
            [(path, stats) for path, stats in path_stats.items()],
            key=lambda x: x[1]["avg_response_time"],
            reverse=True,
        )[:5]

        # 找出错误率最高的端点
        error_endpoints = sorted(
            [
                (path, stats)
                for path, stats in path_stats.items()
                if stats["error_rate"] > 0
            ],
            key=lambda x: x[1]["error_rate"],
            reverse=True,
        )[:5]

        return {
            "timestamp": datetime.utcnow().isoformat(),
            "request_stats": request_stats,
            "system_stats": system_stats,
            "slowest_endpoints": [
                {"path": path, "avg_response_time": stats["avg_response_time"]}
                for path, stats in slowest_endpoints
            ],
            "error_endpoints": [
                {"path": path, "error_rate": stats["error_rate"]}
                for path, stats in error_endpoints
            ],
        }

    def clear_old_metrics(self, hours: int = 24) -> None:
        """清理旧指标数据"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)

        with self._lock:
            # 清理请求指标
            self._request_metrics = deque(
                [m for m in self._request_metrics if m.timestamp > cutoff_time],
                maxlen=self.max_records,
            )

            # 清理系统指标
            self._system_metrics = deque(
                [m for m in self._system_metrics if m.timestamp > cutoff_time],
                maxlen=self.max_records // 10,
            )


class PerformanceMonitoringMiddleware(BaseHTTPMiddleware):
    """性能监控中间件"""

    def __init__(self, app, collector: MetricsCollector):
        super().__init__(app)
        self.collector = collector

    async def dispatch(self, request: Request, call_next) -> Response:
        """处理请求并收集性能指标"""
        start_time = time.time()
        self.collector.increment_active_requests()

        try:
            response = await call_next(request)
            response_time = time.time() - start_time

            # 记录请求指标
            metrics = RequestMetrics(
                path=request.url.path,
                method=request.method,
                status_code=response.status_code,
                response_time=response_time,
                timestamp=datetime.utcnow(),
                ip_address=request.client.host if request.client else "",
                user_agent=request.headers.get("user-agent", ""),
            )

            self.collector.record_request(metrics)

            # 添加性能头信息
            response.headers["X-Response-Time"] = f"{response_time:.3f}s"

            return response

        except Exception as e:
            response_time = time.time() - start_time

            # 记录异常请求
            metrics = RequestMetrics(
                path=request.url.path,
                method=request.method,
                status_code=500,
                response_time=response_time,
                timestamp=datetime.utcnow(),
                ip_address=request.client.host if request.client else "",
                user_agent=request.headers.get("user-agent", ""),
            )

            self.collector.record_request(metrics)
            raise

        finally:
            self.collector.decrement_active_requests()


class SystemMetricsCollector:
    """系统指标定期收集器"""

    def __init__(self, collector: MetricsCollector, interval: int = 60):
        self.collector = collector
        self.interval = interval
        self._running = False
        self._task: Optional[asyncio.Task] = None

    async def start(self) -> None:
        """启动系统指标收集"""
        if self._running:
            return

        self._running = True
        self._task = asyncio.create_task(self._collect_loop())
        logger.info("System metrics collector started")

    async def stop(self) -> None:
        """停止系统指标收集"""
        if not self._running:
            return

        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

        logger.info("System metrics collector stopped")

    async def _collect_loop(self) -> None:
        """指标收集循环"""
        while self._running:
            try:
                self.collector.record_system_metrics()
                await asyncio.sleep(self.interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in system metrics collection: {e}")
                await asyncio.sleep(self.interval)


# 全局指标收集器实例
metrics_collector = MetricsCollector()
system_collector = SystemMetricsCollector(metrics_collector)


def get_metrics_collector() -> MetricsCollector:
    """获取指标收集器实例"""
    return metrics_collector


def get_system_collector() -> SystemMetricsCollector:
    """获取系统指标收集器实例"""
    return system_collector


async def cleanup_old_metrics() -> None:
    """清理旧指标数据的后台任务"""
    while True:
        try:
            metrics_collector.clear_old_metrics(hours=24)
            await asyncio.sleep(3600)  # 每小时清理一次
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"Error cleaning up old metrics: {e}")
            await asyncio.sleep(3600)


# ==================== 公式渲染监控指标 ====================


class FormulaRenderMetrics:
    """公式渲染监控指标收集器 - 支持多层降级策略"""

    def __init__(self):
        self._lock = threading.RLock()
        # 渲染统计
        self.total_requests = 0
        self.cache_hits = 0
        self.cache_misses = 0
        self.render_success = 0
        self.render_failures = 0

        # 响应时间统计（秒）
        self.response_times: Deque[float] = deque(maxlen=1000)

        # 错误统计
        self.quicklatex_errors = 0
        self.oss_upload_errors = 0
        self.db_cache_errors = 0

        # 按类型统计
        self.inline_count = 0
        self.block_count = 0

        # 新增: 降级策略统计
        self.quicklatex_success = 0  # QuickLaTeX成功
        self.local_render_success = 0  # 本地渲染成功
        self.simple_formula_count = 0  # 简单公式数量
        self.complex_formula_count = 0  # 复杂公式数量

        # 最近错误记录
        self.recent_errors: Deque[Dict] = deque(maxlen=100)

    def record_request(self, formula_type: str = "inline") -> None:
        """记录渲染请求"""
        with self._lock:
            self.total_requests += 1
            if formula_type == "inline":
                self.inline_count += 1
            elif formula_type == "block":
                self.block_count += 1

    def record_success(self, response_time: float, formula_type: str) -> None:
        """记录渲染成功"""
        with self._lock:
            self.render_success += 1
            self.response_times.append(response_time)

            # 区分渲染方式
            if "_local" in formula_type:
                self.local_render_success += 1
            else:
                self.quicklatex_success += 1

    def record_failure(
        self, error_type: str, error_msg: str, formula_content: str = ""
    ) -> None:
        """记录渲染失败"""
        with self._lock:
            self.render_failures += 1

            if error_type == "quicklatex":
                self.quicklatex_errors += 1
            elif error_type == "oss_upload":
                self.oss_upload_errors += 1
            elif error_type == "db_cache":
                self.db_cache_errors += 1

            # 记录错误详情
            self.recent_errors.append(
                {
                    "timestamp": datetime.utcnow().isoformat(),
                    "type": error_type,
                    "message": error_msg,
                    "formula": formula_content[:100] if formula_content else "",
                }
            )

    def get_cache_hit_rate(self) -> float:
        """获取缓存命中率"""
        with self._lock:
            if self.total_requests == 0:
                return 0.0
            return round(self.cache_hits / self.total_requests * 100, 2)

    def get_success_rate(self) -> float:
        """获取渲染成功率"""
        with self._lock:
            total = self.render_success + self.render_failures
            if total == 0:
                return 100.0
            return round(self.render_success / total * 100, 2)

    def get_avg_response_time(self) -> float:
        """获取平均响应时间（毫秒）"""
        with self._lock:
            if not self.response_times:
                return 0.0
            return round(sum(self.response_times) / len(self.response_times) * 1000, 2)

    def get_p95_response_time(self) -> float:
        """获取P95响应时间（毫秒）"""
        with self._lock:
            if not self.response_times:
                return 0.0
            sorted_times = sorted(self.response_times)
            p95_index = int(len(sorted_times) * 0.95)
            return round(sorted_times[p95_index] * 1000, 2)

    def get_stats(self) -> Dict[str, Any]:
        """获取完整统计信息"""
        with self._lock:
            return {
                "total_requests": self.total_requests,
                "cache_hits": self.cache_hits,
                "cache_misses": self.cache_misses,
                "cache_hit_rate": f"{self.get_cache_hit_rate()}%",
                "render_success": self.render_success,
                "render_failures": self.render_failures,
                "success_rate": f"{self.get_success_rate()}%",
                "avg_response_time_ms": self.get_avg_response_time(),
                "p95_response_time_ms": self.get_p95_response_time(),
                "by_type": {"inline": self.inline_count, "block": self.block_count},
                "by_method": {
                    "quicklatex": self.quicklatex_success,
                    "local_render": self.local_render_success,
                    "local_render_rate": f"{round(self.local_render_success / max(1, self.render_success) * 100, 2)}%",
                },
                "formula_complexity": {
                    "simple": self.simple_formula_count,
                    "complex": self.complex_formula_count,
                },
                "errors": {
                    "quicklatex": self.quicklatex_errors,
                    "oss_upload": self.oss_upload_errors,
                    "db_cache": self.db_cache_errors,
                    "total": self.render_failures,
                },
                "recent_errors": list(self.recent_errors)[-10:],  # 最近10个错误
            }

    def reset(self) -> None:
        """重置所有统计（用于测试或定期清理）"""
        with self._lock:
            self.total_requests = 0
            self.cache_hits = 0
            self.cache_misses = 0
            self.render_success = 0
            self.render_failures = 0
            self.response_times.clear()
            self.quicklatex_errors = 0
            self.oss_upload_errors = 0
            self.db_cache_errors = 0
            self.inline_count = 0
            self.block_count = 0
            self.quicklatex_success = 0
            self.local_render_success = 0
            self.simple_formula_count = 0
            self.complex_formula_count = 0
            self.recent_errors.clear()


# 全局公式渲染指标实例
formula_metrics = FormulaRenderMetrics()


def get_formula_metrics() -> FormulaRenderMetrics:
    """获取公式渲染指标实例"""
    return formula_metrics
