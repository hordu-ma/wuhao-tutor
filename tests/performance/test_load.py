"""
API性能和负载测试脚本
测试API端点的响应时间、并发能力和系统稳定性
"""

import asyncio
import logging
import statistics
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional

import aiohttp
import pytest

logger = logging.getLogger(__name__)


@dataclass
class LoadTestResult:
    """负载测试结果"""

    endpoint: str
    method: str
    total_requests: int
    successful_requests: int
    failed_requests: int
    avg_response_time: float
    min_response_time: float
    max_response_time: float
    percentile_95: float
    percentile_99: float
    requests_per_second: float
    error_rate: float
    errors: List[str] = field(default_factory=list)


@dataclass
class RequestResult:
    """单次请求结果"""

    success: bool
    response_time: float
    status_code: int
    error_message: Optional[str] = None


class LoadTester:
    """负载测试器"""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        """异步上下文管理器入口"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            connector=aiohttp.TCPConnector(limit=100),
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        if self.session:
            await self.session.close()

    async def single_request(
        self,
        endpoint: str,
        method: str = "GET",
        json_data: Optional[Dict] = None,
        headers: Optional[Dict] = None,
    ) -> RequestResult:
        """执行单次请求"""
        start_time = time.time()

        try:
            url = f"{self.base_url}{endpoint}"

            async with self.session.request(
                method=method, url=url, json=json_data, headers=headers
            ) as response:
                response_time = time.time() - start_time
                await response.text()  # 读取响应内容

                return RequestResult(
                    success=response.status < 400,
                    response_time=response_time,
                    status_code=response.status,
                    error_message=None
                    if response.status < 400
                    else f"HTTP {response.status}",
                )

        except Exception as e:
            response_time = time.time() - start_time
            return RequestResult(
                success=False,
                response_time=response_time,
                status_code=0,
                error_message=str(e),
            )

    async def concurrent_load_test(
        self,
        endpoint: str,
        concurrent_users: int,
        requests_per_user: int,
        method: str = "GET",
        json_data: Optional[Dict] = None,
        headers: Optional[Dict] = None,
    ) -> LoadTestResult:
        """并发负载测试"""
        print(f"开始负载测试: {endpoint}")
        print(f"并发用户数: {concurrent_users}, 每用户请求数: {requests_per_user}")

        start_time = time.time()

        # 创建任务
        tasks = []
        for _ in range(concurrent_users):
            for _ in range(requests_per_user):
                task = asyncio.create_task(
                    self.single_request(endpoint, method, json_data, headers)
                )
                tasks.append(task)

        # 执行所有任务
        results = await asyncio.gather(*tasks)

        total_time = time.time() - start_time

        # 分析结果
        successful_results = [r for r in results if r.success]
        failed_results = [r for r in results if not r.success]

        response_times = [r.response_time for r in successful_results]

        if response_times:
            avg_response_time = statistics.mean(response_times)
            min_response_time = min(response_times)
            max_response_time = max(response_times)
            percentile_95 = self._percentile(response_times, 95)
            percentile_99 = self._percentile(response_times, 99)
        else:
            avg_response_time = 0
            min_response_time = 0
            max_response_time = 0
            percentile_95 = 0
            percentile_99 = 0

        total_requests = len(results)
        successful_requests = len(successful_results)
        failed_requests = len(failed_results)
        requests_per_second = total_requests / total_time
        error_rate = (failed_requests / total_requests) * 100

        # 收集错误信息
        errors = [r.error_message for r in failed_results if r.error_message]
        error_summary = list(set(errors))[:10]  # 最多显示10种不同错误

        result = LoadTestResult(
            endpoint=endpoint,
            method=method,
            total_requests=total_requests,
            successful_requests=successful_requests,
            failed_requests=failed_requests,
            avg_response_time=avg_response_time,
            min_response_time=min_response_time,
            max_response_time=max_response_time,
            percentile_95=percentile_95,
            percentile_99=percentile_99,
            requests_per_second=requests_per_second,
            error_rate=error_rate,
            errors=error_summary,
        )

        self._print_result(result)
        return result

    def _percentile(self, data: List[float], percentile: float) -> float:
        """计算百分位数"""
        if not data:
            return 0.0

        sorted_data = sorted(data)
        index = (percentile / 100) * (len(sorted_data) - 1)

        if index.is_integer():
            return sorted_data[int(index)]
        else:
            lower = sorted_data[int(index)]
            upper = sorted_data[int(index) + 1]
            return lower + (upper - lower) * (index - int(index))

    def _print_result(self, result: LoadTestResult):
        """打印测试结果"""
        print(f"\n{'=' * 60}")
        print(f"负载测试结果: {result.method} {result.endpoint}")
        print(f"{'=' * 60}")
        print(f"总请求数:     {result.total_requests}")
        print(f"成功请求数:   {result.successful_requests}")
        print(f"失败请求数:   {result.failed_requests}")
        print(f"错误率:       {result.error_rate:.2f}%")
        print(f"平均响应时间: {result.avg_response_time:.3f}s")
        print(f"最小响应时间: {result.min_response_time:.3f}s")
        print(f"最大响应时间: {result.max_response_time:.3f}s")
        print(f"95%响应时间:  {result.percentile_95:.3f}s")
        print(f"99%响应时间:  {result.percentile_99:.3f}s")
        print(f"吞吐量:       {result.requests_per_second:.2f} req/s")

        if result.errors:
            print("\n主要错误:")
            for error in result.errors[:5]:
                print(f"  - {error}")

        print(f"{'=' * 60}\n")


class PerformanceTestSuite:
    """性能测试套件"""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.results: List[LoadTestResult] = []

    async def run_basic_health_tests(self) -> List[LoadTestResult]:
        """运行基础健康检查测试"""
        tests = [
            {
                "endpoint": "/health",
                "method": "GET",
                "concurrent_users": 10,
                "requests_per_user": 10,
                "description": "健康检查端点",
            },
            {
                "endpoint": "/health/readiness",
                "method": "GET",
                "concurrent_users": 5,
                "requests_per_user": 5,
                "description": "就绪检查端点",
            },
            {
                "endpoint": "/health/liveness",
                "method": "GET",
                "concurrent_users": 20,
                "requests_per_user": 10,
                "description": "活性检查端点",
            },
        ]

        results = []
        async with LoadTester(self.base_url) as tester:
            for test in tests:
                print(f"\n运行测试: {test['description']}")
                result = await tester.concurrent_load_test(
                    endpoint=test["endpoint"],
                    method=test["method"],
                    concurrent_users=test["concurrent_users"],
                    requests_per_user=test["requests_per_user"],
                )
                results.append(result)

                # 测试间隔，避免压力过大
                await asyncio.sleep(1)

        self.results.extend(results)
        return results

    async def run_api_stress_tests(self) -> List[LoadTestResult]:
        """运行API压力测试"""
        tests = [
            {
                "endpoint": "/api/v1/health/metrics",
                "method": "GET",
                "concurrent_users": 5,
                "requests_per_user": 10,
                "description": "系统指标端点",
            },
            {
                "endpoint": "/api/v1/health/performance",
                "method": "GET",
                "concurrent_users": 3,
                "requests_per_user": 5,
                "description": "性能监控端点",
            },
        ]

        results = []
        async with LoadTester(self.base_url) as tester:
            for test in tests:
                print(f"\n运行压力测试: {test['description']}")
                result = await tester.concurrent_load_test(
                    endpoint=test["endpoint"],
                    method=test["method"],
                    concurrent_users=test["concurrent_users"],
                    requests_per_user=test["requests_per_user"],
                )
                results.append(result)

                # 测试间隔
                await asyncio.sleep(2)

        self.results.extend(results)
        return results

    async def run_rate_limit_tests(self) -> List[LoadTestResult]:
        """运行限流测试"""
        print("\n运行限流测试...")

        async with LoadTester(self.base_url) as tester:
            # 快速发送大量请求，触发限流
            result = await tester.concurrent_load_test(
                endpoint="/health",
                method="GET",
                concurrent_users=20,
                requests_per_user=10,
            )

            self.results.append(result)
            return [result]

    def generate_report(self) -> str:
        """生成测试报告"""
        if not self.results:
            return "没有测试结果"

        report = []
        report.append("=" * 80)
        report.append("性能测试报告")
        report.append(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"测试基础URL: {self.base_url}")
        report.append("=" * 80)

        # 汇总统计
        total_requests = sum(r.total_requests for r in self.results)
        total_successful = sum(r.successful_requests for r in self.results)
        total_failed = sum(r.failed_requests for r in self.results)
        overall_error_rate = (
            (total_failed / total_requests * 100) if total_requests > 0 else 0
        )

        report.append("\n总体统计:")
        report.append(f"  总请求数: {total_requests}")
        report.append(f"  成功请求: {total_successful}")
        report.append(f"  失败请求: {total_failed}")
        report.append(f"  整体错误率: {overall_error_rate:.2f}%")

        # 性能指标
        avg_response_times = [
            r.avg_response_time for r in self.results if r.successful_requests > 0
        ]
        if avg_response_times:
            report.append(f"  平均响应时间: {statistics.mean(avg_response_times):.3f}s")
            report.append(f"  最佳响应时间: {min(avg_response_times):.3f}s")
            report.append(f"  最差响应时间: {max(avg_response_times):.3f}s")

        # 详细结果
        report.append("\n详细结果:")
        report.append("-" * 80)
        for result in self.results:
            report.append(f"端点: {result.method} {result.endpoint}")
            report.append(
                f"  成功率: {((result.successful_requests / result.total_requests) * 100):.1f}%"
            )
            report.append(f"  平均响应时间: {result.avg_response_time:.3f}s")
            report.append(f"  95%响应时间: {result.percentile_95:.3f}s")
            report.append(f"  吞吐量: {result.requests_per_second:.2f} req/s")
            if result.errors:
                report.append(f"  主要错误: {', '.join(result.errors[:3])}")
            report.append("")

        # 性能评估
        report.append("性能评估:")
        report.append("-" * 40)

        if overall_error_rate < 1:
            report.append("✅ 错误率良好 (< 1%)")
        elif overall_error_rate < 5:
            report.append("⚠️  错误率一般 (1-5%)")
        else:
            report.append("❌ 错误率过高 (> 5%)")

        if avg_response_times and statistics.mean(avg_response_times) < 1.0:
            report.append("✅ 响应时间良好 (< 1s)")
        elif avg_response_times and statistics.mean(avg_response_times) < 3.0:
            report.append("⚠️  响应时间一般 (1-3s)")
        else:
            report.append("❌ 响应时间过慢 (> 3s)")

        total_rps = sum(r.requests_per_second for r in self.results)
        if total_rps > 100:
            report.append("✅ 吞吐量良好 (> 100 req/s)")
        elif total_rps > 50:
            report.append("⚠️  吞吐量一般 (50-100 req/s)")
        else:
            report.append("❌ 吞吐量偏低 (< 50 req/s)")

        report.append("=" * 80)

        return "\n".join(report)


# pytest测试用例
class TestPerformance:
    """性能测试类"""

    @pytest.mark.asyncio
    async def test_health_endpoint_performance(self):
        """测试健康检查端点性能"""
        suite = PerformanceTestSuite()
        results = await suite.run_basic_health_tests()

        # 断言检查
        for result in results:
            assert result.error_rate < 10, f"错误率过高: {result.error_rate}%"
            assert result.avg_response_time < 2.0, (
                f"响应时间过慢: {result.avg_response_time}s"
            )
            assert result.requests_per_second > 10, (
                f"吞吐量过低: {result.requests_per_second} req/s"
            )

    @pytest.mark.asyncio
    async def test_api_stress_performance(self):
        """测试API压力性能"""
        suite = PerformanceTestSuite()
        results = await suite.run_api_stress_tests()

        # 检查关键指标
        for result in results:
            assert result.error_rate < 20, f"压力测试错误率过高: {result.error_rate}%"
            assert result.percentile_95 < 5.0, (
                f"95%响应时间过慢: {result.percentile_95}s"
            )

    @pytest.mark.asyncio
    async def test_rate_limiting(self):
        """测试限流功能"""
        suite = PerformanceTestSuite()
        results = await suite.run_rate_limit_tests()

        # 检查是否有限流响应
        for result in results:
            # 在高并发情况下应该有一些429响应
            if result.total_requests > 100:
                assert result.error_rate > 0, "高并发测试应该触发限流"


# 主执行函数
async def main():
    """主测试函数"""
    print("开始性能测试...")

    suite = PerformanceTestSuite()

    # 运行所有测试
    await suite.run_basic_health_tests()
    await suite.run_api_stress_tests()
    await suite.run_rate_limit_tests()

    # 生成报告
    report = suite.generate_report()
    print("\n" + report)

    # 保存报告
    with open("performance_test_report.txt", "w", encoding="utf-8") as f:
        f.write(report)

    print("\n报告已保存到: performance_test_report.txt")


if __name__ == "__main__":
    asyncio.run(main())
