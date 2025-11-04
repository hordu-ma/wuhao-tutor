#!/usr/bin/env python3
"""
增强版公式处理诊断脚本
专门诊断部分公式显示失败的问题
"""

import asyncio
import logging
import re
from typing import Any, Dict, List


# 模拟 FormulaService 的关键逻辑
class FormulaDebugger:

    def __init__(self):
        self.default_formula_size = "\\large"

    def extract_formulas(self, text: str) -> List[Dict[str, Any]]:
        """提取公式的调试版本"""
        formulas = []

        print("🔍 开始提取公式...")
        print(f"📝 文本长度: {len(text)} 字符")

        # 1. 匹配块级公式 $$...$$
        print("\n1️⃣ 检查块级公式 $$...$$")
        block_pattern = r"\$\$\s*(.*?)\s*\$\$"
        block_matches = list(re.finditer(block_pattern, text, re.DOTALL))
        print(f"找到 {len(block_matches)} 个块级公式")

        for i, match in enumerate(block_matches):
            formula_info = {
                "type": "block",
                "content": match.group(1).strip(),
                "full_match": match.group(0),
                "start": match.start(),
                "end": match.end(),
            }
            formulas.append(formula_info)
            print(f"  块级 {i+1}: {formula_info['content'][:50]}...")

        # 2. 匹配行内公式 $...$
        print("\n2️⃣ 检查行内公式 $...$")
        inline_pattern = r"(?<!\$)\$([^$\n]+)\$(?!\$)"
        inline_matches = list(re.finditer(inline_pattern, text))
        print(f"找到 {len(inline_matches)} 个候选行内公式")

        for i, match in enumerate(inline_matches):
            # 检查是否在块级公式内
            is_inside_block = any(
                block["start"] <= match.start() < block["end"]
                for block in formulas
                if block["type"] == "block"
            )

            if not is_inside_block:
                formula_info = {
                    "type": "inline",
                    "content": match.group(1).strip(),
                    "full_match": match.group(0),
                    "start": match.start(),
                    "end": match.end(),
                }
                formulas.append(formula_info)
                print(
                    f"  行内 {len([f for f in formulas if f['type'] == 'inline'])}: {formula_info['content'][:30]}..."
                )
            else:
                print(f"  跳过 {i+1} (在块级公式内): {match.group(1)[:30]}...")

        # 按位置排序
        formulas.sort(key=lambda x: x["start"])

        print(f"\n✅ 总共提取到 {len(formulas)} 个公式")
        return formulas

    def simulate_quicklatex_call(self, latex_code: str) -> bool:
        """模拟QuickLaTeX调用，检查哪些公式可能失败"""

        # 检查可能导致失败的模式
        failure_patterns = [
            (r"\\text\{[^}]*\}", "\\text{} 标签可能不支持"),
            (r"\\approx", "\\approx 符号可能有问题"),
            (r"\\cdot", "\\cdot 符号可能有问题"),
            (r"\\times", "\\times 符号检查"),
            (r"\\frac\{[^}]*\}\{[^}]*\}", "分数表达式检查"),
            (r"\^[0-9]+", "上标检查"),
            (r"_{[^}]*}", "下标检查"),
        ]

        issues = []
        for pattern, description in failure_patterns:
            if re.search(pattern, latex_code):
                issues.append(description)

        # 检查长度
        if len(latex_code) > 200:
            issues.append("公式过长，可能超时")

        # 检查特殊字符
        if "\\newline" in latex_code or "\\\\n" in latex_code:
            issues.append("包含换行符，可能导致渲染失败")

        success_probability = max(0.1, 1.0 - len(issues) * 0.2)

        return success_probability > 0.5, issues


def test_formula_extraction():
    """测试公式提取"""

    # 从截图中推断的测试文本
    test_text = """
球体积公式是：

$$ V = \\frac{4}{3} \\pi r^3 $$

其中：
- $ V $ 表示球的体积；
- $ r $ 表示球的半径；
- $ \\pi $ 是圆周率，约等于3.14；

解题步骤示范：

假设有一个球的半径是 3 厘米，那么它的体积是多少？

解：

$$ V = \\frac{4}{3} \\times \\pi \\times r^3 = \\frac{4}{3} \\times 3.14 \\times 3^3 = \\frac{4}{3} \\times 3.14 \\times 27 $$

先算 $ 3^3 = 27 $

然后 $ \\frac{4}{3} \\times 27 = 36 $

配后：$ 36 \\times 3.14 = 113.04 $ 立方厘米。

所以这个球的体积是 113.04 立方厘米。
"""

    debugger = FormulaDebugger()

    print("=" * 60)
    print("🧪 公式提取和渲染诊断")
    print("=" * 60)

    # 提取公式
    formulas = debugger.extract_formulas(test_text)

    print("\n" + "=" * 60)
    print("🎯 渲染成功率预测")
    print("=" * 60)

    success_count = 0
    for i, formula in enumerate(formulas, 1):
        print(f"\n📐 公式 {i} ({formula['type']}):")
        print(f"   内容: {formula['content']}")

        # 准备LaTeX代码
        if formula["type"] == "block":
            latex_code = f"\\large {formula['content']}"
        else:
            latex_code = f"\\large {formula['content']}"

        # 模拟渲染
        success, issues = debugger.simulate_quicklatex_call(latex_code)

        if success:
            print(f"   ✅ 预期成功")
            success_count += 1
        else:
            print(f"   ❌ 预期失败")
            for issue in issues:
                print(f"      - {issue}")

    print(
        f"\n📊 预期成功率: {success_count}/{len(formulas)} ({success_count/len(formulas)*100:.1f}%)"
    )

    # 给出建议
    print("\n" + "=" * 60)
    print("💡 优化建议")
    print("=" * 60)

    suggestions = [
        "1. 增加公式渲染的错误重试机制",
        "2. 对失败的公式使用降级显示（显示原始LaTeX）",
        "3. 添加公式复杂度检测，拆分复杂公式",
        "4. 增加QuickLaTeX API的超时和并发限制",
        "5. 添加详细的渲染日志，便于调试",
    ]

    for suggestion in suggestions:
        print(suggestion)


if __name__ == "__main__":
    test_formula_extraction()
