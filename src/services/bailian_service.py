"""
阿里云百炼智能体服务

该模块提供统一的百炼智能体调用接口，支持：
- 聊天补全（Chat Completion）
- 错误处理和重试机制
- 请求/响应日志记录
- 成本监控（Token使用量）
"""

import asyncio
import json
import logging
import time
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, asdict
from enum import Enum

import httpx
from pydantic import BaseModel, Field

from src.core.config import get_settings
from src.core.exceptions import (
    BailianServiceError,
    BailianRateLimitError,
    BailianAuthError,
    BailianTimeoutError,
)


logger = logging.getLogger("bailian_service")
settings = get_settings()


class MessageRole(str, Enum):
    """消息角色枚举"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


@dataclass
class ChatMessage:
    """聊天消息"""
    role: MessageRole
    content: str


@dataclass
class AIContext:
    """AI调用上下文"""
    user_id: Optional[str] = None
    subject: Optional[str] = None
    grade_level: Optional[int] = None
    session_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class ChatCompletionResponse:
    """聊天补全响应"""
    content: str
    tokens_used: int
    processing_time: float
    model: str
    request_id: str
    success: bool = True
    error_message: Optional[str] = None


class BailianService:
    """阿里云百炼智能体服务"""

    def __init__(self, settings_override=None):
        _settings = settings_override or get_settings()
        self.application_id = _settings.BAILIAN_APPLICATION_ID
        self.api_key = _settings.BAILIAN_API_KEY
        self.base_url = _settings.BAILIAN_BASE_URL
        self.timeout = _settings.BAILIAN_TIMEOUT
        self.max_retries = _settings.BAILIAN_MAX_RETRIES

        # HTTP客户端配置
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(self.timeout),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "User-Agent": "wuhao-tutor/0.1.0"
            }
        )

        logger.info(f"百炼服务初始化成功: {self.application_id[:8]}...")

    async def chat_completion(
        self,
        messages: List[Union[Dict[str, str], ChatMessage]],
        context: Optional[AIContext] = None,
        **kwargs
    ) -> ChatCompletionResponse:
        """
        聊天补全接口

        Args:
            messages: 消息列表
            context: 调用上下文
            **kwargs: 其他参数（temperature, max_tokens等）

        Returns:
            ChatCompletionResponse: 聊天补全响应

        Raises:
            BailianServiceError: 服务调用失败
        """
        start_time = time.time()

        try:
            # 标准化消息格式
            formatted_messages = self._format_messages(messages)

            # 构建请求载荷
            payload = self._build_request_payload(
                formatted_messages,
                context,
                **kwargs
            )

            # 记录请求日志
            self._log_request(payload, context)

            # 调用API（带重试）
            response_data = await self._call_bailian_api_with_retry(payload)

            # 解析响应
            response = self._parse_response(response_data, start_time)

            # 记录响应日志
            self._log_response(response, context)

            return response

        except Exception as e:
            processing_time = time.time() - start_time
            error_response = ChatCompletionResponse(
                content="",
                tokens_used=0,
                processing_time=processing_time,
                model="",
                request_id="",
                success=False,
                error_message=str(e)
            )

            logger.error(f"百炼API调用失败: {e}")
            if context:
                logger.error(f"调用上下文: {asdict(context)}")

            raise BailianServiceError(f"聊天补全调用失败: {str(e)}") from e

    async def _call_bailian_api_with_retry(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        带重试机制的API调用

        Args:
            payload: 请求载荷

        Returns:
            Dict: API响应数据
        """
        last_exception = None

        for attempt in range(self.max_retries + 1):
            try:
                if attempt > 0:
                    # 指数退避
                    wait_time = min(2 ** attempt, 30)
                    logger.info(f"百炼API重试第{attempt}次，等待{wait_time}秒...")
                    await asyncio.sleep(wait_time)

                return await self._call_bailian_api(payload)

            except BailianRateLimitError as e:
                last_exception = e
                if attempt == self.max_retries:
                    raise BailianServiceError(f"API调用失败，已重试{self.max_retries}次: {str(e)}") from e
                logger.warning(f"遇到限流，准备重试: {e}")

            except BailianTimeoutError as e:
                last_exception = e
                if attempt == self.max_retries:
                    raise BailianServiceError(f"API调用失败，已重试{self.max_retries}次: {str(e)}") from e
                logger.warning(f"请求超时，准备重试: {e}")

            except (BailianAuthError, BailianServiceError) as e:
                # 认证错误和服务错误不重试
                raise e

            except Exception as e:
                last_exception = e
                if attempt == self.max_retries:
                    raise BailianServiceError(f"API调用失败: {str(e)}") from e
                logger.warning(f"未知错误，准备重试: {e}")

        # 所有重试都失败
        raise BailianServiceError(f"API调用失败，已重试{self.max_retries}次") from last_exception

    async def _call_bailian_api(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        调用百炼API

        Args:
            payload: 请求载荷

        Returns:
            Dict: API响应数据

        Raises:
            BailianServiceError: 各种API调用错误
        """
        url = f"{self.base_url}/services/aigc/text-generation/generation"

        try:
            response = await self.client.post(url, json=payload)

            # 处理HTTP错误
            if response.status_code == 401:
                raise BailianAuthError("API密钥无效或过期")
            elif response.status_code == 429:
                retry_after = response.headers.get("Retry-After", 60)
                raise BailianRateLimitError(f"API调用频率过高，请{retry_after}秒后重试")
            elif response.status_code >= 400:
                error_text = response.text
                raise BailianServiceError(
                    f"HTTP错误 {response.status_code}: {error_text}"
                )

            # 解析JSON响应
            try:
                response_data = response.json()
            except json.JSONDecodeError:
                raise BailianServiceError(f"无效的JSON响应: {response.text}")

            # 检查业务错误
            if not response_data.get("success", True):
                error_msg = response_data.get("message", "未知业务错误")
                error_code = response_data.get("code", "UNKNOWN")
                raise BailianServiceError(f"业务错误 [{error_code}]: {error_msg}")

            return response_data

        except httpx.TimeoutException:
            raise BailianTimeoutError(f"API调用超时（{self.timeout}秒）")
        except httpx.RequestError as e:
            raise BailianServiceError(f"网络请求错误: {str(e)}") from e

    def _format_messages(
        self,
        messages: List[Union[Dict[str, str], ChatMessage]]
    ) -> List[Dict[str, str]]:
        """
        标准化消息格式

        Args:
            messages: 原始消息列表

        Returns:
            List[Dict]: 标准化的消息列表
        """
        formatted = []

        for msg in messages:
            if isinstance(msg, ChatMessage):
                formatted.append({
                    "role": msg.role.value,
                    "content": msg.content
                })
            elif isinstance(msg, dict):
                # 验证必要字段
                if "role" not in msg or "content" not in msg:
                    raise ValueError("消息必须包含'role'和'content'字段")
                formatted.append({
                    "role": msg["role"],
                    "content": str(msg["content"])
                })
            else:
                raise ValueError(f"不支持的消息类型: {type(msg)}")

        return formatted

    def _build_request_payload(
        self,
        messages: List[Dict[str, str]],
        context: Optional[AIContext] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        构建API请求载荷

        Args:
            messages: 格式化的消息列表
            context: 调用上下文
            **kwargs: 其他参数

        Returns:
            Dict: 请求载荷
        """
        payload = {
            "model": "qwen-turbo",  # 默认模型
            "input": {
                "messages": messages
            },
            "parameters": {
                "result_format": "message",
                "max_tokens": kwargs.get("max_tokens", 1500),
                "temperature": kwargs.get("temperature", 0.7),
                "top_p": kwargs.get("top_p", 0.8),
                "top_k": kwargs.get("top_k", 100),
            }
        }

        # 添加应用ID
        if self.application_id:
            payload["app_id"] = self.application_id

        # 添加上下文信息
        if context:
            if context.user_id:
                payload["user_id"] = context.user_id
            if context.session_id:
                payload["session_id"] = context.session_id
            if context.metadata:
                payload.setdefault("parameters", {}).update(context.metadata)

        return payload

    def _parse_response(
        self,
        response_data: Dict[str, Any],
        start_time: float
    ) -> ChatCompletionResponse:
        """
        解析API响应

        Args:
            response_data: API响应数据
            start_time: 请求开始时间

        Returns:
            ChatCompletionResponse: 解析后的响应
        """
        processing_time = time.time() - start_time

        # 提取响应内容
        output = response_data.get("output", {})
        choices = output.get("choices", [])

        if not choices:
            raise BailianServiceError("API响应中没有生成内容")

        # 获取第一个选择的内容
        first_choice = choices[0]
        message = first_choice.get("message", {})
        content = message.get("content", "")

        # 提取使用统计
        usage = response_data.get("usage", {})
        tokens_used = usage.get("total_tokens", 0)

        # 提取请求ID
        request_id = response_data.get("request_id", "")

        # 提取模型信息
        model = response_data.get("model", "unknown")

        return ChatCompletionResponse(
            content=content,
            tokens_used=tokens_used,
            processing_time=processing_time,
            model=model,
            request_id=request_id,
            success=True
        )

    def _log_request(self, payload: Dict[str, Any], context: Optional[AIContext]) -> None:
        """记录请求日志"""
        log_data = {
            "action": "bailian_request",
            "model": payload.get("model"),
            "message_count": len(payload.get("input", {}).get("messages", [])),
            "max_tokens": payload.get("parameters", {}).get("max_tokens"),
            "temperature": payload.get("parameters", {}).get("temperature"),
        }

        if context:
            log_data.update({
                "user_id": context.user_id,
                "subject": context.subject,
                "grade_level": context.grade_level,
                "session_id": context.session_id,
            })

        logger.info("百炼API请求", extra=log_data)

    def _log_response(
        self,
        response: ChatCompletionResponse,
        context: Optional[AIContext]
    ) -> None:
        """记录响应日志"""
        log_data = {
            "action": "bailian_response",
            "success": response.success,
            "tokens_used": response.tokens_used,
            "processing_time": round(response.processing_time, 3),
            "model": response.model,
            "request_id": response.request_id,
            "content_length": len(response.content),
        }

        if context:
            log_data.update({
                "user_id": context.user_id,
                "session_id": context.session_id,
            })

        if response.success:
            logger.info("百炼API响应成功", extra=log_data)
        else:
            log_data["error_message"] = response.error_message
            logger.error("百炼API响应失败", extra=log_data)

    async def __aenter__(self):
        """异步上下文管理器入口"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self.client.aclose()

    async def close(self):
        """关闭HTTP客户端"""
        await self.client.aclose()
        logger.info("百炼服务已关闭")


# 创建全局服务实例
_bailian_service: Optional[BailianService] = None


def get_bailian_service() -> BailianService:
    """
    获取百炼服务单例

    Returns:
        BailianService: 百炼服务实例
    """
    global _bailian_service
    if _bailian_service is None:
        _bailian_service = BailianService()
    return _bailian_service


async def close_bailian_service():
    """关闭全局百炼服务实例"""
    global _bailian_service
    if _bailian_service:
        await _bailian_service.close()
        _bailian_service = None
