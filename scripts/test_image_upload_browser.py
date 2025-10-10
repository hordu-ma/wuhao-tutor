#!/usr/bin/env python3
"""
使用 Playwright 测试生产环境的图片识别功能
"""
import asyncio
import json

from playwright.async_api import async_playwright, expect


async def test_image_recognition():
    """测试完整的图片识别流程"""
    print("🚀 启动浏览器测试...")

    async with async_playwright() as p:
        # 启动浏览器（有界面模式，方便查看）
        browser = await p.chromium.launch(headless=False, slow_mo=1000)
        # 忽略HTTPS证书错误（生产环境使用自签名证书）
        context = await browser.new_context(ignore_https_errors=True)

        # 启用请求拦截，记录所有请求
        requests = []

        async def handle_request(route, request):
            requests.append(
                {
                    "url": request.url,
                    "method": request.method,
                    "post_data": request.post_data,
                }
            )
            await route.continue_()

        await context.route("**/*", handle_request)

        page = await context.new_page()

        try:
            # 1. 访问生产环境
            print("📍 访问生产环境...")
            await page.goto(
                "https://121.199.173.244/learning", wait_until="networkidle"
            )

            # 等待页面加载
            await page.wait_for_timeout(2000)

            # 2. 检查是否需要登录
            print("🔐 检查登录状态...")
            try:
                # 如果看到登录页面，尝试登录
                login_button = page.locator('button:has-text("登录")')
                if await login_button.count() > 0:
                    print("⚠️  需要登录，请手动登录...")
                    print("等待30秒让你手动登录...")
                    await page.wait_for_timeout(30000)
            except:
                print("✅ 已登录")

            # 3. 进入学习问答页面
            print("📚 进入学习问答...")
            await page.goto(
                "https://121.199.173.244/learning", wait_until="networkidle"
            )
            await page.wait_for_timeout(2000)

            # 4. 点击图片上传按钮
            print("📎 查找图片上传按钮...")
            # 查找上传按钮
            upload_button = page.locator('input[type="file"][accept*="image"]')

            if await upload_button.count() == 0:
                print("❌ 未找到图片上传按钮")
                await page.screenshot(path="error_no_upload_button.png")
                return

            # 5. 上传图片
            print("🖼️  上传测试图片...")
            await upload_button.set_input_files(
                "/Users/liguoma/my-devs/python/wuhao-tutor/IMG_1018.jpeg"
            )

            # 等待图片预览出现
            print("⏳ 等待图片预览...")
            await page.wait_for_timeout(3000)

            # 截图查看预览
            await page.screenshot(path="after_image_upload.png")
            print("✅ 已截图保存: after_image_upload.png")

            # 6. 输入问题
            print("✍️  输入问题...")
            textarea = page.locator('textarea[placeholder*="输入你的问题"]')
            await textarea.fill("请解答图中的物理题")

            # 7. 点击发送按钮
            print("📤 点击发送按钮...")
            send_button = page.locator('button:has-text("发送")')

            # 监听 /api/v1/learning/ask 请求
            ask_request_data = None

            async def capture_ask_request(route, request):
                nonlocal ask_request_data
                if "/api/v1/learning/ask" in request.url:
                    ask_request_data = request.post_data
                    print(f"\n🎯 捕获到 /api/v1/learning/ask 请求!")
                    print(
                        f"请求体: {request.post_data[:500] if request.post_data else 'None'}..."
                    )
                await route.continue_()

            await page.route("**/api/v1/learning/ask", capture_ask_request)

            # 点击发送
            await send_button.click()

            # 等待请求发送
            print("⏳ 等待请求发送...")
            await page.wait_for_timeout(5000)

            # 8. 分析请求数据
            print("\n" + "=" * 60)
            print("📊 请求分析")
            print("=" * 60)

            if ask_request_data:
                try:
                    request_json = json.loads(ask_request_data)
                    print("\n✅ 请求JSON:")
                    print(json.dumps(request_json, indent=2, ensure_ascii=False))

                    # 检查是否包含 image_urls
                    if "image_urls" in request_json:
                        image_urls = request_json["image_urls"]
                        if image_urls and len(image_urls) > 0:
                            print(f"\n✅ 包含图片URL: {len(image_urls)} 张")
                            for i, url in enumerate(image_urls, 1):
                                print(f"  {i}. {url}")

                                # 检查URL是否是公网地址
                                if "internal" in url:
                                    print(
                                        f"    ❌ 警告：URL包含'internal'，AI服务可能无法访问！"
                                    )
                                elif url.startswith("https://"):
                                    print(f"    ✅ URL格式正确（HTTPS）")
                                else:
                                    print(f"    ⚠️  URL不是HTTPS")
                        else:
                            print("\n❌ image_urls字段存在但为空!")
                    else:
                        print("\n❌ 请求中不包含 image_urls 字段!")
                        print("这意味着前端没有上传图片，或者上传失败了")

                except json.JSONDecodeError as e:
                    print(f"\n❌ 无法解析请求JSON: {e}")
                    print(f"原始数据: {ask_request_data}")
            else:
                print("\n❌ 未捕获到 /api/v1/learning/ask 请求")
                print("请检查是否成功点击了发送按钮")

            # 等待AI响应
            print("\n⏳ 等待AI响应...")
            await page.wait_for_timeout(5000)

            # 截图最终结果
            await page.screenshot(path="final_result.png")
            print("\n✅ 最终结果截图已保存: final_result.png")

            # 保持浏览器打开30秒，方便查看
            print("\n💡 浏览器将在30秒后关闭，你可以手动查看页面...")
            await page.wait_for_timeout(30000)

        except Exception as e:
            print(f"\n❌ 测试出错: {e}")
            import traceback

            traceback.print_exc()
            await page.screenshot(path="error_screenshot.png")
            print("错误截图已保存: error_screenshot.png")

        finally:
            await browser.close()


if __name__ == "__main__":
    print("=" * 60)
    print("🧪 图片识别浏览器测试")
    print("=" * 60)
    asyncio.run(test_image_recognition())
