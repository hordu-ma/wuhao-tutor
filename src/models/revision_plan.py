"""
复习计划数据模型
"""

from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import relationship
from sqlalchemy.types import JSON

from src.models.base import BaseModel


class RevisionPlan(BaseModel):
    """
    AI 复习计划模型
    """

    __tablename__ = "revision_plans"

    user_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
        index=True,
        comment="用户ID",
    )

    # 元数据
    title = Column(String(255), nullable=False, comment="计划标题")
    description = Column(Text, nullable=True, comment="简短描述")
    cycle_type = Column(
        String(20), nullable=False, comment="周期类型: 7days|14days|30days"
    )
    status = Column(
        String(20),
        default="draft",
        nullable=False,
        comment="状态: draft|published|completed|expired",
    )

    # 数据来源
    mistake_count = Column(Integer, default=0, comment="包含的错题数")
    knowledge_points = Column(JSON, default=list, comment="涉及的知识点列表")
    date_range = Column(JSON, nullable=True, comment="日期范围")

    # 复习计划内容
    plan_content = Column(JSON, nullable=True, comment="结构化的复习计划数据")

    # 文件信息
    pdf_url = Column(String(500), nullable=True, comment="PDF下载链接(OSS)")
    pdf_size = Column(Integer, nullable=True, comment="文件大小(字节)")
    markdown_url = Column(String(500), nullable=True, comment="Markdown源文件链接")

    # 时间戳
    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        index=True,
        comment="创建时间",
    )
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
        comment="更新时间",
    )
    expired_at = Column(DateTime, nullable=True, index=True, comment="过期时间")
    completed_at = Column(DateTime, nullable=True, comment="完成时间")

    # 使用统计
    download_count = Column(Integer, default=0, comment="下载次数")
    view_count = Column(Integer, default=0, comment="浏览次数")
    is_shared = Column(Boolean, default=False, comment="是否分享过")

    # 关系
    user = relationship("User", backref="revision_plans")

    def __repr__(self):
        return f"<RevisionPlan(id={self.id}, title='{self.title}', user_id={self.user_id})>"
