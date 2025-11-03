#!/usr/bin/env python3
"""
验证 AI 学情上下文功能

测试新的 AI 分析功能是否正确注入学情上下文
"""

import asyncio
import sys
from pathlib import Path
from uuid import UUID

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from src.core.config import settings
from src.core.logging import get_logger
from src.services.bailian_service import BailianService
from src.services.knowledge_graph_service import KnowledgeGraphService
from src.services.mistake_service import MistakeService

logger = get_logger(__name__)


async def test_ai_context():
    """测试 AI 学情上下文功能"""
    logger.info("🚀 开始验证 AI 学情上下文功能...")

    # 创建数据库连接
    engine = create_async_engine(
        str(settings.SQLALCHEMY_DATABASE_URI), echo=False, pool_pre_ping=True
    )

    async_session = async_sessionmaker(engine, expire_on_commit=False)

    try:
        async with async_session() as db:
            # 初始化服务
            bailian_service = BailianService()
            kg_service = KnowledgeGraphService(db, bailian_service)

            # 测试用例：使用一个已有错题的用户
            # 注意：这里需要替换为实际的用户ID和学科
            test_user_id = UUID(
                "39b9e27c-13fc-4e92-afcf-d16a64e84e27"
            )  # 替换为实际用户ID
            test_subject = "math"

            # 1. 测试构建学情上下文
            logger.info(f"\n{'='*60}")
            logger.info("📊 测试 1: 构建学情上下文")
            logger.info(f"{'='*60}")

            learning_context = await kg_service.build_learning_context(
                user_id=test_user_id, subject=test_subject
            )

            logger.info(f"\n【学情上下文内容】\n{learning_context}\n")

            # 检查是否包含关键信息
            if "初次使用系统" in learning_context:
                logger.warning("⚠️  用户尚无学情数据，跳过后续测试")
            else:
                # 检查是否包含必要字段
                required_keywords = ["学科学情概况", "已学习", "知识点"]
                for keyword in required_keywords:
                    if keyword in learning_context:
                        logger.info(f"✅ 学情上下文包含关键字: {keyword}")
                    else:
                        logger.warning(f"⚠️  学情上下文缺少关键字: {keyword}")

                # 检查是否包含分析建议
                if "分析建议" in learning_context or "薄弱知识点" in learning_context:
                    logger.info("✅ 学情上下文包含个性化分析")

            # 2. 测试 AI 分析（模拟）
            logger.info(f"\n{'='*60}")
            logger.info("🤖 测试 2: AI 分析带学情上下文")
            logger.info(f"{'='*60}")

            # 获取一个错题进行分析（如果有的话）
            from sqlalchemy import select

            from src.models.study import MistakeRecord

            stmt = (
                select(MistakeRecord)
                .where(MistakeRecord.user_id == str(test_user_id))
                .limit(1)
            )
            result = await db.execute(stmt)
            mistake = result.scalar_one_or_none()

            if mistake:
                mistake_service = MistakeService(db, bailian_service)

                logger.info(f"📝 使用错题ID: {mistake.id}")

                # 调用 AI 分析
                analysis_result = await mistake_service.analyze_mistake_with_ai(
                    mistake_id=UUID(str(mistake.id)), user_id=test_user_id
                )

                # 检查分析结果
                logger.info("\n【AI 分析结果】")
                logger.info(
                    f"知识点数量: {len(analysis_result.get('knowledge_points', []))}"
                )
                logger.info(
                    f"错误原因: {analysis_result.get('error_reason', '')[:100]}..."
                )
                logger.info(
                    f"学习建议: {analysis_result.get('suggestions', '')[:100]}..."
                )

                # 检查是否包含个性化洞察
                personalized_insight = analysis_result.get("personalized_insight", "")
                if personalized_insight:
                    logger.info(f"✅ 包含个性化洞察: {personalized_insight[:100]}...")
                else:
                    logger.info("ℹ️  无个性化洞察（可能是初次使用）")

                # 检查是否使用了学情上下文
                has_context = analysis_result.get("has_learning_context", False)
                if has_context:
                    logger.info("✅ AI 分析使用了学情上下文")
                else:
                    logger.warning("⚠️  AI 分析未使用学情上下文")

                # 显示知识点详情
                knowledge_points = analysis_result.get("knowledge_points", [])
                if knowledge_points:
                    logger.info("\n【提取的知识点】")
                    for idx, kp in enumerate(knowledge_points, 1):
                        if isinstance(kp, dict):
                            logger.info(
                                f"{idx}. {kp.get('name', '')} "
                                f"- 相关性: {kp.get('relevance', 0):.2f}, "
                                f"错误类型: {kp.get('error_type', '')}"
                            )
                        else:
                            logger.info(f"{idx}. {kp}")

            else:
                logger.warning("⚠️  用户没有错题记录，跳过 AI 分析测试")

            # 3. 验证完成
            logger.info(f"\n{'='*60}")
            logger.info("✨ AI 学情上下文功能验证完成！")
            logger.info(f"{'='*60}\n")

    except Exception as e:
        logger.error(f"❌ 验证失败: {e}", exc_info=True)
        raise
    finally:
        await engine.dispose()


def main():
    """主函数"""
    try:
        asyncio.run(test_ai_context())
        logger.info("✅ 验证成功！")
        sys.exit(0)
    except Exception as e:
        logger.error(f"💥 验证失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
