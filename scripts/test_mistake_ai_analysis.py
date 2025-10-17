#!/usr/bin/env python3
"""
测试错题AI分析功能
用于验证 analyze_mistake_with_ai 方法的实现

使用方法:
    python test_mistake_ai_analysis.py
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from uuid import UUID

from src.core.database import AsyncSessionLocal
from src.services.bailian_service import BailianService
from src.services.mistake_service import MistakeService


async def test_ai_analysis():
    """测试AI分析功能"""

    print("=" * 60)
    print("错题AI分析功能测试")
    print("=" * 60)

    # 测试用户ID（使用生产环境测试账号 - 张小明）
    # SQLite中user_id存储为字符串，所以查询时也使用字符串
    test_user_id_str = "c8d57bff-2c76-411a-a770-15e9373d2329"
    test_user_id = UUID(test_user_id_str)

    async with AsyncSessionLocal() as db:
        # 创建BailianService实例
        bailian_service = BailianService()
        service = MistakeService(db, bailian_service=bailian_service)

        # Step 1: 查询用户的错题列表
        print("\n📋 Step 1: 获取用户错题列表...")
        mistakes = await service.get_mistake_list(
            user_id=test_user_id, page=1, page_size=5, filters={}
        )

        if not mistakes.items:
            print("❌ 该用户没有错题记录")
            print("\n💡 提示: 请先创建一条测试错题，或使用有错题的账号")
            print("可以使用以下SQL创建测试错题：")
            print(
                """
INSERT INTO mistake_records (
    id, user_id, subject, difficulty_level,
    question_content, student_answer, correct_answer,
    explanation, created_at, updated_at
) VALUES (
    gen_random_uuid(),
    'c8d57bff-2c76-411a-a770-15e9373d2329',
    'math',
    2,
    '解方程：x² - 5x + 6 = 0',
    'x = 2',
    'x₁ = 2, x₂ = 3',
    '这是一个一元二次方程，可以用因式分解法：(x-2)(x-3)=0',
    NOW(),
    NOW()
);
            """
            )
            return

        print(f"✅ 找到 {mistakes.total} 条错题记录")

        # 选择第一条错题进行分析
        mistake = mistakes.items[0]
        print(f"\n📝 选择错题: {mistake.id}")
        print(f"   标题: {mistake.title}")
        print(f"   学科: {mistake.subject}")
        print(f"   难度: {mistake.difficulty_level}")

        # Step 2: 调用AI分析
        print(f"\n🤖 Step 2: 调用AI分析错题...")
        print("   (这可能需要几秒钟...)")

        try:
            result = await service.analyze_mistake_with_ai(
                mistake_id=(
                    UUID(mistake.id) if not isinstance(mistake.id, UUID) else mistake.id
                ),
                user_id=test_user_id,
            )

            print("\n✅ AI分析完成！")
            print("=" * 60)

            # Step 3: 显示分析结果
            print("\n📊 分析结果:")
            print("-" * 60)

            print(f"\n🎯 知识点 ({len(result.get('knowledge_points', []))} 个):")
            for i, kp in enumerate(result.get("knowledge_points", []), 1):
                print(f"   {i}. {kp}")

            print(f"\n🔍 错误原因:")
            print(f"   {result.get('error_reason', '无')}")

            print(f"\n💡 学习建议:")
            print(f"   {result.get('suggestions', '无')}")

            print("\n📈 统计信息:")
            print(f"   Token使用: {result.get('ai_tokens_used', 0)}")
            print(f"   分析耗时: {result.get('analysis_time', 0):.2f}秒")

            if result.get("is_fallback"):
                print("   ⚠️  注意: 使用了降级方案（AI调用失败）")

            print("\n" + "=" * 60)
            print("✅ 测试完成！")

        except Exception as e:
            print(f"\n❌ AI分析失败: {e}")
            import traceback

            traceback.print_exc()
            return


async def test_bailian_connection():
    """测试百炼服务连接"""
    print("\n🔧 测试百炼服务连接...")

    try:
        bailian = BailianService()

        # 简单测试
        response = await bailian.chat_completion(
            messages=[{"role": "user", "content": "你好，请回复'连接成功'"}],
            stream=False,
            max_tokens=50,
        )

        if response.success:
            print(f"✅ 百炼服务连接正常")
            print(f"   响应: {response.content[:50]}")
            print(f"   Token使用: {response.tokens_used}")
        else:
            print(f"❌ 百炼服务调用失败: {response.error_message}")

    except Exception as e:
        print(f"❌ 百炼服务连接失败: {e}")
        import traceback

        traceback.print_exc()


def main():
    """主函数"""
    print("\n🚀 开始测试...\n")

    # 测试百炼服务连接
    asyncio.run(test_bailian_connection())

    # 测试AI分析功能
    asyncio.run(test_ai_analysis())


if __name__ == "__main__":
    main()
