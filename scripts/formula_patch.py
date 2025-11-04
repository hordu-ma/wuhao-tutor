#!/usr/bin/env python3
"""
公式服务增强版补丁
解决复杂公式渲染失败问题
"""


# FormulaService 增强版本
class FormulaServicePatch:

    @staticmethod
    def should_split_complex_formula(content: str) -> bool:
        """检查是否应该拆分复杂公式"""
        # 检查复杂度指标
        complexity_score = 0

        # 长度检查
        if len(content) > 80:
            complexity_score += 2

        # 运算符数量
        times_count = content.count(r"\times")
        frac_count = content.count(r"\frac")
        eq_count = content.count("=")

        complexity_score += times_count * 0.5
        complexity_score += frac_count * 1
        complexity_score += max(0, eq_count - 1) * 1  # 多个等号

        return complexity_score > 3

    @staticmethod
    def split_formula_by_equals(content: str) -> list:
        """按等号拆分复杂公式"""
        if "=" not in content:
            return [content]

        # 简单按等号拆分
        parts = content.split("=")

        if len(parts) <= 2:
            return [content]  # 只有一个等号，不拆分

        # 构建拆分后的公式
        formulas = []
        for i in range(len(parts) - 1):
            if i == 0:
                # 第一个公式：A = B
                formula = f"{parts[i].strip()} = {parts[i+1].strip()}"
            else:
                # 后续公式：= B = C
                formula = f"= {parts[i+1].strip()}"
            formulas.append(formula)

        return formulas

    @staticmethod
    def add_fallback_handling():
        """添加降级处理"""
        return """
        # 在 _render_single_formula 方法中添加：
        
        try:
            # 原有渲染逻辑...
            image_url = await self._call_quicklatex_api(latex_code)
            if image_url:
                return image_url
        except Exception as e:
            logger.warning(f"公式渲染失败，尝试简化: {content} - {e}")
            
            # 降级1: 尝试简化公式
            simplified = self._simplify_formula(content)
            if simplified != content:
                try:
                    simplified_latex = self._prepare_latex_code(simplified, formula_type)
                    image_url = await self._call_quicklatex_api(simplified_latex)
                    if image_url:
                        return image_url
                except:
                    pass
            
            # 降级2: 返回None，让替换逻辑保留原文
            logger.warning(f"公式渲染完全失败，保留原文: {content}")
            return None
        """


def print_patch_code():
    """打印需要添加到FormulaService的代码"""

    patch_code = '''
# 在FormulaService类中添加以下方法：

def _should_split_complex_formula(self, content: str) -> bool:
    """检查是否应该拆分复杂公式"""
    complexity_score = 0
    
    # 长度检查
    if len(content) > 80:
        complexity_score += 2
        
    # 运算符数量
    times_count = content.count(r'\\times')
    frac_count = content.count(r'\\frac')
    eq_count = content.count('=')
    
    complexity_score += times_count * 0.5
    complexity_score += frac_count * 1
    complexity_score += max(0, eq_count - 1) * 1
    
    return complexity_score > 3

def _split_formula_by_equals(self, content: str) -> List[str]:
    """按等号拆分复杂公式"""
    if '=' not in content or not self._should_split_complex_formula(content):
        return [content]
    
    # 按等号拆分
    parts = [part.strip() for part in content.split('=')]
    
    if len(parts) <= 2:
        return [content]
    
    # 构建拆分后的公式
    formulas = []
    for i in range(len(parts) - 1):
        if i == 0:
            formula = f"{parts[i]} = {parts[i+1]}"
        else:
            formula = f"= {parts[i+1]}"
        formulas.append(formula)
    
    return formulas

def _simplify_formula(self, content: str) -> str:
    """简化公式"""
    # 替换可能有问题的符号
    simplified = content
    simplified = simplified.replace(r'\\times', r'\\cdot')  # 使用更简单的乘号
    simplified = simplified.replace('3.14', r'\\pi')        # 替换数字π
    
    return simplified

# 修改 _extract_formulas 方法，在提取后进行拆分：
# 在返回前添加：

expanded_formulas = []
for formula in formulas:
    if formula["type"] == "block":
        # 尝试拆分复杂的块级公式
        split_parts = self._split_formula_by_equals(formula["content"])
        if len(split_parts) > 1:
            logger.debug(f"拆分复杂公式为 {len(split_parts)} 部分")
            for i, part in enumerate(split_parts):
                new_formula = formula.copy()
                new_formula["content"] = part
                new_formula["split_index"] = i
                expanded_formulas.append(new_formula)
        else:
            expanded_formulas.append(formula)
    else:
        expanded_formulas.append(formula)

return expanded_formulas
'''

    print("🔧 FormulaService 增强补丁代码：")
    print("=" * 60)
    print(patch_code)
    print("=" * 60)


if __name__ == "__main__":
    print_patch_code()

    # 测试拆分逻辑
    test_formula = r"V = \frac{4}{3} \times \pi \times r^3 = \frac{4}{3} \times 3.14 \times 3^3 = \frac{4}{3} \times 3.14 \times 27"

    print(f"\n🧪 测试公式拆分：")
    print(f"原公式: {test_formula}")

    patch = FormulaServicePatch()
    should_split = patch.should_split_complex_formula(test_formula)
    print(f"需要拆分: {should_split}")

    if should_split:
        split_parts = patch.split_formula_by_equals(test_formula)
        print(f"拆分结果 ({len(split_parts)} 部分):")
        for i, part in enumerate(split_parts, 1):
            print(f"  {i}. {part}")

    print(
        f"\n✅ 这样可以将1个复杂公式拆分为{len(split_parts) if should_split else 1}个简单公式，提高成功率！"
    )
