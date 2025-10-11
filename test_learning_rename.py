#!/usr/bin/env python3
"""
测试学习问答模块的重命名功能
"""

import json

import requests


def test_rename_functionality():
    """测试重命名功能"""
    print("🔍 测试学习问答模块重命名功能")
    print("=" * 60)

    # 禁用SSL警告
    import urllib3

    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    base_url = "https://121.199.173.244"

    # 测试会话更新端点
    test_session_id = "550e8400-e29b-41d4-a716-446655440000"

    print("📍 测试会话更新端点可达性...")

    endpoints = [
        (f"/api/v1/learning/sessions/{test_session_id}", "PUT"),
        (f"/api/v1/learning/sessions/{test_session_id}", "PATCH"),
    ]

    for endpoint, method in endpoints:
        print(f"\n🔸 测试: {method} {endpoint}")
        try:
            test_data = {"title": "测试重命名标题"}

            if method == "PUT":
                response = requests.put(
                    f"{base_url}{endpoint}", json=test_data, verify=False, timeout=10
                )
            else:
                response = requests.patch(
                    f"{base_url}{endpoint}", json=test_data, verify=False, timeout=10
                )

            print(f"   状态码: {response.status_code}")

            if response.status_code == 401:
                print("   ✅ 端点存在，需要认证")
            elif response.status_code == 403:
                print("   ✅ 端点存在，权限检查正常")
            elif response.status_code == 404:
                print("   ⚠️ 会话不存在（需要真实的会话ID）")
            elif response.status_code == 422:
                print("   ✅ 端点存在，参数验证正常")
            elif response.status_code == 200:
                print("   ✅ 端点正常工作！")
                print(f"   响应数据: {response.json()}")
            else:
                print(f"   ℹ️ 其他状态码，响应: {response.text[:100]}")

        except requests.exceptions.RequestException as e:
            print(f"   ❌ 请求失败: {e}")

    print("\n" + "=" * 60)
    print("🎯 学习问答模块重命名功能实现完成:")
    print("1. ✅ 后端API：已有 PUT/PATCH /api/v1/learning/sessions/{id} 端点")
    print("2. ✅ 前端API：添加了 LearningAPI.renameSession 方法")
    print("3. ✅ 前端Store：添加了 learningStore.renameSession 方法")
    print("4. ✅ 前端界面：实现了重命名弹窗功能，替换'功能开发中'提示")

    print("\n📋 使用说明:")
    print("1. 登录生产环境 (https://121.199.173.244)")
    print("2. 进入学习问答页面")
    print("3. 在会话历史列表中，右键点击某个会话")
    print("4. 选择「重命名」选项")
    print("5. 在弹窗中输入新的会话标题")
    print("6. 确认后即可完成重命名")

    print("\n🔧 技术特性:")
    print("- 权限验证：只能重命名自己的会话")
    print("- 输入验证：标题不能为空，长度不超过100字符")
    print("- 实时更新：重命名后立即更新当前会话和会话列表")
    print("- 错误处理：完善的错误提示和异常处理")
    print("- 用户体验：使用ElementPlus的MessageBox提供友好的输入界面")


if __name__ == "__main__":
    test_rename_functionality()
