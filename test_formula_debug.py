#!/usr/bin/env python3
"""
测试数学公式处理流程
"""

import asyncio
import logging
import sys
from pathlib import Path

# 添加src到路径
sys.path.append(str(Path(__file__).parent / "src"))

from src.services.bailian_service import BailianService

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_formula_processing():
    """测试公式处理功能"""

    # 初始化服务
    bailian_service = BailianService()

    # 测试文本 - 包含LaTeX公式
    test_text = """球的体积公式是：

$$V = \\frac{4}{3}\\pi r^3$$

其中：
- $V$ 表示体积
- $r$ 表示半径
- $\\pi$ 是圆周率，约等于 3.14"""

    print("=== 原始文本 ===")
    print(test_text)
    print("\n" + "=" * 50 + "\n")

    # 检查是否识别为需要公式处理
    should_process = bailian_service._should_process_formulas(test_text)
    print(f"是否需要处理公式: {should_process}")

    if should_process:
        # 处理公式
        processed_text = await bailian_service._process_math_formulas(test_text)
        print("=== 处理后文本 ===")
        print(processed_text)
    else:
        print("跳过公式处理")


if __name__ == "__main__":
    asyncio.run(test_formula_processing())
