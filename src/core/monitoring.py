"""
性能监控核心模块
提供API响应时间监控、系统指标收集和性能分析功能
"""

import asyncio
import time
from collections import defaultdict, deque
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Deque
from dataclasses import dataclass, field
import threading
import psutil
import logging

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
        self._path_stats: Dict[str, Dict] = defaultdict(lambda: {
            'count': 0,
            'total_time': 0.0,
            'min_time': float('inf'),
            'max_time': 0.0,
            'error_count': 0
        })
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
            stats['count'] += 1
            stats['total_time'] += metrics.response_time
            stats['min_time'] = min(stats['min_time'], metrics.response_time)
            stats['max_time'] = max(stats['max_time'], metrics.response_time)

            if metrics.status_code >= 400:
                stats['error_count'] += 1

    def record_system_metrics(self) -> None:
        """记录系统指标"""
        try:
            with self._lock:
                metrics = SystemMetrics(
                    timestamp=datetime.utcnow(),
                    cpu_percent=psutil.cpu_percent(interval=None),
                    memory_percent=psutil.virtual_memory().percent,
                    disk_usage_percent=psutil.disk_usage('/').percent,
                    active_connections=self._active_requests,
                    request_count=len(self._request_metrics)
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
                m for m in self._request_metrics
                if m.timestamp > cutoff_time
            ]

            if not recent_requests:
                return {
                    'total_requests': 0,
                    'avg_response_time': 0.0,
                    'min_response_time': 0.0,
                    'max_response_time': 0.0,
                    'error_rate': 0.0,
                    'requests_per_minute': 0.0
                }

            response_times = [m.response_time for m in recent_requests]
            error_count = sum(1 for m in recent_requests if m.status_code >= 400)

            return {
                'total_requests': len(recent_requests),
                'avg_response_time': round(sum(response_times) / len(response_times), 3),
                'min_response_time': round(min(response_times), 3),
                'max_response_time': round(max(response_times), 3),
                'error_rate': round((error_count / len(recent_requests)) * 100, 2),
                'requests_per_minute': round(len(recent_requests) / minutes, 2)
            }

    def get_path_stats(self) -> Dict[str, Dict]:
        """获取路径统计信息"""
        with self._lock:
            stats = {}
            for path, data in self._path_stats.items():
                if data['count'] > 0:
                    stats[path] = {
                        'count': data['count'],
                        'avg_response_time': round(data['total_time'] / data['count'], 3),
                        'min_response_time': round(data['min_time'], 3),
                        'max_response_time': round(data['max_time'], 3),
                        'error_count': data['error_count'],
                        'error_rate': round((data['error_count'] / data['count']) * 100, 2)
                    }
            return stats

    def get_system_stats(self) -> Dict[str, Any]:
        """获取系统统计信息"""
        with self._lock:
            if not self._system_metrics:
                return {
                    'cpu_percent': 0.0,
                    'memory_percent': 0.0,
                    'disk_usage_percent': 0.0,
                    'active_connections': self._active_requests,
                    'uptime_seconds': round(time.time() - self._start_time, 2)
                }

            latest = self._system_metrics[-1]
            return {
                'cpu_percent': latest.cpu_percent,
                'memory_percent': latest.memory_percent,
                'disk_usage_percent': latest.disk_usage_percent,
                'active_connections': latest.active_connections,
                'uptime_seconds': round(time.time() - self._start_time, 2),
                'total_requests': latest.request_count
            }

    def get_performance_summary(self) -> Dict[str, Any]:
        """获取性能总结"""
        request_stats = self.get_request_stats()
        path_stats = self.get_path_stats()
        system_stats = self.get_system_stats()

        # 找出最慢的端点
        slowest_endpoints = sorted(
            [(path, stats) for path, stats in path_stats.items()],
            key=lambda x: x[1]['avg_response_time'],
            reverse=True
        )[:5]

        # 找出错误率最高的端点
        error_endpoints = sorted(
            [(path, stats) for path, stats in path_stats.items() if stats['error_rate'] > 0],
            key=lambda x: x[1]['error_rate'],
            reverse=True
        )[:5]

        return {
            'timestamp': datetime.utcnow().isoformat(),
            'request_stats': request_stats,
            'system_stats': system_stats,
            'slowest_endpoints': [
                {'path': path, 'avg_response_time': stats['avg_response_time']}
                for path, stats in slowest_endpoints
            ],
            'error_endpoints': [
                {'path': path, 'error_rate': stats['error_rate']}
                for path, stats in error_endpoints
            ]
        }

    def clear_old_metrics(self, hours: int = 24) -> None:
        """清理旧指标数据"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)

        with self._lock:
            # 清理请求指标
            self._request_metrics = deque(
                [m for m in self._request_metrics if m.timestamp > cutoff_time],
                maxlen=self.max_records
            )

            # 清理系统指标
            self._system_metrics = deque(
                [m for m in self._system_metrics if m.timestamp > cutoff_time],
                maxlen=self.max_records // 10
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
                user_agent=request.headers.get("user-agent", "")
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
                user_agent=request.headers.get("user-agent", "")
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
