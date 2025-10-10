#!/usr/bin/env python3
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
            print(f"\n🤖 AI回复:")
            print(response.content)
            
            # 检查是否真的看到了图片
            if any(keyword in response.content for keyword in ["图片", "图像", "女士", "狗", "海滩"]):
                print("\n✅ VL模型成功识别图片内容！")
                return True
            else:
                print("\n⚠️  VL模型回复了，但可能未正确识别图片")
                return False
        else:
            print(f"\n❌ VL模型调用失败: {response.error_message}")
            return False
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_normal_model():
    """测试普通模型是否仍正常工作"""
    print("\n🔧 测试普通模型兼容性...")
    
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
    
    print("\n📊 测试结果总结:")
    print(f"   VL模型: {'✅ 成功' if vl_success else '❌ 失败'}")
    print(f"   普通模型: {'✅ 成功' if normal_success else '❌ 失败'}")
    
    if vl_success:
        print("\n🎉 VL模型修复成功！")
        print("   现在可以正常识别和分析图片内容了")
        print("\n🚀 下一步:")
        print("   1. 部署到生产环境")
        print("   2. 测试图片上传+VL识别完整流程")
    else:
        print("\n😞 VL模型仍有问题，需要进一步调试")


if __name__ == "__main__":
    asyncio.run(main())
