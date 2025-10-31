#!/usr/bin/env python3
"""
WebSocket 流式问答测试脚本
用于验证生产环境的 WebSocket 连接和流式响应
"""

import asyncio
import json
import sys

import websockets


async def test_websocket_stream():
    """测试 WebSocket 流式问答"""

    # 1. 登录获取 token
    import httpx

    print("🔐 正在登录获取 token...")
    login_url = "https://horsduroot.com/api/v1/auth/login"
    login_data = {"phone": "13800000001", "password": "password123"}

    async with httpx.AsyncClient() as client:
        response = await client.post(login_url, json=login_data)
        if response.status_code != 200:
            print(f"❌ 登录失败: {response.status_code}")
            print(response.text)
            return

        token = response.json()["access_token"]
        print(f"✅ 登录成功，获取到 token: {token[:20]}...")

    # 2. 连接 WebSocket
    ws_url = "wss://horsduroot.com/api/v1/learning/ws/ask"

    print(f"\n🔌 正在连接 WebSocket: {ws_url}")

    try:
        async with websockets.connect(
            ws_url,
            ping_interval=20,
            ping_timeout=10,
        ) as websocket:
            print("✅ WebSocket 连接成功")

            # 3. 发送请求
            request_data = {
                "token": token,
                "params": {
                    "content": "什么是勾股定理？请简要说明。",
                    "question_type": "concept",
                    "subject": "math",
                    "use_context": False,
                },
            }

            print(f"\n📤 发送请求: {request_data['params']['content']}")
            await websocket.send(json.dumps(request_data))
            print("✅ 请求已发送")

            # 4. 接收流式响应
            print("\n📥 接收流式响应:")
            print("-" * 60)

            full_content = ""
            chunk_count = 0

            async for message in websocket:
                chunk = json.loads(message)
                chunk_count += 1

                if chunk["type"] == "content":
                    # 显示流式内容
                    content = chunk.get("content", "")
                    full_content += content
                    print(content, end="", flush=True)

                elif chunk["type"] == "done":
                    print("\n" + "-" * 60)
                    print(f"\n✅ 流式响应完成!")
                    print(f"📊 统计信息:")
                    print(f"  - 总块数: {chunk_count}")
                    print(f"  - 总字符数: {len(full_content)}")
                    print(f"  - question_id: {chunk.get('question_id', 'N/A')}")
                    print(f"  - answer_id: {chunk.get('answer_id', 'N/A')}")
                    print(f"  - session_id: {chunk.get('session_id', 'N/A')}")

                    if chunk.get("usage"):
                        print(f"  - Token 使用: {chunk['usage']}")

                    break

                elif chunk["type"] == "error":
                    print(f"\n❌ 错误: {chunk.get('message', '未知错误')}")
                    break

            print("\n✅ 测试完成")

    except websockets.exceptions.WebSocketException as e:
        print(f"❌ WebSocket 连接错误: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    print("=" * 60)
    print("🧪 WebSocket 流式问答测试")
    print("=" * 60)

    asyncio.run(test_websocket_stream())
