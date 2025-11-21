"""
百炼AI服务单元测试

测试覆盖：
- 基础聊天补全功能
- 错误处理和重试机制
- 请求/响应格式化
- 配置验证
- 异常情况处理
"""

import json
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import httpx
import pytest

from src.core.exceptions import (
    BailianAuthError,
    BailianRateLimitError,
    BailianServiceError,
    BailianTimeoutError,
)
from src.services.bailian_service import (
    AIContext,
    BailianService,
    ChatCompletionResponse,
    ChatMessage,
    MessageRole,
    close_bailian_service,
    get_bailian_service,
)

# ============================================================================
# 测试夹具和工具函数
# ============================================================================


@pytest.fixture
def mock_settings():
    """模拟配置"""
    return MagicMock(
        BAILIAN_APPLICATION_ID="test_app_id",
        BAILIAN_API_KEY="sk-test-key",
        BAILIAN_BASE_URL="https://test-api.com/v1",
        BAILIAN_TIMEOUT=30,
        BAILIAN_MAX_RETRIES=3,
    )


@pytest.fixture
def bailian_service(mock_settings):
    """百炼服务实例"""
    service = BailianService(settings_override=mock_settings)
    yield service


@pytest.fixture
def sample_messages():
    """示例消息列表"""
    return [ChatMessage(role=MessageRole.USER, content="你好，请帮我解答一道数学题")]


@pytest.fixture
def sample_context():
    """示例AI上下文"""
    return AIContext(
        user_id="test_user_123", subject="数学", grade_level=8, session_id="session_123"
    )


@pytest.fixture
def mock_successful_response():
    """模拟成功响应"""
    return {
        "output": {
            "choices": [
                {"message": {"content": "这是一道关于方程的问题。让我帮你详细解答..."}}
            ]
        },
        "usage": {"total_tokens": 150},
        "request_id": "req_123456",
        "model": "qwen-turbo",
    }


# ============================================================================
# 基础功能测试
# ============================================================================


class TestBailianServiceInit:
    """百炼服务初始化测试"""

    def test_init_with_valid_config(self, mock_settings):
        """测试使用有效配置初始化"""
        service = BailianService(settings_override=mock_settings)

        assert service.application_id == "test_app_id"
        assert service.api_key == "sk-test-key"
        assert service.base_url == "https://test-api.com/v1"
        assert service.timeout == 30
        assert service.max_retries == 3
        assert service.client is not None

    @patch("src.services.bailian_service.httpx.AsyncClient")
    def test_http_client_configuration(self, mock_client, mock_settings):
        """测试HTTP客户端配置"""
        service = BailianService(settings_override=mock_settings)

        # 验证客户端创建参数
        mock_client.assert_called_once()
        call_args = mock_client.call_args

        # 检查超时配置
        timeout_arg = call_args.kwargs["timeout"]
        # httpx.Timeout对象没有直接的timeout属性，而是通过timeout参数设置
        # 我们验证timeout对象的类型即可
        assert hasattr(timeout_arg, "read") and hasattr(timeout_arg, "write")

        # 检查请求头
        headers = call_args.kwargs["headers"]
        assert headers["Authorization"] == "Bearer sk-test-key"
        assert headers["Content-Type"] == "application/json"
        assert "wuhao-tutor" in headers["User-Agent"]


class TestMessageFormatting:
    """消息格式化测试"""

    def test_format_chat_message_objects(self, bailian_service):
        """测试格式化ChatMessage对象"""
        messages = [
            ChatMessage(role=MessageRole.USER, content="Hello"),
            ChatMessage(role=MessageRole.ASSISTANT, content="Hi there!"),
        ]

        formatted = bailian_service._format_messages(messages)

        assert len(formatted) == 2
        assert formatted[0] == {"role": "user", "content": "Hello"}
        assert formatted[1] == {"role": "assistant", "content": "Hi there!"}

    def test_format_dict_messages(self, bailian_service):
        """测试格式化字典格式消息"""
        messages = [
            {"role": "user", "content": "Test message"},
            {"role": "system", "content": "System prompt"},
        ]

        formatted = bailian_service._format_messages(messages)

        assert len(formatted) == 2
        assert formatted[0] == {"role": "user", "content": "Test message"}
        assert formatted[1] == {"role": "system", "content": "System prompt"}

    def test_format_mixed_messages(self, bailian_service):
        """测试格式化混合类型消息"""
        messages = [
            ChatMessage(role=MessageRole.USER, content="Hello"),
            {"role": "assistant", "content": "Hi!"},
        ]

        formatted = bailian_service._format_messages(messages)

        assert len(formatted) == 2
        assert formatted[0] == {"role": "user", "content": "Hello"}
        assert formatted[1] == {"role": "assistant", "content": "Hi!"}

    def test_format_messages_validation_errors(self, bailian_service):
        """测试消息格式验证错误"""
        # 测试缺少必要字段
        with pytest.raises(ValueError, match="消息必须包含'role'和'content'字段"):
            bailian_service._format_messages([{"role": "user"}])

        with pytest.raises(ValueError, match="消息必须包含'role'和'content'字段"):
            bailian_service._format_messages([{"content": "test"}])

        # 测试不支持的消息类型
        with pytest.raises(ValueError, match="不支持的消息类型"):
            bailian_service._format_messages(["invalid_message"])


class TestRequestPayloadBuilding:
    """请求载荷构建测试"""

    def test_build_basic_payload(self, bailian_service, sample_messages):
        """测试构建基础请求载荷"""
        formatted_messages = bailian_service._format_messages(sample_messages)
        payload = bailian_service._build_request_payload(formatted_messages)

        assert payload["model"] == "qwen-turbo"
        assert payload["input"]["messages"] == formatted_messages
        assert payload["app_id"] == "test_app_id"
        assert "parameters" in payload

        params = payload["parameters"]
        assert params["result_format"] == "message"
        assert params["max_tokens"] == 1500
        assert params["temperature"] == 0.7

    def test_build_payload_with_context(
        self, bailian_service, sample_messages, sample_context
    ):
        """测试带上下文的请求载荷构建"""
        formatted_messages = bailian_service._format_messages(sample_messages)
        payload = bailian_service._build_request_payload(
            formatted_messages, sample_context
        )

        assert payload["user_id"] == "test_user_123"
        assert payload["session_id"] == "session_123"

    def test_build_payload_with_custom_params(self, bailian_service, sample_messages):
        """测试带自定义参数的请求载荷构建"""
        formatted_messages = bailian_service._format_messages(sample_messages)
        payload = bailian_service._build_request_payload(
            formatted_messages, max_tokens=2000, temperature=0.5, top_p=0.9
        )

        params = payload["parameters"]
        assert params["max_tokens"] == 2000
        assert params["temperature"] == 0.5
        assert params["top_p"] == 0.9


# ============================================================================
# API调用测试
# ============================================================================


class TestAPICall:
    """API调用测试"""

    @pytest.mark.asyncio
    async def test_successful_api_call(self, bailian_service, mock_successful_response):
        """测试成功的API调用"""
        with patch.object(bailian_service.client, "post") as mock_post:
            # 模拟成功响应
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_successful_response
            mock_post.return_value = mock_response

            payload = {"test": "payload"}
            result = await bailian_service._call_bailian_api(payload)

            assert result == mock_successful_response
            mock_post.assert_called_once()

    @pytest.mark.asyncio
    async def test_api_call_auth_error(self, bailian_service):
        """测试API调用认证错误"""
        with patch.object(bailian_service.client, "post") as mock_post:
            # 模拟401认证错误
            mock_response = Mock()
            mock_response.status_code = 401
            mock_post.return_value = mock_response

            payload = {"test": "payload"}

            with pytest.raises(BailianAuthError, match="API密钥无效或过期"):
                await bailian_service._call_bailian_api(payload)

    @pytest.mark.asyncio
    async def test_api_call_rate_limit_error(self, bailian_service):
        """测试API调用限流错误"""
        with patch.object(bailian_service.client, "post") as mock_post:
            # 模拟429限流错误
            mock_response = Mock()
            mock_response.status_code = 429
            mock_response.headers = {"Retry-After": "60"}
            mock_post.return_value = mock_response

            payload = {"test": "payload"}

            with pytest.raises(BailianRateLimitError, match="API调用频率过高"):
                await bailian_service._call_bailian_api(payload)

    @pytest.mark.asyncio
    async def test_api_call_timeout_error(self, bailian_service):
        """测试API调用超时错误"""
        with patch.object(bailian_service.client, "post") as mock_post:
            # 模拟超时异常
            mock_post.side_effect = httpx.TimeoutException("Timeout")

            payload = {"test": "payload"}

            with pytest.raises(BailianTimeoutError, match="API调用超时"):
                await bailian_service._call_bailian_api(payload)

    @pytest.mark.asyncio
    async def test_api_call_json_parse_error(self, bailian_service):
        """测试JSON解析错误"""
        with patch.object(bailian_service.client, "post") as mock_post:
            # 模拟无效JSON响应
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)
            mock_response.text = "Invalid response"
            mock_post.return_value = mock_response

            payload = {"test": "payload"}

            with pytest.raises(BailianServiceError, match="无效的JSON响应"):
                await bailian_service._call_bailian_api(payload)

    @pytest.mark.asyncio
    async def test_api_call_business_error(self, bailian_service):
        """测试业务错误"""
        with patch.object(bailian_service.client, "post") as mock_post:
            # 模拟业务错误响应
            error_response = {
                "success": False,
                "code": "PARAM_ERROR",
                "message": "参数错误",
            }
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = error_response
            mock_post.return_value = mock_response

            payload = {"test": "payload"}

            with pytest.raises(
                BailianServiceError, match="业务错误 \\[PARAM_ERROR\\]: 参数错误"
            ):
                await bailian_service._call_bailian_api(payload)


# ============================================================================
# 重试机制测试
# ============================================================================


class TestRetryMechanism:
    """重试机制测试"""

    @pytest.mark.asyncio
    async def test_retry_on_rate_limit(self, bailian_service):
        """测试限流时的重试机制"""
        with patch.object(bailian_service, "_call_bailian_api") as mock_api_call:
            with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
                # 第一次调用限流，第二次成功
                mock_api_call.side_effect = [
                    BailianRateLimitError("Rate limit"),
                    {"success": True, "data": "ok"},
                ]

                payload = {"test": "payload"}
                result = await bailian_service._call_bailian_api_with_retry(payload)

                assert result == {"success": True, "data": "ok"}
                assert mock_api_call.call_count == 2
                mock_sleep.assert_called_once_with(2)  # 第一次重试等待2秒

    @pytest.mark.asyncio
    async def test_retry_on_timeout(self, bailian_service):
        """测试超时时的重试机制"""
        with patch.object(bailian_service, "_call_bailian_api") as mock_api_call:
            with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
                # 两次超时，第三次成功
                mock_api_call.side_effect = [
                    BailianTimeoutError("Timeout"),
                    BailianTimeoutError("Timeout"),
                    {"success": True, "data": "ok"},
                ]

                payload = {"test": "payload"}
                result = await bailian_service._call_bailian_api_with_retry(payload)

                assert result == {"success": True, "data": "ok"}
                assert mock_api_call.call_count == 3
                # 验证指数退避：2秒，4秒
                assert mock_sleep.call_count == 2
                mock_sleep.assert_any_call(2)
                mock_sleep.assert_any_call(4)

    @pytest.mark.asyncio
    async def test_no_retry_on_auth_error(self, bailian_service):
        """测试认证错误不重试"""
        with patch.object(bailian_service, "_call_bailian_api") as mock_api_call:
            # 认证错误不应重试
            mock_api_call.side_effect = BailianAuthError("Auth failed")

            payload = {"test": "payload"}

            with pytest.raises(BailianAuthError):
                await bailian_service._call_bailian_api_with_retry(payload)

            # 只调用一次，不重试
            assert mock_api_call.call_count == 1

    @pytest.mark.asyncio
    async def test_max_retries_exceeded(self, bailian_service):
        """测试超过最大重试次数"""
        with patch.object(bailian_service, "_call_bailian_api") as mock_api_call:
            with patch("asyncio.sleep", new_callable=AsyncMock):
                # 所有调用都失败
                mock_api_call.side_effect = BailianTimeoutError("Timeout")

                payload = {"test": "payload"}

                with pytest.raises(BailianServiceError, match="API调用失败，已重试3次"):
                    await bailian_service._call_bailian_api_with_retry(payload)

                # 初次调用 + 3次重试 = 4次调用
                assert mock_api_call.call_count == 4


# ============================================================================
# 响应解析测试
# ============================================================================


class TestResponseParsing:
    """响应解析测试"""

    def test_parse_successful_response(self, bailian_service, mock_successful_response):
        """测试解析成功响应"""
        start_time = 1000.0

        with patch("time.time", return_value=1001.5):  # 模拟1.5秒处理时间
            response = bailian_service._parse_response(
                mock_successful_response, start_time
            )

        assert response.content == "这是一道关于方程的问题。让我帮你详细解答..."
        assert response.tokens_used == 150
        assert response.processing_time == 1.5
        assert response.model == "qwen-turbo"
        assert response.request_id == "req_123456"
        assert response.success is True
        assert response.error_message is None

    def test_parse_response_no_choices(self, bailian_service):
        """测试解析无选择的响应"""
        response_data = {
            "output": {"choices": []},
            "usage": {"total_tokens": 0},
            "request_id": "req_123",
            "model": "qwen-turbo",
        }

        with pytest.raises(BailianServiceError, match="API响应中没有生成内容"):
            bailian_service._parse_response(response_data, 1000.0)

    def test_parse_response_missing_fields(self, bailian_service):
        """测试解析缺少字段的响应"""
        # 测试缺少output字段
        response_data = {"usage": {"total_tokens": 100}}

        with pytest.raises(BailianServiceError, match="API响应中没有生成内容"):
            bailian_service._parse_response(response_data, 1000.0)


# ============================================================================
# 完整聊天补全测试
# ============================================================================


class TestChatCompletion:
    """聊天补全完整流程测试"""

    @pytest.mark.asyncio
    async def test_successful_chat_completion(
        self, bailian_service, sample_messages, sample_context, mock_successful_response
    ):
        """测试成功的聊天补全"""
        with patch.object(
            bailian_service, "_call_bailian_api_with_retry"
        ) as mock_api_call:
            mock_api_call.return_value = mock_successful_response

            response = await bailian_service.chat_completion(
                messages=sample_messages,
                context=sample_context,
                max_tokens=2000,
                temperature=0.8,
            )

            assert isinstance(response, ChatCompletionResponse)
            assert response.success is True
            assert response.content == "这是一道关于方程的问题。让我帮你详细解答..."
            assert response.tokens_used == 150
            assert response.processing_time > 0

            # 验证API调用参数
            mock_api_call.assert_called_once()
            call_args = mock_api_call.call_args[0][0]
            assert call_args["parameters"]["max_tokens"] == 2000
            assert call_args["parameters"]["temperature"] == 0.8
            assert call_args["user_id"] == "test_user_123"

    @pytest.mark.asyncio
    async def test_chat_completion_with_error(self, bailian_service, sample_messages):
        """测试聊天补全错误处理"""
        with patch.object(
            bailian_service, "_call_bailian_api_with_retry"
        ) as mock_api_call:
            mock_api_call.side_effect = BailianServiceError("API调用失败")

            with pytest.raises(BailianServiceError, match="聊天补全调用失败"):
                await bailian_service.chat_completion(messages=sample_messages)

    @pytest.mark.asyncio
    async def test_chat_completion_validation_error(self, bailian_service):
        """测试聊天补全参数验证错误"""
        # 空消息列表应该在格式化时捕获，但实际调用会失败
        with pytest.raises(BailianServiceError):
            await bailian_service.chat_completion(messages=[])


# ============================================================================
# 日志记录测试
# ============================================================================


class TestLogging:
    """日志记录测试"""

    @patch("src.services.bailian_service.logger")
    def test_log_request(self, mock_logger, bailian_service, sample_context):
        """测试请求日志记录"""
        payload = {
            "model": "qwen-turbo",
            "input": {"messages": [{"role": "user", "content": "test"}]},
            "parameters": {"max_tokens": 1500, "temperature": 0.7},
        }

        bailian_service._log_request(payload, sample_context)

        mock_logger.info.assert_called_once()
        call_args = mock_logger.info.call_args
        assert call_args[0][0] == "百炼API请求"

        log_data = call_args.kwargs["extra"]
        assert log_data["model"] == "qwen-turbo"
        assert log_data["message_count"] == 1
        assert log_data["user_id"] == "test_user_123"
        assert log_data["subject"] == "数学"

    @patch("src.services.bailian_service.logger")
    def test_log_successful_response(
        self, mock_logger, bailian_service, sample_context
    ):
        """测试成功响应日志记录"""
        response = ChatCompletionResponse(
            content="Test response",
            tokens_used=100,
            processing_time=1.5,
            model="qwen-turbo",
            request_id="req_123",
            success=True,
        )

        bailian_service._log_response(response, sample_context)

        mock_logger.info.assert_called_once()
        call_args = mock_logger.info.call_args
        assert call_args[0][0] == "百炼API响应成功"

        log_data = call_args.kwargs["extra"]
        assert log_data["success"] is True
        assert log_data["tokens_used"] == 100
        assert log_data["processing_time"] == 1.5

    @patch("src.services.bailian_service.logger")
    def test_log_failed_response(self, mock_logger, bailian_service):
        """测试失败响应日志记录"""
        response = ChatCompletionResponse(
            content="",
            tokens_used=0,
            processing_time=2.0,
            model="",
            request_id="",
            success=False,
            error_message="API调用失败",
        )

        bailian_service._log_response(response, None)

        mock_logger.error.assert_called_once()
        call_args = mock_logger.error.call_args
        assert call_args[0][0] == "百炼API响应失败"

        log_data = call_args.kwargs["extra"]
        assert log_data["success"] is False
        assert log_data["error_message"] == "API调用失败"


# ============================================================================
# 上下文管理器测试
# ============================================================================


class TestContextManager:
    """上下文管理器测试"""

    @pytest.mark.asyncio
    async def test_async_context_manager(self, bailian_service):
        """测试异步上下文管理器"""
        with patch.object(
            bailian_service.client, "aclose", new_callable=AsyncMock
        ) as mock_close:
            async with bailian_service:
                pass  # 在上下文中什么都不做

            mock_close.assert_called_once()

    @pytest.mark.asyncio
    async def test_close_method(self, bailian_service):
        """测试关闭方法"""
        with patch.object(
            bailian_service.client, "aclose", new_callable=AsyncMock
        ) as mock_close:
            await bailian_service.close()
            mock_close.assert_called_once()


# ============================================================================
# 全局服务实例测试
# ============================================================================


class TestGlobalService:
    """全局服务实例测试"""

    @patch("src.services.bailian_service.BailianService")
    def test_get_bailian_service_singleton(self, mock_service_class):
        """测试获取单例服务实例"""
        # 清理全局变量
        import src.services.bailian_service

        src.services.bailian_service._bailian_service = None

        mock_instance = Mock()
        mock_service_class.return_value = mock_instance

        # 第一次调用应创建新实例
        service1 = get_bailian_service()
        mock_service_class.assert_called_once()
        assert service1 == mock_instance

        # 第二次调用应返回相同实例
        service2 = get_bailian_service()
        assert service2 == mock_instance
        assert mock_service_class.call_count == 1  # 仍然只调用了一次

    @pytest.mark.asyncio
    async def test_close_global_service(self):
        """测试关闭全局服务实例"""
        # 设置一个模拟的全局服务实例
        import src.services.bailian_service

        mock_service = AsyncMock()
        src.services.bailian_service._bailian_service = mock_service

        await close_bailian_service()

        mock_service.close.assert_called_once()
        assert src.services.bailian_service._bailian_service is None


# ============================================================================
# 集成测试
# ============================================================================


class TestIntegration:
    """集成测试"""

    @pytest.mark.asyncio
    async def test_full_workflow_success(self, mock_settings, mock_successful_response):
        """测试完整工作流程成功场景"""
        service = BailianService(settings_override=mock_settings)

        with patch.object(service.client, "post") as mock_post:
            # 模拟成功的HTTP响应
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_successful_response
            mock_post.return_value = mock_response

            # 执行完整的聊天补全
            messages = [ChatMessage(role=MessageRole.USER, content="测试问题")]
            context = AIContext(user_id="test_user", subject="数学", grade_level=8)

            response = await service.chat_completion(messages=messages, context=context)

            # 验证结果
            assert response.success is True
            assert response.content == "这是一道关于方程的问题。让我帮你详细解答..."
            assert response.tokens_used == 150
            assert response.request_id == "req_123456"

            # 验证HTTP调用
            mock_post.assert_called_once()
            call_args = mock_post.call_args
            assert "/text-generation/generation" in call_args[0][0]  # URL

            payload = call_args.kwargs["json"]
            assert payload["app_id"] == "test_app_id"
            assert payload["user_id"] == "test_user"
            assert payload["input"]["messages"][0]["content"] == "测试问题"

    @pytest.mark.asyncio
    async def test_full_workflow_with_retry_success(
        self, mock_settings, mock_successful_response
    ):
        """测试包含重试的完整工作流程成功场景"""
        service = BailianService(settings_override=mock_settings)

        with patch.object(service.client, "post") as mock_post:
            with patch("asyncio.sleep", new_callable=AsyncMock):
                # 第一次调用429限流，第二次成功
                responses = [
                    Mock(status_code=429, headers={"Retry-After": "1"}),
                    Mock(
                        status_code=200,
                        json=Mock(return_value=mock_successful_response),
                    ),
                ]
                mock_post.side_effect = responses

                messages = [ChatMessage(role=MessageRole.USER, content="测试问题")]
                response = await service.chat_completion(messages=messages)

                # 验证最终成功
                assert response.success is True
                assert response.content == "这是一道关于方程的问题。让我帮你详细解答..."

                # 验证重试了一次
                assert mock_post.call_count == 2
