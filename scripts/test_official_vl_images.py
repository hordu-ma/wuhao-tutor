#!/usr/bin/env python3
"""
使用官方示例图片测试百炼VL模型

通过使用阿里云官方文档中的示例图片URL，验证我们的代码逻辑是否正确
"""

import asyncio
import sys

sys.path.insert(0, "/Users/liguoma/my-devs/python/wuhao-tutor")

from typing import Any, Dict, List, Union

from src.services.bailian_service import (
    AIContext,
    BailianService,
    ChatMessage,
    MessageRole,
)


async def test_with_official_image():
    """使用官方示例图片测试VL模型"""
    print("🧪 使用官方示例图片测试百炼VL模型...")

    # 使用官方文档中的示例图片URL
    official_image_urls = [
        "https://help-static-aliyun-doc.aliyuncs.com/file-manage-files/zh-CN/20241022/emyrja/dog_and_girl.jpeg",
        "https://dashscope.oss-cn-beijing.aliyuncs.com/images/tiger.png",
    ]

    for i, image_url in enumerate(official_image_urls, 1):
        print(f"\n📷 测试官方图片 {i}: {image_url}")

        # 创建测试消息
        messages: List[Union[Dict[str, Any], ChatMessage]] = [
            ChatMessage(
                role=MessageRole.SYSTEM, content="You are a helpful assistant."
            ),
            ChatMessage(
                role=MessageRole.USER,
                content="请描述这张图片的内容",
                image_urls=[image_url],
            ),
        ]

        # 创建百炼服务和上下文
        bailian_service = BailianService()
        context = AIContext(user_id="test_user", session_id="test_session")

        try:
            print(f"   📤 发送请求...")

            response = await bailian_service.chat_completion(
                messages=messages, context=context, max_tokens=500, temperature=0.7
            )

            print(f"   📥 响应结果:")
            print(f"      成功: {response.success}")
            print(f"      模型: {response.model}")
            print(f"      Token使用: {response.tokens_used}")

            if response.success:
                print(f"      🤖 AI回复: {response.content[:200]}...")
                print(f"   ✅ 官方图片 {i} 测试成功")
            else:
                print(f"      ❌ 失败: {response.error_message}")

        except Exception as e:
            print(f"   ❌ 异常: {str(e)}")


async def test_oss_image_access():
    """测试OSS图片访问权限"""
    print("\n🔐 测试OSS图片访问权限...")

    # 构建我们自己的OSS图片URL格式
    from src.core.config import get_settings

    settings = get_settings()

    # 模拟我们生成的OSS URL
    our_oss_urls = [
        f"https://{settings.OSS_BUCKET_NAME}.oss-cn-hangzhou.aliyuncs.com/ai_analysis/test_user/sample.jpg",
        f"https://{settings.OSS_BUCKET_NAME}.oss-cn-hangzhou.aliyuncs.com/uploads/test-image.png",
    ]

    print(f"📍 我们的OSS配置:")
    print(f"   Bucket: {settings.OSS_BUCKET_NAME}")
    print(f"   Endpoint: {settings.OSS_ENDPOINT}")

    for i, test_url in enumerate(our_oss_urls, 1):
        print(f"\n🔗 测试URL {i}: {test_url}")

        # 先测试URL是否可访问
        import httpx

        try:
            async with httpx.AsyncClient() as client:
                response = await client.head(test_url, timeout=10.0)
                print(f"   HTTP状态: {response.status_code}")
                if response.status_code == 200:
                    print(f"   ✅ URL可访问")
                elif response.status_code == 404:
                    print(f"   ⚠️  文件不存在")
                elif response.status_code == 403:
                    print(f"   ❌ 访问被拒绝（权限问题）")
                else:
                    print(f"   ⚠️  其他状态码")
        except Exception as e:
            print(f"   ❌ 网络请求失败: {e}")


async def test_base64_alternative():
    """测试Base64编码替代方案"""
    print("\n🔄 测试Base64编码替代方案...")

    # 创建一个简单的测试图片的Base64编码
    # 这里使用一个最小的1x1像素PNG图片的Base64
    base64_image = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="

    print(f"📎 使用Base64编码图片")

    messages: List[Union[Dict[str, Any], ChatMessage]] = [
        ChatMessage(role=MessageRole.SYSTEM, content="You are a helpful assistant."),
        ChatMessage(
            role=MessageRole.USER, content="这是一个测试图片", image_urls=[base64_image]
        ),
    ]

    bailian_service = BailianService()
    context = AIContext(user_id="test_user", session_id="test_session")

    try:
        print("   📤 发送Base64编码图片请求...")

        response = await bailian_service.chat_completion(
            messages=messages, context=context, max_tokens=200, temperature=0.7
        )

        print(f"   📥 Base64测试结果:")
        print(f"      成功: {response.success}")
        if response.success:
            print(f"      🤖 AI回复: {response.content}")
            print(f"   ✅ Base64编码支持正常")
        else:
            print(f"      ❌ 失败: {response.error_message}")

    except Exception as e:
        print(f"   ❌ Base64测试异常: {str(e)}")


async def main():
    """主函数"""
    print("🔍 百炼VL模型图片访问问题深度诊断")
    print("=" * 60)

    # 1. 使用官方示例图片测试
    await test_with_official_image()

    # 2. 测试OSS访问权限
    await test_oss_image_access()

    # 3. 测试Base64替代方案
    await test_base64_alternative()

    print("\n📋 诊断总结:")
    print("1. 如果官方图片测试成功，说明我们的代码逻辑正确")
    print("2. 如果我们的OSS URL无法访问，需要检查OSS权限设置")
    print("3. Base64编码可以作为备选方案")

    print("\n💡 可能的解决方案:")
    print("1. 检查并修复OSS bucket的公开读取权限")
    print("2. 将图片转换为Base64编码发送")
    print("3. 使用CDN域名替代原始OSS域名")
    print("4. 联系阿里云技术支持确认域名白名单")


if __name__ == "__main__":
    asyncio.run(main())
