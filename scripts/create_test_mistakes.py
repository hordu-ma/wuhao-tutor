#!/usr/bin/env python3
"""
创建测试错题记录
用于测试AI分析功能
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from uuid import UUID

from src.core.database import AsyncSessionLocal
from src.models.user import User
from src.schemas.mistake import CreateMistakeRequest
from src.services.mistake_service import MistakeService


async def create_test_user(db):
    """创建测试用户"""
    test_user_id = "c8d57bff-2c76-411a-a770-15e9373d2329"

    # 检查用户是否已存在
    from sqlalchemy import select

    result = await db.execute(select(User).where(User.id == test_user_id))
    existing_user = result.scalar_one_or_none()

    if existing_user:
        print(f"✅ 测试用户已存在: {existing_user.name} ({existing_user.phone})")
        return test_user_id

    # 创建新用户
    new_user = User(
        id=test_user_id,
        phone="13800138000",
        password_hash="$2b$12$dummy_password_hash",  # 占位符
        name="张小明",
        role="student",
        grade_level="junior2",
        is_active=True,
        is_verified=True,
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    print(f"✅ 创建测试用户成功: {new_user.name} ({new_user.phone})")
    return test_user_id


# 测试错题数据
TEST_MISTAKES = [
    {
        "title": "一元二次方程求解",
        "subject": "math",
        "difficulty_level": 2,
        "question_content": "解方程：x² - 5x + 6 = 0",
        "student_answer": "x = 2",
        "correct_answer": "x₁ = 2, x₂ = 3",
        "explanation": "这是一个一元二次方程，可以用因式分解法求解：\n(x-2)(x-3)=0\n所以 x₁=2 或 x₂=3",
    },
    {
        "title": "自由落体运动",
        "subject": "physics",
        "difficulty_level": 3,
        "question_content": "一个物体从高度为20m的地方自由落下，忽略空气阻力，求物体落地时的速度。(g=10m/s²)",
        "student_answer": "v = 10 m/s",
        "correct_answer": "v = 20 m/s",
        "explanation": "根据自由落体运动公式：v² = 2gh\nv = √(2×10×20) = √400 = 20 m/s",
    },
    {
        "title": "一般现在时第三人称单数",
        "subject": "english",
        "difficulty_level": 1,
        "question_content": "Choose the correct word: He _____ to school every day.\nA. go  B. goes  C. going  D. gone",
        "student_answer": "A",
        "correct_answer": "B",
        "explanation": "主语He是第三人称单数，谓语动词要用第三人称单数形式goes。",
    },
    {
        "title": "汉字读音辨析",
        "subject": "chinese",
        "difficulty_level": 2,
        "question_content": "下列词语中，加点字的读音全都正确的一项是（  ）\nA. 惬(qiè)意  粗犷(guǎng)\nB. 着(zháo)急  憎(zēng)恨\nC. 角(jué)色  间(jiàn)隙\nD. 模(mó)样  勉强(qiǎng)",
        "student_answer": "A",
        "correct_answer": "B",
        "explanation": "A项中'犷'应读'kuàng'；C项中'角'在'角色'中读'jué'；D项中'强'在'勉强'中读'qiǎng'。只有B项全部正确。",
    },
]


async def create_test_mistakes():
    """创建测试错题"""

    print("=" * 60)
    print("创建测试错题数据")
    print("=" * 60)

    async with AsyncSessionLocal() as db:
        # 先创建测试用户
        print("\n📝 Step 1: 创建测试用户...")
        test_user_id = await create_test_user(db)

        service = MistakeService(db)

        print(f"\n👤 测试用户: 张小明 ({test_user_id})")
        print(f"\n📝 Step 2: 创建 {len(TEST_MISTAKES)} 条测试错题...\n")

        created_count = 0
        for i, mistake_data in enumerate(TEST_MISTAKES, 1):
            try:
                print(
                    f"{i}. 创建错题: {mistake_data['subject']} - {mistake_data['question_content'][:30]}..."
                )

                request = CreateMistakeRequest(**mistake_data)

                result = await service.create_mistake(
                    user_id=UUID(test_user_id), request=request
                )

                print(f"   ✅ 成功! ID: {result.id}")
                created_count += 1

            except Exception as e:
                print(f"   ❌ 失败: {e}")

        print("\n" + "=" * 60)
        print(f"✅ 完成! 成功创建 {created_count}/{len(TEST_MISTAKES)} 条错题")
        print("=" * 60)
        print("\n💡 下一步: 运行 python scripts/test_mistake_ai_analysis.py 测试AI分析")


def main():
    """主函数"""
    asyncio.run(create_test_mistakes())


if __name__ == "__main__":
    main()
