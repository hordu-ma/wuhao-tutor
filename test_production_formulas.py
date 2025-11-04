#!/usr/bin/env python3
"""
生产环境公式处理验证脚本
测试增强的FormulaService在真实环境中的表现
"""

import json
import time

import requests


def test_production_formula_service():
    """测试生产环境的公式处理功能"""

    # 生产环境API地址
    BASE_URL = "https://horsduroot.com/api/v1"

    print("=" * 60)
    print("🌐 生产环境公式处理功能验证")
    print("=" * 60)

    # 测试用例 - 包含不同复杂度的公式
    test_cases = [
        {"name": "简单公式", "content": "球的体积公式：$V = \\frac{4}{3} \\pi r^3$"},
        {
            "name": "复杂公式（应该被拆分）",
            "content": "复杂计算：$$V = \\frac{4}{3} \\times \\pi \\times r^3 = \\frac{4}{3} \\times 3.14 \\times 3^3 = \\frac{4}{3} \\times 3.14 \\times 27$$",
        },
        {
            "name": "超复杂公式",
            "content": "能量公式：$$E = mc^2 = m \\times c \\times c = m \\times 299792458 \\times 299792458$$",
        },
    ]

    try:
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n📐 测试用例 {i}: {test_case['name']}")
            print(f"   内容: {test_case['content'][:50]}...")

            # 构造请求数据
            payload = {"content": test_case["content"], "subject": "math"}

            # 发送请求
            print("   🚀 发送请求...")
            start_time = time.time()

            response = requests.post(
                f"{BASE_URL}/homework/extract-formulas",
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=30,
            )

            end_time = time.time()
            duration = end_time - start_time

            print(f"   ⏱️  响应时间: {duration:.2f}s")

            if response.status_code == 200:
                result = response.json()
                print(f"   ✅ 成功响应")
                print(f"   📊 提取到 {len(result.get('formulas', []))} 个公式")

                # 显示处理后的公式
                for j, formula in enumerate(result.get("formulas", []), 1):
                    print(f"     公式 {j}: {formula.get('content', '')[:40]}...")
                    if formula.get("image_url"):
                        print(f"     图片: {formula['image_url']}")

            else:
                print(f"   ❌ 请求失败: {response.status_code}")
                print(f"   错误信息: {response.text[:100]}...")

            # 避免请求过于频繁
            if i < len(test_cases):
                time.sleep(2)

    except Exception as e:
        print(f"❌ 测试过程中出现错误: {e}")

    print("\n" + "=" * 60)
    print("✅ 生产环境验证完成！")
    print("\n💡 接下来可以在微信小程序中测试实际效果")


if __name__ == "__main__":
    test_production_formula_service()
