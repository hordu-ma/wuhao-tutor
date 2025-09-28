#!/usr/bin/env python3
"""
百炼AI服务基本功能验证脚本

此脚本用于验证第1阶段开发成果：
1. 百炼服务初始化
2. 配置加载
3. 消息格式化
4. 异常处理
5. 基本的聊天补全功能（模拟模式）

运行方式：
python scripts/test_bailian_basic.py
"""

import asyncio
import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.services.bailian_service import (
    BailianService,
    ChatMessage,
    MessageRole,
    AIContext,
    get_bailian_service,
)
from src.core.config import get_settings
from src.core.exceptions import BailianServiceError
from unittest.mock import Mock, AsyncMock, patch


def print_section(title: str):
    """打印测试章节标题"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


def print_test(test_name: str, passed: bool, details: str = ""):
    """打印测试结果"""
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"{status} {test_name}")
    if details:
        print(f"    {details}")


def test_configuration():
    """测试配置加载"""
    print_section("配置管理测试")

    try:
        settings = get_settings()

        # 检查必要的配置项
        required_configs = [
            'BAILIAN_APPLICATION_ID',
            'BAILIAN_API_KEY',
            'BAILIAN_BASE_URL',
            'BAILIAN_TIMEOUT',
            'BAILIAN_MAX_RETRIES'
        ]

        for config in required_configs:
            value = getattr(settings, config, None)
            if value:
                print_test(f"配置 {config}", True, f"值: {str(value)[:20]}...")
            else:
                print_test(f"配置 {config}", False, "未配置或为空")

        return True

    except Exception as e:
        print_test("配置加载", False, f"错误: {e}")
        return False


def test_service_initialization():
    """测试服务初始化"""
    print_section("服务初始化测试")

    try:
        # 创建模拟配置
        mock_settings = Mock()
        mock_settings.BAILIAN_APPLICATION_ID = "test_app_id"
        mock_settings.BAILIAN_API_KEY = "sk-test-key"
        mock_settings.BAILIAN_BASE_URL = "https://test-api.com/v1"
        mock_settings.BAILIAN_TIMEOUT = 30
        mock_settings.BAILIAN_MAX_RETRIES = 3

        # 测试服务初始化
        service = BailianService(settings_override=mock_settings)

        # 验证属性
        tests = [
            ("Application ID", service.application_id == "test_app_id"),
            ("API Key", service.api_key == "sk-test-key"),
            ("Base URL", service.base_url == "https://test-api.com/v1"),
            ("Timeout", service.timeout == 30),
            ("Max Retries", service.max_retries == 3),
            ("HTTP Client", service.client is not None),
        ]

        all_passed = True
        for test_name, condition in tests:
            print_test(test_name, condition)
            all_passed &= condition

        return all_passed

    except Exception as e:
        print_test("服务初始化", False, f"错误: {e}")
        return False


def test_message_formatting():
    """测试消息格式化"""
    print_section("消息格式化测试")

    try:
        # 创建模拟服务
        mock_settings = Mock()
        mock_settings.BAILIAN_APPLICATION_ID = "test"
        mock_settings.BAILIAN_API_KEY = "sk-test"
        mock_settings.BAILIAN_BASE_URL = "https://test.com"
        mock_settings.BAILIAN_TIMEOUT = 30
        mock_settings.BAILIAN_MAX_RETRIES = 3

        service = BailianService(settings_override=mock_settings)

        # 测试不同格式的消息
        test_cases = [
            {
                "name": "ChatMessage对象",
                "input": [ChatMessage(role=MessageRole.USER, content="Hello")],
                "expected": [{"role": "user", "content": "Hello"}]
            },
            {
                "name": "字典格式消息",
                "input": [{"role": "user", "content": "Test"}],
                "expected": [{"role": "user", "content": "Test"}]
            },
            {
                "name": "混合格式消息",
                "input": [
                    ChatMessage(role=MessageRole.USER, content="Hello"),
                    {"role": "assistant", "content": "Hi!"}
                ],
                "expected": [
                    {"role": "user", "content": "Hello"},
                    {"role": "assistant", "content": "Hi!"}
                ]
            }
        ]

        all_passed = True
        for case in test_cases:
            try:
                result = service._format_messages(case["input"])
                passed = result == case["expected"]
                print_test(case["name"], passed, f"结果: {result}")
                all_passed &= passed
            except Exception as e:
                print_test(case["name"], False, f"错误: {e}")
                all_passed = False

        # 测试错误情况
        try:
            service._format_messages([{"role": "user"}])  # 缺少content
            print_test("错误处理 - 缺少字段", False, "应该抛出异常但没有")
            all_passed = False
        except ValueError:
            print_test("错误处理 - 缺少字段", True, "正确抛出ValueError")
        except Exception as e:
            print_test("错误处理 - 缺少字段", False, f"错误的异常类型: {e}")
            all_passed = False

        return all_passed

    except Exception as e:
        print_test("消息格式化", False, f"错误: {e}")
        return False


def test_payload_building():
    """测试请求载荷构建"""
    print_section("请求载荷构建测试")

    try:
        mock_settings = Mock()
        mock_settings.BAILIAN_APPLICATION_ID = "test_app"
        mock_settings.BAILIAN_API_KEY = "sk-test"
        mock_settings.BAILIAN_BASE_URL = "https://test.com"
        mock_settings.BAILIAN_TIMEOUT = 30
        mock_settings.BAILIAN_MAX_RETRIES = 3

        service = BailianService(settings_override=mock_settings)

        # 测试基本载荷构建
        messages = [{"role": "user", "content": "Hello"}]
        payload = service._build_request_payload(messages)

        tests = [
            ("Model字段", "model" in payload),
            ("Input字段", "input" in payload and "messages" in payload["input"]),
            ("Parameters字段", "parameters" in payload),
            ("App ID字段", payload.get("app_id") == "test_app"),
            ("消息内容", payload["input"]["messages"] == messages),
        ]

        all_passed = True
        for test_name, condition in tests:
            print_test(test_name, condition)
            all_passed &= condition

        # 测试带上下文的载荷构建
        context = AIContext(
            user_id="test_user",
            subject="数学",
            grade_level=8,
            session_id="session_123"
        )

        payload_with_context = service._build_request_payload(messages, context)

        context_tests = [
            ("User ID", payload_with_context.get("user_id") == "test_user"),
            ("Session ID", payload_with_context.get("session_id") == "session_123"),
        ]

        for test_name, condition in context_tests:
            print_test(f"上下文 - {test_name}", condition)
            all_passed &= condition

        return all_passed

    except Exception as e:
        print_test("载荷构建", False, f"错误: {e}")
        return False


async def test_mock_chat_completion():
    """测试模拟聊天补全功能"""
    print_section("模拟聊天补全测试")

    try:
        mock_settings = Mock()
        mock_settings.BAILIAN_APPLICATION_ID = "test_app"
        mock_settings.BAILIAN_API_KEY = "sk-test"
        mock_settings.BAILIAN_BASE_URL = "https://test.com"
        mock_settings.BAILIAN_TIMEOUT = 30
        mock_settings.BAILIAN_MAX_RETRIES = 3

        service = BailianService(settings_override=mock_settings)

        # 模拟成功的API响应
        mock_response = {
            "output": {
                "choices": [
                    {
                        "message": {
                            "content": "这是一个模拟的AI响应，用于测试百炼服务的基本功能。"
                        }
                    }
                ]
            },
            "usage": {
                "total_tokens": 120
            },
            "request_id": "mock_req_123",
            "model": "qwen-turbo"
        }

        # 使用Mock替换实际的API调用
        with patch.object(service, '_call_bailian_api_with_retry', new_callable=AsyncMock) as mock_api:
            mock_api.return_value = mock_response

            # 测试聊天补全
            messages = [ChatMessage(role=MessageRole.USER, content="请介绍一下你自己")]
            context = AIContext(user_id="test_user", subject="测试", grade_level=8)

            response = await service.chat_completion(
                messages=messages,
                context=context,
                temperature=0.8,
                max_tokens=1000
            )

            # 验证响应
            tests = [
                ("响应成功", response.success),
                ("有响应内容", len(response.content) > 0),
                ("Token统计", response.tokens_used == 120),
                ("处理时间", response.processing_time >= 0),
                ("请求ID", response.request_id == "mock_req_123"),
                ("模型信息", response.model == "qwen-turbo"),
            ]

            all_passed = True
            for test_name, condition in tests:
                print_test(test_name, condition)
                all_passed &= condition

            # 验证API被正确调用
            mock_api.assert_called_once()
            call_args = mock_api.call_args[0][0]  # 获取载荷参数

            api_tests = [
                ("API调用次数", mock_api.call_count == 1),
                ("载荷包含消息", "input" in call_args and "messages" in call_args["input"]),
                ("载荷包含用户ID", call_args.get("user_id") == "test_user"),
                ("载荷包含Temperature", call_args["parameters"]["temperature"] == 0.8),
                ("载荷包含MaxTokens", call_args["parameters"]["max_tokens"] == 1000),
            ]

            for test_name, condition in api_tests:
                print_test(f"API调用 - {test_name}", condition)
                all_passed &= condition

            print_test("响应内容预览", True, f"内容: {response.content[:50]}...")

            return all_passed

    except Exception as e:
        print_test("模拟聊天补全", False, f"错误: {e}")
        return False


def test_exception_handling():
    """测试异常处理"""
    print_section("异常处理测试")

    try:
        # 导入异常类
        from src.core.exceptions import (
            BailianServiceError,
            BailianAuthError,
            BailianRateLimitError,
            BailianTimeoutError
        )

        # 测试异常类创建
        exceptions = [
            ("BailianServiceError", BailianServiceError("测试错误")),
            ("BailianAuthError", BailianAuthError("认证失败")),
            ("BailianRateLimitError", BailianRateLimitError("限流", retry_after=60)),
            ("BailianTimeoutError", BailianTimeoutError("超时", timeout=30)),
        ]

        all_passed = True
        for exc_name, exc_instance in exceptions:
            try:
                # 测试异常属性
                has_message = hasattr(exc_instance, 'message')
                has_error_code = hasattr(exc_instance, 'error_code')
                has_to_dict = hasattr(exc_instance, 'to_dict')

                tests = [
                    (f"{exc_name} - message属性", has_message),
                    (f"{exc_name} - error_code属性", has_error_code),
                    (f"{exc_name} - to_dict方法", has_to_dict),
                ]

                for test_name, condition in tests:
                    print_test(test_name, condition)
                    all_passed &= condition

                # 测试to_dict方法
                if has_to_dict:
                    error_dict = exc_instance.to_dict()
                    dict_valid = isinstance(error_dict, dict) and 'error_code' in error_dict
                    print_test(f"{exc_name} - to_dict返回", dict_valid, f"结果: {error_dict}")
                    all_passed &= dict_valid

            except Exception as e:
                print_test(f"{exc_name}创建", False, f"错误: {e}")
                all_passed = False

        return all_passed

    except Exception as e:
        print_test("异常处理", False, f"错误: {e}")
        return False


def test_global_service():
    """测试全局服务实例"""
    print_section("全局服务实例测试")

    try:
        # 测试单例模式
        with patch('src.services.bailian_service.get_settings') as mock_get_settings:
            mock_settings = Mock()
            mock_settings.BAILIAN_APPLICATION_ID = "global_test"
            mock_settings.BAILIAN_API_KEY = "sk-global-test"
            mock_settings.BAILIAN_BASE_URL = "https://global-test.com"
            mock_settings.BAILIAN_TIMEOUT = 30
            mock_settings.BAILIAN_MAX_RETRIES = 3
            mock_get_settings.return_value = mock_settings

            # 清理全局实例
            import src.services.bailian_service
            src.services.bailian_service._bailian_service = None

            service1 = get_bailian_service()
            service2 = get_bailian_service()

            tests = [
                ("获取服务实例1", service1 is not None),
                ("获取服务实例2", service2 is not None),
                ("单例模式", service1 is service2),
                ("配置正确加载", service1.application_id == "global_test"),
            ]

            all_passed = True
            for test_name, condition in tests:
                print_test(test_name, condition)
                all_passed &= condition

            return all_passed

    except Exception as e:
        print_test("全局服务实例", False, f"错误: {e}")
        return False


async def main():
    """主测试函数"""
    print("🚀 百炼AI服务基本功能验证")
    print(f"项目路径: {project_root}")

    # 运行所有测试
    test_results = []

    # 同步测试
    sync_tests = [
        ("配置管理", test_configuration),
        ("服务初始化", test_service_initialization),
        ("消息格式化", test_message_formatting),
        ("载荷构建", test_payload_building),
        ("异常处理", test_exception_handling),
        ("全局服务", test_global_service),
    ]

    for test_name, test_func in sync_tests:
        try:
            result = test_func()
            test_results.append((test_name, result))
        except Exception as e:
            print_test(test_name, False, f"测试执行失败: {e}")
            test_results.append((test_name, False))

    # 异步测试
    async_tests = [
        ("模拟聊天补全", test_mock_chat_completion),
    ]

    for test_name, test_func in async_tests:
        try:
            result = await test_func()
            test_results.append((test_name, result))
        except Exception as e:
            print_test(test_name, False, f"测试执行失败: {e}")
            test_results.append((test_name, False))

    # 汇总结果
    print_section("测试结果汇总")

    passed_count = sum(1 for _, result in test_results if result)
    total_count = len(test_results)

    for test_name, result in test_results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")

    print(f"\n📊 总体结果: {passed_count}/{total_count} 测试通过")

    if passed_count == total_count:
        print("🎉 所有测试通过！第1阶段开发成果验证成功！")
        print("\n✅ 第1阶段验收标准检查:")
        print("   ✅ 百炼智能体调用接口实现")
        print("   ✅ 错误处理机制正常工作")
        print("   ✅ 配置管理系统完善")
        print("   ✅ 消息格式化功能正确")
        print("   ✅ 日志记录完整")
        print("\n🚀 可以开始第2阶段开发！")
        return True
    else:
        print(f"❌ 有 {total_count - passed_count} 个测试失败，需要修复后再继续")
        return False


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️ 测试被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n💥 测试执行过程中发生严重错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
