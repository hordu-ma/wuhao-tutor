"""
基础数据库模型
提供通用字段和功能
"""

import uuid
from datetime import datetime
from typing import Any, Dict

from sqlalchemy import Column, DateTime, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base
from sqlalchemy.sql import func

from src.core.database import Base


class BaseModel(Base):
    """
    抽象基础模型类
    包含所有模型共有的字段
    """
    __abstract__ = True
    
    # 主键 - 使用UUID确保跨数据库唯一性
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        unique=True,
        nullable=False,
        comment="主键ID"
    )
    
    # 创建时间
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="创建时间"
    )
    
    # 更新时间
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="更新时间"
    )
    
    def to_dict(self, exclude_fields: set = None) -> Dict[str, Any]:
        """
        将模型转换为字典
        
        Args:
            exclude_fields: 需要排除的字段集合
            
        Returns:
            模型数据字典
        """
        exclude_fields = exclude_fields or set()
        result = {}
        
        for column in self.__table__.columns:
            if column.name not in exclude_fields:
                value = getattr(self, column.name)
                # 处理特殊类型的序列化
                if isinstance(value, datetime):
                    result[column.name] = value.isoformat()
                elif isinstance(value, uuid.UUID):
                    result[column.name] = str(value)
                else:
                    result[column.name] = value
        
        return result
    
    def update_from_dict(self, data: Dict[str, Any], exclude_fields: set = None) -> None:
        """
        从字典更新模型字段
        
        Args:
            data: 更新数据字典
            exclude_fields: 需要排除的字段集合
        """
        exclude_fields = exclude_fields or {"id", "created_at"}
        
        for key, value in data.items():
            if (hasattr(self, key) and 
                key not in exclude_fields and 
                value is not None):
                setattr(self, key, value)
    
    def __repr__(self) -> str:
        """字符串表示"""
        return f"<{self.__class__.__name__}(id='{self.id}')>"