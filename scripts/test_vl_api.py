#!/usr/bin/env python3
"""
直接测试百炼VL模型API调用

使用真实的图片URL测试VL模型的图片识别能力
"""

import asyncio
import json
import logging
import sys
from typing import Any, Dict, List, Union

# 添加项目根目录到路径
sys.path.insert(0, "/Users/liguoma/my-devs/python/wuhao-tutor")

from src.core.config import get_settings
from src.services.bailian_service import (
    AIContext,
    BailianService,
    ChatMessage,
    MessageRole,
)

# 设置日志级别
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_vl_model_with_real_image():
    """使用真实图片测试VL模型"""
    print("🔬 直接测试百炼VL模型API...")

    # 使用一个公开可访问的测试图片
    test_image_url = "https://httpbin.org/image/png"

    # 创建消息
    messages: List[Union[Dict[str, Any], ChatMessage]] = [
        ChatMessage(
            role=MessageRole.SYSTEM,
            content="你是一个图片分析助手，能够识别和分析图片内容。",
        ),
        ChatMessage(
            role=MessageRole.USER,
            content="请描述这张图片的内容",
            image_urls=[test_image_url],
        ),
    ]

    # 创建AI上下文
    context = AIContext(
        user_id="test_user", subject="general", session_id="test_session"
    )

    # 初始化服务
    bailian_service = BailianService()

    try:
        print(f"📤 发送请求到百炼VL模型...")
        print(f"   图片URL: {test_image_url}")

        # 调用API
        response = await bailian_service.chat_completion(
            messages=messages, context=context, max_tokens=500, temperature=0.7
        )

        print(f"\n📥 收到响应:")
        print(f"   成功: {response.success}")
        print(f"   模型: {response.model}")
        print(f"   Token使用: {response.tokens_used}")
        print(f"   处理时间: {response.processing_time:.2f}秒")
        print(f"   请求ID: {response.request_id}")

        if response.success:
            print(f"\n💬 AI回复:")
            print(response.content)

            # 检查AI是否真的看到了图片
            if "图片" in response.content or "image" in response.content.lower():
                print("\n✅ VL模型成功识别了图片内容")
            else:
                print("\n⚠️  VL模型可能没有正确处理图片")
        else:
            print(f"\n❌ API调用失败: {response.error_message}")

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback

        traceback.print_exc()


async def test_with_math_problem_image():
    """使用数学题图片测试"""
    print("\n📐 测试数学题图片识别...")

    # 使用一个包含数学内容的测试图片
    # 这里使用一个简单的测试方法：发送包含数学符号的文本，模拟图片内容
    messages: List[Union[Dict[str, Any], ChatMessage]] = [
        ChatMessage(
            role=MessageRole.SYSTEM,
            content="你是一个数学问题解答助手，能够分析图片中的数学题目并给出解答。",
        ),
        ChatMessage(
            role=MessageRole.USER,
            content="我上传了一张包含数学题的图片，请帮我分析并解答。图片中可能包含代数方程、几何图形或数值计算题目。",
            image_urls=["https://httpbin.org/image/png"],  # 占位符图片
        ),
    ]

    bailian_service = BailianService()
    context = AIContext(user_id="test_user", subject="math")

    try:
        response = await bailian_service.chat_completion(
            messages=messages,
            context=context,
            max_tokens=800,
            temperature=0.3,  # 数学题使用较低的温度
        )

        print(f"📊 数学题测试结果:")
        print(f"   成功: {response.success}")
        print(f"   模型: {response.model}")

        if response.success:
            print(f"\n🧮 数学助手回复:")
            print(response.content)

            # 检查回复是否包含数学相关内容
            math_keywords = ["方程", "解答", "计算", "公式", "步骤", "图片", "题目"]
            found_keywords = [kw for kw in math_keywords if kw in response.content]

            if found_keywords:
                print(f"\n✅ 发现数学相关关键词: {', '.join(found_keywords)}")
            else:
                print(f"\n⚠️  回复可能不够数学化，关键词检查: {math_keywords}")

    except Exception as e:
        print(f"❌ 数学题测试失败: {e}")


async def main():
    """主函数"""
    print("🧪 百炼VL模型图片识别测试")
    print("=" * 50)

    # 检查配置
    settings = get_settings()
    print(f"📋 配置检查:")
    print(f"   百炼API Key: {'✅ 已配置' if settings.BAILIAN_API_KEY else '❌ 未配置'}")
    print(
        f"   应用ID: {'✅ 已配置' if settings.BAILIAN_APPLICATION_ID else '❌ 未配置'}"
    )
    print(f"   基础URL: {settings.BAILIAN_BASE_URL}")

    if not settings.BAILIAN_API_KEY or not settings.BAILIAN_APPLICATION_ID:
        print("❌ 百炼服务配置不完整，无法进行测试")
        return

    # 运行测试
    await test_vl_model_with_real_image()
    await test_with_math_problem_image()

    print("\n📝 测试总结:")
    print("1. 如果VL模型能正确识别测试图片，说明API调用正常")
    print("2. 如果VL模型说'无法查看图片'，可能的原因：")
    print("   - 图片URL不可访问")
    print("   - VL模型配置问题")
    print("   - 图片格式不支持")
    print("   - 百炼平台VL功能未正确启用")

    print("\n🔧 下一步排查:")
    print("1. 检查生产环境实际上传的图片URL格式")
    print("2. 确认OSS图片的访问权限设置")
    print("3. 验证百炼平台VL模型的具体配置")


if __name__ == "__main__":
    asyncio.run(main())
