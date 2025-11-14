from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID as PostgreSQL_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import BaseModel

if TYPE_CHECKING:
    from .study import MistakeRecord
    from .user import User


class MistakeReviewSession(BaseModel):
    __tablename__ = "mistake_review_sessions"

    # 使用 PostgreSQL UUID 类型
    mistake_id: Mapped[UUID] = mapped_column(
        PostgreSQL_UUID(as_uuid=True), ForeignKey("mistake_records.id"), nullable=False
    )
    user_id: Mapped[UUID] = mapped_column(
        PostgreSQL_UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )

    status: Mapped[str] = mapped_column(String, default="in_progress", index=True)
    current_stage: Mapped[int] = mapped_column(Integer, default=1)
    attempts: Mapped[int] = mapped_column(Integer, default=0)

    # 关联关系
    user: Mapped["User"] = relationship()
    mistake: Mapped["MistakeRecord"] = relationship(back_populates="review_sessions")
