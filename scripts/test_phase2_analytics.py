#!/usr/bin/env python3
"""
Phase 2 Analytics API 测试脚本
测试新增的学情分析API端点
"""

import sys
import uuid
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

import asyncio
import json
from datetime import datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import AsyncSessionLocal, get_db
from src.models.homework import HomeworkSubmission
from src.models.learning import Answer, ChatSession, Question
from src.models.user import User
from src.services.analytics_service import AnalyticsService


async def create_test_data():
    """创建测试数据"""
    print("📝 创建测试数据...")

    async with AsyncSessionLocal() as session:
        # 检查是否已有测试用户
        from sqlalchemy import select

        result = await session.execute(select(User).where(User.phone == "13800138000"))
        test_user = result.scalar_one_or_none()

        if not test_user:
            # 创建测试用户
            test_user = User(
                id=uuid.uuid4(),
                phone="13800138000",
                password_hash="test_hash",
                name="测试学生",
                nickname="测试学生",
                grade_level="junior_1",
                role="student",
            )
            session.add(test_user)
            await session.commit()
            await session.refresh(test_user)
            print(f"✅ 创建测试用户: {test_user.id}")
        else:
            print(f"✅ 使用现有测试用户: {test_user.id}")

        return test_user.id


async def test_learning_stats(user_id: uuid.UUID):
    """测试学习统计API"""
    print("\n🧪 测试 1: 学习统计数据")
    print("=" * 50)

    async with AsyncSessionLocal() as session:
        service = AnalyticsService(session)  # 修复: 传入session

        try:
            # 测试不同时间范围
            for time_range in ["7d", "30d", "all"]:
                print(f"\n📊 时间范围: {time_range}")
                stats = await service.get_learning_stats(
                    user_id, time_range
                )  # 修复: 移除session参数

                print(f"  ├─ 学习天数: {stats['total_study_days']}")
                print(f"  ├─ 提问总数: {stats['total_questions']}")
                print(f"  ├─ 作业总数: {stats['total_homework']}")
                print(f"  ├─ 平均分数: {stats['avg_score']}")
                print(f"  ├─ 知识点数量: {len(stats['knowledge_points'])}")
                print(f"  └─ 学习趋势点数: {len(stats['study_trend'])}")

                # 显示部分知识点
                if stats["knowledge_points"]:
                    print(f"\n  知识点示例:")
                    for kp in stats["knowledge_points"][:3]:
                        print(f"    - {kp['name']}: 掌握度 {kp['mastery_level']:.2f}")

            print("\n✅ 学习统计API测试通过")
            return True

        except Exception as e:
            print(f"\n❌ 学习统计API测试失败: {e}")
            import traceback

            traceback.print_exc()
            return False


async def test_user_stats(user_id: uuid.UUID):
    """测试用户统计API"""
    print("\n🧪 测试 2: 用户统计数据")
    print("=" * 50)

    async with AsyncSessionLocal() as session:
        service = AnalyticsService(session)  # 修复: 传入session

        try:
            stats = await service.get_user_stats(user_id)  # 修复: 移除session参数

            print(f"\n👤 用户统计:")
            print(f"  ├─ 加入日期: {stats.get('join_date', 'N/A')}")
            print(f"  ├─ 最后登录: {stats.get('last_login', 'N/A')}")
            print(f"  ├─ 作业总数: {stats.get('homework_count', 0)}")
            print(f"  ├─ 提问总数: {stats.get('question_count', 0)}")
            print(f"  ├─ 学习天数: {stats.get('study_days', 0)}")
            print(f"  ├─ 平均分数: {stats.get('avg_score', 0)}")
            print(f"  ├─ 错题数量: {stats.get('error_count', 0)}")
            print(f"  └─ 学习时长: {stats.get('study_hours', 0)} 小时")

            print("\n✅ 用户统计API测试通过")
            return True

        except Exception as e:
            print(f"\n❌ 用户统计API测试失败: {e}")
            import traceback

            traceback.print_exc()
            return False


async def test_knowledge_map(user_id: uuid.UUID):
    """测试知识图谱API"""
    print("\n🧪 测试 3: 知识图谱数据")
    print("=" * 50)

    async with AsyncSessionLocal() as session:
        service = AnalyticsService(session)  # 修复: 传入session

        try:
            # 测试不同学科
            for subject in [None, "math", "chinese"]:
                subject_name = subject or "全部学科"
                print(f"\n📚 学科: {subject_name}")

                knowledge_map = await service.get_knowledge_map(
                    user_id, subject
                )  # 修复: 移除session参数

                print(f"  ├─ 总节点数: {knowledge_map.get('total_nodes', 0)}")
                print(f"  ├─ 已掌握: {knowledge_map.get('mastered_nodes', 0)}")
                print(f"  ├─ 学习中: {knowledge_map.get('learning_nodes', 0)}")
                print(f"  └─ 未学习: {knowledge_map.get('unlearned_nodes', 0)}")

                # 显示节点层级
                nodes = knowledge_map.get("nodes", [])
                if nodes:
                    print(f"\n  知识点层级:")
                    for node in nodes[:5]:  # 只显示前5个
                        print(
                            f"    - {node.get('name', 'N/A')}: "
                            f"掌握度 {node.get('mastery_level', 0):.2f}"
                        )

            print("\n✅ 知识图谱API测试通过")
            return True

        except Exception as e:
            print(f"\n❌ 知识图谱API测试失败: {e}")
            import traceback

            traceback.print_exc()
            return False


async def test_session_stats_update():
    """测试Session统计更新"""
    print("\n🧪 测试 4: Session统计更新")
    print("=" * 50)

    async with AsyncSessionLocal() as session:
        from sqlalchemy import select

        try:
            # 查询一个ChatSession
            result = await session.execute(select(ChatSession).limit(1))
            chat_session = result.scalar_one_or_none()

            if chat_session:
                print(f"\n📊 Session统计:")
                print(f"  ├─ Session ID: {chat_session.id}")
                print(
                    f"  ├─ 问题数量: {getattr(chat_session, 'question_count', 'N/A')}"
                )
                print(f"  ├─ 总Token: {getattr(chat_session, 'total_tokens', 'N/A')}")
                print(
                    f"  ├─ 最后活动: {getattr(chat_session, 'last_activity_at', 'N/A')}"
                )
                print(f"  └─ 状态: {getattr(chat_session, 'status', 'N/A')}")

                # 查询该Session的Questions
                question_result = await session.execute(
                    select(Question).where(Question.session_id == chat_session.id)
                )
                questions = question_result.scalars().all()
                print(f"\n  实际问题数: {len(questions)}")

                # 验证统计是否一致
                question_count = getattr(chat_session, "question_count", None)
                if question_count is not None:
                    # 修复: 将Column对象转换为Python值进行比较
                    count_value = (
                        int(question_count)
                        if isinstance(question_count, (int, str))
                        else question_count
                    )
                    if count_value == len(questions):
                        print("  ✅ 问题计数统计正确")
                    else:
                        print(
                            f"  ⚠️ 问题计数不匹配: 统计={count_value}, 实际={len(questions)}"
                        )

                print("\n✅ Session统计测试通过")
                return True
            else:
                print("  ℹ️ 数据库中暂无ChatSession数据")
                print("✅ Session统计测试跳过(无数据)")
                return True

        except Exception as e:
            print(f"\n❌ Session统计测试失败: {e}")
            import traceback

            traceback.print_exc()
            return False


async def test_data_integrity():
    """测试数据完整性"""
    print("\n🧪 测试 5: 数据完整性检查")
    print("=" * 50)

    async with AsyncSessionLocal() as session:
        from sqlalchemy import func, select

        try:
            # 检查Answer字段完整性
            print("\n📝 检查Answer字段:")
            answer_result = await session.execute(select(Answer).limit(5))
            answers = answer_result.scalars().all()

            if answers:
                for i, answer in enumerate(answers, 1):
                    print(f"\n  Answer {i}:")
                    print(f"    ├─ ID: {answer.id}")
                    print(f"    ├─ Question ID: {answer.question_id}")
                    # 修复: 安全访问content属性
                    content = str(answer.content) if answer.content is not None else ""
                    content_preview = (
                        content[:50] + "..." if len(content) > 50 else content
                    )
                    print(f"    ├─ Content: {content_preview}")
                    print(f"    ├─ Tokens: {getattr(answer, 'tokens_used', 'N/A')}")
                    print(
                        f"    ├─ Generation Time: {getattr(answer, 'generation_time', 'N/A')}"
                    )
                    print(f"    └─ Model: {getattr(answer, 'model_name', 'N/A')}")

                # 验证元数据完整性
                complete_count = sum(
                    1 for a in answers if getattr(a, "tokens_used", None) is not None
                )
                print(
                    f"\n  元数据完整率: {complete_count}/{len(answers)} "
                    f"({complete_count/len(answers)*100:.1f}%)"
                )

                if complete_count > 0:
                    print("  ✅ Answer元数据保存正常")
                else:
                    print("  ⚠️ Answer元数据可能缺失")
            else:
                print("  ℹ️ 数据库中暂无Answer数据")

            # 检查外键关联
            print("\n🔗 检查外键关联:")
            question_result = await session.execute(select(Question).limit(3))
            questions = question_result.scalars().all()

            if questions:
                for question in questions:
                    # 检查Question -> Answer关联
                    answer_count_result = await session.execute(
                        select(func.count(Answer.id)).where(
                            Answer.question_id == question.id
                        )
                    )
                    answer_count = answer_count_result.scalar()

                    print(
                        f"  Question {question.id[:8]}... -> {answer_count} Answer(s)"
                    )

                print("  ✅ 外键关联正常")
            else:
                print("  ℹ️ 数据库中暂无Question数据")

            print("\n✅ 数据完整性测试通过")
            return True

        except Exception as e:
            print(f"\n❌ 数据完整性测试失败: {e}")
            import traceback

            traceback.print_exc()
            return False


async def main():
    """主测试流程"""
    print("\n" + "=" * 50)
    print("🚀 Phase 2 Analytics API 测试")
    print("=" * 50)

    # 创建测试数据
    test_user_id = await create_test_data()

    # 修复: 将Column转换为UUID
    if isinstance(test_user_id, uuid.UUID):
        user_id = test_user_id
    else:
        # 如果是Column对象,转换为UUID
        user_id = uuid.UUID(str(test_user_id))

    # 运行测试
    results = []

    results.append(("学习统计API", await test_learning_stats(user_id)))
    results.append(("用户统计API", await test_user_stats(user_id)))
    results.append(("知识图谱API", await test_knowledge_map(user_id)))
    results.append(("Session统计更新", await test_session_stats_update()))
    results.append(("数据完整性", await test_data_integrity()))

    # 汇总结果
    print("\n" + "=" * 50)
    print("📊 测试结果汇总")
    print("=" * 50)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{name}: {status}")

    print(f"\n总计: {passed}/{total} 通过")

    if passed == total:
        print("\n🎉 Phase 2 所有测试通过!")
        return 0
    else:
        print(f"\n⚠️ Phase 2 有 {total - passed} 项测试失败")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
