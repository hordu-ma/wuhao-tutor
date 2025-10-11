#!/usr/bin/env python3
"""
测试生产环境的修复
验证学习问答功能是否正常工作
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select

from src.core.database import AsyncSessionLocal
from src.models.learning import Question
from src.schemas.learning import QuestionResponse


async def test_question_serialization():
    """测试Question模型的序列化"""
    print("🔍 开始测试Question序列化...")

    async with AsyncSessionLocal() as session:
        # 查询第一个问题
        stmt = select(Question).limit(1)
        result = await session.execute(stmt)
        question = result.scalar_one_or_none()

        if not question:
            print("❌ 数据库中没有问题记录")
            return False

        print(f"✅ 找到问题记录: ID={question.id}")
        print(f"   - content: {question.content[:50]}...")
        print(f"   - image_urls (raw): {question.image_urls}")
        print(f"   - image_urls type: {type(question.image_urls)}")

        # 尝试序列化
        try:
            response = QuestionResponse.model_validate(question)
            print(f"✅ 序列化成功!")
            print(f"   - image_urls (parsed): {response.image_urls}")
            print(f"   - image_urls type: {type(response.image_urls)}")
            print(f"   - context_data: {response.context_data}")
            return True
        except Exception as e:
            print(f"❌ 序列化失败: {e}")
            import traceback

            traceback.print_exc()
            return False


async def main():
    """主函数"""
    print("=" * 60)
    print("生产环境修复验证")
    print("=" * 60)

    success = await test_question_serialization()

    print("=" * 60)
    if success:
        print("✅ 测试通过!")
        return 0
    else:
        print("❌ 测试失败!")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
