#!/usr/bin/env python3
"""
测试增强的公式处理功能
验证复杂公式拆分和简化功能
"""

import asyncio
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

from core.config import settings
from services.formula_service import FormulaService


async def test_enhanced_formula_processing():
    """测试增强的公式处理功能"""
    print("=" * 60)
    print("🚀 测试增强的公式处理功能")
    print("=" * 60)

    # 测试文本 - 包含复杂公式
    test_text = """
    计算球的体积：$$V = \\frac{4}{3} \\times \\pi \\times r^3 = \\frac{4}{3} \\times 3.14 \\times 3^3 = \\frac{4}{3} \\times 3.14 \\times 27$$
    
    简单公式：$V = \\frac{4}{3} \\pi r^3$
    
    另一个复杂公式：$$E = mc^2 = m \\times c \\times c = m \\times 299792458 \\times 299792458$$
    """

    try:
        # 创建FormulaService实例
        formula_service = FormulaService()

        print("📝 原始文本:")
        print(test_text)
        print("\n" + "=" * 60)

        # 提取公式
        print("🔍 1. 提取公式...")
        formulas = formula_service._extract_formulas(test_text)
        print(f"✅ 提取到 {len(formulas)} 个公式")

        for i, formula in enumerate(formulas, 1):
            print(f"   公式 {i}: {formula['content'][:50]}...")

        print("\n" + "=" * 60)

        # 测试复杂度检测
        print("🎯 2. 复杂度检测...")
        for i, formula in enumerate(formulas, 1):
            content = formula["content"]
            is_complex = formula_service._should_split_complex_formula(content)
            print(f"   公式 {i}: {'🔴 复杂' if is_complex else '🟢 简单'}")

            if is_complex:
                # 尝试拆分
                split_parts = formula_service._split_formula_by_equals(content)
                print(f"     拆分为 {len(split_parts)} 部分:")
                for j, part in enumerate(split_parts):
                    print(f"       {j+1}. {part}")

        print("\n" + "=" * 60)

        # 测试简化功能
        print("🔧 3. 公式简化测试...")
        complex_formula = "V = \\frac{4}{3} \\times \\pi \\times r^3"
        simplified = formula_service._simplify_formula(complex_formula)
        print(f"原始: {complex_formula}")
        print(f"简化: {simplified}")

        print("\n" + "=" * 60)
        print("✅ 增强功能测试完成！")

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_enhanced_formula_processing())
