#!/usr/bin/env python3
"""
学习问答API简单测试
绕过复杂的认证系统，直接测试API功能
"""

import asyncio
import os
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 设置测试环境
os.environ["ENVIRONMENT"] = "testing"


async def main():
    print("🔍 开始学习问答API简单测试...")

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
        from src.services.auth_service import get_auth_service
        from src.services.user_service import get_user_service
        from tests.conftest import (
            mock_get_auth_service,
            mock_get_current_user,
            mock_get_current_user_id,
            mock_get_user_service,
            mock_http_bearer,
            override_get_db,
        )

        print("✅ 成功导入模块")

        # 设置所有必要的依赖覆盖
        app.dependency_overrides.clear()  # 清除任何现有覆盖
        app.dependency_overrides[get_db] = override_get_db
        app.dependency_overrides[get_current_user] = mock_get_current_user
        app.dependency_overrides[get_current_user_id] = mock_get_current_user_id
        app.dependency_overrides[security] = mock_http_bearer
        app.dependency_overrides[get_auth_service] = mock_get_auth_service
        app.dependency_overrides[get_user_service] = mock_get_user_service

        print(f"✅ 设置了 {len(app.dependency_overrides)} 个依赖覆盖")

        # 创建测试客户端
        client = TestClient(app)
        print("✅ 创建测试客户端")

        # 测试1: 健康检查
        print("\n🧪 测试1: 健康检查")
        try:
            response = client.get("/api/v1/health")
            print(f"健康检查 - 状态码: {response.status_code}")
        except Exception as e:
            print(f"健康检查失败: {e}")

        # 测试2: 提问API
        print("\n🧪 测试2: 学习提问API")
        try:
            question_data = {
                "content": "什么是二次函数？",
                "question_type": "concept",
                "subject": "math",
                "topic": "functions",
                "difficulty_level": 3,
            }

            response = client.post(
                "/api/v1/learning/ask",
                json=question_data,
                headers={"Authorization": "Bearer mock_jwt_token"},
            )

            print(f"提问API - 状态码: {response.status_code}")
            print(f"响应内容: {response.text[:200]}...")

            if response.status_code == 200:
                print("✅ 学习提问API测试成功!")
            elif response.status_code == 401:
                print("❌ 认证问题仍然存在")
            elif response.status_code >= 500:
                print("⚠️ 服务器内部错误（可能是服务未完全实现）")
            else:
                print(f"⚠️ 其他状态码: {response.status_code}")

        except Exception as e:
            print(f"提问API测试失败: {e}")

        # 测试3: 创建会话API
        print("\n🧪 测试3: 创建学习会话API")
        try:
            session_data = {
                "session_name": "测试会话",
                "subject": "math",
                "topic": "algebra",
                "difficulty_level": 3,
            }

            response = client.post(
                "/api/v1/learning/sessions",
                json=session_data,
                headers={"Authorization": "Bearer mock_jwt_token"},
            )

            print(f"创建会话API - 状态码: {response.status_code}")
            print(f"响应内容: {response.text[:200]}...")

            if response.status_code in [200, 201]:
                print("✅ 创建会话API测试成功!")
            elif response.status_code == 401:
                print("❌ 认证问题仍然存在")
            elif response.status_code >= 500:
                print("⚠️ 服务器内部错误（可能是服务未完全实现）")
            else:
                print(f"⚠️ 其他状态码: {response.status_code}")

        except Exception as e:
            print(f"创建会话API测试失败: {e}")

        # 测试4: 获取会话列表API
        print("\n🧪 测试4: 获取会话列表API")
        try:
            response = client.get(
                "/api/v1/learning/sessions",
                headers={"Authorization": "Bearer mock_jwt_token"},
            )

            print(f"获取会话列表API - 状态码: {response.status_code}")
            print(f"响应内容: {response.text[:200]}...")

            if response.status_code == 200:
                print("✅ 获取会话列表API测试成功!")
            elif response.status_code == 401:
                print("❌ 认证问题仍然存在")
            elif response.status_code >= 500:
                print("⚠️ 服务器内部错误（可能是服务未完全实现）")
            else:
                print(f"⚠️ 其他状态码: {response.status_code}")

        except Exception as e:
            print(f"获取会话列表API测试失败: {e}")

        print("\n🎉 学习问答API测试完成!")

    except Exception as e:
        print(f"❌ 测试执行失败: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
