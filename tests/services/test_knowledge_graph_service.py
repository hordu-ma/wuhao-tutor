"""
知识图谱服务单元测试
测试 KnowledgeGraphService 核心功能

作者: AI Agent
创建时间: 2025-11-12
版本: v1.0
"""

from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from src.models.base import Base
from src.models.study import KnowledgeMastery
from src.services.knowledge_graph_service import KnowledgeGraphService


@pytest.fixture
async def db_session():
    """创建测试数据库会话"""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)  # type: ignore

    async with async_session() as session:  # type: ignore
        yield session

    await engine.dispose()


@pytest.fixture
async def kg_service(db_session):
    """创建知识图谱服务实例"""
    return KnowledgeGraphService(db_session)


@pytest.fixture
def sample_user_id():
    """创建测试用户ID"""
    return uuid4()


@pytest.fixture
async def sample_knowledge_points(db_session, sample_user_id):
    """创建测试知识点数据"""
    user_id = sample_user_id

    # 创建数学学科的知识点
    math_points = [
        {
            "user_id": user_id,  # 使用 UUID 对象而非字符串
            "subject": "math",
            "knowledge_point": "二次函数",
            "mastery_level": 0.3,
            "mistake_count": 5,
            "correct_count": 2,
            "total_attempts": 7,
        },
        {
            "user_id": user_id,
            "subject": "math",
            "knowledge_point": "三角函数",
            "mastery_level": 0.6,
            "mistake_count": 2,
            "correct_count": 5,
            "total_attempts": 7,
        },
        {
            "user_id": user_id,
            "subject": "math",
            "knowledge_point": "数列",
            "mastery_level": 0.8,
            "mistake_count": 1,
            "correct_count": 8,
            "total_attempts": 9,
        },
    ]

    # 创建英语学科的知识点
    english_points = [
        {
            "user_id": user_id,
            "subject": "english",
            "knowledge_point": "现在完成时",
            "mastery_level": 0.5,
            "mistake_count": 3,
            "correct_count": 3,
            "total_attempts": 6,
        },
    ]

    all_points = math_points + english_points

    for point_data in all_points:
        km = KnowledgeMastery(**point_data)
        db_session.add(km)

    await db_session.commit()

    return {"math": math_points, "english": english_points}


class TestKnowledgeGraphService:
    """测试知识图谱服务"""

    @pytest.mark.asyncio
    async def test_service_initialization(self, kg_service):
        """测试服务初始化"""
        assert kg_service is not None
        assert kg_service.db is not None
        assert kg_service.mkp_repo is not None
        assert kg_service.snapshot_repo is not None
        assert kg_service.track_repo is not None

    @pytest.mark.asyncio
    async def test_get_subject_knowledge_graph_normal(
        self, kg_service, sample_user_id, sample_knowledge_points
    ):
        """测试获取学科知识图谱 - 正常场景"""
        user_id = sample_user_id
        # sample_knowledge_points 是 async fixture，已经自动执行

        result = await kg_service.get_subject_knowledge_graph(user_id, "math")

        # 验证基本结构
        assert result["subject"] == "math"
        assert "nodes" in result
        assert "weak_chains" in result
        assert "mastery_distribution" in result
        assert "total_points" in result
        assert "avg_mastery" in result
        assert "recommendations" in result

        # 验证节点数据
        assert len(result["nodes"]) == 3
        assert result["total_points"] == 3

        # 验证节点按掌握度升序排列
        masteries = [node["mastery"] for node in result["nodes"]]
        assert masteries == sorted(masteries)

        # 验证掌握度分布
        dist = result["mastery_distribution"]
        assert dist["weak"] == 1  # 0.3
        assert dist["learning"] == 1  # 0.6
        assert dist["mastered"] == 1  # 0.8

        # 验证平均掌握度
        expected_avg = round((0.3 + 0.6 + 0.8) / 3, 2)
        assert result["avg_mastery"] == expected_avg

    @pytest.mark.asyncio
    async def test_get_subject_knowledge_graph_empty(self, kg_service, sample_user_id):
        """测试获取学科知识图谱 - 空数据场景"""
        user_id = sample_user_id

        # 查询一个没有数据的学科
        result = await kg_service.get_subject_knowledge_graph(user_id, "physics")

        # 验证返回空结果
        assert result["subject"] == "physics"
        assert result["nodes"] == []
        assert result["weak_chains"] == []
        assert result["total_points"] == 0
        assert result["avg_mastery"] == 0.0
        assert result["mastery_distribution"] == {
            "weak": 0,
            "learning": 0,
            "mastered": 0,
        }

    @pytest.mark.asyncio
    async def test_get_subject_knowledge_graph_different_subjects(
        self, kg_service, sample_user_id, sample_knowledge_points
    ):
        """测试获取学科知识图谱 - 不同学科隔离"""
        user_id = sample_user_id
        # sample_knowledge_points 已自动执行

        # 查询数学
        math_result = await kg_service.get_subject_knowledge_graph(user_id, "math")
        assert len(math_result["nodes"]) == 3
        assert all(
            node["name"] in ["二次函数", "三角函数", "数列"]
            for node in math_result["nodes"]
        )

        # 查询英语
        english_result = await kg_service.get_subject_knowledge_graph(
            user_id, "english"
        )
        assert len(english_result["nodes"]) == 1
        assert english_result["nodes"][0]["name"] == "现在完成时"

        # 确保学科数据隔离
        assert math_result["nodes"] != english_result["nodes"]

    @pytest.mark.asyncio
    async def test_get_subject_knowledge_graph_node_fields(
        self, kg_service, sample_user_id, sample_knowledge_points
    ):
        """测试获取学科知识图谱 - 节点字段完整性"""
        user_id = sample_user_id
        # sample_knowledge_points 已自动执行

        result = await kg_service.get_subject_knowledge_graph(user_id, "math")

        # 验证每个节点都有必需字段
        for node in result["nodes"]:
            assert "id" in node
            assert "name" in node
            assert "mastery" in node
            assert "mistake_count" in node
            assert "correct_count" in node
            assert "last_practiced_at" in node

            # 验证字段类型
            assert isinstance(node["id"], str)
            assert isinstance(node["name"], str)
            assert isinstance(node["mastery"], float)
            assert isinstance(node["mistake_count"], int)
            assert isinstance(node["correct_count"], int)

    @pytest.mark.asyncio
    async def test_get_subject_knowledge_graph_mastery_distribution(
        self, kg_service, sample_user_id, sample_knowledge_points
    ):
        """测试获取学科知识图谱 - 掌握度分布统计"""
        user_id = sample_user_id
        # sample_knowledge_points 已自动执行

        result = await kg_service.get_subject_knowledge_graph(user_id, "math")

        dist = result["mastery_distribution"]

        # 验证分布统计正确
        assert (
            dist["weak"] + dist["learning"] + dist["mastered"] == result["total_points"]
        )

        # 验证分类阈值
        for node in result["nodes"]:
            mastery = node["mastery"]
            if mastery < 0.4:
                assert dist["weak"] > 0
            elif mastery < 0.7:
                assert dist["learning"] > 0
            else:
                assert dist["mastered"] > 0


if __name__ == "__main__":
    """直接运行测试"""
    pytest.main([__file__, "-v", "-s"])
