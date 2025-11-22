"""
复习计划服务
"""

import json
import logging
import re
from datetime import datetime, timedelta
from typing import Any, Dict, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions import ServiceError
from src.models.revision_plan import RevisionPlan
from src.repositories.revision_plan_repository import RevisionPlanRepository
from src.services.bailian_service import BailianService, ChatMessage, MessageRole
from src.services.file_service import FileService
from src.services.mistake_service import MistakeService
from src.services.pdf_generator_service import PDFGeneratorService

logger = logging.getLogger(__name__)


class RevisionPlanService:
    """复习计划生成服务"""

    def __init__(
        self,
        db: AsyncSession,
        mistake_service: MistakeService,
        bailian_service: BailianService,
        file_service: FileService,
    ):
        self.db = db
        self.mistake_service = mistake_service
        self.bailian_service = bailian_service
        self.file_service = file_service
        self.revision_repo = RevisionPlanRepository(db)
        self.pdf_generator = PDFGeneratorService()

    async def generate_revision_plan(
        self,
        user_id: UUID,
        cycle_type: str = "7days",  # "7days" | "14days" | "30days"
        days_lookback: int = 30,  # 回顾近N天的错题
        force_regenerate: bool = False,  # 强制重新生成
        title: Optional[str] = None,  # 用户自定义标题
    ) -> RevisionPlan:
        """
        生成个性化复习计划
        """
        # 1. 缓存检查
        if not force_regenerate:
            cached_plan = await self._get_cached_plan(user_id, cycle_type)
            if cached_plan:
                logger.info(f"使用缓存复习计划: {cached_plan.id}")
                return cached_plan

        # 2. 获取错题数据
        mistakes_data = await self.mistake_service.get_mistakes_for_revision(
            user_id=user_id,
            days_lookback=days_lookback,
        )

        if not mistakes_data["items"]:
            raise ServiceError("没有错题数据，无法生成复习计划")

        # 3. 生成 Markdown 文本
        markdown_content = await self.mistake_service.generate_markdown_export(
            user_id=user_id,
            mistakes_data=mistakes_data,
        )

        # 4. 调用大模型
        plan_json = await self._call_ai_for_plan(
            user_id=user_id,
            markdown_content=markdown_content,
            cycle_type=cycle_type,
            mistakes_stats=mistakes_data["statistics"],
        )

        # 5. 生成 PDF
        pdf_info = await self._generate_pdf(
            user_id=user_id,
            plan_json=plan_json,
            markdown_content=markdown_content,
        )

        # 6. 保存到数据库
        final_title = title if title else plan_json["title"]
        revision_plan = await self.revision_repo.create(
            {
                "user_id": str(user_id),
                "title": final_title,
                "description": plan_json.get("description", ""),
                "cycle_type": cycle_type,
                "status": "published",
                "mistake_count": len(mistakes_data["items"]),
                "knowledge_points": mistakes_data["knowledge_points"],
                "date_range": mistakes_data["date_range"],
                "plan_content": plan_json,
                "pdf_url": pdf_info["url"],
                "pdf_size": pdf_info["size"],
                "expired_at": self._calculate_expiry(cycle_type),
            }
        )

        logger.info(f"✅ 复习计划生成成功: {revision_plan.id}")
        return revision_plan

    async def _get_cached_plan(
        self,
        user_id: UUID,
        cycle_type: str,
    ) -> Optional[RevisionPlan]:
        """检查是否有有效的缓存计划"""
        # 简单实现：查询最新的计划，如果未过期且类型匹配，则返回
        plans, _ = await self.revision_repo.find_by_user(
            user_id=user_id,
            page=1,
            page_size=1,
        )
        if plans:
            latest_plan = plans[0]
            if (
                latest_plan.cycle_type == cycle_type
                and latest_plan.expired_at
                and latest_plan.expired_at > datetime.utcnow()
            ):
                return latest_plan
        return None

    async def _call_ai_for_plan(
        self,
        user_id: UUID,
        markdown_content: str,
        cycle_type: str,
        mistakes_stats: Dict[str, Any],
    ) -> Dict[str, Any]:
        """调用百炼大模型生成复习计划"""

        messages = [
            ChatMessage(
                role=MessageRole.SYSTEM, content=self._build_system_prompt(cycle_type)
            ),
            ChatMessage(
                role=MessageRole.USER,
                content=f"""
请根据以下学生的错题数据生成一份详尽的{cycle_type}复习计划。

【错题统计】
{json.dumps(mistakes_stats, ensure_ascii=False)}

【错题详情】
{markdown_content}

【要求】
1. 制定明确的学习目标
2. 分解为每日任务（含时间估计）
3. 指定复习重点和方法
4. 提供自测题和评估标准
5. 考虑学生的学习风格和薄弱点

请以 JSON 格式返回，包含以下字段：
- title: 计划标题
- description: 简短描述
- overview: 概述
- statistics: 数据统计
- daily_tasks: 每日任务数组
- review_focus: 重点复习内容
- assessment: 评估标准
- tips: 学习建议
""",
            ),
        ]

        response = await self.bailian_service.chat_completion(
            messages=messages,
        )

        # 解析并验证 JSON
        plan_json = self._parse_json_response(response.content)
        return plan_json

    async def _generate_pdf(
        self,
        user_id: UUID,
        plan_json: Dict[str, Any],
        markdown_content: str,
    ) -> Dict[str, Any]:
        """生成 PDF 文件并上传至 OSS"""

        # 调用 PDFGeneratorService
        pdf_buffer = await self.pdf_generator.generate(
            title=plan_json["title"],
            content=plan_json,
            metadata={
                "user_id": str(user_id),
                "generated_at": datetime.utcnow().isoformat(),
                "markdown_source": markdown_content,
            },
        )

        # 上传到阿里云 OSS
        # 路径格式: revision-plans/{user_id}/{YYYYMMDD_HHMMSS}.pdf
        file_key = f"revision-plans/{user_id}/{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.pdf"

        # 使用 FileService
        url = await self.file_service.save_file(
            file_buffer=pdf_buffer,
            file_key=file_key,
            content_type="application/pdf",
        )

        return {
            "url": url,
            "size": len(pdf_buffer.getvalue()),
        }

    def _build_system_prompt(self, cycle_type: str) -> str:
        """构建系统提示词"""
        return f"""
你是一位经验丰富的学习规划师。你的任务是根据学生的错题数据生成个性化的{cycle_type}复习计划。

## 规划原则
1. **数据驱动**：基于错题频率、错误类型决定复习重点
2. **循序渐进**：从基础概念到综合应用
3. **时间合理**：每日任务时间控制在 1-3 小时
4. **可执行性**：具体明确，包含具体方法和资源
5. **反馈机制**：包含自测和评估标准

## 复习计划结构
- 周期：{cycle_type}
- 目标：提升错题涉及知识点的掌握度
- 评估：包含前期、中期、后期评估

## 注意事项
- 考虑学生的认知水平和学习进度
- 避免过度安排，留出缓冲时间
- 每日任务应包含具体的学习方法（不只是题目）
"""

    def _calculate_expiry(self, cycle_type: str) -> datetime:
        """计算计划过期时间"""
        days_map = {
            "7days": 7,
            "14days": 14,
            "30days": 30,
        }
        days = days_map.get(cycle_type, 7)
        return datetime.utcnow() + timedelta(days=days)

    async def get_revision_plan(
        self,
        user_id: UUID,
        plan_id: UUID,
    ) -> RevisionPlan:
        """获取复习计划详情"""
        logger.info(f"🔍 查询复习计划: plan_id={plan_id}, user_id={user_id}")
        plan = await self.revision_repo.get_by_id(str(plan_id))

        if not plan:
            logger.warning(f"❌ 计划不存在: plan_id={plan_id}")
            raise ServiceError("计划不存在或无权访问")
        
        logger.info(f"📌 找到计划: plan.id={plan.id}, plan.user_id={plan.user_id}, type(plan.user_id)={type(plan.user_id)}")
        logger.info(f"📌 用户校验: user_id={user_id}, str(user_id)={str(user_id)}, type(user_id)={type(user_id)}")
        
        if plan.user_id != str(user_id):
            logger.warning(f"❌ 权限拒绝: plan.user_id={plan.user_id} != str(user_id)={str(user_id)}")
            raise ServiceError("计划不存在或无权访问")

        # 更新访问计数
        plan.view_count += 1
        await self.revision_repo.update(str(plan_id), {"view_count": plan.view_count})

        return plan

    async def list_revision_plans(
        self,
        user_id: UUID,
        limit: int = 10,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """获取复习计划列表"""
        plans, total = await self.revision_repo.find_by_user(
            user_id=user_id, page=offset // limit + 1, page_size=limit
        )

        return {
            "total": total,
            "items": plans,
            "limit": limit,
            "offset": offset,
        }

    async def download_revision_plan(
        self,
        user_id: UUID,
        plan_id: UUID,
    ) -> str:
        """记录下载统计"""
        plan = await self.get_revision_plan(user_id, plan_id)

        # 更新下载计数
        plan.download_count += 1
        await self.revision_repo.update(
            str(plan_id), {"download_count": plan.download_count}
        )

        return plan.pdf_url

    async def delete_revision_plan(
        self,
        user_id: UUID,
        plan_id: UUID,
    ) -> bool:
        """删除复习计划"""
        plan = await self.revision_repo.get_by_id(str(plan_id))

        if not plan or plan.user_id != str(user_id):
            raise ServiceError("计划不存在或无权访问")

        return await self.revision_repo.delete(str(plan_id))

    def _parse_json_response(self, response: str) -> Dict[str, Any]:
        """从 AI 响应中解析 JSON"""
        # 尝试找到 JSON 块
        match = re.search(r"\{[\s\S]*\}", response)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass

        # 如果失败，返回默认结构
        logger.warning("无法从 AI 响应解析 JSON，将使用默认结构")
        return self._generate_default_plan()

    def _generate_default_plan(self) -> Dict[str, Any]:
        """生成默认复习计划结构"""
        return {
            "title": "个性化复习计划",
            "description": "基于你的错题数据生成的复习计划",
            "overview": "...",
            "statistics": {},
            "daily_tasks": [],
            "review_focus": [],
            "assessment": {},
            "tips": [],
        }
