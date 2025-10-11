#!/usr/bin/env python3
"""
测试修复后的删除功能
"""

import requests
import json
import sys

def test_delete_functionality():
    """测试删除功能"""
    print("🔍 测试修复后的删除功能")
    print("=" * 60)
    
    # 禁用SSL警告
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    base_url = "https://121.199.173.244"
    
    # 测试DELETE端点是否存在
    test_endpoints = [
        f"/api/v1/homework/550e8400-e29b-41d4-a716-446655440000",  # 单个删除
        f"/api/v1/homework/batch-delete",  # 批量删除
    ]
    
    print("📍 测试DELETE端点可达性...")
    
    for endpoint in test_endpoints:
        print(f"\n🔸 测试: {endpoint}")
        try:
            if "batch-delete" in endpoint:
                # 测试POST批量删除
                response = requests.post(
                    f"{base_url}{endpoint}",
                    json={"homework_ids": ["550e8400-e29b-41d4-a716-446655440000"]},
                    verify=False, 
                    timeout=10
                )
            else:
                # 测试DELETE单个删除
                response = requests.delete(
                    f"{base_url}{endpoint}", 
                    verify=False, 
                    timeout=10
                )
            
            print(f"   状态码: {response.status_code}")
            
            if response.status_code == 401:
                print("   ✅ 端点存在，需要认证")
            elif response.status_code == 403:
                print("   ✅ 端点存在，权限检查正常")
            elif response.status_code == 404:
                print("   ❌ 端点不存在或路由错误")
            elif response.status_code == 422:
                print("   ✅ 端点存在，参数验证正常")
            else:
                print(f"   ℹ️ 其他状态码，响应: {response.text[:100]}")
                
        except requests.exceptions.RequestException as e:
            print(f"   ❌ 请求失败: {e}")
    
    print("\n" + "=" * 60)
    print("🎯 主要改进:")
    print("1. ✅ 修复了_delete_submission_files方法，先删除数据库中的图片记录")
    print("2. ✅ 修复了delete_submission方法，明确删除顺序避免外键约束冲突")
    print("3. ✅ 添加了删除批改记录的逻辑，确保完整清理")
    print("4. ✅ 改进了错误处理和类型安全")
    
    print("\n📋 下一步测试:")
    print("1. 登录生产环境测试实际的作业删除功能")
    print("2. 验证单个删除（右下角删除按钮）是否正常工作")
    print("3. 确认批量删除功能仍然正常")
    print("4. 检查数据库中的记录是否正确清理")

if __name__ == "__main__":
    test_delete_functionality()