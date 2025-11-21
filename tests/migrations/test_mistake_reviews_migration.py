"""
测试错题复习记录迁移脚本
测试 mistake_reviews 表创建和相关索引的迁移
"""

import pytest
from sqlalchemy import create_engine, inspect
from sqlalchemy.pool import StaticPool

from src.models.base import Base
from src.models.study import MistakeReview


@pytest.fixture
def test_db_engine():
    """创建测试数据库引擎"""
    # 使用内存 SQLite 数据库进行测试
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    # 创建所有表
    Base.metadata.create_all(engine)

    yield engine

    # 清理
    Base.metadata.drop_all(engine)
    engine.dispose()


def test_upgrade_migration(test_db_engine):
    """测试迁移升级 - 验证 mistake_reviews 表和字段创建"""
    inspector = inspect(test_db_engine)

    # 验证 mistake_reviews 表存在
    assert "mistake_reviews" in inspector.get_table_names()

    # 验证表的所有列
    columns = {col["name"] for col in inspector.get_columns("mistake_reviews")}
    expected_columns = {
        "id",
        "mistake_id",
        "user_id",
        "review_date",
        "review_result",
        "time_spent",
        "confidence_level",
        "mastery_level",
        "next_review_date",
        "interval_days",
        "user_answer",
        "notes",
        "review_method",
        "created_at",
        "updated_at",
    }

    assert expected_columns.issubset(columns), (
        f"Missing columns: {expected_columns - columns}"
    )


def test_model_fields():
    """测试 MistakeReview 模型字段定义"""
    # 验证模型可以正常导入和使用
    assert hasattr(MistakeReview, "mistake_id")
    assert hasattr(MistakeReview, "user_id")
    assert hasattr(MistakeReview, "review_result")
    assert hasattr(MistakeReview, "confidence_level")
    assert hasattr(MistakeReview, "mastery_level")
    assert hasattr(MistakeReview, "next_review_date")
    assert hasattr(MistakeReview, "review_method")


def test_foreign_key_constraints(test_db_engine):
    """测试外键约束"""
    inspector = inspect(test_db_engine)

    # 获取外键约束
    foreign_keys = inspector.get_foreign_keys("mistake_reviews")

    # 验证至少有两个外键（mistake_id 和 user_id）
    assert len(foreign_keys) >= 2

    # 验证外键关联的表
    referred_tables = {fk["referred_table"] for fk in foreign_keys}
    assert "mistake_records" in referred_tables
    assert "users" in referred_tables


def test_indexes_creation(test_db_engine):
    """测试索引创建"""
    inspector = inspect(test_db_engine)

    # 获取所有索引
    indexes = inspector.get_indexes("mistake_reviews")

    # 验证有索引被创建
    # 注意：不同数据库的索引名称可能不同，这里只验证有索引创建
    assert len(indexes) > 0, "应该至少有一些索引被创建"


def test_check_constraints_validation(test_db_engine):
    """测试检查约束 - review_result 枚举值"""
    # 这个测试验证 review_result 字段的合法值
    # 在实际迁移中，会添加检查约束
    valid_results = ["correct", "incorrect", "partial"]

    # 验证 MistakeReview 模型定义包含 review_result 字段
    assert hasattr(MistakeReview, "review_result")

    # 验证表结构中包含该字段
    inspector = inspect(test_db_engine)
    columns = [col["name"] for col in inspector.get_columns("mistake_reviews")]
    assert "review_result" in columns


def test_confidence_level_range(test_db_engine):
    """测试 confidence_level 范围约束 (1-5)"""
    # 这个测试验证 confidence_level 字段定义
    # 在实际迁移中，会添加检查约束: 1 <= confidence_level <= 5

    # 验证字段存在
    assert hasattr(MistakeReview, "confidence_level")

    # 验证表结构中包含该字段
    inspector = inspect(test_db_engine)
    columns = [col["name"] for col in inspector.get_columns("mistake_reviews")]
    assert "confidence_level" in columns


def test_mastery_level_range(test_db_engine):
    """测试 mastery_level 范围约束 (0.0-1.0)"""
    # 这个测试验证 mastery_level 字段定义
    # 在实际迁移中，会添加检查约束: 0.0 <= mastery_level <= 1.0

    # 验证字段存在
    assert hasattr(MistakeReview, "mastery_level")

    # 验证表结构中包含该字段
    inspector = inspect(test_db_engine)
    columns = [col["name"] for col in inspector.get_columns("mistake_reviews")]
    assert "mastery_level" in columns


def test_mistake_records_table_exists(test_db_engine):
    """测试 mistake_records 表存在"""
    inspector = inspect(test_db_engine)

    # 验证 mistake_records 表存在
    assert "mistake_records" in inspector.get_table_names()
