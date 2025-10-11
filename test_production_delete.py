#!/usr/bin/env python3
"""
生产环境作业删除功能验证脚本
"""

import json

import requests


def test_production_delete_endpoints():
    """测试生产环境删除端点"""
    print("🔍 生产环境作业删除功能验证")
    print("=" * 50)

    base_url = "https://121.199.173.244/api/v1/homework"
    test_id = "550e8400-e29b-41d4-a716-446655440000"

    # 禁用SSL警告 (自签名证书)
    import urllib3

    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    # 测试1: 作业模块健康检查
    print("📍 测试1: 作业模块健康检查")
    try:
        response = requests.get(f"{base_url}/health", verify=False, timeout=10)
        if response.status_code == 200:
            print("✅ 作业模块运行正常")
            print(f"   响应: {response.json()}")
        else:
            print(f"❌ 作业模块异常: {response.status_code}")
    except Exception as e:
        print(f"❌ 连接失败: {e}")
        return False

    # 测试2: DELETE端点存在性
    print("\n📍 测试2: 删除端点验证")
    try:
        response = requests.delete(f"{base_url}/{test_id}", verify=False, timeout=10)
        if response.status_code == 403:
            print("✅ DELETE端点存在且需要认证 (符合预期)")
        elif response.status_code == 404:
            print("❌ DELETE端点不存在 (修复失败)")
            return False
        else:
            print(f"✅ DELETE端点存在 (状态码: {response.status_code})")
    except Exception as e:
        print(f"❌ DELETE端点测试失败: {e}")
        return False

    # 测试3: 批量删除端点
    print("\n📍 测试3: 批量删除端点验证")
    try:
        response = requests.post(
            f"{base_url}/batch-delete",
            json={"homework_ids": [test_id]},
            verify=False,
            timeout=10,
        )
        if response.status_code == 403:
            print("✅ 批量删除端点存在且需要认证 (符合预期)")
        elif response.status_code == 404:
            print("❌ 批量删除端点不存在 (修复失败)")
            return False
        else:
            print(f"✅ 批量删除端点存在 (状态码: {response.status_code})")
    except Exception as e:
        print(f"❌ 批量删除端点测试失败: {e}")
        return False

    # 测试4: 前端可访问性
    print("\n📍 测试4: 前端页面可访问性")
    try:
        response = requests.get("https://121.199.173.244", verify=False, timeout=10)
        if response.status_code == 200:
            print("✅ 前端页面可访问")
        else:
            print(f"⚠️ 前端访问异常: {response.status_code}")
    except Exception as e:
        print(f"⚠️ 前端访问测试失败: {e}")

    print("\n" + "=" * 50)
    print("🎉 生产环境验证完成!")
    print("\n💡 验证结果说明:")
    print("- 返回403表示端点存在但需要用户认证 ✅")
    print("- 返回404表示端点不存在 ❌")
    print("- 修复成功的标志是返回403而不是404")
    print("\n🌐 前端访问地址: https://121.199.173.244")
    print("📋 管理员可通过前端界面测试完整的删除功能")

    return True


if __name__ == "__main__":
    test_production_delete_endpoints()
