#!/usr/bin/env python3
"""
语音识别服务测试脚本
用于诊断ASR配置和API调用问题
"""

import asyncio
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.config import get_settings
from src.services.speech_recognition_service import get_speech_recognition_service


async def test_asr_config():
    """测试ASR配置"""
    print("=" * 60)
    print("1. 检查ASR配置")
    print("=" * 60)

    settings = get_settings()

    config_items = [
        ("ASR_ENABLED", settings.ASR_ENABLED),
        (
            "ASR_APP_KEY",
            settings.ASR_APP_KEY[:10] + "..." if settings.ASR_APP_KEY else None,
        ),
        (
            "ASR_ACCESS_KEY_ID",
            (
                settings.ASR_ACCESS_KEY_ID[:10] + "..."
                if settings.ASR_ACCESS_KEY_ID
                else None
            ),
        ),
        (
            "ASR_ACCESS_KEY_SECRET",
            "***已配置***" if settings.ASR_ACCESS_KEY_SECRET else None,
        ),
        ("ASR_ENDPOINT", settings.ASR_ENDPOINT),
        ("ASR_FORMAT", settings.ASR_FORMAT),
        ("ASR_SAMPLE_RATE", settings.ASR_SAMPLE_RATE),
    ]

    for key, value in config_items:
        status = "✅" if value else "❌"
        print(f"{status} {key:35s}: {value}")

    # 检查必需配置
    missing = []
    if not settings.ASR_APP_KEY:
        missing.append("ASR_APP_KEY")
    if not settings.ASR_ACCESS_KEY_ID:
        missing.append("ASR_ACCESS_KEY_ID")
    if not settings.ASR_ACCESS_KEY_SECRET:
        missing.append("ASR_ACCESS_KEY_SECRET")

    if missing:
        print(f"\n❌ 缺少必需配置: {', '.join(missing)}")
        return False
    else:
        print("\n✅ 所有必需配置项都已设置")
        return True


async def test_token_acquisition():
    """测试Token获取"""
    print("\n" + "=" * 60)
    print("2. 测试Token获取")
    print("=" * 60)

    try:
        service = get_speech_recognition_service()
        token = await service._get_access_token()

        print(f"✅ Token获取成功")
        print(f"   Token: {token[:20]}...{token[-10:] if len(token) > 30 else ''}")
        print(f"   长度: {len(token)} 字符")
        return True

    except Exception as e:
        print(f"❌ Token获取失败: {str(e)}")
        return False


async def test_health_check():
    """测试服务健康检查"""
    print("\n" + "=" * 60)
    print("3. 服务健康检查")
    print("=" * 60)

    try:
        service = get_speech_recognition_service()
        status = await service.health_check()

        print(f"服务状态: {status['status']}")
        print(f"消息: {status.get('message', 'N/A')}")

        if status["status"] == "healthy":
            print("✅ 服务健康")
            return True
        else:
            print(f"❌ 服务不健康: {status.get('message')}")
            return False

    except Exception as e:
        print(f"❌ 健康检查失败: {str(e)}")
        return False


async def test_recognition_with_sample():
    """使用示例音频测试识别"""
    print("\n" + "=" * 60)
    print("4. 音频识别测试 (可选)")
    print("=" * 60)

    # 这里需要一个测试音频文件
    sample_audio_path = (
        Path(__file__).parent.parent / "tests" / "fixtures" / "test_audio.mp3"
    )

    if not sample_audio_path.exists():
        print("⚠️  未找到测试音频文件,跳过此测试")
        print(f"   请将测试音频放置在: {sample_audio_path}")
        return None

    try:
        service = get_speech_recognition_service()

        # 创建模拟UploadFile对象
        from io import BytesIO

        from fastapi import UploadFile

        with open(sample_audio_path, "rb") as f:
            audio_data = f.read()

        upload_file = UploadFile(filename="test_audio.mp3", file=BytesIO(audio_data))

        result = await service.recognize_from_file(upload_file, "zh-CN")

        if result["success"]:
            print("✅ 识别成功")
            print(f"   识别文本: {result['text']}")
            print(f"   置信度: {result['confidence']:.2%}")
            return True
        else:
            print(f"❌ 识别失败: {result.get('error')}")
            return False

    except Exception as e:
        print(f"❌ 识别测试失败: {str(e)}")
        import traceback

        traceback.print_exc()
        return False


async def main():
    """主函数"""
    print("\n🔍 阿里云语音识别服务诊断工具\n")

    results = []

    # 1. 配置检查
    config_ok = await test_asr_config()
    results.append(("配置检查", config_ok))

    if not config_ok:
        print("\n⚠️  配置不完整,无法继续后续测试")
        return

    # 2. Token测试
    token_ok = await test_token_acquisition()
    results.append(("Token获取", token_ok))

    # 3. 健康检查
    health_ok = await test_health_check()
    results.append(("健康检查", health_ok))

    # 4. 识别测试
    recognition_ok = await test_recognition_with_sample()
    if recognition_ok is not None:
        results.append(("音频识别", recognition_ok))

    # 汇总结果
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)

    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name:15s}: {status}")

    # 诊断建议
    print("\n" + "=" * 60)
    print("诊断建议")
    print("=" * 60)

    if not token_ok:
        print("\n❌ Token获取失败的可能原因:")
        print("   1. AccessKey ID或Secret配置错误")
        print("   2. AccessKey已过期或被删除")
        print("   3. 网络连接问题")
        print("\n   解决方法:")
        print("   - 登录阿里云控制台检查AccessKey状态")
        print("   - 重新创建AccessKey并更新配置")
        print("   - 检查服务器网络连接")

    if token_ok and not health_ok:
        print("\n⚠️  Token正常但健康检查失败:")
        print("   可能是阿里云ASR服务暂时不可用")
        print("   请稍后重试或联系阿里云技术支持")

    if token_ok and health_ok and recognition_ok is False:
        print("\n❌ Token和健康检查正常但识别失败:")
        print("   1. AppKey配置错误")
        print("   2. 音频格式不支持")
        print("   3. 音频文件损坏")
        print("\n   解决方法:")
        print("   - 检查ASR_APP_KEY是否正确")
        print("   - 确认音频格式为mp3/wav等支持格式")
        print("   - 采样率设置为16000Hz")


if __name__ == "__main__":
    asyncio.run(main())
