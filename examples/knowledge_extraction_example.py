"""
知识点提取服务集成示例

展示如何在作业批改和学习问答中使用知识点提取服务。
"""

import asyncio
from src.services.knowledge.extraction_service import KnowledgeExtractionService
from src.services.bailian_service import get_bailian_service


async def example_homework_extraction():
    """作业批改中的知识点提取示例"""
    # 初始化服务
    bailian_service = get_bailian_service()
    extraction_service = KnowledgeExtractionService(bailian_service)

    # 示例作业内容
    homework_content = """
    1. 已知二次函数 y = x² - 4x + 3，求其顶点坐标和对称轴。
    2. 求抛物线 y = 2x² - 8x + 6 的开口方向和最值。
    3. 已知圆的半径为 5cm，求圆的面积。
    """

    # 提取知识点
    knowledge_points = await extraction_service.extract_from_homework(
        content=homework_content, subject="math", grade="九年级"
    )

    print("=== 作业批改知识点提取 ===")
    for kp in knowledge_points:
        print(f"知识点: {kp.name}")
        print(f"  置信度: {kp.confidence:.2f}")
        print(f"  提取方法: {kp.method}")
        print(f"  匹配关键词: {kp.matched_keywords}")
        print(f"  相关知识点: {kp.related}")
        print()


async def example_question_extraction():
    """学习问答中的知识点提取示例"""
    # 初始化服务 (同步版本，不需要 AI)
    extraction_service = KnowledgeExtractionService()

    # 示例问题内容
    question_content = "老师，我不太理解被动语态的用法，什么时候用 be done 这种形式呢？"

    # 提取知识点 (仅规则)
    knowledge_points = extraction_service.extract_from_question(
        content=question_content, subject="english", grade="九年级"
    )

    print("=== 学习问答知识点提取 ===")
    for kp in knowledge_points:
        print(f"知识点: {kp.name}")
        print(f"  置信度: {kp.confidence:.2f}")
        print(f"  匹配关键词: {kp.matched_keywords}")
        print()


async def main():
    """运行示例"""
    print("知识点提取服务示例\n")

    # 示例 1: 作业批改
    await example_homework_extraction()

    print("\n" + "=" * 50 + "\n")

    # 示例 2: 学习问答
    await example_question_extraction()


if __name__ == "__main__":
    asyncio.run(main())
