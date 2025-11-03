"""
知识图谱仓储层
提供错题-知识点关联、知识图谱快照和学习轨迹的数据访问方法

作者: AI Agent
创建时间: 2025-11-03
版本: v1.0
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.logging import get_logger
from src.models.knowledge_graph import (
    KnowledgePointLearningTrack,
    MistakeKnowledgePoint,
    UserKnowledgeGraphSnapshot,
)
from src.repositories.base_repository import BaseRepository

logger = get_logger(__name__)


class MistakeKnowledgePointRepository(BaseRepository[MistakeKnowledgePoint]):
    """错题-知识点关联仓储"""

    async def find_by_mistake(self, mistake_id: UUID) -> List[MistakeKnowledgePoint]:
        """
        查询错题关联的所有知识点

        Args:
            mistake_id: 错题ID

        Returns:
            知识点关联列表
        """
        stmt = (
            select(MistakeKnowledgePoint)
            .where(MistakeKnowledgePoint.mistake_id == str(mistake_id))
            .order_by(
                MistakeKnowledgePoint.is_primary.desc(),
                MistakeKnowledgePoint.relevance_score.desc(),
            )
        )

        result = await self.db.execute(stmt)
        items = result.scalars().all()

        logger.debug(f"Found {len(items)} knowledge points for mistake {mistake_id}")

        return list(items)

    async def find_by_knowledge_point(
        self,
        knowledge_point_id: UUID,
        user_id: Optional[UUID] = None,
        include_mastered: bool = False,
    ) -> List[MistakeKnowledgePoint]:
        """
        查询知识点关联的所有错题

        Args:
            knowledge_point_id: 知识点ID
            user_id: 用户ID筛选（可选）
            include_mastered: 是否包含已掌握的

        Returns:
            错题关联列表
        """
        conditions = [
            MistakeKnowledgePoint.knowledge_point_id == str(knowledge_point_id)
        ]

        if not include_mastered:
            conditions.append(
                MistakeKnowledgePoint.mastered_after_review == False  # noqa: E712
            )

        stmt = select(MistakeKnowledgePoint).where(and_(*conditions))

        result = await self.db.execute(stmt)
        items = result.scalars().all()

        logger.debug(
            f"Found {len(items)} mistakes for knowledge point {knowledge_point_id}"
        )

        return list(items)

    async def find_primary_by_mistake(
        self, mistake_id: UUID
    ) -> Optional[MistakeKnowledgePoint]:
        """
        查询错题的主要知识点关联

        Args:
            mistake_id: 错题ID

        Returns:
            主要知识点关联（如果有）
        """
        stmt = select(MistakeKnowledgePoint).where(
            and_(
                MistakeKnowledgePoint.mistake_id == str(mistake_id),
                MistakeKnowledgePoint.is_primary == True,  # noqa: E712
            )
        )

        result = await self.db.execute(stmt)
        item = result.scalar_one_or_none()

        return item

    async def batch_create_associations(
        self, associations: List[Dict[str, Any]]
    ) -> List[MistakeKnowledgePoint]:
        """
        批量创建错题-知识点关联

        Args:
            associations: 关联数据列表

        Returns:
            创建的关联记录列表
        """
        results = []
        for assoc_data in associations:
            assoc = MistakeKnowledgePoint(**assoc_data)
            self.db.add(assoc)
            results.append(assoc)

        await self.db.flush()

        logger.debug(f"Batch created {len(results)} mistake-knowledge associations")

        return results

    async def update_review_result(
        self,
        association_id: UUID,
        review_result: str,
        mastered: bool = False,
    ) -> MistakeKnowledgePoint:
        """
        更新复习结果

        Args:
            association_id: 关联ID
            review_result: 复习结果
            mastered: 是否已掌握

        Returns:
            更新后的关联记录
        """
        update_data = {
            "last_review_result": review_result,
            "review_count": MistakeKnowledgePoint.review_count + 1,
            "last_review_at": datetime.now(),
        }

        if mastered:
            update_data["mastered_after_review"] = True
            update_data["mastered_at"] = datetime.now()

        association = await self.update(str(association_id), update_data)

        logger.debug(
            f"Updated association {association_id} review result to {review_result}"
        )

        return association

    async def get_weak_associations(
        self,
        user_id: UUID,
        subject: Optional[str] = None,
        limit: int = 20,
    ) -> List[MistakeKnowledgePoint]:
        """
        查询薄弱知识点关联（未掌握且复习次数多）

        Args:
            user_id: 用户ID
            subject: 学科筛选（可选）
            limit: 返回数量限制

        Returns:
            薄弱知识点关联列表
        """
        # 需要join mistake_records表获取user_id
        from src.models.study import MistakeRecord

        stmt = (
            select(MistakeKnowledgePoint)
            .join(
                MistakeRecord,
                MistakeKnowledgePoint.mistake_id == MistakeRecord.id,
            )
            .where(
                and_(
                    MistakeRecord.user_id == str(user_id),
                    MistakeKnowledgePoint.mastered_after_review == False,  # noqa: E712
                )
            )
            .order_by(MistakeKnowledgePoint.review_count.desc())
            .limit(limit)
        )

        if subject:
            stmt = stmt.where(MistakeRecord.subject == subject)

        result = await self.db.execute(stmt)
        items = result.scalars().all()

        logger.debug(f"Found {len(items)} weak associations for user {user_id}")

        return list(items)


class UserKnowledgeGraphSnapshotRepository(BaseRepository[UserKnowledgeGraphSnapshot]):
    """用户知识图谱快照仓储"""

    async def find_latest_by_user(
        self, user_id: UUID, subject: str
    ) -> Optional[UserKnowledgeGraphSnapshot]:
        """
        查询用户最新的知识图谱快照

        Args:
            user_id: 用户ID
            subject: 学科

        Returns:
            最新快照（如果有）
        """
        stmt = (
            select(UserKnowledgeGraphSnapshot)
            .where(
                and_(
                    UserKnowledgeGraphSnapshot.user_id == str(user_id),
                    UserKnowledgeGraphSnapshot.subject == subject,
                )
            )
            .order_by(UserKnowledgeGraphSnapshot.snapshot_date.desc())
            .limit(1)
        )

        result = await self.db.execute(stmt)
        item = result.scalar_one_or_none()

        return item

    async def find_by_period(
        self,
        user_id: UUID,
        subject: str,
        period_type: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[UserKnowledgeGraphSnapshot]:
        """
        查询指定周期的快照列表

        Args:
            user_id: 用户ID
            subject: 学科
            period_type: 周期类型
            start_date: 开始时间（可选）
            end_date: 结束时间（可选）

        Returns:
            快照列表
        """
        conditions = [
            UserKnowledgeGraphSnapshot.user_id == str(user_id),
            UserKnowledgeGraphSnapshot.subject == subject,
            UserKnowledgeGraphSnapshot.period_type == period_type,
        ]

        if start_date:
            conditions.append(UserKnowledgeGraphSnapshot.snapshot_date >= start_date)

        if end_date:
            conditions.append(UserKnowledgeGraphSnapshot.snapshot_date <= end_date)

        stmt = (
            select(UserKnowledgeGraphSnapshot)
            .where(and_(*conditions))
            .order_by(UserKnowledgeGraphSnapshot.snapshot_date.desc())
        )

        result = await self.db.execute(stmt)
        items = result.scalars().all()

        logger.debug(
            f"Found {len(items)} snapshots for user {user_id}, subject {subject}, period {period_type}"
        )

        return list(items)

    async def create_snapshot(
        self, snapshot_data: Dict[str, Any]
    ) -> UserKnowledgeGraphSnapshot:
        """
        创建知识图谱快照

        Args:
            snapshot_data: 快照数据

        Returns:
            创建的快照记录
        """
        # 查找上一次快照
        latest = await self.find_latest_by_user(
            UUID(snapshot_data["user_id"]), snapshot_data["subject"]
        )

        if latest:
            snapshot_data["previous_snapshot_id"] = str(latest.id)

        snapshot = UserKnowledgeGraphSnapshot(**snapshot_data)
        self.db.add(snapshot)
        await self.db.flush()

        logger.debug(
            f"Created snapshot for user {snapshot_data['user_id']}, subject {snapshot_data['subject']}"
        )

        return snapshot

    async def compare_snapshots(
        self, current_id: UUID, previous_id: UUID
    ) -> Dict[str, Any]:
        """
        对比两个快照的变化

        Args:
            current_id: 当前快照ID
            previous_id: 之前快照ID

        Returns:
            变化统计
        """
        current = await self.get_by_id(str(current_id))
        previous = await self.get_by_id(str(previous_id))

        if not current or not previous:
            raise ValueError("Snapshot not found")

        comparison = {
            "period_days": (current.snapshot_date - previous.snapshot_date).days,
            "total_change": current.total_knowledge_points
            - previous.total_knowledge_points,
            "mastered_change": current.mastered_count - previous.mastered_count,
            "learning_change": current.learning_count - previous.learning_count,
            "weak_change": current.weak_count - previous.weak_count,
            "mastery_rate_change": (
                current.mastered_count / max(current.total_knowledge_points, 1)
                - previous.mastered_count / max(previous.total_knowledge_points, 1)
            ),
        }

        return comparison


class KnowledgePointLearningTrackRepository(
    BaseRepository[KnowledgePointLearningTrack]
):
    """知识点学习轨迹仓储"""

    async def find_by_knowledge_point(
        self,
        user_id: UUID,
        knowledge_point_id: UUID,
        limit: int = 50,
    ) -> List[KnowledgePointLearningTrack]:
        """
        查询知识点的学习轨迹

        Args:
            user_id: 用户ID
            knowledge_point_id: 知识点ID
            limit: 返回数量限制

        Returns:
            学习轨迹列表
        """
        stmt = (
            select(KnowledgePointLearningTrack)
            .where(
                and_(
                    KnowledgePointLearningTrack.user_id == str(user_id),
                    KnowledgePointLearningTrack.knowledge_point_id
                    == str(knowledge_point_id),
                )
            )
            .order_by(KnowledgePointLearningTrack.activity_date.desc())
            .limit(limit)
        )

        result = await self.db.execute(stmt)
        items = result.scalars().all()

        logger.debug(
            f"Found {len(items)} learning tracks for knowledge point {knowledge_point_id}"
        )

        return list(items)

    async def find_by_user_recent(
        self,
        user_id: UUID,
        days: int = 7,
        subject: Optional[str] = None,
    ) -> List[KnowledgePointLearningTrack]:
        """
        查询用户最近的学习轨迹

        Args:
            user_id: 用户ID
            days: 最近天数
            subject: 学科筛选（可选）

        Returns:
            学习轨迹列表
        """
        from datetime import timedelta

        start_date = datetime.now() - timedelta(days=days)

        stmt = (
            select(KnowledgePointLearningTrack)
            .where(
                and_(
                    KnowledgePointLearningTrack.user_id == str(user_id),
                    KnowledgePointLearningTrack.activity_date >= start_date,
                )
            )
            .order_by(KnowledgePointLearningTrack.activity_date.desc())
        )

        result = await self.db.execute(stmt)
        items = result.scalars().all()

        logger.debug(
            f"Found {len(items)} recent learning tracks for user {user_id} in {days} days"
        )

        return list(items)

    async def record_activity(
        self, track_data: Dict[str, Any]
    ) -> KnowledgePointLearningTrack:
        """
        记录学习活动

        Args:
            track_data: 轨迹数据

        Returns:
            创建的轨迹记录
        """
        track = KnowledgePointLearningTrack(**track_data)
        self.db.add(track)
        await self.db.flush()

        logger.debug(
            f"Recorded learning activity for user {track_data['user_id']}, knowledge point {track_data['knowledge_point_id']}"
        )

        return track

    async def get_learning_curve(
        self, user_id: UUID, knowledge_point_id: UUID
    ) -> List[Dict[str, Any]]:
        """
        获取学习曲线数据

        Args:
            user_id: 用户ID
            knowledge_point_id: 知识点ID

        Returns:
            学习曲线数据点列表
        """
        tracks = await self.find_by_knowledge_point(user_id, knowledge_point_id)

        curve = []
        for track in reversed(tracks):  # 从最早到最新
            curve.append(
                {
                    "date": track.activity_date,
                    "mastery_after": float(track.mastery_after) if track.mastery_after else 0.0,
                    "result": track.result,
                    "activity_type": track.activity_type,
                    "improvement": track.improvement_detected,
                }
            )

        return curve

    async def detect_improvement(
        self, user_id: UUID, knowledge_point_id: UUID, recent_count: int = 3
    ) -> bool:
        """
        检测知识点是否有进步

        Args:
            user_id: 用户ID
            knowledge_point_id: 知识点ID
            recent_count: 检查最近几次

        Returns:
            是否有进步
        """
        tracks = await self.find_by_knowledge_point(
            user_id, knowledge_point_id, limit=recent_count
        )

        if len(tracks) < 2:
            return False

        # 检查最近的记录是否有连续正确或掌握度提升
        recent_correct_tracks = [t for t in tracks if t.result == "correct"]
        recent_correct = len(recent_correct_tracks)

        # 如果最近记录中有50%以上正确，认为有进步
        improvement = recent_correct >= (len(tracks) * 0.5)

        return improvement
