#!/usr/bin/env python3
"""
公式渲染修复验证脚本
验证后端公式增强事件是否正确发送
"""

import asyncio
import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.services.learning_service import LearningService
from src.core.database import get_db
from src.models.user import UserModel
from src.schemas.learning import AskQuestionRequest
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def test_formula_enhancement():
    """测试公式增强功能"""

    logger.info("=" * 60)
    logger.info("开始测试公式渲染修复")
    logger.info("=" * 60)

    # 获取数据库会话
    async for db in get_db():
        try:
            # 获取测试用户 (假设存在ID为1的用户)
            from sqlalchemy import select

            stmt = select(UserModel).limit(1)
            result = await db.execute(stmt)
            user = result.scalar_one_or_none()

            if not user:
                logger.error("❌ 未找到测试用户，请先创建用户")
                return False

            user_id = str(user.id)
            logger.info(f"✅ 使用测试用户: {user.username} (ID: {user_id})")

            # 创建学习服务实例
            learning_service = LearningService(db)

            # 准备测试问题 (包含数学公式)
            test_questions = [
                {
                    "content": "球的体积公式是什么?",
                    "expected_formulas": ["$$", "frac", "pi"],
                },
                {
                    "content": "什么是二次方程求根公式?",
                    "expected_formulas": ["$$", "sqrt", "pm"],
                },
                {
                    "content": "圆的面积公式是 $A = \\pi r^2$，对吗?",
                    "expected_formulas": ["$", "pi", "r^2"],
                },
            ]

            success_count = 0
            total_count = len(test_questions)

            for idx, test_case in enumerate(test_questions, 1):
                logger.info(f"\n{'=' * 60}")
                logger.info(f"测试用例 {idx}/{total_count}: {test_case['content']}")
                logger.info(f"{'=' * 60}")

                # 创建请求
                request = AskQuestionRequest(
                    content=test_case["content"],
                    subject="math",
                    question_type="concept",
                    use_context=False,
                    include_history=False,
                )

                # 收集流式响应
                chunks = []
                has_formula_enhanced = False
                final_content = ""

                try:
                    async for chunk in learning_service.ask_question_stream(
                        user_id, request
                    ):
                        chunk_type = chunk.get("type", "unknown")
                        chunks.append(chunk)

                        logger.info(
                            f"📦 收到chunk: type={chunk_type}, "
                            f"content_len={len(chunk.get('content', ''))}"
                        )

                        # 检查是否收到 formula_enhanced 事件
                        if chunk_type == "formula_enhanced":
                            has_formula_enhanced = True
                            final_content = chunk.get("content", "")
                            logger.info(f"✅ 收到 formula_enhanced 事件!")
                            logger.info(f"   增强内容长度: {len(final_content)}")

                            # 检查是否包含公式图片标签
                            if '<img class="math-formula-' in final_content:
                                logger.info(f"✅ 内容包含公式图片标签")
                            else:
                                logger.warning(f"⚠️ 内容不包含公式图片标签")

                        # 累积内容
                        if chunk.get("content"):
                            if not final_content:  # 如果还没有增强内容
                                final_content += chunk.get("content", "")

                    # 验证结果
                    logger.info(f"\n{'=' * 60}")
                    logger.info("验证结果:")
                    logger.info(f"{'=' * 60}")
                    logger.info(f"总chunk数: {len(chunks)}")
                    logger.info(f"收到formula_enhanced事件: {has_formula_enhanced}")
                    logger.info(f"最终内容长度: {len(final_content)}")

                    # 检查公式是否被渲染
                    has_formula_img = '<img class="math-formula-' in final_content
                    has_latex_raw = "$$" in final_content or "$" in final_content

                    logger.info(f"包含公式图片标签: {has_formula_img}")
                    logger.info(f"包含原始LaTeX: {has_latex_raw}")

                    if has_formula_enhanced and has_formula_img:
                        logger.info("✅ 测试通过: 公式已正确增强并包含图片标签")
                        success_count += 1
                    elif not has_formula_enhanced:
                        logger.warning("⚠️ 警告: 未收到formula_enhanced事件")
                        if has_formula_img:
                            logger.info(
                                "   但内容中包含公式图片标签 (可能在其他事件中发送)"
                            )
                            success_count += 1
                    else:
                        logger.error("❌ 测试失败: 未找到公式图片标签")

                    # 显示部分内容预览
                    preview = final_content[:200] if final_content else "(空)"
                    logger.info(f"\n内容预览 (前200字符):")
                    logger.info(f"{preview}...")

                except Exception as e:
                    logger.error(f"❌ 测试失败: {e}", exc_info=True)

            # 总结
            logger.info(f"\n{'=' * 60}")
            logger.info("测试总结")
            logger.info(f"{'=' * 60}")
            logger.info(f"总测试用例: {total_count}")
            logger.info(f"成功: {success_count}")
            logger.info(f"失败: {total_count - success_count}")
            logger.info(f"成功率: {success_count/total_count*100:.1f}%")

            if success_count == total_count:
                logger.info("\n✅ 所有测试通过! 公式渲染修复成功!")
                return True
            else:
                logger.warning(f"\n⚠️ 部分测试失败，请检查日志")
                return False

        except Exception as e:
            logger.error(f"❌ 测试过程出错: {e}", exc_info=True)
            return False

        finally:
            await db.close()


async def test_formula_service():
    """单独测试公式服务"""
    logger.info("\n" + "=" * 60)
    logger.info("测试公式服务")
    logger.info("=" * 60)

    from src.services.formula_service import get_formula_service

    formula_service = get_formula_service()

    # 测试公式处理
    test_texts = [
        "圆的面积公式是 $A = \\pi r^2$",
        "球的体积公式: $$V = \\frac{4}{3} \\pi r^3$$",
        "二次方程: $x = \\frac{-b \\pm \\sqrt{b^2 - 4ac}}{2a}$",
    ]

    for idx, text in enumerate(test_texts, 1):
        logger.info(f"\n测试 {idx}: {text[:50]}...")

        try:
            result = await formula_service.process_text_with_formulas(text)

            has_img = '<img class="math-formula-' in result
            logger.info(f"原文长度: {len(text)}")
            logger.info(f"结果长度: {len(result)}")
            logger.info(f"包含图片标签: {has_img}")

            if has_img:
                logger.info("✅ 公式处理成功")
            else:
                logger.warning("⚠️ 未找到公式图片标签")

            # 显示结果预览
            logger.info(f"结果预览: {result[:150]}...")

        except Exception as e:
            logger.error(f"❌ 处理失败: {e}", exc_info=True)


async def main():
    """主函数"""
    logger.info("🚀 公式渲染修复验证脚本")
    logger.info("=" * 60)

    # 测试公式服务
    await test_formula_service()

    # 等待用户确认
    logger.info("\n" + "=" * 60)
    logger.info("准备测试完整流程 (需要数据库)")
    logger.info("=" * 60)

    # 测试完整流程
    success = await test_formula_enhancement()

    if success:
        logger.info("\n🎉 所有测试通过!")
        sys.exit(0)
    else:
        logger.warning("\n⚠️ 部分测试失败")
        sys.exit(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\n⏹️ 测试被用户中断")
        sys.exit(0)
    except Exception as e:
        logger.error(f"\n❌ 测试失败: {e}", exc_info=True)
        sys.exit(1)
