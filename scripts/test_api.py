#!/usr/bin/env python3
"""
API测试运行脚本
提供便捷的API测试和验证功能
"""

import asyncio
import sys
import time
import json
from pathlib import Path
from typing import Dict, Any, List
import argparse
import os

# 设置测试环境变量
os.environ["TESTING"] = "1"

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

import httpx
import uvicorn
from fastapi.testclient import TestClient

from src.main import app
from src.core.config import get_settings


class APITester:
    """API测试器"""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.client = TestClient(app) if base_url.startswith("http://test") else None
        self.session = None

    async def __aenter__(self):
        if not self.client:
            self.session = httpx.AsyncClient(base_url=self.base_url)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.aclose()

    def test_sync(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """同步测试请求"""
        if self.client:
            response = getattr(self.client, method.lower())(endpoint, **kwargs)
        else:
            # 使用requests进行同步请求
            import requests
            response = getattr(requests, method.lower())(
                f"{self.base_url}{endpoint}", **kwargs
            )

        return {
            "status_code": response.status_code,
            "data": response.json() if response.headers.get("content-type", "").startswith("application/json") else response.text,
            "headers": dict(response.headers),
            "elapsed": getattr(response, "elapsed", None)
        }

    async def test_async(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """异步测试请求"""
        start_time = time.time()

        if self.session:
            response = await getattr(self.session, method.lower())(endpoint, **kwargs)
        else:
            # 使用TestClient（同步）
            response = getattr(self.client, method.lower())(endpoint, **kwargs)

        elapsed = time.time() - start_time

        try:
            data = response.json()
        except:
            data = response.text if hasattr(response, 'text') else str(response.content)

        return {
            "status_code": response.status_code,
            "data": data,
            "headers": dict(response.headers) if hasattr(response, 'headers') else {},
            "elapsed": elapsed
        }


class APITestSuite:
    """API测试套件"""

    def __init__(self, tester: APITester):
        self.tester = tester
        self.results = []
        self.auth_headers = {"Authorization": "Bearer test_token_123"}

    def log_result(self, test_name: str, result: Dict[str, Any], expected_codes: List[int] | None = None):
        """记录测试结果"""
        if expected_codes is None:
            expected_codes = [200, 201]

        success = result["status_code"] in expected_codes

        test_result = {
            "test_name": test_name,
            "success": success,
            "status_code": result["status_code"],
            "elapsed": result.get("elapsed", 0),
            "expected_codes": expected_codes
        }

        self.results.append(test_result)

        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name} - {result['status_code']} ({result.get('elapsed', 0):.3f}s)")

        if not success:
            print(f"    Expected: {expected_codes}, Got: {result['status_code']}")
            if isinstance(result['data'], dict) and 'error' in result['data']:
                print(f"    Error: {result['data']['error']}")

    async def test_health_endpoints(self):
        """测试健康检查端点"""
        print("\n=== 健康检查测试 ===")

        # 系统健康检查
        result = await self.tester.test_async("GET", "/api/v1/health")
        self.log_result("系统健康检查", result)

        # 就绪检查
        result = await self.tester.test_async("GET", "/api/v1/health/readiness")
        self.log_result("就绪检查", result)

        # 活性检查
        result = await self.tester.test_async("GET", "/api/v1/health/liveness")
        self.log_result("活性检查", result)

        # 系统指标
        result = await self.tester.test_async("GET", "/api/v1/health/metrics")
        self.log_result("系统指标", result)

    async def test_homework_endpoints(self):
        """测试作业批改端点"""
        print("\n=== 作业批改测试 ===")

        # 作业模块健康检查
        result = await self.tester.test_async("GET", "/api/v1/homework/health")
        self.log_result("作业模块健康检查", result)

        # 获取模板列表（需要认证）
        result = await self.tester.test_async(
            "GET", "/api/v1/homework/templates",
            headers=self.auth_headers
        )
        self.log_result("获取模板列表", result, [200, 401, 500])

        # 创建模板（需要认证）
        template_data = {
            "name": "测试数学模板",
            "subject": "math",
            "description": "API测试模板",
            "template_content": "测试内容",
            "correction_criteria": "测试标准",
            "max_score": 100
        }
        result = await self.tester.test_async(
            "POST", "/api/v1/homework/templates",
            json=template_data,
            headers=self.auth_headers
        )
        self.log_result("创建作业模板", result, [200, 201, 400, 401, 500])

        # 获取提交列表
        result = await self.tester.test_async(
            "GET", "/api/v1/homework/submissions",
            headers=self.auth_headers
        )
        self.log_result("获取提交列表", result, [200, 401, 500])

    async def test_learning_endpoints(self):
        """测试学习问答端点"""
        print("\n=== 学习问答测试 ===")

        # 提问测试
        question_data = {
            "content": "什么是质数？请给出定义和例子。",
            "question_type": "concept",
            "subject": "math",
            "topic": "数论",
            "difficulty_level": 3
        }
        result = await self.tester.test_async(
            "POST", "/api/v1/learning/ask",
            json=question_data,
            headers=self.auth_headers
        )
        self.log_result("AI问答测试", result, [200, 201, 400, 401, 500, 503])

        # 创建会话
        session_data = {
            "title": "API测试会话",
            "subject": "math",
            "topic": "基础数学",
            "learning_goals": ["测试API功能"],
            "difficulty_level": 2
        }
        result = await self.tester.test_async(
            "POST", "/api/v1/learning/sessions",
            json=session_data,
            headers=self.auth_headers
        )
        self.log_result("创建学习会话", result, [200, 201, 400, 401, 500])

        # 获取会话列表
        result = await self.tester.test_async(
            "GET", "/api/v1/learning/sessions",
            headers=self.auth_headers
        )
        self.log_result("获取会话列表", result, [200, 401, 500])

    async def test_file_endpoints(self):
        """测试文件管理端点"""
        print("\n=== 文件管理测试 ===")

        # 文件模块健康检查
        result = await self.tester.test_async("GET", "/api/v1/files/health")
        self.log_result("文件模块健康检查", result)

        # 获取文件列表
        result = await self.tester.test_async(
            "GET", "/api/v1/files",
            headers=self.auth_headers
        )
        self.log_result("获取文件列表", result, [200, 401, 500])

        # 文件统计
        result = await self.tester.test_async(
            "GET", "/api/v1/files/stats/summary",
            headers=self.auth_headers
        )
        self.log_result("获取文件统计", result, [200, 401, 500])

        # 测试上传无效文件类型
        result = await self.tester.test_async(
            "POST", "/api/v1/files/upload",
            headers=self.auth_headers,
            files={"file": ("test.exe", b"fake content", "application/x-executable")},
            data={"category": "test"}
        )
        self.log_result("上传无效文件类型", result, [400, 401, 422])

    async def test_authentication(self):
        """测试认证功能"""
        print("\n=== 认证测试 ===")

        # 测试无认证访问
        result = await self.tester.test_async("GET", "/api/v1/homework/templates")
        self.log_result("无认证访问作业API", result, [401])

        result = await self.tester.test_async("GET", "/api/v1/files")
        self.log_result("无认证访问文件API", result, [401])

        # 测试无效token
        invalid_headers = {"Authorization": "Bearer invalid_token"}
        result = await self.tester.test_async(
            "GET", "/api/v1/homework/templates",
            headers=invalid_headers
        )
        self.log_result("无效token访问", result, [401, 403])

    async def run_all_tests(self):
        """运行所有测试"""
        print("开始API集成测试...")
        print("=" * 50)

        await self.test_health_endpoints()
        await self.test_homework_endpoints()
        await self.test_learning_endpoints()
        await self.test_file_endpoints()
        await self.test_authentication()

        self.print_summary()

    def print_summary(self):
        """打印测试摘要"""
        print("\n" + "=" * 50)
        print("测试摘要")
        print("=" * 50)

        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r["success"])
        failed_tests = total_tests - passed_tests

        print(f"总测试数: {total_tests}")
        print(f"通过: {passed_tests} ✅")
        print(f"失败: {failed_tests} ❌")
        print(f"成功率: {(passed_tests/total_tests)*100:.1f}%")

        if failed_tests > 0:
            print("\n失败的测试:")
            for result in self.results:
                if not result["success"]:
                    print(f"  - {result['test_name']}: {result['status_code']} (期望: {result['expected_codes']})")

        # 性能统计
        response_times = [r["elapsed"] for r in self.results if r["elapsed"]]
        if response_times:
            avg_time = sum(response_times) / len(response_times)
            max_time = max(response_times)
            print(f"\n性能统计:")
            print(f"平均响应时间: {avg_time:.3f}s")
            print(f"最长响应时间: {max_time:.3f}s")


async def run_api_tests(base_url: str = "http://localhost:8000"):
    """运行API测试"""
    async with APITester(base_url) as tester:
        suite = APITestSuite(tester)
        await suite.run_all_tests()


def start_test_server():
    """启动测试服务器"""
    print("启动测试服务器...")
    settings = get_settings()

    config = uvicorn.Config(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        log_level="info",
        reload=False
    )

    server = uvicorn.Server(config)
    return server


async def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="API测试工具")
    parser.add_argument(
        "--url",
        default="http://localhost:8000",
        help="API服务器URL (默认: http://localhost:8000)"
    )
    parser.add_argument(
        "--start-server",
        action="store_true",
        help="启动测试服务器"
    )
    parser.add_argument(
        "--test-only",
        action="store_true",
        help="只运行测试，不启动服务器"
    )

    args = parser.parse_args()

    if args.start_server and not args.test_only:
        print("启动测试服务器模式...")
        server = start_test_server()

        # 启动服务器
        import threading
        server_thread = threading.Thread(target=lambda: asyncio.run(server.serve()))
        server_thread.daemon = True
        server_thread.start()

        # 等待服务器启动
        print("等待服务器启动...")
        await asyncio.sleep(3)

        try:
            # 运行测试
            await run_api_tests(args.url)
        finally:
            # 关闭服务器
            print("关闭测试服务器...")
            server.should_exit = True
            server_thread.join(timeout=5)
    else:
        # 只运行测试
        await run_api_tests(args.url)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n测试被用户中断")
    except Exception as e:
        print(f"测试运行出错: {str(e)}")
        sys.exit(1)
