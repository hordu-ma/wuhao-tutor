#!/usr/bin/env python3
"""
作业API性能测试脚本
测试作业相关API端点的性能并生成报告
"""

import asyncio
import json
import statistics
import time
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import aiohttp

# 测试配置
BASE_URL = "http://localhost:8000/api/v1"
TEST_USER_ID = "550e8400-e29b-41d4-a716-446655440000"  # 测试用户ID
API_ENDPOINTS = {
    "submissions_list": "/homework/submissions",
    "submission_detail": "/homework/submissions/{submission_id}",
    "correction_result": "/homework/submissions/{submission_id}/correction",
    "statistics": "/homework/stats",
}

# 测试参数
CONCURRENT_REQUESTS = 10  # 并发请求数
REQUESTS_PER_ENDPOINT = 50  # 每个端点的请求次数


class APIPerformanceTester:
    """API性能测试器"""

    def __init__(self):
        self.session = None
        self.results = {}

    async def __aenter__(self):
        """异步上下文管理器入口"""
        timeout = aiohttp.ClientTimeout(total=30)
        self.session = aiohttp.ClientSession(
            timeout=timeout,
            headers={
                "Content-Type": "application/json",
                "User-Agent": "PerformanceTest/1.0",
                "X-User-ID": TEST_USER_ID,  # 模拟用户认证
            },
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        if self.session:
            await self.session.close()

    async def test_endpoint(
        self, endpoint_name: str, url: str, params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """测试单个端点性能"""
        print(f"\n🚀 测试端点: {endpoint_name}")
        print(f"   URL: {url}")

        response_times = []
        error_count = 0
        status_codes = {}

        # 执行测试请求
        for i in range(REQUESTS_PER_ENDPOINT):
            start_time = time.time()

            try:
                if not self.session:
                    raise RuntimeError("HTTP session not initialized")

                async with self.session.get(url, params=params) as response:
                    response_data = await response.text()
                    end_time = time.time()

                    response_time = (end_time - start_time) * 1000  # 转换为毫秒
                    response_times.append(response_time)

                    # 统计状态码
                    status_code = response.status
                    status_codes[status_code] = status_codes.get(status_code, 0) + 1

                    if status_code >= 400:
                        error_count += 1
                        print(
                            f"   ❌ 错误 #{i+1}: {status_code} - {response_data[:100]}"
                        )
                    elif i % 10 == 0:
                        print(f"   ✅ 请求 #{i+1}: {response_time:.2f}ms")

            except Exception as e:
                error_count += 1
                end_time = time.time()
                response_time = (end_time - start_time) * 1000
                response_times.append(response_time)
                print(f"   ❌ 异常 #{i+1}: {str(e)}")

        # 计算统计数据
        if response_times:
            avg_time = statistics.mean(response_times)
            median_time = statistics.median(response_times)
            min_time = min(response_times)
            max_time = max(response_times)
            p95_time = sorted(response_times)[int(len(response_times) * 0.95)]
            p99_time = sorted(response_times)[int(len(response_times) * 0.99)]
        else:
            avg_time = median_time = min_time = max_time = p95_time = p99_time = 0

        result = {
            "endpoint": endpoint_name,
            "total_requests": REQUESTS_PER_ENDPOINT,
            "error_count": error_count,
            "error_rate": (error_count / REQUESTS_PER_ENDPOINT) * 100,
            "status_codes": status_codes,
            "response_times": {
                "average": round(avg_time, 2),
                "median": round(median_time, 2),
                "min": round(min_time, 2),
                "max": round(max_time, 2),
                "p95": round(p95_time, 2),
                "p99": round(p99_time, 2),
            },
        }

        return result

    async def test_concurrent_requests(
        self, url: str, concurrent_count: int = CONCURRENT_REQUESTS
    ) -> Dict[str, Any]:
        """测试并发请求性能"""
        print(f"\n🔥 并发测试: {concurrent_count} 个并发请求")

        start_time = time.time()

        # 创建并发任务
        tasks = []
        for i in range(concurrent_count):
            task = asyncio.create_task(self.single_request(url, f"concurrent-{i}"))
            tasks.append(task)

        # 等待所有任务完成
        results = await asyncio.gather(*tasks, return_exceptions=True)

        end_time = time.time()
        total_time = (end_time - start_time) * 1000

        # 分析结果
        success_count = 0
        error_count = 0
        response_times = []

        for result in results:
            if isinstance(result, Exception):
                error_count += 1
            elif isinstance(result, dict):
                success_count += 1
                response_times.append(result.get("response_time", 0))

        return {
            "concurrent_requests": concurrent_count,
            "total_time": round(total_time, 2),
            "success_count": success_count,
            "error_count": error_count,
            "throughput": round(
                success_count / (total_time / 1000), 2
            ),  # requests per second
            "avg_response_time": (
                round(statistics.mean(response_times), 2) if response_times else 0
            ),
        }

    async def single_request(self, url: str, request_id: str) -> Dict[str, Any]:
        """执行单个请求"""
        start_time = time.time()

        try:
            if not self.session:
                raise RuntimeError("HTTP session not initialized")

            async with self.session.get(url) as response:
                await response.text()
                end_time = time.time()

                return {
                    "request_id": request_id,
                    "status_code": response.status,
                    "response_time": (end_time - start_time) * 1000,
                    "success": response.status < 400,
                }
        except Exception as e:
            end_time = time.time()
            return {
                "request_id": request_id,
                "error": str(e),
                "response_time": (end_time - start_time) * 1000,
                "success": False,
            }

    async def run_performance_tests(self):
        """运行所有性能测试"""
        print("🎯 开始作业API性能测试")
        print(f"   测试目标: {BASE_URL}")
        print(f"   每个端点请求数: {REQUESTS_PER_ENDPOINT}")
        print(f"   并发请求数: {CONCURRENT_REQUESTS}")

        all_results = []

        # 1. 测试提交列表端点
        list_url = f"{BASE_URL}{API_ENDPOINTS['submissions_list']}"
        list_params = {"page": 1, "size": 20, "status": "reviewed"}
        list_result = await self.test_endpoint(
            "submissions_list", list_url, list_params
        )
        all_results.append(list_result)

        # 2. 测试统计端点
        stats_url = f"{BASE_URL}{API_ENDPOINTS['statistics']}"
        stats_params = {"granularity": "day"}
        stats_result = await self.test_endpoint("statistics", stats_url, stats_params)
        all_results.append(stats_result)

        # 3. 测试提交详情端点（需要实际的submission_id）
        # 这里使用一个示例ID，实际测试时应该使用真实ID
        sample_submission_id = "660e8400-e29b-41d4-a716-446655440001"
        detail_url = f"{BASE_URL}{API_ENDPOINTS['submission_detail'].format(submission_id=sample_submission_id)}"
        detail_result = await self.test_endpoint("submission_detail", detail_url)
        all_results.append(detail_result)

        # 4. 测试批改结果端点
        correction_url = f"{BASE_URL}{API_ENDPOINTS['correction_result'].format(submission_id=sample_submission_id)}"
        correction_params = {"format_type": "json"}
        correction_result = await self.test_endpoint(
            "correction_result", correction_url, correction_params
        )
        all_results.append(correction_result)

        # 5. 并发测试（使用最快的端点）
        fastest_endpoint = min(
            all_results, key=lambda x: x["response_times"]["average"]
        )
        if fastest_endpoint["endpoint"] == "submissions_list":
            concurrent_url = list_url
        elif fastest_endpoint["endpoint"] == "statistics":
            concurrent_url = stats_url
        else:
            concurrent_url = list_url  # 默认使用列表端点

        concurrent_result = await self.test_concurrent_requests(concurrent_url)

        # 生成报告
        self.generate_report(all_results, concurrent_result)

    def generate_report(self, results: List[Dict], concurrent_result: Dict):
        """生成性能测试报告"""
        print("\n" + "=" * 80)
        print("📊 性能测试报告")
        print("=" * 80)

        # 1. 端点性能汇总
        print("\n🔍 端点性能汇总:")
        print(
            f"{'端点名称':<20} {'平均响应时间':<12} {'P95响应时间':<12} {'错误率':<8} {'状态'}"
        )
        print("-" * 70)

        for result in results:
            endpoint = result["endpoint"]
            avg_time = result["response_times"]["average"]
            p95_time = result["response_times"]["p95"]
            error_rate = result["error_rate"]

            # 评估性能状态
            if avg_time < 100 and error_rate < 1:
                status = "✅ 优秀"
            elif avg_time < 500 and error_rate < 5:
                status = "⚠️  良好"
            else:
                status = "❌ 需优化"

            print(
                f"{endpoint:<20} {avg_time:<12.2f}ms {p95_time:<12.2f}ms {error_rate:<8.1f}% {status}"
            )

        # 2. 详细性能数据
        print("\n📈 详细性能数据:")
        for result in results:
            print(f"\n{result['endpoint']}:")
            print(f"  总请求数: {result['total_requests']}")
            print(f"  错误数量: {result['error_count']}")
            print(f"  响应时间 - 平均: {result['response_times']['average']}ms")
            print(f"  响应时间 - 中位数: {result['response_times']['median']}ms")
            print(f"  响应时间 - 最小: {result['response_times']['min']}ms")
            print(f"  响应时间 - 最大: {result['response_times']['max']}ms")
            print(f"  响应时间 - P95: {result['response_times']['p95']}ms")
            print(f"  响应时间 - P99: {result['response_times']['p99']}ms")
            print(f"  状态码分布: {result['status_codes']}")

        # 3. 并发测试结果
        print(f"\n🔥 并发测试结果:")
        print(f"  并发请求数: {concurrent_result['concurrent_requests']}")
        print(f"  总耗时: {concurrent_result['total_time']}ms")
        print(f"  成功请求: {concurrent_result['success_count']}")
        print(f"  失败请求: {concurrent_result['error_count']}")
        print(f"  吞吐量: {concurrent_result['throughput']} req/s")
        print(f"  平均响应时间: {concurrent_result['avg_response_time']}ms")

        # 4. 性能建议
        print(f"\n💡 性能优化建议:")

        slow_endpoints = [r for r in results if r["response_times"]["average"] > 500]
        if slow_endpoints:
            print("  📌 响应时间超过500ms的端点需要优化:")
            for ep in slow_endpoints:
                print(f"     - {ep['endpoint']}: {ep['response_times']['average']}ms")

        high_error_endpoints = [r for r in results if r["error_rate"] > 5]
        if high_error_endpoints:
            print("  📌 错误率超过5%的端点需要检查:")
            for ep in high_error_endpoints:
                print(f"     - {ep['endpoint']}: {ep['error_rate']}%")

        if concurrent_result["throughput"] < 10:
            print("  📌 并发性能较低，建议:")
            print("     - 检查数据库连接池配置")
            print("     - 优化SQL查询")
            print("     - 考虑添加缓存")

        # 5. 数据库索引建议
        print(f"\n🗄️  数据库索引建议:")
        print("  建议添加以下复合索引以优化查询性能:")
        print("  1. homework_submissions 表:")
        print(
            "     - CREATE INDEX idx_submissions_student_created ON homework_submissions(student_id, created_at);"
        )
        print(
            "     - CREATE INDEX idx_submissions_status_created ON homework_submissions(status, created_at);"
        )
        print("  2. homework_reviews 表:")
        print(
            "     - CREATE INDEX idx_reviews_submission_status ON homework_reviews(submission_id, status);"
        )
        print(
            "     - CREATE INDEX idx_reviews_completed_at ON homework_reviews(completed_at);"
        )
        print("  3. homework 表:")
        print(
            "     - CREATE INDEX idx_homework_subject_grade ON homework(subject, grade_level);"
        )

        print("\n" + "=" * 80)
        print(f"测试完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)


async def main():
    """主函数"""
    print("🎯 作业API性能测试工具")
    print(f"目标服务器: {BASE_URL}")

    try:
        async with APIPerformanceTester() as tester:
            await tester.run_performance_tests()
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {e}")


if __name__ == "__main__":
    asyncio.run(main())
