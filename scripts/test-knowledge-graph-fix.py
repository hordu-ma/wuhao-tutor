#!/usr/bin/env python3
"""
知识图谱修复本地测试脚本
用于验证修复后的功能是否正常工作

使用方法:
    python scripts/test-knowledge-graph-fix.py
    python scripts/test-knowledge-graph-fix.py --user-id <UUID>
"""

import asyncio
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional
from uuid import UUID, uuid4

import click
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.config import settings
from src.models.knowledge_graph import MistakeKnowledgePoint
from src.models.study import KnowledgeMastery, MistakeRecord
from src.services.knowledge_graph_service import KnowledgeGraphService


class KnowledgeGraphTestSuite:
    """知识图谱修复测试套件"""

    def __init__(self, db_url: str):
        self.db_url = db_url
        self.engine = None
        self.session_maker = None
        self.test_results = []

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

    def add_result(self, test_name: str, passed: bool, message: str = ""):
        """添加测试结果"""
        self.test_results.append(
            {
                "test": test_name,
                "passed": passed,
                "message": message,
                "timestamp": datetime.now().isoformat(),
            }
        )

    async def test_knowledge_mastery_query(self, user_id: UUID, subject: str) -> bool:
        """测试 KnowledgeMastery 查询"""
        print("\n🧪 测试 1: KnowledgeMastery 查询")

        async with self.session_maker() as session:
            try:
                stmt = select(KnowledgeMastery).where(
                    and_(
                        KnowledgeMastery.user_id == str(user_id),
                        KnowledgeMastery.subject == subject,
                    )
                )
                result = await session.execute(stmt)
                kms = result.scalars().all()

                if kms:
                    print(f"   ✅ 查询成功，找到 {len(kms)} 条记录")
                    self.add_result(
                        "KnowledgeMastery 查询", True, f"找到 {len(kms)} 条记录"
                    )
                    return True
                else:
                    print(f"   ⚠️ 查询成功，但未找到记录")
                    self.add_result("KnowledgeMastery 查询", False, "未找到任何记录")
                    return False

            except Exception as e:
                print(f"   ❌ 查询失败: {e}")
                self.add_result("KnowledgeMastery 查询", False, str(e))
                return False

    async def test_mistake_record_query(self, user_id: UUID, subject: str) -> bool:
        """测试 MistakeRecord 查询"""
        print("\n🧪 测试 2: MistakeRecord 查询")

        async with self.session_maker() as session:
            try:
                stmt = select(MistakeRecord).where(
                    and_(
                        MistakeRecord.user_id == str(user_id),
                        MistakeRecord.subject == subject,
                    )
                )
                result = await session.execute(stmt)
                mistakes = result.scalars().all()

                if mistakes:
                    print(f"   ✅ 查询成功，找到 {len(mistakes)} 条错题记录")
                    self.add_result(
                        "MistakeRecord 查询", True, f"找到 {len(mistakes)} 条记录"
                    )
                    return True
                else:
                    print(f"   ⚠️ 查询成功，但未找到错题记录")
                    self.add_result("MistakeRecord 查询", False, "未找到任何记录")
                    return False

            except Exception as e:
                print(f"   ❌ 查询失败: {e}")
                self.add_result("MistakeRecord 查询", False, str(e))
                return False

    async def test_knowledge_point_association(self, user_id: UUID) -> bool:
        """测试知识点关联"""
        print("\n🧪 测试 3: 知识点关联完整性")

        async with self.session_maker() as session:
            try:
                # 获取用户的所有错题
                stmt = select(MistakeRecord).where(
                    MistakeRecord.user_id == str(user_id)
                )
                result = await session.execute(stmt)
                mistakes = result.scalars().all()

                if not mistakes:
                    print("   ℹ️ 用户无错题记录")
                    self.add_result("知识点关联", True, "用户无错题记录")
                    return True

                # 检查关联
                total_assocs = 0
                mistakes_with_assoc = 0

                for mistake in mistakes:
                    assoc_stmt = select(MistakeKnowledgePoint).where(
                        MistakeKnowledgePoint.mistake_id == str(mistake.id)
                    )
                    assoc_result = await session.execute(assoc_stmt)
                    assocs = assoc_result.scalars().all()

                    if assocs:
                        mistakes_with_assoc += 1
                        total_assocs += len(assocs)

                coverage = (
                    (mistakes_with_assoc / len(mistakes) * 100) if mistakes else 0
                )
                print(
                    f"   ✅ 关联覆盖率: {mistakes_with_assoc}/{len(mistakes)} "
                    f"({coverage:.1f}%), 总关联数: {total_assocs}"
                )

                if coverage >= 80:
                    self.add_result("知识点关联", True, f"覆盖率 {coverage:.1f}%")
                    return True
                else:
                    self.add_result("知识点关联", False, f"覆盖率过低: {coverage:.1f}%")
                    return False

            except Exception as e:
                print(f"   ❌ 测试失败: {e}")
                self.add_result("知识点关联", False, str(e))
                return False

    async def test_get_subject_knowledge_graph(
        self, user_id: UUID, subject: str
    ) -> bool:
        """测试 get_subject_knowledge_graph 方法"""
        print("\n🧪 测试 4: get_subject_knowledge_graph() 方法")

        async with self.session_maker() as session:
            try:
                service = KnowledgeGraphService(session)
                result = await service.get_subject_knowledge_graph(user_id, subject)

                print(f"   响应字段检查:")
                print(f"     - subject: {result.get('subject')}")
                print(f"     - nodes: {len(result.get('nodes', []))} 个")
                print(f"     - weak_chains: {len(result.get('weak_chains', []))} 个")
                print(
                    f"     - mastery_distribution: {result.get('mastery_distribution')}"
                )
                print(f"     - total_points: {result.get('total_points')}")
                print(f"     - avg_mastery: {result.get('avg_mastery')}")

                # 检查必要字段
                required_fields = [
                    "subject",
                    "nodes",
                    "weak_chains",
                    "mastery_distribution",
                    "total_points",
                    "avg_mastery",
                ]
                missing_fields = [f for f in required_fields if f not in result]

                if missing_fields:
                    print(f"   ❌ 缺少必要字段: {missing_fields}")
                    self.add_result(
                        "get_subject_knowledge_graph()",
                        False,
                        f"缺少字段: {missing_fields}",
                    )
                    return False

                nodes_count = len(result.get("nodes", []))
                if nodes_count > 0:
                    print(f"   ✅ 成功返回 {nodes_count} 个知识点节点")
                    self.add_result(
                        "get_subject_knowledge_graph()",
                        True,
                        f"返回 {nodes_count} 个节点",
                    )
                    return True
                else:
                    print(f"   ⚠️ 返回了响应但 nodes 为空")
                    self.add_result(
                        "get_subject_knowledge_graph()", False, "nodes 为空"
                    )
                    return False

            except Exception as e:
                print(f"   ❌ 方法调用失败: {e}")
                self.add_result("get_subject_knowledge_graph()", False, str(e))
                return False

    async def test_data_consistency(self, user_id: UUID, subject: str) -> bool:
        """测试数据一致性"""
        print("\n🧪 测试 5: 数据一致性检查")

        async with self.session_maker() as session:
            try:
                km_stmt = select(KnowledgeMastery).where(
                    and_(
                        KnowledgeMastery.user_id == str(user_id),
                        KnowledgeMastery.subject == subject,
                    )
                )
                km_result = await session.execute(km_stmt)
                kms = km_result.scalars().all()

                mistake_stmt = select(MistakeRecord).where(
                    and_(
                        MistakeRecord.user_id == str(user_id),
                        MistakeRecord.subject == subject,
                    )
                )
                mistake_result = await session.execute(mistake_stmt)
                mistakes = mistake_result.scalars().all()

                print(f"   KnowledgeMastery 数量: {len(kms)}")
                print(f"   MistakeRecord 数量: {len(mistakes)}")

                if len(kms) > 0 and len(mistakes) > 0:
                    print(f"   ✅ 两个表都有数据，一致性良好")
                    self.add_result("数据一致性", True, "两个表都有数据")
                    return True
                elif len(kms) == 0 and len(mistakes) == 0:
                    print(f"   ℹ️ 两个表都没有数据")
                    self.add_result("数据一致性", True, "表都为空")
                    return True
                else:
                    print(
                        f"   ⚠️ 数据不一致: KnowledgeMastery={len(kms)}, MistakeRecord={len(mistakes)}"
                    )
                    self.add_result(
                        "数据一致性",
                        False,
                        f"不一致: KM={len(kms)}, MR={len(mistakes)}",
                    )
                    return False

            except Exception as e:
                print(f"   ❌ 检查失败: {e}")
                self.add_result("数据一致性", False, str(e))
                return False

    async def run_all_tests(self, user_id: UUID, subject: str = "数学"):
        """运行所有测试"""
        print("=" * 60)
        print("知识图谱修复测试套件")
        print("=" * 60)
        print(f"用户 ID: {user_id}")
        print(f"学科: {subject}")
        print("=" * 60)

        # 运行测试
        results = []
        results.append(await self.test_knowledge_mastery_query(user_id, subject))
        results.append(await self.test_mistake_record_query(user_id, subject))
        results.append(await self.test_knowledge_point_association(user_id))
        results.append(await self.test_get_subject_knowledge_graph(user_id, subject))
        results.append(await self.test_data_consistency(user_id, subject))

        # 打印总结
        print("\n" + "=" * 60)
        print("测试总结")
        print("=" * 60)

        passed = sum(results)
        total = len(results)
        pass_rate = (passed / total * 100) if total > 0 else 0

        print(f"\n通过: {passed}/{total} ({pass_rate:.1f}%)")
        print("\n详细结果:")

        for result in self.test_results:
            status = "✅" if result["passed"] else "❌"
            print(f"  {status} {result['test']}: {result['message']}")

        if pass_rate >= 80:
            print("\n🎉 测试通过！知识图谱修复成功")
            return True
        else:
            print("\n⚠️ 测试部分失败，请检查日志")
            return False


@click.command()
@click.option(
    "--user-id",
    type=str,
    default=None,
    help="特定用户ID (UUID格式，如果不指定则使用测试用户)",
)
@click.option(
    "--subject",
    type=str,
    default="数学",
    help="学科 (默认: 数学)",
)
async def main(user_id: Optional[str], subject: str):
    """知识图谱修复测试"""

    db_url = settings.SQLALCHEMY_DATABASE_URI
    tester = KnowledgeGraphTestSuite(db_url)

    try:
        await tester.init()

        if not user_id:
            print("🔍 查找有数据的用户...")
            async with tester.session_maker() as session:
                stmt = select(MistakeRecord.user_id).limit(1)
                result = await session.execute(stmt)
                found_user = result.scalar_one_or_none()

                if found_user:
                    user_id = found_user
                    print(f"✓ 使用用户: {user_id}")
                else:
                    print("❌ 数据库中没有找到任何错题记录")
                    print("请先在微信小程序中创建一些错题")
                    sys.exit(1)

        await tester.run_all_tests(UUID(user_id), subject)

    except Exception as e:
        print(f"❌ 测试执行失败: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
    finally:
        await tester.close()


if __name__ == "__main__":
    asyncio.run(main())
