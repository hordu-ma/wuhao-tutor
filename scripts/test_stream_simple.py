#!/usr/bin/env python3
"""简化的百炼流式测试"""
import asyncio

import httpx

API_KEY = "sk-2d1b9696e5804d21868ec4cdf3695762"
URL = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"


async def test_stream():
    print("🔍 测试百炼流式响应...")

    payload = {
        "model": "qwen-plus",
        "input": {"messages": [{"role": "user", "content": "你好"}]},
        "parameters": {"result_format": "message", "incremental_output": True},
    }

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
        "Accept": "text/event-stream",
    }

    async with httpx.AsyncClient(timeout=30) as client:
        async with client.stream("POST", URL, json=payload, headers=headers) as resp:
            print(f"状态码: {resp.status_code}")
            print(f"Content-Type: {resp.headers.get('content-type')}")

            if resp.status_code == 200:
                count = 0
                async for line in resp.aiter_lines():
                    if line.strip():
                        count += 1
                        if count <= 5:
                            print(f"[{count}] {line[:100]}")

                if count > 1:
                    print(f"\n✅ 流式支持! 收到 {count} 个数据块")
                    return True
                else:
                    print(f"\n❌ 非流式,只有 {count} 个响应")
            else:
                text = await resp.aread()
                print(f"❌ 错误: {text.decode()[:200]}")

    return False


if __name__ == "__main__":
    result = asyncio.run(test_stream())
    print(f"\n结论: {'✅ 支持流式' if result else '❌ 不支持流式'}")
