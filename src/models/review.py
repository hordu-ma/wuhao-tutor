from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from .base import BaseModel, is_sqlite

if TYPE_CHECKING:
    from .homework import MistakeRecord
    from .user import User


class MistakeReviewSession(BaseModel):
    __tablename__ = "mistake_review_sessions"
    __allow_unmapped__ = True

    if is_sqlite:
        mistake_id: str = Column(
            String(36), ForeignKey("mistake_records.id"), nullable=False
        )
        user_id: str = Column(String(36), ForeignKey("users.id"), nullable=False)
    else:
        from sqlalchemy.dialects.postgresql import UUID as PG_UUID

        mistake_id: UUID = Column(
            PG_UUID(as_uuid=True), ForeignKey("mistake_records.id"), nullable=False
        )
        user_id: UUID = Column(
            PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
        )

    status: str = Column(String, default="in_progress", index=True)
    current_stage: int = Column(Integer, default=1)
    attempts: int = Column(Integer, default=0)

    # 关联关系
    mistake: "MistakeRecord" = relationship(back_populates="review_sessions")
    user: "User" = relationship()
