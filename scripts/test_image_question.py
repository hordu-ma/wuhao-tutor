#!/usr/bin/env python3
"""
测试图片上传和AI识别的完整流程
"""

import asyncio
import json
import sys
from pathlib import Path

import httpx

# 配置
API_BASE = "https://121.199.173.244/api/v1"
TEST_IMAGE = "/Users/liguoma/my-devs/python/wuhao-tutor/IMG_1018.jpeg"
TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJlMTBkOGI2Yi0wMzNhLTQxOTgtYmI3Yi05OWZmMWQ0ZDVlYTgiLCJleHAiOjE3NjAyMDA2MTEsImlhdCI6MTcyODY2NDYxMX0.SJkW_0LwRBf5fKPBhOZ8Mf1bM7NE6VcHtNHMDPvPCFE"


async def main():
    # 忽略SSL证书验证
    client = httpx.AsyncClient(verify=False, timeout=30.0)

    try:
        print("=" * 60)
        print("🧪 测试图片上传和AI识别")
        print("=" * 60)

        # 1. 上传图片
        print("\n📤 步骤1: 上传图片到OSS...")
        with open(TEST_IMAGE, "rb") as f:
            files = {"file": ("test.jpg", f, "image/jpeg")}
            headers = {"Authorization": f"Bearer {TOKEN}"}

            upload_response = await client.post(
                f"{API_BASE}/files/upload-for-ai",
                files=files,
                headers=headers,
            )

        print(f"   状态码: {upload_response.status_code}")

        if upload_response.status_code != 200:
            print(f"   ❌ 上传失败: {upload_response.text}")
            return

        upload_data = upload_response.json()
        image_url = upload_data["ai_accessible_url"]
        print(f"   ✅ 上传成功!")
        print(f"   📸 图片URL: {image_url}")

        # 2. 发送问题给AI
        print("\n💬 步骤2: 发送图片问题给AI...")
        ask_payload = {
            "content": "解答图片中的物理题",
            "question_type": "problem_solving",
            "image_urls": [image_url],
            "use_context": False,
            "include_history": False,
            "max_history": 0,
        }

        print(f"   请求体: {json.dumps(ask_payload, ensure_ascii=False, indent=2)}")

        ask_response = await client.post(
            f"{API_BASE}/learning/ask",
            json=ask_payload,
            headers=headers,
        )

        print(f"\n   状态码: {ask_response.status_code}")

        if ask_response.status_code != 200:
            print(f"   ❌ 提问失败: {ask_response.text}")
            return

        ask_data = ask_response.json()
        print(f"   ✅ AI响应:")
        print(f"   {ask_data['answer'][:200]}...")

        # 检查AI是否提到无法查看图片
        if "无法" in ask_data["answer"] and "图片" in ask_data["answer"]:
            print("\n   ⚠️  AI仍然说无法查看图片！")
        else:
            print("\n   ✅ AI成功分析了图片内容！")

        print("\n" + "=" * 60)
        print("📋 完整AI响应:")
        print("=" * 60)
        print(ask_data["answer"])

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback

        traceback.print_exc()
    finally:
        await client.aclose()


if __name__ == "__main__":
    asyncio.run(main())
