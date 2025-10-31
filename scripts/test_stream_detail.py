#!/usr/bin/env python3
"""详细测试百炼流式响应格式"""
import asyncio
import json

import httpx

API_KEY = "sk-2d1b9696e5804d21868ec4cdf3695762"
URL = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"


async def test_stream_detail():
    print("=" * 70)
    print("🔍 详细测试百炼流式响应")
    print("=" * 70)

    payload = {
        "model": "qwen-plus",
        "input": {
            "messages": [{"role": "user", "content": "请简单介绍一下Python编程语言"}]
        },
        "parameters": {
            "result_format": "message",
            "incremental_output": True,  # 启用流式
        },
    }

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
        "Accept": "text/event-stream",
    }

    async with httpx.AsyncClient(timeout=60) as client:
        async with client.stream("POST", URL, json=payload, headers=headers) as resp:
            print(f"✅ 状态码: {resp.status_code}")
            print(f"✅ Content-Type: {resp.headers.get('content-type')}")
            print(
                f"✅ Transfer-Encoding: {resp.headers.get('transfer-encoding', 'N/A')}"
            )
            print("\n" + "=" * 70)
            print("📨 SSE 数据流:")
            print("=" * 70)

            if resp.status_code == 200:
                count = 0
                full_content = ""

                async for line in resp.aiter_lines():
                    if not line.strip():
                        continue

                    count += 1
                    print(f"\n[Chunk {count}]")
                    print(line)

                    # 解析 SSE 格式
                    if line.startswith("data:"):
                        data_str = line[5:].strip()
                        try:
                            data = json.loads(data_str)
                            # 提取增量内容
                            choices = data.get("output", {}).get("choices", [])
                            if choices:
                                content = (
                                    choices[0].get("message", {}).get("content", "")
                                )
                                full_content += content
                                finish_reason = choices[0].get("finish_reason")

                                print(f"  └─ 增量内容: {repr(content)}")
                                print(f"  └─ 完成状态: {finish_reason}")
                        except json.JSONDecodeError:
                            print(f"  └─ 非JSON数据")

                    if count >= 20:  # 限制显示
                        print(f"\n... (还有更多数据,已省略) ...")
                        # 继续接收但不打印
                        async for _ in resp.aiter_lines():
                            count += 1
                        break

                print("\n" + "=" * 70)
                print(f"📊 统计:")
                print(f"  - 总数据块: {count}")
                print(f"  - 完整内容: {full_content[:200]}...")
                print(f"  - 内容长度: {len(full_content)} 字符")
                print("=" * 70)

                return True
            else:
                text = await resp.aread()
                print(f"❌ 错误: {text.decode()}")
                return False


if __name__ == "__main__":
    result = asyncio.run(test_stream_detail())

    print("\n" + "🎯" * 35)
    if result:
        print("✅ 百炼 API 完全支持 SSE 流式响应!")
        print("📝 建议: 立即实施方案 A - SSE 流式输出")
        print("🚀 用户体验将显著提升!")
    else:
        print("❌ 流式测试失败")
    print("🎯" * 35)
