#!/usr/bin/env python3
"""
生产环境图片上传问题诊断脚本

诊断内容：
1. OSS配置完整性检查
2. AIImageAccessService初始化状态
3. 网络连接测试
4. 降级方案路由检查
"""

import asyncio
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, "/Users/liguoma/my-devs/python/wuhao-tutor")

import httpx

from src.core.config import get_settings
from src.services.ai_image_service import AIImageAccessService


async def diagnose_oss_config():
    """诊断OSS配置"""
    print("🔍 诊断OSS配置...")
    settings = get_settings()

    print(f"   Bucket名称: {settings.OSS_BUCKET_NAME}")
    print(f"   端点地址: {settings.OSS_ENDPOINT}")
    print(
        f"   Access Key ID: {settings.OSS_ACCESS_KEY_ID[:10] if settings.OSS_ACCESS_KEY_ID else 'None'}..."
    )
    print(
        f"   Access Key Secret: {'已配置' if settings.OSS_ACCESS_KEY_SECRET else '未配置'}"
    )

    # 检查配置完整性
    required_fields = [
        settings.OSS_ACCESS_KEY_ID,
        settings.OSS_ACCESS_KEY_SECRET,
        settings.OSS_BUCKET_NAME,
    ]

    is_complete = all(required_fields)
    print(f"   配置完整性: {'✅ 完整' if is_complete else '❌ 不完整'}")

    return is_complete


async def test_ai_image_service():
    """测试AIImageAccessService初始化"""
    print("\n🧪 测试AIImageAccessService初始化...")

    try:
        service = AIImageAccessService()
        print(f"   OSS可用性: {'✅ 可用' if service.is_oss_available else '❌ 不可用'}")
        print(f"   Bucket对象: {'✅ 已初始化' if service.bucket else '❌ 未初始化'}")

        if service.is_oss_available:
            # 测试端点转换
            public_endpoint = service._get_public_endpoint()
            print(f"   公网端点: {public_endpoint}")

            # 测试URL生成
            test_object = "test/image.jpg"
            test_url = service._generate_ai_accessible_url(test_object)
            print(f"   测试URL: {test_url}")

            # 检查是否包含内网端点
            if "internal" in test_url:
                print("   ⚠️ 警告: 生成的URL包含内网端点，AI服务可能无法访问")
            else:
                print("   ✅ URL使用公网端点")

        return service.is_oss_available

    except Exception as e:
        print(f"   ❌ 初始化失败: {e}")
        return False


async def test_production_api():
    """测试生产环境API端点"""
    print("\n🌐 测试生产环境API端点...")

    base_url = "https://121.199.173.244"

    async with httpx.AsyncClient(timeout=10.0, verify=False) as client:
        try:
            # 测试文件健康检查
            response = await client.get(f"{base_url}/api/v1/files/health")
            print(f"   健康检查: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                storage = data.get("storage", {})
                print(f"   存储目录: {storage.get('upload_directory')}")
                print(f"   目录可写: {storage.get('directory_writable')}")
                print(f"   剩余空间: {storage.get('free_space_formatted')}")

            # 测试AI文件路由（这个应该是404）
            ai_file_response = await client.get(f"{base_url}/api/v1/files/ai/test.jpg")
            print(f"   AI文件路由: {ai_file_response.status_code} (预期404)")

        except Exception as e:
            print(f"   ❌ API测试失败: {e}")


async def check_local_fallback():
    """检查本地降级方案"""
    print("\n📁 检查本地降级方案...")

    settings = get_settings()
    upload_dir = Path("uploads/ai_analysis")

    print(f"   上传目录: {upload_dir.absolute()}")
    print(f"   目录存在: {'✅ 是' if upload_dir.exists() else '❌ 否'}")
    print(f"   BASE_URL配置: {settings.BASE_URL}")

    if settings.BASE_URL == "http://localhost:8000":
        print("   ⚠️ 警告: BASE_URL仍为localhost，生产环境无法访问")


async def main():
    """主诊断函数"""
    print("🩺 五好伴学图片上传问题诊断")
    print("=" * 50)

    # 1. OSS配置检查
    oss_complete = await diagnose_oss_config()

    # 2. 服务初始化检查
    oss_available = await test_ai_image_service()

    # 3. 生产环境API测试
    await test_production_api()

    # 4. 本地降级方案检查
    await check_local_fallback()

    # 总结诊断结果
    print("\n📋 诊断结果总结")
    print("=" * 30)

    if oss_complete and oss_available:
        print("✅ OSS配置正常，问题可能在网络连接或权限")
        print("   建议: 检查OSS bucket权限设置")
    elif oss_complete and not oss_available:
        print("❌ OSS配置存在但初始化失败")
        print("   建议: 检查OSS密钥是否正确")
    else:
        print("❌ OSS配置不完整，正在使用降级方案")
        print("   建议: 配置OSS或修复本地存储路由")

    print("\n🛠️ 修复建议:")
    print("1. 如需使用OSS: 配置完整的OSS环境变量")
    print("2. 如使用本地存储: 添加 /api/v1/files/ai/ 路由")
    print("3. 修复BASE_URL为生产环境地址")


if __name__ == "__main__":
    asyncio.run(main())
