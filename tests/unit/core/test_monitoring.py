"""
监控模块单元测试
测试性能指标收集、慢查询检测等功能
"""

import pytest
import time
from unittest.mock import MagicMock, patch
from fastapi import Request, Response

from src.core.monitoring import (
    MetricsCollector,
    PerformanceMonitor,
    SlowQueryDetector
)


class TestMetricsCollector:
    """指标收集器测试"""

    def test_metrics_collector_initialization(self):
        """测试指标收集器初始化"""
        collector = MetricsCollector()
        
        assert collector is not None
        assert hasattr(collector, 'request_count')
        assert hasattr(collector, 'response_times')

    def test_record_request(self):
        """测试记录请求"""
        collector = MetricsCollector()
        
        collector.record_request(
            method="GET",
            path="/api/test",
            status_code=200,
            response_time=0.1
        )
        
        assert collector.request_count > 0

    def test_record_multiple_requests(self):
        """测试记录多个请求"""
        collector = MetricsCollector()
        
        for i in range(10):
            collector.record_request(
                method="GET",
                path="/api/test",
                status_code=200,
                response_time=0.1 * (i + 1)
            )
        
        assert collector.request_count == 10

    def test_get_average_response_time(self):
        """测试获取平均响应时间"""
        collector = MetricsCollector()
        
        # 记录响应时间: 0.1, 0.2, 0.3
        for time_val in [0.1, 0.2, 0.3]:
            collector.record_request(
                method="GET",
                path="/api/test",
                status_code=200,
                response_time=time_val
            )
        
        avg_time = collector.get_average_response_time()
        
        assert avg_time == pytest.approx(0.2, rel=0.1)

    def test_get_request_count_by_status(self):
        """测试按状态码统计请求"""
        collector = MetricsCollector()
        
        # 记录不同状态码
        collector.record_request("GET", "/api/test", 200, 0.1)
        collector.record_request("GET", "/api/test", 200, 0.1)
        collector.record_request("GET", "/api/test", 404, 0.1)
        collector.record_request("GET", "/api/test", 500, 0.1)
        
        count_200 = collector.get_request_count_by_status(200)
        count_404 = collector.get_request_count_by_status(404)
        
        assert count_200 == 2
        assert count_404 == 1

    def test_get_metrics_summary(self):
        """测试获取指标摘要"""
        collector = MetricsCollector()
        
        for _ in range(5):
            collector.record_request("GET", "/api/test", 200, 0.1)
        
        summary = collector.get_metrics_summary()
        
        assert "total_requests" in summary
        assert "average_response_time" in summary
        assert summary["total_requests"] == 5


class TestPerformanceMonitor:
    """性能监控器测试"""

    def test_performance_monitor_initialization(self):
        """测试性能监控器初始化"""
        monitor = PerformanceMonitor()
        
        assert monitor is not None

    def test_track_endpoint_performance(self):
        """测试跟踪端点性能"""
        monitor = PerformanceMonitor()
        
        endpoint = "/api/users"
        response_time = 0.25
        
        monitor.track_endpoint(endpoint, response_time)
        
        stats = monitor.get_endpoint_stats(endpoint)
        
        assert stats is not None
        assert stats["count"] > 0

    def test_identify_slow_endpoints(self):
        """测试识别慢端点"""
        monitor = PerformanceMonitor()
        
        # 添加快速端点
        monitor.track_endpoint("/api/fast", 0.05)
        monitor.track_endpoint("/api/fast", 0.06)
        
        # 添加慢端点
        monitor.track_endpoint("/api/slow", 1.5)
        monitor.track_endpoint("/api/slow", 2.0)
        
        slow_endpoints = monitor.get_slow_endpoints(threshold=1.0)
        
        assert len(slow_endpoints) > 0
        assert any(e["endpoint"] == "/api/slow" for e in slow_endpoints)

    def test_get_percentile_response_time(self):
        """测试获取响应时间百分位数"""
        monitor = PerformanceMonitor()
        
        endpoint = "/api/test"
        
        # 添加多个响应时间
        for i in range(100):
            monitor.track_endpoint(endpoint, i * 0.01)  # 0.00 到 0.99
        
        p95 = monitor.get_percentile(endpoint, 95)
        
        assert p95 is not None
        assert p95 > 0.9  # 95th百分位应该接近0.95


class TestSlowQueryDetector:
    """慢查询检测器测试"""

    def test_slow_query_detector_initialization(self):
        """测试慢查询检测器初始化"""
        detector = SlowQueryDetector(threshold=0.5)
        
        assert detector is not None
        assert detector.threshold == 0.5

    def test_detect_slow_query(self):
        """测试检测慢查询"""
        detector = SlowQueryDetector(threshold=0.5)
        
        # 模拟慢查询
        query = "SELECT * FROM users WHERE id = 1"
        execution_time = 1.5
        
        is_slow = detector.is_slow_query(execution_time)
        
        assert is_slow is True

    def test_detect_fast_query(self):
        """测试检测快速查询"""
        detector = SlowQueryDetector(threshold=0.5)
        
        query = "SELECT * FROM users WHERE id = 1"
        execution_time = 0.1
        
        is_slow = detector.is_slow_query(execution_time)
        
        assert is_slow is False

    def test_log_slow_query(self):
        """测试记录慢查询"""
        detector = SlowQueryDetector(threshold=0.5)
        
        query = "SELECT * FROM large_table"
        execution_time = 2.0
        
        detector.log_slow_query(query, execution_time)
        
        slow_queries = detector.get_slow_queries()
        
        assert len(slow_queries) > 0
        assert slow_queries[0]["query"] == query

    def test_get_slowest_queries(self):
        """测试获取最慢查询"""
        detector = SlowQueryDetector(threshold=0.5)
        
        # 记录多个慢查询
        detector.log_slow_query("QUERY 1", 1.0)
        detector.log_slow_query("QUERY 2", 2.0)
        detector.log_slow_query("QUERY 3", 1.5)
        
        slowest = detector.get_slowest_queries(limit=2)
        
        assert len(slowest) == 2
        assert slowest[0]["execution_time"] == 2.0  # 最慢的应该在第一位


class TestMonitoringMiddleware:
    """监控中间件测试"""

    @pytest.mark.asyncio
    async def test_middleware_records_request(self):
        """测试中间件记录请求"""
        collector = MetricsCollector()
        
        # 创建mock中间件
        from src.core.monitoring import create_monitoring_middleware
        
        mock_app = MagicMock()
        middleware = create_monitoring_middleware(mock_app, collector)
        
        # Mock request
        mock_request = MagicMock(spec=Request)
        mock_request.method = "GET"
        mock_request.url.path = "/api/test"
        
        # Mock call_next
        mock_response = Response(status_code=200)
        
        async def mock_call_next(request):
            return mock_response
        
        initial_count = collector.request_count
        
        # 执行中间件
        await middleware.dispatch(mock_request, mock_call_next)
        
        assert collector.request_count > initial_count

    @pytest.mark.asyncio
    async def test_middleware_measures_response_time(self):
        """测试中间件测量响应时间"""
        collector = MetricsCollector()
        
        from src.core.monitoring import create_monitoring_middleware
        
        mock_app = MagicMock()
        middleware = create_monitoring_middleware(mock_app, collector)
        
        mock_request = MagicMock(spec=Request)
        mock_request.method = "GET"
        mock_request.url.path = "/api/test"
        
        async def slow_call_next(request):
            await asyncio.sleep(0.1)  # 模拟慢响应
            return Response(status_code=200)
        
        import asyncio
        await middleware.dispatch(mock_request, slow_call_next)
        
        avg_time = collector.get_average_response_time()
        assert avg_time > 0


class TestMetricsExport:
    """指标导出测试"""

    def test_export_prometheus_format(self):
        """测试导出Prometheus格式"""
        collector = MetricsCollector()
        
        # 记录一些请求
        collector.record_request("GET", "/api/test", 200, 0.1)
        collector.record_request("POST", "/api/test", 201, 0.2)
        
        prometheus_data = collector.export_prometheus()
        
        assert prometheus_data is not None
        assert "request_count" in prometheus_data or isinstance(prometheus_data, str)

    def test_export_json_format(self):
        """测试导出JSON格式"""
        collector = MetricsCollector()
        
        collector.record_request("GET", "/api/test", 200, 0.1)
        
        json_data = collector.export_json()
        
        assert json_data is not None
        assert isinstance(json_data, (dict, str))


class TestMonitoringEdgeCases:
    """监控边界情况测试"""

    def test_collector_with_zero_requests(self):
        """测试零请求的收集器"""
        collector = MetricsCollector()
        
        avg_time = collector.get_average_response_time()
        
        assert avg_time == 0 or avg_time is None

    def test_detector_with_zero_threshold(self):
        """测试零阈值的检测器"""
        detector = SlowQueryDetector(threshold=0.0)
        
        # 任何查询都应该被视为慢查询
        is_slow = detector.is_slow_query(0.001)
        
        assert is_slow is True

    def test_monitor_endpoint_stats_not_found(self):
        """测试获取不存在端点的统计"""
        monitor = PerformanceMonitor()
        
        stats = monitor.get_endpoint_stats("/api/nonexistent")
        
        assert stats is None or stats == {}

    def test_concurrent_metric_recording(self):
        """测试并发指标记录"""
        collector = MetricsCollector()
        
        import threading
        
        def record_metric():
            for _ in range(10):
                collector.record_request("GET", "/api/test", 200, 0.1)
        
        threads = [threading.Thread(target=record_metric) for _ in range(5)]
        
        for thread in threads:
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # 应该记录了50个请求
        assert collector.request_count == 50


class TestAlertingThresholds:
    """告警阈值测试"""

    def test_trigger_high_response_time_alert(self):
        """测试触发高响应时间告警"""
        monitor = PerformanceMonitor()
        
        # 设置告警阈值
        alert_threshold = 1.0
        
        # 记录高响应时间
        monitor.track_endpoint("/api/test", 2.0)
        
        should_alert = monitor.should_alert("/api/test", alert_threshold)
        
        assert should_alert is True

    def test_trigger_high_error_rate_alert(self):
        """测试触发高错误率告警"""
        collector = MetricsCollector()
        
        # 记录大量错误
        for _ in range(7):
            collector.record_request("GET", "/api/test", 500, 0.1)
        
        for _ in range(3):
            collector.record_request("GET", "/api/test", 200, 0.1)
        
        error_rate = collector.get_error_rate()
        
        # 错误率应该是70%
        assert error_rate > 0.6
