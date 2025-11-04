#!/usr/bin/env python3
"""
测试增强的公式处理功能 - 简化版本
不依赖外部模块，直接测试核心逻辑
"""

import re


def should_split_complex_formula(content: str) -> bool:
    """检查是否应该拆分复杂公式"""
    # 长度检查
    if len(content) > 80:
        return True

    # 复杂符号检查
    complex_patterns = [
        r"\\times.*\\times",  # 多个乘法
        r"\\frac.*\\frac",  # 多个分数
        r"=.*=.*=",  # 多个等号
        r"\\sum.*\\sum",  # 多个求和
        r"\\int.*\\int",  # 多个积分
    ]

    for pattern in complex_patterns:
        if re.search(pattern, content):
            return True

    return False


def split_formula_by_equals(content: str) -> list:
    """按等号拆分公式"""
    # 避免拆分函数内的等号，如 \sum_{i=1}^{n}
    parts = []
    current_part = ""
    in_braces = 0

    i = 0
    while i < len(content):
        char = content[i]

        if char == "{":
            in_braces += 1
        elif char == "}":
            in_braces -= 1
        elif char == "=" and in_braces == 0:
            # 找到顶级等号
            if current_part.strip():
                parts.append(current_part.strip())
            current_part = ""
            i += 1
            continue

        current_part += char
        i += 1

    # 添加最后一部分
    if current_part.strip():
        parts.append(current_part.strip())

    # 重构为完整等式
    if len(parts) > 1:
        reconstructed = []
        for i in range(len(parts) - 1):
            if i == 0:
                reconstructed.append(f"{parts[i]} = {parts[i+1]}")
            else:
                reconstructed.append(f"= {parts[i+1]}")
        return reconstructed

    return [content]


def simplify_formula(content: str) -> str:
    """简化公式表达式"""
    simplified = content

    # 简单的字符串替换
    simplified = simplified.replace("\\times", "\\cdot")  # 乘法符号简化
    simplified = simplified.replace("\\displaystyle", "")  # 移除显示样式
    simplified = simplified.replace("\\left(", "(")  # 简化括号
    simplified = simplified.replace("\\right)", ")")
    simplified = simplified.replace("\\left[", "[")
    simplified = simplified.replace("\\right]", "]")

    return simplified


def test_enhanced_processing():
    """测试增强处理功能"""
    print("=" * 60)
    print("🧪 增强公式处理功能测试")
    print("=" * 60)

    # 测试用例
    test_cases = [
        "V = \\frac{4}{3} \\pi r^3",  # 简单公式
        "V = \\frac{4}{3} \\times \\pi \\times r^3 = \\frac{4}{3} \\times 3.14 \\times 27",  # 复杂公式
        "E = mc^2 = m \\times c \\times c = m \\times 299792458 \\times 299792458",  # 超复杂公式
        "\\sum_{i=1}^{n} x_i = x_1 + x_2 + \\ldots + x_n",  # 求和公式
    ]

    for i, formula in enumerate(test_cases, 1):
        print(f"\n📐 测试用例 {i}:")
        print(f"   原始: {formula}")

        # 复杂度检测
        is_complex = should_split_complex_formula(formula)
        print(f"   复杂度: {'🔴 复杂' if is_complex else '🟢 简单'}")

        if is_complex:
            # 拆分测试
            split_parts = split_formula_by_equals(formula)
            print(f"   拆分为 {len(split_parts)} 部分:")
            for j, part in enumerate(split_parts):
                print(f"     {j+1}. {part}")

        # 简化测试
        simplified = simplify_formula(formula)
        if simplified != formula:
            print(f"   简化: {simplified}")

    print("\n" + "=" * 60)
    print("✅ 测试完成！")


if __name__ == "__main__":
    test_enhanced_processing()
