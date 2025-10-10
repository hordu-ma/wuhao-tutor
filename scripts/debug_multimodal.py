#!/usr/bin/env python3
"""
调试多模态消息构建问题

检查：
1. ChatMessage中image_urls是否正确传递
2. BailianService中多模态消息格式是否符合VL模型要求
3. 消息转换过程中是否有数据丢失
"""

import asyncio
import logging
import sys
from typing import Any, Dict, List

# 添加项目根目录到路径
sys.path.insert(0, "/Users/liguoma/my-devs/python/wuhao-tutor")

from src.core.config import get_settings
from src.services.bailian_service import BailianService, ChatMessage, MessageRole

# 设置日志级别为DEBUG以查看详细信息
logging.basicConfig(level=logging.DEBUG, format="%(levelname)s:%(name)s:%(message)s")
logger = logging.getLogger(__name__)


async def test_multimodal_message_construction():
    """测试多模态消息构建"""
    print("🔍 开始调试多模态消息构建...")

    # 测试图片URL（使用一个公开的测试图片）
    test_image_url = (
        "https://wuhao-tutor.oss-cn-shanghai.aliyuncs.com/uploads/test-image.jpg"
    )

    # 1. 创建包含图片的ChatMessage
    test_message = ChatMessage(
        role=MessageRole.USER,
        content="请分析这张图片中的数学题目",
        image_urls=[test_image_url],
    )

    print(f"✅ 创建ChatMessage成功:")
    print(f"   - role: {test_message.role}")
    print(f"   - content: {test_message.content}")
    print(f"   - image_urls: {test_message.image_urls}")

    # 2. 初始化BailianService
    settings = get_settings()
    bailian_service = BailianService()

    # 3. 测试消息格式化
    from typing import Union

    messages: List[Union[Dict[str, Any], ChatMessage]] = [test_message]
    formatted_messages = bailian_service._format_messages(messages)

    print(f"\n🔄 格式化后的消息:")
    for i, msg in enumerate(formatted_messages):
        print(f"   消息 {i+1}:")
        print(f"     - role: {msg.get('role')}")
        print(f"     - content type: {type(msg.get('content'))}")
        print(f"     - content: {msg.get('content')}")
        if isinstance(msg.get("content"), list):
            for j, content_item in enumerate(msg["content"]):
                print(f"       内容项 {j+1}: {content_item}")

    # 4. 测试请求载荷构建
    payload = bailian_service._build_request_payload(formatted_messages)

    print(f"\n📦 构建的请求载荷:")
    print(f"   - model: {payload.get('model')}")
    print(f"   - messages count: {len(payload.get('input', {}).get('messages', []))}")

    for i, msg in enumerate(payload.get("input", {}).get("messages", [])):
        print(f"   消息 {i+1}:")
        print(f"     - role: {msg.get('role')}")
        print(f"     - content: {msg.get('content')}")

    # 5. 检查是否正确识别为包含图片的消息
    has_images = bailian_service._has_images_in_messages(formatted_messages)
    print(f"\n🖼️  是否检测到图片: {has_images}")
    print(f"   选择的模型: {payload.get('model')}")

    return formatted_messages, payload


async def test_image_url_accessibility():
    """测试图片URL的可访问性"""
    print("\n🌐 测试图片URL可访问性...")

    import httpx

    # 测试一个通过新上传API上传的图片URL
    test_urls = [
        "https://wuhao-tutor.oss-cn-shanghai.aliyuncs.com/uploads/ai-images/",  # 前缀
        "https://httpbin.org/image/png",  # 公开测试图片
    ]

    async with httpx.AsyncClient() as client:
        for url in test_urls:
            try:
                if "uploads/ai-images/" in url:
                    print(f"   ⚠️  需要完整的图片URL (格式: {url}[实际文件名])")
                    continue

                response = await client.head(url, timeout=10.0)
                print(f"   ✅ {url}: {response.status_code}")
                print(
                    f"      Content-Type: {response.headers.get('content-type', 'unknown')}"
                )
            except Exception as e:
                print(f"   ❌ {url}: {str(e)}")


async def main():
    """主函数"""
    print("🚀 VL模型图片处理问题诊断工具")
    print("=" * 50)

    try:
        # 测试消息构建
        formatted_messages, payload = await test_multimodal_message_construction()

        # 测试图片可访问性
        await test_image_url_accessibility()

        print("\n📋 诊断总结:")
        print("1. 检查Learning.vue中是否正确获取ai_accessible_url")
        print("2. 验证上传的图片URL是否可以被百炼AI访问")
        print("3. 确认VL模型配置是否正确启用OCR功能")
        print("4. 检查图片格式是否符合VL模型要求")

        print("\n🔧 建议的排查步骤:")
        print("1. 在生产环境测试图片上传，查看返回的ai_accessible_url")
        print("2. 直接在浏览器访问该URL，确认图片可正常显示")
        print("3. 检查百炼平台VL模型的具体配置参数")
        print("4. 尝试使用不同格式/大小的图片进行测试")

    except Exception as e:
        print(f"❌ 诊断过程中出现错误: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
