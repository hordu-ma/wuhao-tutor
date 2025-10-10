#!/usr/bin/env python
"""
AI图片识别诊断脚本
测试图片上传和百炼VL模型调用流程
"""

import asyncio
import logging
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.config import get_settings
from src.services.ai_image_service import AIImageAccessService
from src.services.bailian_service import BailianService, ChatMessage, MessageRole

# 配置日志
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def test_image_url_accessibility():
    """测试图片URL是否可被AI访问"""
    logger.info("=" * 60)
    logger.info("步骤 1: 测试 OSS 配置和公网端点")
    logger.info("=" * 60)

    settings = get_settings()
    ai_image_service = AIImageAccessService()

    # 显示配置信息
    logger.info(f"OSS Bucket: {settings.OSS_BUCKET_NAME}")
    logger.info(f"OSS Endpoint: {settings.OSS_ENDPOINT}")
    logger.info(f"OSS 可用: {ai_image_service.is_oss_available}")

    if ai_image_service.is_oss_available:
        # 测试公网端点转换
        public_endpoint = ai_image_service._get_public_endpoint()
        logger.info(f"公网端点: {public_endpoint}")

        # 生成测试URL
        test_object = "ai_analysis/test/20250110_120000_abc123.jpg"
        test_url = ai_image_service._generate_ai_accessible_url(test_object)
        logger.info(f"测试URL: {test_url}")

        # 验证URL格式
        if test_url.startswith("https://") and "internal" not in test_url:
            logger.info("✅ URL格式正确，使用公网端点")
        else:
            logger.error("❌ URL格式错误或包含内网端点")
            return False
    else:
        logger.warning("⚠️  OSS未配置，将使用本地存储（开发环境）")

    return True


async def test_vl_model_detection():
    """测试VL模型检测和调用"""
    logger.info("\n" + "=" * 60)
    logger.info("步骤 2: 测试VL模型检测")
    logger.info("=" * 60)

    bailian_service = BailianService()

    # 测试1: 纯文本消息
    text_only_messages = [{"role": "user", "content": "你好"}]

    has_images = bailian_service._has_images_in_messages(text_only_messages)
    logger.info(f"纯文本消息检测: has_images={has_images} (应该是False)")

    if has_images:
        logger.error("❌ 纯文本消息被错误识别为包含图片")
        return False

    # 测试2: 多模态消息
    multimodal_messages = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "这是什么？"},
                {
                    "type": "image_url",
                    "image_url": {"url": "https://example.com/test.jpg"},
                },
            ],
        }
    ]

    has_images = bailian_service._has_images_in_messages(multimodal_messages)
    logger.info(f"多模态消息检测: has_images={has_images} (应该是True)")

    if not has_images:
        logger.error("❌ 多模态消息未被识别为包含图片")
        return False

    # 测试3: 构建请求载荷
    payload = bailian_service._build_request_payload(multimodal_messages)
    model = payload.get("model")
    logger.info(f"选择的模型: {model}")

    if model == "qwen-vl-max":
        logger.info("✅ 正确选择了VL模型")
    else:
        logger.error(f"❌ 错误的模型选择: {model}，应该是 qwen-vl-max")
        return False

    # 测试4: 检查VL模型判断
    is_vl = bailian_service._is_vl_model(model)
    logger.info(f"VL模型判断: {is_vl} (应该是True)")

    if not is_vl:
        logger.error("❌ VL模型判断失败")
        return False

    logger.info("✅ VL模型检测和选择逻辑正确")
    return True


async def test_multimodal_content_building():
    """测试多模态内容构建"""
    logger.info("\n" + "=" * 60)
    logger.info("步骤 3: 测试多模态内容构建")
    logger.info("=" * 60)

    bailian_service = BailianService()

    # 构建包含文本和图片的内容
    text = "请分析这张图片上的数学题"
    image_urls = [
        "https://example.com/math_problem.jpg",
        "https://example.com/math_problem2.jpg",
    ]

    content = bailian_service._build_multimodal_content(text, image_urls)

    logger.info(f"生成的内容部分: {len(content)} 个")
    logger.info(f"内容详情: {content}")

    # 验证结构
    if len(content) != 3:  # 1个文本 + 2个图片
        logger.error(f"❌ 内容部分数量错误: {len(content)}，应该是3")
        return False

    if content[0]["type"] != "text":
        logger.error("❌ 第一个部分应该是text类型")
        return False

    if content[1]["type"] != "image_url" or content[2]["type"] != "image_url":
        logger.error("❌ 第2、3个部分应该是image_url类型")
        return False

    logger.info("✅ 多模态内容构建正确")
    return True


async def test_api_configuration():
    """测试API配置"""
    logger.info("\n" + "=" * 60)
    logger.info("步骤 4: 检查百炼API配置")
    logger.info("=" * 60)

    settings = get_settings()

    # 检查必要的配置
    api_key = settings.BAILIAN_API_KEY
    app_id = settings.BAILIAN_APPLICATION_ID
    base_url = settings.BAILIAN_BASE_URL

    logger.info(f"API Key: {'已配置' if api_key else '❌ 未配置'}")
    logger.info(f"Application ID: {'已配置' if app_id else '❌ 未配置'}")
    logger.info(f"Base URL: {base_url}")

    if not api_key or not app_id:
        logger.error("❌ 百炼API配置不完整")
        logger.error("请在 .env 文件中配置:")
        logger.error("  - BAILIAN_API_KEY")
        logger.error("  - BAILIAN_APPLICATION_ID")
        return False

    logger.info("✅ 百炼API配置完整")
    return True


async def main():
    """运行所有诊断测试"""
    logger.info("🔍 开始AI图片识别诊断...")
    logger.info("")

    results = {}

    # 运行所有测试
    results["image_url"] = await test_image_url_accessibility()
    results["vl_model"] = await test_vl_model_detection()
    results["multimodal"] = await test_multimodal_content_building()
    results["api_config"] = await test_api_configuration()

    # 汇总结果
    logger.info("\n" + "=" * 60)
    logger.info("诊断结果汇总")
    logger.info("=" * 60)

    all_passed = True
    for test_name, passed in results.items():
        status = "✅ 通过" if passed else "❌ 失败"
        logger.info(f"{test_name.ljust(20)}: {status}")
        if not passed:
            all_passed = False

    logger.info("=" * 60)

    if all_passed:
        logger.info("🎉 所有测试通过！系统配置正确。")
        logger.info("")
        logger.info("✨ 下一步操作:")
        logger.info("1. 在生产环境查看日志，确认图片URL格式")
        logger.info("2. 检查OSS配置是否使用公网端点")
        logger.info("3. 确认百炼API密钥权限包含VL模型")
        return 0
    else:
        logger.error("❌ 部分测试失败，请检查配置和代码。")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
