"""
基础数据库模型
提供通用字段和功能
"""

import uuid
from datetime import datetime
from typing import Any, Dict

from sqlalchemy import Column, DateTime, String
from sqlalchemy.sql import func

from src.core.config import get_settings
from src.core.database import Base

# 获取配置以确定数据库类型
settings = get_settings()
is_sqlite = settings.SQLALCHEMY_DATABASE_URI and "sqlite" in str(settings.SQLALCHEMY_DATABASE_URI)  # type: ignore


class BaseModel(Base):
    """
    抽象基础模型类
    包含所有模型共有的字段
    """

    __abstract__ = True

    # 主键 - 兼容SQLite和PostgreSQL
    if is_sqlite:
        # SQLite使用字符串类型
        id = Column(
            String(36),
            primary_key=True,
            default=lambda: str(uuid.uuid4()),
            unique=True,
            nullable=False,
            comment="主键ID",
        )
    else:
        # PostgreSQL使用UUID类型
        from sqlalchemy.dialects.postgresql import UUID

        id = Column(
            UUID(as_uuid=True),
            primary_key=True,
            default=uuid.uuid4,
            unique=True,
            nullable=False,
            comment="主键ID",
        )

    # 创建时间
    created_at = Column(
        DateTime(timezone=True) if not is_sqlite else String(50),  # type: ignore
        server_default=func.now() if not is_sqlite else None,
        default=lambda: (
            datetime.now() if not is_sqlite else datetime.now().isoformat()
        ),
        nullable=False,
        comment="创建时间",
    )

    # 更新时间
    updated_at = Column(
        DateTime(timezone=True) if not is_sqlite else String(50),  # type: ignore
        server_default=func.now() if not is_sqlite else None,
        onupdate=func.now() if not is_sqlite else None,
        default=lambda: (
            datetime.now() if not is_sqlite else datetime.now().isoformat()
        ),
        nullable=False,
        comment="更新时间",
    )

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        result = {}
        for column in self.__table__.columns:
            value = getattr(self, column.name)
            if isinstance(value, uuid.UUID):
                value = str(value)
            elif isinstance(value, datetime):
                value = value.isoformat()
            result[column.name] = value
        return result

    def update_timestamp(self):
        """更新时间戳"""
        if is_sqlite:
            self.updated_at = datetime.now().isoformat()
        else:
            self.updated_at = datetime.now()

    def __repr__(self) -> str:
        """字符串表示"""
        return f"<{self.__class__.__name__}(id={self.id})>"
