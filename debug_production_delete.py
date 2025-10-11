#!/usr/bin/env python3
"""
生产环境删除功能调试脚本
"""

import json
import sys

import requests


def debug_production_delete():
    """调试生产环境删除功能"""
    print("🔍 生产环境删除功能调试")
    print("=" * 60)

    # 禁用SSL警告
    import urllib3

    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    base_url = "https://121.199.173.244"
    test_id = "550e8400-e29b-41d4-a716-446655440000"

    # 测试所有可能的删除端点路径
    delete_endpoints = [
        f"/api/v1/homework/{test_id}",  # 我们实现的端点
        f"/api/v1/homework/submissions/{test_id}",  # 可能的submissions端点
        f"/homework/{test_id}",  # 无前缀的端点
        f"/api/v1/homework/{test_id}/delete",  # 可能的动作端点
    ]

    print("📍 测试各种DELETE端点路径...")
    for endpoint in delete_endpoints:
        print(f"\n🔸 测试: DELETE {endpoint}")
        try:
            response = requests.delete(
                f"{base_url}{endpoint}", verify=False, timeout=10
            )
            print(f"   状态码: {response.status_code}")
            print(f"   响应: {response.text[:100]}")

            if response.status_code == 401:
                print("   ✅ 端点存在但需要认证")
            elif response.status_code == 403:
                print("   ✅ 端点存在但权限不足")
            elif response.status_code == 404:
                print("   ❌ 端点不存在")
            elif response.status_code == 405:
                print("   ❌ 方法不允许")
            else:
                print(f"   ⚠️ 其他状态码: {response.status_code}")

        except Exception as e:
            print(f"   ❌ 请求失败: {e}")

    # 测试批量删除
    print(f"\n📍 测试批量删除端点...")
    batch_endpoints = [
        "/api/v1/homework/batch-delete",
        "/homework/batch-delete",
    ]

    for endpoint in batch_endpoints:
        print(f"\n🔸 测试: POST {endpoint}")
        try:
            response = requests.post(
                f"{base_url}{endpoint}",
                json={"homework_ids": [test_id]},
                verify=False,
                timeout=10,
            )
            print(f"   状态码: {response.status_code}")
            print(f"   响应: {response.text[:100]}")

            if response.status_code == 401:
                print("   ✅ 端点存在但需要认证")
            elif response.status_code == 403:
                print("   ✅ 端点存在但权限不足")
            elif response.status_code == 404:
                print("   ❌ 端点不存在")
            else:
                print(f"   ⚠️ 其他状态码: {response.status_code}")

        except Exception as e:
            print(f"   ❌ 请求失败: {e}")

    # 获取OpenAPI文档检查端点
    print(f"\n📍 检查OpenAPI文档中的端点...")
    try:
        response = requests.get(f"{base_url}/openapi.json", verify=False, timeout=10)
        if response.status_code == 200:
            openapi_data = response.json()
            paths = openapi_data.get("paths", {})

            homework_paths = [path for path in paths.keys() if "homework" in path]
            print(f"   找到 {len(homework_paths)} 个作业相关端点:")
            for path in sorted(homework_paths):
                methods = list(paths[path].keys())
                print(f"     {path}: {methods}")

            # 检查是否存在DELETE方法
            delete_paths = []
            for path, methods in paths.items():
                if "homework" in path and "delete" in methods:
                    delete_paths.append(path)

            if delete_paths:
                print(f"\n   ✅ 找到DELETE端点: {delete_paths}")
            else:
                print(f"\n   ❌ 未找到DELETE端点")
        else:
            print(f"   无法获取OpenAPI文档: {response.status_code}")

    except Exception as e:
        print(f"   获取OpenAPI文档失败: {e}")

    print("\n" + "=" * 60)
    print("🎯 调试建议:")
    print("1. 检查前端实际发送的请求URL")
    print("2. 检查服务器日志中的DELETE请求")
    print("3. 验证前端和后端的路径是否一致")

    return True


if __name__ == "__main__":
    debug_production_delete()
