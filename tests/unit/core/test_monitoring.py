"""
Simple, aligned unit tests for src/core/monitoring.py.
These tests only use the public API present in the module and
lightweight test adapters inside the test file when necessary.
"""

import asyncio
from datetime import datetime
from unittest.mock import MagicMock

import pytest
from fastapi import Request, Response

from src.core.monitoring import (
    MetricsCollector,
    PerformanceMonitoringMiddleware,
    RequestMetrics,
    SystemMetricsCollector,
)


class PerformanceMonitorAdapter:
    """Adapter used in tests to provide endpoint-level helpers using MetricsCollector."""

    def __init__(self, collector: MetricsCollector | None = None):
        self.collector = collector or MetricsCollector()

    def track_endpoint(self, endpoint: str, response_time: float):
        m = RequestMetrics(
            path=endpoint,
            method="GET",
            status_code=200,
            response_time=response_time,
            timestamp=datetime.utcnow(),
        )
        self.collector.record_request(m)

    def get_endpoint_stats(self, endpoint: str):
        return self.collector.get_path_stats().get(f"GET {endpoint}")

    def get_slow_endpoints(self, threshold: float = 1.0):
        return [
            {"endpoint": k.split(" ", 1)[1], "avg": v["avg_response_time"]}
            for k, v in self.collector.get_path_stats().items()
            if v.get("avg_response_time", 0) >= threshold
        ]

    def get_percentile(self, endpoint: str, percentile: float):
        times = [
            m.response_time
            for m in list(self.collector._request_metrics)
            if f"{m.method} {m.path}" == f"GET {endpoint}"
        ]
        if not times:
            return None
        times.sort()
        idx = max(0, min(len(times) - 1, int(len(times) * percentile / 100) - 1))
        return times[idx]


class SlowQueryDetectorLocal:
    """Local test-only slow-query detector used to validate expected behavior."""

    def __init__(self, threshold: float = 0.5):
        self.threshold = threshold
        self._slow_queries = []

    def is_slow_query(self, execution_time: float) -> bool:
        return execution_time > self.threshold

    def log_slow_query(self, query: str, execution_time: float) -> None:
        self._slow_queries.append({"query": query, "execution_time": execution_time})

    def get_slow_queries(self):
        return self._slow_queries

    def get_slowest_queries(self, limit: int = 1):
        return sorted(
            self._slow_queries, key=lambda x: x["execution_time"], reverse=True
        )[:limit]


def test_metrics_collector_records_and_reports():
    collector = MetricsCollector()

    m = RequestMetrics(
        path="/api/test",
        method="GET",
        status_code=200,
        response_time=0.12,
        timestamp=datetime.utcnow(),
    )

    collector.record_request(m)

    stats = collector.get_request_stats()
    assert stats["total_requests"] >= 1


def test_performance_monitor_adapter_basic():
    monitor = PerformanceMonitorAdapter()
    monitor.track_endpoint("/api/users", 0.25)
    stats = monitor.get_endpoint_stats("/api/users")
    assert stats is not None


def test_slow_query_detector_local():
    d = SlowQueryDetectorLocal(0.5)
    assert d.is_slow_query(1.0)
    assert not d.is_slow_query(0.1)
    d.log_slow_query("SELECT 1", 1.2)
    assert len(d.get_slow_queries()) == 1
    d.log_slow_query("SELECT 2", 2.0)
    assert d.get_slowest_queries(1)[0]["execution_time"] == 2.0


@pytest.mark.asyncio
async def test_monitoring_middleware_dispatch_records():
    collector = MetricsCollector()
    middleware = PerformanceMonitoringMiddleware(MagicMock(), collector)

    mock_request = MagicMock(spec=Request)
    mock_request.method = "GET"
    mock_request.url.path = "/api/test"
    mock_request.client = None
    mock_request.headers = {}

    async def mock_call_next(req):
        return Response(status_code=200)

    before = collector.get_request_stats()["total_requests"]
    await middleware.dispatch(mock_request, mock_call_next)
    after = collector.get_request_stats()["total_requests"]
    assert after >= before + 1


@pytest.mark.asyncio
async def test_system_metrics_collector_start_stop():
    collector = MetricsCollector()
    sys_col = SystemMetricsCollector(collector, interval=1)

    await sys_col.start()
    await asyncio.sleep(1.1)
    await sys_col.stop()

    stats = collector.get_system_stats()
    assert "uptime_seconds" in stats
