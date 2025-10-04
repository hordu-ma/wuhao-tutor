#!/usr/bin/env python3
"""
前后端API集成测试
系统性检查前后端API对齐问题
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 设置测试环境
os.environ["ENVIRONMENT"] = "testing"


class APIIntegrationTester:
    """API集成测试器"""

    def __init__(self):
        self.results: List[Dict[str, Any]] = []
        self.errors: List[Dict[str, Any]] = []

    def log_test(self, endpoint: str, method: str, status: str, details: str = ""):
        """记录测试结果"""
        result = {
            "timestamp": datetime.now().isoformat(),
            "endpoint": endpoint,
            "method": method,
            "status": status,
            "details": details,
        }
        self.results.append(result)

        # 彩色输出
        status_color = {
            "✅ PASS": "\033[92m",
            "❌ FAIL": "\033[91m",
            "⚠️  WARN": "\033[93m",
            "ℹ️  INFO": "\033[94m",
        }
        reset = "\033[0m"
        color = status_color.get(status, "")
        print(f"{color}{status}{reset} [{method}] {endpoint} {details}")

    def log_error(self, category: str, error: str, fix_suggestion: str = ""):
        """记录错误"""
        error_item = {
            "category": category,
            "error": error,
            "fix_suggestion": fix_suggestion,
        }
        self.errors.append(error_item)

    async def test_api_routing(self, client):
        """测试API路由配置"""
        print("\n" + "=" * 60)
        print("📋 测试1: API路由配置")
        print("=" * 60)

        # 测试健康检查端点
        tests = [
            ("GET", "/api/v1/health/ping", "健康检查"),
            ("GET", "/api/v1/learning/health", "学习模块健康检查"),
            ("GET", "/api/v1/homework/health", "作业模块健康检查"),
        ]

        for method, endpoint, desc in tests:
            try:
                response = client.get(endpoint)
                if response.status_code == 200:
                    self.log_test(endpoint, method, "✅ PASS", desc)
                else:
                    self.log_test(
                        endpoint,
                        method,
                        "❌ FAIL",
                        f"{desc} - 状态码: {response.status_code}",
                    )
                    self.log_error(
                        "路由配置",
                        f"{endpoint} 返回 {response.status_code}",
                        "检查路由是否正确注册在 src/api/v1/api.py",
                    )
            except Exception as e:
                self.log_test(endpoint, method, "❌ FAIL", f"{desc} - 异常: {str(e)}")
                self.log_error(
                    "路由配置", f"{endpoint} 抛出异常: {str(e)}", "检查路由定义"
                )

    async def test_learning_api(self, client):
        """测试学习问答API"""
        print("\n" + "=" * 60)
        print("📋 测试2: 学习问答API")
        print("=" * 60)

        # 测试提问接口
        ask_payload = {
            "content": "什么是勾股定理？",
            "question_type": "concept",
            "subject": "math",
            "topic": "几何",
            "difficulty_level": 2,
        }

        try:
            response = client.post("/api/v1/learning/ask", json=ask_payload)
            self.log_test(
                "/api/v1/learning/ask",
                "POST",
                "✅ PASS" if response.status_code == 200 else "❌ FAIL",
                f"状态码: {response.status_code}",
            )

            if response.status_code != 200:
                self.log_error(
                    "学习API",
                    f"提问接口返回 {response.status_code}: {response.text}",
                    "检查请求体格式、认证状态、AI服务配置",
                )
            else:
                # 检查响应格式
                data = response.json()
                required_fields = ["answer_id", "answer", "session_id"]
                missing_fields = [f for f in required_fields if f not in data]
                if missing_fields:
                    self.log_error(
                        "响应格式",
                        f"响应缺少字段: {missing_fields}",
                        "检查后端响应模型定义",
                    )

        except Exception as e:
            self.log_test("/api/v1/learning/ask", "POST", "❌ FAIL", f"异常: {str(e)}")
            self.log_error(
                "学习API", f"提问接口异常: {str(e)}", "检查服务依赖和异常处理"
            )

        # 测试会话列表接口
        try:
            response = client.get("/api/v1/learning/sessions")
            self.log_test(
                "/api/v1/learning/sessions",
                "GET",
                "✅ PASS" if response.status_code == 200 else "❌ FAIL",
                f"状态码: {response.status_code}",
            )

            if response.status_code != 200:
                self.log_error(
                    "学习API",
                    f"会话列表接口返回 {response.status_code}",
                    "检查认证和数据库查询",
                )

        except Exception as e:
            self.log_test(
                "/api/v1/learning/sessions", "GET", "❌ FAIL", f"异常: {str(e)}"
            )

    async def test_homework_api(self, client):
        """测试作业批改API"""
        print("\n" + "=" * 60)
        print("📋 测试3: 作业批改API")
        print("=" * 60)

        # 检查路由前缀问题
        endpoints_to_test = [
            ("/api/v1/homework/templates", "GET", "模板列表（正确路径）"),
            ("/homework/templates", "GET", "模板列表（错误路径 - 缺少/api/v1）"),
        ]

        for endpoint, method, desc in endpoints_to_test:
            try:
                response = client.get(endpoint)
                if response.status_code == 200:
                    self.log_test(endpoint, method, "✅ PASS", desc)
                elif response.status_code == 404:
                    self.log_test(endpoint, method, "⚠️  WARN", f"{desc} - 未找到")
                    if "/api/v1/" not in endpoint:
                        self.log_error(
                            "路由前缀",
                            f"{endpoint} 404错误",
                            "前端可能使用了错误的baseURL，应为 /api/v1/homework",
                        )
                else:
                    self.log_test(
                        endpoint,
                        method,
                        "❌ FAIL",
                        f"{desc} - 状态码: {response.status_code}",
                    )
            except Exception as e:
                self.log_test(endpoint, method, "❌ FAIL", f"{desc} - 异常: {str(e)}")

        # 测试作业提交接口（需要文件上传）
        print("\n⚠️  作业提交接口需要文件上传，跳过自动测试")
        self.log_test(
            "/api/v1/homework/submit", "POST", "ℹ️  INFO", "需要手动测试文件上传"
        )

    async def test_authentication(self, client):
        """测试认证相关API"""
        print("\n" + "=" * 60)
        print("📋 测试4: 认证API")
        print("=" * 60)

        # 测试未认证访问受保护端点
        try:
            # 创建不带认证的客户端
            from fastapi.testclient import TestClient

            from src.main import app

            unauthenticated_client = TestClient(app)

            response = unauthenticated_client.post(
                "/api/v1/learning/ask",
                json={
                    "content": "测试",
                    "question_type": "concept",
                    "subject": "math",
                },
            )

            if response.status_code == 401 or response.status_code == 403:
                self.log_test(
                    "/api/v1/learning/ask", "POST", "✅ PASS", "正确拒绝未认证请求"
                )
            else:
                self.log_test(
                    "/api/v1/learning/ask",
                    "POST",
                    "⚠️  WARN",
                    f"未认证请求返回 {response.status_code}（应为401/403）",
                )
                self.log_error(
                    "认证",
                    "受保护端点未正确验证认证",
                    "检查 get_current_user_id 依赖",
                )

        except Exception as e:
            self.log_test(
                "/api/v1/learning/ask", "POST", "❌ FAIL", f"认证测试异常: {str(e)}"
            )

    async def test_response_format(self, client):
        """测试响应格式一致性"""
        print("\n" + "=" * 60)
        print("📋 测试5: 响应格式一致性")
        print("=" * 60)

        # 测试各接口的响应格式
        endpoints = [
            ("/api/v1/health/ping", "GET", {"status", "message"}),
            ("/api/v1/learning/health", "GET", {"status", "module", "timestamp"}),
            ("/api/v1/homework/health", "GET", {"status", "module", "version"}),
        ]

        for endpoint, method, expected_fields in endpoints:
            try:
                response = client.get(endpoint)
                if response.status_code == 200:
                    data = response.json()
                    actual_fields = set(data.keys())
                    missing = expected_fields - actual_fields
                    extra = actual_fields - expected_fields

                    if not missing and not extra:
                        self.log_test(endpoint, method, "✅ PASS", "响应格式正确")
                    else:
                        details = []
                        if missing:
                            details.append(f"缺少字段: {missing}")
                        if extra:
                            details.append(f"额外字段: {extra}")
                        self.log_test(endpoint, method, "⚠️  WARN", "; ".join(details))
                        self.log_error(
                            "响应格式",
                            f"{endpoint} 字段不匹配",
                            "统一响应格式，使用 schemas.common 中的模型",
                        )
            except Exception as e:
                self.log_test(endpoint, method, "❌ FAIL", f"异常: {str(e)}")

    def generate_report(self):
        """生成测试报告"""
        print("\n" + "=" * 60)
        print("📊 测试报告")
        print("=" * 60)

        # 统计测试结果
        total = len(self.results)
        passed = sum(1 for r in self.results if "PASS" in r["status"])
        failed = sum(1 for r in self.results if "FAIL" in r["status"])
        warned = sum(1 for r in self.results if "WARN" in r["status"])

        print(f"\n总测试数: {total}")
        print(f"✅ 通过: {passed}")
        print(f"❌ 失败: {failed}")
        print(f"⚠️  警告: {warned}")
        print(f"成功率: {passed/total*100:.1f}%")

        # 错误汇总
        if self.errors:
            print("\n" + "=" * 60)
            print("🔍 发现的问题及修复建议")
            print("=" * 60)

            for i, error in enumerate(self.errors, 1):
                print(f"\n{i}. 【{error['category']}】")
                print(f"   问题: {error['error']}")
                if error.get("fix_suggestion"):
                    print(f"   建议: {error['fix_suggestion']}")

        # 保存报告
        report_path = (
            project_root
            / "reports"
            / f"api_integration_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        report_path.parent.mkdir(exist_ok=True)

        report_data = {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total": total,
                "passed": passed,
                "failed": failed,
                "warned": warned,
                "success_rate": f"{passed/total*100:.1f}%",
            },
            "results": self.results,
            "errors": self.errors,
        }

        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)

        print(f"\n📄 详细报告已保存至: {report_path}")


async def main():
    """主测试函数"""
    print("🚀 开始前后端API集成测试...")
    print(f"⏰ 测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    try:
        # 导入必要的模块
        from fastapi.testclient import TestClient

        from src.api.dependencies.auth import (
            get_current_user,
            get_current_user_id,
            security,
        )
        from src.core.database import get_db
        from src.main import app

        # 简单的mock函数
        def mock_get_current_user_id():
            return "test-user-id-123"

        def mock_get_current_user():
            return {
                "id": "test-user-id-123",
                "username": "test_user",
                "role": "student",
            }

        async def mock_get_db():
            from sqlalchemy.ext.asyncio import (
                AsyncSession,
                async_sessionmaker,
                create_async_engine,
            )

            engine = create_async_engine("sqlite+aiosqlite:///:memory:")
            async_session = async_sessionmaker(
                engine, class_=AsyncSession, expire_on_commit=False
            )
            async with async_session() as session:
                yield session

        def mock_security():
            return None

        # 覆盖依赖
        app.dependency_overrides.clear()
        app.dependency_overrides[get_current_user_id] = mock_get_current_user_id
        app.dependency_overrides[get_current_user] = mock_get_current_user
        app.dependency_overrides[get_db] = mock_get_db
        app.dependency_overrides[security] = mock_security

        # 创建测试客户端
        client = TestClient(app)

        # 创建测试器
        tester = APIIntegrationTester()

        # 运行测试
        await tester.test_api_routing(client)
        await tester.test_learning_api(client)
        await tester.test_homework_api(client)
        await tester.test_authentication(client)
        await tester.test_response_format(client)

        # 生成报告
        tester.generate_report()

        print("\n✅ 测试完成!")

        # 返回错误数
        return len(tester.errors)

    except Exception as e:
        print(f"\n❌ 测试过程中发生错误: {str(e)}")
        import traceback

        traceback.print_exc()
        return -1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(min(exit_code, 1))  # 0表示成功，1表示有错误
