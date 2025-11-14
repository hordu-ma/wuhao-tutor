#!/usr/bin/env python3
"""检查错题记录的实际数据"""
import asyncio
import sys
from uuid import UUID

# 添加项目路径
sys.path.insert(0, "/opt/wuhao-tutor")

from sqlalchemy import select

from src.core.database import get_async_session_context
from src.models.study import MistakeRecord


async def check_mistake(mistake_id: str):
    """检查指定错题的数据"""
    async with get_async_session_context() as db:
        stmt = select(MistakeRecord).where(MistakeRecord.id == UUID(mistake_id))
        result = await db.execute(stmt)
        mistake = result.scalar_one_or_none()

        if not mistake:
            print(f"错题 {mistake_id} 不存在")
            return

        print(f"=== 错题 {mistake_id} 数据 ===")
        print(f"标题: {mistake.title}")
        print(f"ocr_text: {mistake.ocr_text[:100] if mistake.ocr_text else 'NULL'}")
        print(f"ai_feedback类型: {type(mistake.ai_feedback)}")

        if mistake.ai_feedback:
            import json

            feedback = (
                json.loads(mistake.ai_feedback)
                if isinstance(mistake.ai_feedback, str)
                else mistake.ai_feedback
            )
            print(
                f"ai_feedback keys: {list(feedback.keys()) if isinstance(feedback, dict) else 'Not a dict'}"
            )
            print(
                f"ai_feedback内容: {json.dumps(feedback, ensure_ascii=False, indent=2)[:500]}"
            )
        else:
            print(f"ai_feedback: NULL")

        print(f"图片URLs: {mistake.image_urls}")
        print(f"来源: {mistake.source}")


if __name__ == "__main__":
    mistake_id = (
        sys.argv[1] if len(sys.argv) > 1 else "1b88243a-2313-46f2-8dad-d41cf001a39a"
    )
    asyncio.run(check_mistake(mistake_id))
