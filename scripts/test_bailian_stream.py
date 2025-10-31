#!/usr/bin/env python3
"""
测试阿里云百炼 API 流式响应支持

参考文档: https://help.aliyun.com/zh/dashscope/developer-reference/api-details
"""

import asyncio
import json
import os
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import httpx
from dotenv import load_dotenv

# 加载环境变量
load_dotenv(project_root / ".env.production")


async def test_stream_support():
    """测试百炼 API 是否支持流式响应"""

    # 优先从环境变量获取，如果没有则使用硬编码的生产 Key
    api_key = os.getenv("BAILIAN_API_KEY") or "sk-2d1b9696e5804d21868ec4cdf3695762"

    if not api_key or not api_key.startswith("sk-"):
        print("❌ 错误: API Key 无效")
        return False

    print("=" * 60)
    print("🔍 测试阿里云百炼 API 流式响应支持")
    print("=" * 60)

    # 测试 URL
    base_url = "https://dashscope.aliyuncs.com/api/v1"
    url = f"{base_url}/services/aigc/text-generation/generation"

    # 测试载荷 - 尝试添加 stream 参数
    payload = {
        "model": "qwen-plus",  # 使用标准模型
        "input": {"messages": [{"role": "user", "content": "请用50字介绍一下你自己"}]},
        "parameters": {
            "result_format": "message",
            "incremental_output": True,  # 阿里云流式输出参数
        },
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "Accept": "text/event-stream",  # SSE 格式
        "X-DashScope-SSE": "enable",  # 可能需要的标志
    }

    print(f"\n📡 请求 URL: {url}")
    print(f"🔑 API Key: {api_key[:10]}...{api_key[-10:]}")
    print(f"📦 Payload: {json.dumps(payload, ensure_ascii=False, indent=2)}")

    # 测试1: 尝试 SSE 流式请求
    print("\n" + "=" * 60)
    print("测试 1: SSE 流式请求 (incremental_output=True)")
    print("=" * 60)

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            async with client.stream(
                "POST",
                url,
                json=payload,
                headers=headers,
            ) as response:
                print(f"✅ 状态码: {response.status_code}")
                print(f"📋 响应头: {dict(response.headers)}")

                if response.status_code == 200:
                    print("\n📨 流式数据:")
                    chunk_count = 0
                    async for line in response.aiter_lines():
                        if line.strip():
                            chunk_count += 1
                            print(f"  [{chunk_count}] {line}")

                    if chunk_count > 0:
                        print(f"\n✅ 成功接收到 {chunk_count} 个数据块 - 支持流式响应!")
                        return True
                    else:
                        print("\n⚠️ 未接收到流式数据块")
                else:
                    error_text = await response.aread()
                    print(f"❌ 请求失败: {error_text.decode('utf-8')}")

    except Exception as e:
        print(f"❌ 流式请求异常: {e}")

    # 测试2: 标准请求对比
    print("\n" + "=" * 60)
    print("测试 2: 标准非流式请求 (作为对比)")
    print("=" * 60)

    standard_payload = {
        "model": "qwen-plus",
        "input": {"messages": [{"role": "user", "content": "请用50字介绍一下你自己"}]},
        "parameters": {
            "result_format": "message",
        },
    }

    standard_headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                url,
                json=standard_payload,
                headers=standard_headers,
            )
            print(f"✅ 状态码: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                print(f"📦 响应数据结构:")
                print(json.dumps(data, ensure_ascii=False, indent=2))
                return False  # 标准请求可用,但不是流式
            else:
                print(f"❌ 请求失败: {response.text}")

    except Exception as e:
        print(f"❌ 标准请求异常: {e}")

    return False


async def main():
    """主函数"""
    supported = await test_stream_support()

    print("\n" + "=" * 60)
    print("🎯 结论:")
    print("=" * 60)

    if supported:
        print("✅ 阿里云百炼 API 支持流式响应!")
        print("📝 建议: 实施方案 A (SSE 流式响应)")
        print("🚀 可以继续开发流式输出功能")
    else:
        print("❌ 阿里云百炼 API 暂不支持流式响应")
        print("📝 建议: 实施方案 B (假进度条) 或方案 C (分段返回)")
        print("💡 可以联系阿里云技术支持确认是否有流式 API")

    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
