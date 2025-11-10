from __future__ import annotations

from typing import TYPE_CHECKING, Union
from uuid import UUID

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import BaseModel

if TYPE_CHECKING:
    from .user import User


class MistakeReviewSession(BaseModel):
    __tablename__ = "mistake_review_sessions"

    # 使用 Union 类型来支持 SQLite 和 PostgreSQL
    mistake_id: Mapped[Union[str, UUID]] = mapped_column(
        String(36), ForeignKey("mistake_records.id"), nullable=False
    )
    user_id: Mapped[Union[str, UUID]] = mapped_column(
        String(36), ForeignKey("users.id"), nullable=False
    )

    status: Mapped[str] = mapped_column(String, default="in_progress", index=True)
    current_stage: Mapped[int] = mapped_column(Integer, default=1)
    attempts: Mapped[int] = mapped_column(Integer, default=0)

    # 关联关系
    user: Mapped["User"] = relationship()
