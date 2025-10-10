#!/usr/bin/env python3
"""
修复百炼VL模型API端点问题

核心问题：VL模型需要使用OpenAI兼容模式的端点，而不是原生API端点
解决方案：为VL模型使用不同的API调用逻辑
"""

import sys

sys.path.insert(0, "/Users/liguoma/my-devs/python/wuhao-tutor")

import shutil
from pathlib import Path


def create_fixed_bailian_service():
    """修复百炼服务以支持VL模型"""

    # 备份原文件
    original_file = Path(
        "/Users/liguoma/my-devs/python/wuhao-tutor/src/services/bailian_service.py"
    )
    backup_file = original_file.with_suffix(".py.backup2")

    if not backup_file.exists():
        shutil.copy2(original_file, backup_file)
        print(f"✅ 已备份原文件: {backup_file}")

    # 读取原文件内容
    with open(original_file, "r", encoding="utf-8") as f:
        content = f.read()

    # 添加OpenAI兼容模式支持
    openai_import = """import asyncio
import json
import logging
import time
from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Union

import httpx
from pydantic import BaseModel, Field

from src.core.config import get_settings
from src.core.exceptions import (
    BailianAuthError,
    BailianRateLimitError,
    BailianServiceError,
    BailianTimeoutError,
)"""

    # 添加VL模型专用方法
    vl_methods = '''
    async def _call_vl_model_api(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        调用VL模型专用API（OpenAI兼容模式）
        
        VL模型使用不同的端点和请求格式
        """
        # VL模型使用OpenAI兼容模式端点
        url = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"
        
        # 转换为OpenAI兼容格式
        openai_payload = self._convert_to_openai_format(payload)
        
        try:
            response = await self.client.post(url, json=openai_payload)
            
            # 处理HTTP错误
            if response.status_code == 401:
                raise BailianAuthError("API密钥无效或过期")
            elif response.status_code == 429:
                retry_after = response.headers.get("Retry-After", 60)
                raise BailianRateLimitError(f"API调用频率过高，请{retry_after}秒后重试")
            elif response.status_code >= 400:
                error_text = response.text
                raise BailianServiceError(
                    f"VL模型HTTP错误 {response.status_code}: {error_text}"
                )
            
            # 解析JSON响应
            try:
                response_data = response.json()
            except json.JSONDecodeError:
                raise BailianServiceError(f"VL模型无效的JSON响应: {response.text}")
            
            # 转换回标准格式
            return self._convert_from_openai_format(response_data)
            
        except httpx.TimeoutException:
            raise BailianTimeoutError(f"VL模型API调用超时（{self.timeout}秒）")
        except httpx.RequestError as e:
            raise BailianServiceError(f"VL模型网络请求错误: {str(e)}") from e

    def _convert_to_openai_format(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        将原生API格式转换为OpenAI兼容格式
        """
        model = payload.get("model", "qwen-vl-max")
        messages = payload.get("input", {}).get("messages", [])
        parameters = payload.get("parameters", {})
        
        openai_payload = {
            "model": model,
            "messages": messages,
            "max_tokens": parameters.get("max_tokens", 1500),
            "temperature": parameters.get("temperature", 0.7),
            "top_p": parameters.get("top_p", 0.8),
        }
        
        logger.debug(f"转换为OpenAI格式: {openai_payload}")
        return openai_payload

    def _convert_from_openai_format(self, response_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        将OpenAI格式响应转换为原生API格式
        """
        choices = response_data.get("choices", [])
        if not choices:
            raise BailianServiceError("VL模型响应中没有choices")
        
        message = choices[0].get("message", {})
        content = message.get("content", "")
        
        # 构建标准响应格式
        standard_response = {
            "output": {
                "text": content,
                "choices": [{"message": {"content": content}}]
            },
            "usage": response_data.get("usage", {}),
            "request_id": response_data.get("id", ""),
        }
        
        return standard_response

    def _is_vl_model(self, model: str) -> bool:
        """
        判断是否为VL模型
        """
        vl_models = ["qwen-vl-max", "qwen-vl-plus", "qwen-vl-max-latest"]
        return model in vl_models
'''

    # 修改 _call_bailian_api 方法以支持VL模型
    old_call_api = '''    async def _call_bailian_api(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        调用百炼API

        Args:
            payload: 请求载荷

        Returns:
            Dict: API响应数据

        Raises:
            BailianServiceError: 各种API调用错误
        """
        url = f"{self.base_url}/services/aigc/text-generation/generation"'''

    new_call_api = '''    async def _call_bailian_api(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        调用百炼API

        Args:
            payload: 请求载荷

        Returns:
            Dict: API响应数据

        Raises:
            BailianServiceError: 各种API调用错误
        """
        model = payload.get("model", "")
        
        # VL模型使用OpenAI兼容模式
        if self._is_vl_model(model):
            logger.info(f"使用VL模型OpenAI兼容模式: {model}")
            return await self._call_vl_model_api(payload)
        
        # 普通模型使用原生API
        url = f"{self.base_url}/services/aigc/text-generation/generation"'''

    # 检查是否已经包含VL方法
    if "_call_vl_model_api" in content:
        print("⚠️  VL模型方法已存在，跳过添加")
    else:
        # 在类的末尾添加VL方法
        class_end = content.rfind("    def _log_response(")
        if class_end != -1:
            insert_pos = content.rfind("\n", 0, class_end)
            content = content[:insert_pos] + vl_methods + content[insert_pos:]
            print("✅ 已添加VL模型专用方法")
        else:
            print("❌ 未找到合适的插入位置")

    # 替换 _call_bailian_api 方法
    if old_call_api in content:
        content = content.replace(old_call_api, new_call_api)
        print("✅ 已修复API调用方法")
    else:
        print("⚠️  API调用方法可能已修复")

    # 写入修复后的文件
    with open(original_file, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"✅ 已保存修复后的文件: {original_file}")
    return True


def create_test_vl_api():
    """创建测试VL API的脚本"""

    test_script = '''#!/usr/bin/env python3
"""
测试修复后的VL模型API

使用官方示例图片验证OpenAI兼容模式是否工作正常
"""

import asyncio
import sys
sys.path.insert(0, "/Users/liguoma/my-devs/python/wuhao-tutor")

from src.services.bailian_service import ChatMessage, MessageRole, BailianService, AIContext
from typing import List, Union, Dict, Any


async def test_vl_openai_mode():
    """测试VL模型OpenAI兼容模式"""
    print("🧪 测试VL模型OpenAI兼容模式...")
    
    # 使用官方示例图片
    test_image = "https://help-static-aliyun-doc.aliyuncs.com/file-manage-files/zh-CN/20241022/emyrja/dog_and_girl.jpeg"
    
    messages: List[Union[Dict[str, Any], ChatMessage]] = [
        ChatMessage(
            role=MessageRole.SYSTEM,
            content="You are a helpful assistant."
        ),
        ChatMessage(
            role=MessageRole.USER,
            content="请描述这张图片的内容",
            image_urls=[test_image]
        )
    ]
    
    bailian_service = BailianService()
    context = AIContext(user_id="test_user", session_id="test_session")
    
    try:
        print(f"📷 测试图片: {test_image}")
        print("📤 发送VL模型请求...")
        
        response = await bailian_service.chat_completion(
            messages=messages,
            context=context,
            max_tokens=500,
            temperature=0.7
        )
        
        print("📥 VL模型响应:")
        print(f"   成功: {response.success}")
        print(f"   模型: {response.model}")
        print(f"   Token使用: {response.tokens_used}")
        print(f"   处理时间: {response.processing_time:.2f}秒")
        
        if response.success:
            print(f"\\n🤖 AI回复:")
            print(response.content)
            
            # 检查是否真的看到了图片
            if any(keyword in response.content for keyword in ["图片", "图像", "女士", "狗", "海滩"]):
                print("\\n✅ VL模型成功识别图片内容！")
                return True
            else:
                print("\\n⚠️  VL模型回复了，但可能未正确识别图片")
                return False
        else:
            print(f"\\n❌ VL模型调用失败: {response.error_message}")
            return False
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_normal_model():
    """测试普通模型是否仍正常工作"""
    print("\\n🔧 测试普通模型兼容性...")
    
    messages: List[Union[Dict[str, Any], ChatMessage]] = [
        ChatMessage(
            role=MessageRole.USER,
            content="你好，请介绍一下你自己"
        )
    ]
    
    bailian_service = BailianService()
    context = AIContext(user_id="test_user", session_id="test_session")
    
    try:
        print("📤 发送普通模型请求...")
        
        response = await bailian_service.chat_completion(
            messages=messages,
            context=context,
            max_tokens=200,
            temperature=0.7
        )
        
        print("📥 普通模型响应:")
        print(f"   成功: {response.success}")
        print(f"   模型: {response.model}")
        
        if response.success:
            print(f"   🤖 AI回复: {response.content[:100]}...")
            print("   ✅ 普通模型工作正常")
            return True
        else:
            print(f"   ❌ 普通模型失败: {response.error_message}")
            return False
            
    except Exception as e:
        print(f"❌ 普通模型测试失败: {e}")
        return False


async def main():
    """主函数"""
    print("🚀 VL模型API端点修复测试")
    print("=" * 40)
    
    # 测试VL模型
    vl_success = await test_vl_openai_mode()
    
    # 测试普通模型兼容性
    normal_success = await test_normal_model()
    
    print("\\n📊 测试结果总结:")
    print(f"   VL模型: {'✅ 成功' if vl_success else '❌ 失败'}")
    print(f"   普通模型: {'✅ 成功' if normal_success else '❌ 失败'}")
    
    if vl_success:
        print("\\n🎉 VL模型修复成功！")
        print("   现在可以正常识别和分析图片内容了")
        print("\\n🚀 下一步:")
        print("   1. 部署到生产环境")
        print("   2. 测试图片上传+VL识别完整流程")
    else:
        print("\\n😞 VL模型仍有问题，需要进一步调试")


if __name__ == "__main__":
    asyncio.run(main())
'''

    test_file = Path(
        "/Users/liguoma/my-devs/python/wuhao-tutor/scripts/test_vl_openai_mode.py"
    )
    with open(test_file, "w", encoding="utf-8") as f:
        f.write(test_script)

    print(f"✅ 已创建VL测试脚本: {test_file}")


def main():
    """主函数"""
    print("🔧 百炼VL模型API端点修复工具")
    print("=" * 50)

    print("🔍 问题分析:")
    print("1. VL模型需要使用OpenAI兼容模式端点")
    print("2. 当前使用的是原生API端点，不支持多模态输入")
    print("3. 需要为VL模型添加专用的API调用逻辑")

    # 应用修复
    if create_fixed_bailian_service():
        print("\\n✅ 修复完成!")

        # 创建测试脚本
        create_test_vl_api()

        print("\\n📝 修复内容:")
        print("1. 添加了VL模型检测逻辑")
        print("2. 为VL模型使用OpenAI兼容模式端点")
        print("3. 添加了格式转换方法")
        print("4. 保持普通模型使用原生API")

        print("\\n🧪 运行测试:")
        print("   cd /Users/liguoma/my-devs/python/wuhao-tutor")
        print("   uv run python scripts/test_vl_openai_mode.py")

    else:
        print("❌ 修复失败，请检查代码结构")


if __name__ == "__main__":
    main()
