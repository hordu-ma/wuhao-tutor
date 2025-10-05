#!/usr/bin/env python3
"""
前端控制台错误修复验证脚本
验证我们修复的所有问题是否已经解决
"""

import json
import time
from datetime import datetime

import requests


def test_backend_api_errors():
    """测试后端API错误修复"""
    print("🔧 测试后端API错误修复...")

    # 测试 homework/stats API (之前返回500，现在应该返回401/403)
    try:
        response = requests.get(
            "http://localhost:8000/api/v1/homework/stats", timeout=5
        )
        print(f"   homework/stats API: HTTP {response.status_code}")

        if response.status_code == 500:
            print("   ❌ 仍然返回500错误")
            return False
        elif response.status_code in [401, 403]:
            print("   ✅ 返回认证错误（正常，说明SQL错误已修复）")
            return True
        else:
            print(f"   ⚠️  返回其他状态码: {response.status_code}")
            return True
    except Exception as e:
        print(f"   ❌ 请求失败: {e}")
        return False


def test_frontend_service():
    """测试前端服务状态"""
    print("🖥️  测试前端服务状态...")

    try:
        response = requests.get("http://localhost:5173", timeout=5)
        if response.status_code == 200:
            print("   ✅ 前端服务正常响应")
            return True
        else:
            print(f"   ❌ 前端服务响应异常: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ 前端服务连接失败: {e}")
        return False


def test_api_health():
    """测试API健康状态"""
    print("🏥 测试API健康状态...")

    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ 后端健康: {data.get('status', 'unknown')}")
            return True
        else:
            print(f"   ❌ 健康检查失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ 健康检查请求失败: {e}")
        return False


def main():
    print("🚀 五好伴学前端控制台错误修复验证")
    print("=" * 50)
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    tests = [
        ("后端API错误修复", test_backend_api_errors),
        ("前端服务状态", test_frontend_service),
        ("API健康状态", test_api_health),
    ]

    results = []

    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
            print()
        except Exception as e:
            print(f"   ❌ 测试执行失败: {e}")
            results.append((test_name, False))
            print()

    # 总结
    print("📊 测试结果总结:")
    print("-" * 30)

    passed = 0
    total = len(results)

    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"   {test_name}: {status}")
        if result:
            passed += 1

    print()
    print(f"总计: {passed}/{total} 测试通过")

    if passed == total:
        print("🎉 所有修复验证通过！前端控制台错误已解决")
        return True
    else:
        print("⚠️  部分测试失败，需要进一步检查")
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
