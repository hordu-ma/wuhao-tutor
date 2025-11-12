#!/usr/bin/env python3
"""
删除用户前清理相关数据脚本

用于删除用户的所有关联数据（会话、问题、回答等），然后安全删除用户。
这是一个临时方案，直到数据库模型添加 ondelete="CASCADE" 为止。

使用方法:
    python scripts/cleanup_user_data.py <user_id>

示例:
    python scripts/cleanup_user_data.py 9d19ad9f-3877-4de8-8cb6-408df548b89d
"""

import asyncio
import sys
from pathlib import Path

from sqlalchemy import delete, select

# 添加src到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.database import get_db_session
from src.models.homework import HomeworkAnswer, HomeworkQuestion
from src.models.knowledge import AIKnowledge
from src.models.learning import ChatAnswer, ChatMessage, ChatSession
from src.models.review import ReviewRecord
from src.models.study import KnowledgePoint, Mistake, MistakeAnalysis, MistakePhoto
from src.models.user import User


async def cleanup_user_data(user_id: str) -> None:
    """删除用户的所有关联数据"""
    print(f"\n🧹 清理用户数据")
    print(f"   用户ID: {user_id}")
    print(f"   此操作将删除该用户的所有相关数据\n")

    try:
        async with await get_db_session() as db:
            # 验证用户存在
            print("📍 验证用户存在...")
            user_result = await db.execute(select(User).where(User.id == user_id))
            user = user_result.scalar_one_or_none()
            if not user:
                print(f"❌ 用户不存在: {user_id}")
                return

            print(f"✅ 找到用户: {user.name} ({user.phone})")

            # 删除所有相关数据
            print(f"\n🗑️  删除相关数据...\n")

            # 1. ChatSession及相关数据
            chat_sessions = await db.execute(
                select(ChatSession).where(ChatSession.user_id == user_id)
            )
            sessions = chat_sessions.scalars().all()
            for session in sessions:
                # 删除该会话的所有消息
                await db.execute(
                    delete(ChatMessage).where(ChatMessage.session_id == session.id)
                )
                # 删除该会话的所有回答
                await db.execute(
                    delete(ChatAnswer).where(ChatAnswer.session_id == session.id)
                )

            session_count = len(sessions)
            if session_count > 0:
                await db.execute(
                    delete(ChatSession).where(ChatSession.user_id == user_id)
                )
                print(f"   ✓ 删除 {session_count} 个学习会话及其消息")

            # 2. Mistake及相关数据
            mistakes = await db.execute(
                select(Mistake).where(Mistake.user_id == user_id)
            )
            mistake_list = mistakes.scalars().all()
            for mistake in mistake_list:
                # 删除分析数据
                await db.execute(
                    delete(MistakeAnalysis).where(
                        MistakeAnalysis.mistake_id == mistake.id
                    )
                )
                # 删除知识点关联
                await db.execute(
                    delete(KnowledgePoint).where(
                        KnowledgePoint.mistake_id == mistake.id
                    )
                )
                # 删除照片
                await db.execute(
                    delete(MistakePhoto).where(MistakePhoto.mistake_id == mistake.id)
                )

            mistake_count = len(mistake_list)
            if mistake_count > 0:
                await db.execute(delete(Mistake).where(Mistake.user_id == user_id))
                print(f"   ✓ 删除 {mistake_count} 个错题记录")

            # 3. HomeworkQuestion及相关数据
            hw_questions = await db.execute(
                select(HomeworkQuestion).where(HomeworkQuestion.user_id == user_id)
            )
            hw_list = hw_questions.scalars().all()
            for hw in hw_list:
                # 删除作业回答
                await db.execute(
                    delete(HomeworkAnswer).where(HomeworkAnswer.question_id == hw.id)
                )

            hw_count = len(hw_list)
            if hw_count > 0:
                await db.execute(
                    delete(HomeworkQuestion).where(HomeworkQuestion.user_id == user_id)
                )
                print(f"   ✓ 删除 {hw_count} 个作业问题")

            # 4. AIKnowledge
            ai_count = await db.execute(
                delete(AIKnowledge).where(AIKnowledge.user_id == user_id)
            )
            if ai_count:
                print(f"   ✓ 删除 AI 知识记录")

            # 5. ReviewRecord
            review_count = await db.execute(
                delete(ReviewRecord).where(ReviewRecord.user_id == user_id)
            )
            if review_count:
                print(f"   ✓ 删除复习记录")

            # 提交所有删除操作
            print(f"\n💾 提交更改...")
            await db.commit()

            print(f"\n✅ 用户数据清理成功！")
            print(f"   现在可以安全删除用户了")

    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback

        traceback.print_exc()


async def main():
    """主函数"""
    if len(sys.argv) != 2:
        print("使用方法: python scripts/cleanup_user_data.py <user_id>")
        print(
            "示例:     python scripts/cleanup_user_data.py 9d19ad9f-3877-4de8-8cb6-408df548b89d"
        )
        sys.exit(1)

    user_id = sys.argv[1]
    await cleanup_user_data(user_id)


if __name__ == "__main__":
    asyncio.run(main())
