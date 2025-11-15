#!/usr/bin/env python3
"""
知识图谱诊断脚本
用于检查数据一致性和问题根源

使用方法:
    python scripts/diagnose-knowledge-graph.py --user-id <UUID> --subject <subject>
    python scripts/diagnose-knowledge-graph.py --all-users
"""

import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional
from uuid import UUID

import click
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.config import settings
from src.models.knowledge_graph import MistakeKnowledgePoint
from src.models.study import KnowledgeMastery, MistakeRecord


class KnowledgeGraphDiagnoser:
    """知识图谱诊断器"""

    def __init__(self, db_url: str):
        self.db_url = db_url
        self.engine = None
        self.session_maker = None

    async def init(self):
        """初始化数据库连接"""
        self.engine = create_async_engine(self.db_url, echo=False)
        self.session_maker = sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )

    async def close(self):
        """关闭数据库连接"""
        if self.engine:
            await self.engine.dispose()

    async def diagnose_user_subject(self, user_id: UUID, subject: str) -> dict:
        """诊断特定用户和学科"""
        async with self.session_maker() as session:
            result = {
                "user_id": str(user_id),
                "subject": subject,
                "timestamp": datetime.now().isoformat(),
                "checks": {},
            }

            # 检查 1: KnowledgeMastery 数据
            result["checks"]["knowledge_mastery"] = await self._check_knowledge_mastery(
                session, user_id, subject
            )

            # 检查 2: MistakeRecord 数据
            result["checks"]["mistake_records"] = await self._check_mistake_records(
                session, user_id, subject
            )

            # 检查 3: MistakeKnowledgePoint 关联
            result["checks"][
                "mistake_knowledge_associations"
            ] = await self._check_associations(session, user_id, subject)

            # 检查 4: 数据一致性
            result["checks"]["consistency"] = self._check_consistency(result)

            return result

    async def _check_knowledge_mastery(
        self, session: AsyncSession, user_id: UUID, subject: str
    ) -> dict:
        """检查 KnowledgeMastery 记录"""
        print(f"\n🔍 检查 KnowledgeMastery 数据...")

        stmt = select(KnowledgeMastery).where(
            and_(
                KnowledgeMastery.user_id == str(user_id),
                KnowledgeMastery.subject == subject,
            )
        )
        result = await session.execute(stmt)
        kms = result.scalars().all()

        print(f"   找到 {len(kms)} 条记录")

        data = {
            "total_count": len(kms),
            "records": [],
        }

        for km in kms:
            data["records"].append(
                {
                    "id": str(km.id),
                    "knowledge_point": km.knowledge_point,
                    "mastery_level": float(km.mastery_level)
                    if km.mastery_level
                    else 0.0,
                    "mistake_count": km.mistake_count,
                    "correct_count": km.correct_count,
                    "total_attempts": km.total_attempts,
                    "last_practiced_at": (
                        km.last_practiced_at.isoformat()
                        if km.last_practiced_at
                        else None
                    ),
                }
            )

        return data

    async def _check_mistake_records(
        self, session: AsyncSession, user_id: UUID, subject: str
    ) -> dict:
        """检查 MistakeRecord 数据"""
        print(f"\n🔍 检查 MistakeRecord 数据...")

        stmt = select(MistakeRecord).where(
            and_(
                MistakeRecord.user_id == str(user_id),
                MistakeRecord.subject == subject,
            )
        )
        result = await session.execute(stmt)
        mistakes = result.scalars().all()

        print(f"   找到 {len(mistakes)} 条记录")

        data = {
            "total_count": len(mistakes),
            "records": [],
        }

        for mistake in mistakes:
            kp_list = mistake.knowledge_points or []
            data["records"].append(
                {
                    "id": str(mistake.id),
                    "title": mistake.title,
                    "knowledge_points": kp_list,
                    "knowledge_points_count": len(kp_list),
                    "source": getattr(mistake, "source", "unknown"),
                    "created_at": mistake.created_at.isoformat(),
                }
            )

        return data

    async def _check_associations(
        self, session: AsyncSession, user_id: UUID, subject: str
    ) -> dict:
        """检查 MistakeKnowledgePoint 关联"""
        print(f"\n🔍 检查 MistakeKnowledgePoint 关联...")

        # 获取该用户该学科的所有错题
        stmt = select(MistakeRecord).where(
            and_(
                MistakeRecord.user_id == str(user_id),
                MistakeRecord.subject == subject,
            )
        )
        result = await session.execute(stmt)
        mistakes = result.scalars().all()

        data = {
            "total_mistakes": len(mistakes),
            "mistakes_with_associations": 0,
            "total_associations": 0,
            "details": [],
        }

        for mistake in mistakes:
            # 查询该错题的关联
            assoc_stmt = select(MistakeKnowledgePoint).where(
                MistakeKnowledgePoint.mistake_id == str(mistake.id)
            )
            assoc_result = await session.execute(assoc_stmt)
            assocs = assoc_result.scalars().all()

            if assocs:
                data["mistakes_with_associations"] += 1
                data["total_associations"] += len(assocs)

            data["details"].append(
                {
                    "mistake_id": str(mistake.id),
                    "title": mistake.title,
                    "knowledge_points_json": mistake.knowledge_points or [],
                    "associations_count": len(assocs),
                    "associated_kp_ids": [str(a.knowledge_point_id) for a in assocs],
                }
            )

        print(
            f"   错题总数: {data['total_mistakes']}, "
            f"有关联的错题: {data['mistakes_with_associations']}, "
            f"关联总数: {data['total_associations']}"
        )

        return data

    def _check_consistency(self, result: dict) -> dict:
        """检查数据一致性"""
        print(f"\n🔍 检查数据一致性...")

        checks = result["checks"]
        consistency = {
            "issues": [],
            "warnings": [],
            "summary": "",
        }

        km_count = checks["knowledge_mastery"]["total_count"]
        mistake_count = checks["mistake_records"]["total_count"]
        assoc_count = checks["mistake_knowledge_associations"]["total_associations"]
        mistakes_with_assoc = checks["mistake_knowledge_associations"][
            "mistakes_with_associations"
        ]

        # 问题1: 没有 KnowledgeMastery 数据
        if km_count == 0:
            consistency["issues"].append(
                "❌ 没有 KnowledgeMastery 记录 - 知识图谱无法显示"
            )

        # 问题2: 有错题但没有关联
        if mistake_count > 0 and assoc_count == 0:
            consistency["issues"].append(
                f"❌ 有 {mistake_count} 个错题，但没有知识点关联"
            )

        # 问题3: 有关联但没有对应的 KnowledgeMastery
        if assoc_count > 0 and km_count == 0:
            consistency["issues"].append(
                f"⚠️ 有 {assoc_count} 个知识点关联，但没有对应的 KnowledgeMastery 记录"
            )

        # 警告1: 关联不完整
        if mistake_count > 0 and mistakes_with_assoc < mistake_count:
            consistency["warnings"].append(
                f"⚠️ 只有 {mistakes_with_assoc}/{mistake_count} 个错题有知识点关联"
            )

        # 警告2: 知识点数量不匹配
        for detail in checks["mistake_knowledge_associations"]["details"]:
            json_kp_count = len(detail["knowledge_points_json"])
            assoc_kp_count = detail["associations_count"]
            if json_kp_count > 0 and assoc_kp_count == 0:
                consistency["warnings"].append(
                    f"⚠️ 错题 {detail['mistake_id']} 在 knowledge_points JSON 中有 "
                    f"{json_kp_count} 个知识点，但没有关联记录"
                )

        # 生成摘要
        if consistency["issues"]:
            consistency["summary"] = "🔴 严重问题 - 知识图谱数据链路中断"
        elif consistency["warnings"]:
            consistency["summary"] = "🟡 有警告 - 数据不完整或不一致"
        else:
            consistency["summary"] = "✅ 数据一致 - 知识图谱应该可以正常显示"

        return consistency

    async def diagnose_all_users(self) -> dict:
        """诊断所有用户"""
        async with self.session_maker() as session:
            # 获取所有有错题的用户
            stmt = select(MistakeRecord.user_id, MistakeRecord.subject).distinct()
            result = await session.execute(stmt)
            users = result.all()

            print(f"\n📊 发现 {len(users)} 个用户-学科组合")

            summary = {
                "total_combinations": len(users),
                "issues_found": 0,
                "warnings_found": 0,
                "combinations": [],
            }

            for user_id_str, subject in users:
                user_id = (
                    UUID(user_id_str) if isinstance(user_id_str, str) else user_id_str
                )
                result = await self.diagnose_user_subject(user_id, subject)

                consistency = result["checks"]["consistency"]
                if consistency["issues"]:
                    summary["issues_found"] += 1
                    summary["combinations"].append(
                        {
                            "user_id": str(user_id),
                            "subject": subject,
                            "status": "❌ 有问题",
                            "issues": consistency["issues"],
                        }
                    )
                elif consistency["warnings"]:
                    summary["warnings_found"] += 1

            return summary


@click.command()
@click.option(
    "--user-id",
    type=str,
    default=None,
    help="特定用户ID (UUID格式)",
)
@click.option(
    "--subject",
    type=str,
    default="math",
    help="学科 (默认: math)",
)
@click.option(
    "--all-users",
    is_flag=True,
    help="诊断所有用户",
)
@click.option(
    "--output",
    type=str,
    default=None,
    help="输出文件路径 (JSON格式)",
)
async def main(
    user_id: Optional[str], subject: str, all_users: bool, output: Optional[str]
):
    """知识图谱诊断工具"""

    db_url = settings.SQLALCHEMY_DATABASE_URI
    diagnoser = KnowledgeGraphDiagnoser(db_url)

    try:
        await diagnoser.init()

        if all_users:
            print("🚀 开始全局诊断...")
            result = await diagnoser.diagnose_all_users()
        else:
            if not user_id:
                click.echo("❌ 需要指定 --user-id 或 --all-users")
                sys.exit(1)

            print(f"🚀 开始诊断: user_id={user_id}, subject={subject}")
            result = await diagnoser.diagnose_user_subject(UUID(user_id), subject)

        # 打印结果
        print("\n" + "=" * 80)
        print("诊断报告")
        print("=" * 80)
        print(json.dumps(result, ensure_ascii=False, indent=2))

        # 保存到文件
        if output:
            Path(output).write_text(
                json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
            )
            print(f"\n✅ 诊断报告已保存到: {output}")

    finally:
        await diagnoser.close()


if __name__ == "__main__":
    asyncio.run(main())
