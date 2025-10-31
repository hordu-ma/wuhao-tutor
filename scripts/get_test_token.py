#!/usr/bin/env python3
"""
获取测试用户的访问令牌

用于测试需要认证的API端点
"""
import asyncio
import os
import sys

import httpx

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


async def get_test_token():
    """获取测试用户token"""
    base_url = "https://horsduroot.com"

    # 使用测试账号（需要先在数据库中创建）
    # 或者使用已有的测试账号
    login_data = {
        "phone": os.getenv("TEST_USERNAME", "13800000001"),
        "password": os.getenv("TEST_PASSWORD", "password123"),
    }

    print("=" * 80)
    print("登录获取测试Token")
    print("=" * 80)
    print(f"URL: {base_url}/api/v1/auth/login")
    print(f"手机号: {login_data['phone']}")
    print()

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{base_url}/api/v1/auth/login",
                json=login_data,
            )

            if response.status_code == 200:
                data = response.json()
                token = data.get("access_token")

                print("✅ 登录成功!")
                print()
                print("📋 Token信息:")
                print(f"   Access Token: {token}")
                print()
                print("💡 使用方法:")
                print(f"   export TEST_TOKEN='{token}'")
                print()
                print("   或者在测试脚本中:")
                print(
                    f"   TEST_TOKEN='{token}' python scripts/test_ask_stream_endpoint.py"
                )

                return token
            else:
                print(f"❌ 登录失败: {response.status_code}")
                print(f"   响应: {response.text}")
                return None

    except Exception as e:
        print(f"❌ 登录错误: {e}")
        import traceback

        traceback.print_exc()
        return None


async def create_test_user():
    """创建测试用户（如果不存在）"""
    base_url = "https://horsduroot.com"

    register_data = {
        "username": os.getenv("TEST_USERNAME", "test_user"),
        "password": os.getenv("TEST_PASSWORD", "test123456"),
        "nickname": "测试用户",
        "grade": "grade_9",
    }

    print("=" * 80)
    print("创建测试用户")
    print("=" * 80)
    print(f"用户名: {register_data['username']}")

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{base_url}/api/v1/auth/register",
                json=register_data,
            )

            if response.status_code == 200:
                print("✅ 用户创建成功")
                return True
            elif response.status_code == 400:
                print("ℹ️  用户已存在，跳过创建")
                return True
            else:
                print(f"❌ 创建失败: {response.status_code}")
                print(f"   响应: {response.text}")
                return False

    except Exception as e:
        print(f"❌ 创建用户错误: {e}")
        return False


async def main():
    """主函数"""
    # 先尝试创建测试用户
    print("Step 1: 确保测试用户存在")
    await create_test_user()
    print()

    # 登录获取token
    print("Step 2: 登录获取Token")
    token = await get_test_token()

    if token:
        print()
        print("=" * 80)
        print("✅ 准备就绪！现在可以运行:")
        print(f"   TEST_TOKEN='{token}' python scripts/test_ask_stream_endpoint.py")
        print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
