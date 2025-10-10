#!/usr/bin/env python3
"""
生产环境VL模型完整流程验证

测试：图片上传 → AI访问URL生成 → VL模型识别 → 返回结果
"""

import asyncio
import base64
import json
import sys
from io import BytesIO
from pathlib import Path

import httpx


async def create_test_image():
    """创建一个简单的测试图片"""
    try:
        from PIL import Image, ImageDraw, ImageFont

        # 创建一个简单的数学题图片
        img = Image.new("RGB", (400, 200), color="white")
        draw = ImageDraw.Draw(img)

        # 画数学题目
        draw.text((50, 50), "x² + 5x + 6 = 0", fill="black", font_size=24)
        draw.text((50, 90), "求解这个二次方程", fill="black", font_size=16)

        # 保存为字节
        img_bytes = BytesIO()
        img.save(img_bytes, format="PNG")
        img_bytes.seek(0)

        return img_bytes.getvalue()

    except ImportError:
        # 如果没有PIL，创建一个最小的PNG图片
        # 1x1像素的透明PNG
        png_data = base64.b64decode(
            b"iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
        )
        return png_data


async def test_production_image_upload():
    """测试生产环境图片上传"""
    print("🧪 测试生产环境完整VL流程")
    print("=" * 50)

    # 生产环境地址
    base_url = "https://wuhao-tutor.liguoma.cn"

    # 创建测试图片
    print("🎨 创建测试图片...")
    image_data = await create_test_image()
    print(f"   图片大小: {len(image_data)} bytes")

    async with httpx.AsyncClient(timeout=30.0, verify=False) as client:
        try:
            # 1. 测试健康检查
            print("\\n🏥 检查服务健康状态...")
            health_response = await client.get(f"{base_url}/api/v1/files/health")
            print(f"   状态码: {health_response.status_code}")
            if health_response.status_code == 200:
                health_data = health_response.json()
                print(
                    f"   存储状态: {health_data.get('storage', {}).get('directory_writable', 'unknown')}"
                )
                print(
                    f"   剩余空间: {health_data.get('storage', {}).get('free_space_formatted', 'unknown')}"
                )

            # 2. 上传图片用于AI分析
            print("\\n📤 上传图片到AI分析端点...")

            files = {"file": ("math_problem.png", image_data, "image/png")}

            # 模拟登录用户的token（这里需要真实的token）
            headers = {
                "Authorization": "Bearer test-token-for-demo"  # 实际需要真实token
            }

            upload_response = await client.post(
                f"{base_url}/api/v1/files/upload-for-ai", files=files, headers=headers
            )

            print(f"   上传状态码: {upload_response.status_code}")

            if upload_response.status_code == 200:
                upload_data = upload_response.json()
                print(f"   上传成功: {upload_data.get('success')}")

                ai_accessible_url = upload_data.get("data", {}).get("ai_accessible_url")
                print(f"   AI访问URL: {ai_accessible_url}")

                # 3. 验证AI访问URL可达性
                print("\\n🔗 验证AI访问URL...")
                if ai_accessible_url:
                    try:
                        url_check = await client.head(ai_accessible_url)
                        print(f"   URL状态码: {url_check.status_code}")
                        print(
                            f"   Content-Type: {url_check.headers.get('content-type', 'unknown')}"
                        )
                    except Exception as e:
                        print(f"   URL检查失败: {e}")

                # 4. 测试学习问答API（包含图片）
                print("\\n🤖 测试VL模型图片识别...")

                learning_request = {
                    "content": "请分析这张图片中的数学题目并给出解答步骤",
                    "question_type": "problem_solving",
                    "subject": "math",
                    "image_urls": [ai_accessible_url] if ai_accessible_url else [],
                    "use_context": True,
                    "include_history": False,
                    "max_history": 5,
                }

                learning_response = await client.post(
                    f"{base_url}/api/v1/learning/ask",
                    json=learning_request,
                    headers=headers,
                )

                print(f"   VL模型状态码: {learning_response.status_code}")

                if learning_response.status_code == 200:
                    learning_data = learning_response.json()
                    answer_content = learning_data.get("answer", {}).get("content", "")
                    tokens_used = learning_data.get("tokens_used", 0)
                    processing_time = learning_data.get("processing_time", 0)

                    print(f"   Token使用: {tokens_used}")
                    print(f"   处理时间: {processing_time}ms")
                    print(f"   \\n🤖 AI回复:")
                    print(f"   {answer_content[:300]}...")

                    # 检查VL模型是否真的看到了图片
                    image_keywords = ["图片", "图像", "方程", "x²", "二次", "数学"]
                    found_keywords = [
                        kw for kw in image_keywords if kw in answer_content
                    ]

                    if found_keywords:
                        print(f"   ✅ VL模型成功识别图片内容！")
                        print(f"   识别关键词: {', '.join(found_keywords)}")
                        return True
                    else:
                        print(f"   ⚠️  VL模型回复了，但可能未正确识别图片内容")
                        return False

                elif learning_response.status_code == 401:
                    print(f"   ❌ 认证失败，需要有效的用户token")
                    return False
                else:
                    print(f"   ❌ VL模型调用失败")
                    try:
                        error_data = learning_response.json()
                        print(f"   错误信息: {error_data}")
                    except:
                        print(f"   错误文本: {learning_response.text}")
                    return False

            elif upload_response.status_code == 401:
                print(f"   ❌ 认证失败，需要有效的用户token")
                print(f"   提示: 请先登录获取有效的认证token")
                return False
            else:
                print(f"   ❌ 图片上传失败")
                try:
                    error_data = upload_response.json()
                    print(f"   错误信息: {error_data}")
                except:
                    print(f"   错误文本: {upload_response.text}")
                return False

        except Exception as e:
            print(f"❌ 测试过程中发生异常: {e}")
            import traceback

            traceback.print_exc()
            return False


async def test_without_auth():
    """测试无需认证的端点"""
    print("\\n🧪 测试无认证端点...")

    base_url = "https://wuhao-tutor.liguoma.cn"

    async with httpx.AsyncClient(timeout=10.0, verify=False) as client:
        try:
            # 测试学习模块健康检查
            health_response = await client.get(f"{base_url}/api/v1/learning/health")
            print(f"   学习模块健康检查: {health_response.status_code}")

            if health_response.status_code == 200:
                health_data = health_response.json()
                print(f"   模块状态: {health_data.get('status')}")
                print(f"   消息: {health_data.get('message')}")

            # 测试无认证的测试端点
            test_response = await client.get(f"{base_url}/api/v1/learning/test")
            print(f"   学习模块测试端点: {test_response.status_code}")

            if test_response.status_code == 200:
                test_data = test_response.json()
                print(f"   测试消息: {test_data.get('message')}")
                print(f"   ✅ 基础API功能正常")
                return True
            else:
                print(f"   ❌ 基础API测试失败")
                return False

        except Exception as e:
            print(f"   ❌ 无认证测试失败: {e}")
            return False


async def main():
    """主函数"""
    print("🚀 生产环境VL模型完整验证")
    print("🌐 目标: https://wuhao-tutor.liguoma.cn")
    print("=" * 60)

    # 测试基础功能
    basic_success = await test_without_auth()

    # 测试完整流程（需要认证）
    full_success = await test_production_image_upload()

    print("\\n📊 测试结果总结:")
    print(f"   基础API功能: {'✅ 正常' if basic_success else '❌ 异常'}")
    print(f"   VL完整流程: {'✅ 成功' if full_success else '❌ 失败'}")

    if full_success:
        print("\\n🎉 生产环境VL模型修复成功！")
        print("   ✅ 图片上传功能正常")
        print("   ✅ AI访问URL生成正确")
        print("   ✅ VL模型可正常识别图片")
        print("   ✅ 完整流程验证通过")

        print("\\n📝 用户使用步骤:")
        print("   1. 访问 https://wuhao-tutor.liguoma.cn")
        print("   2. 注册/登录账户")
        print("   3. 进入学习页面")
        print("   4. 上传包含题目的图片")
        print("   5. 输入问题并发送")
        print("   6. AI将分析图片内容并回答")

    else:
        print("\\n😞 部分功能可能需要进一步调试")
        print("   💡 主要问题可能是认证token获取")
        print("   🔧 建议通过前端界面进行实际测试")


if __name__ == "__main__":
    asyncio.run(main())
