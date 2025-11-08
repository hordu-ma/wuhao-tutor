from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class ReviewSessionStartRequest(BaseModel):
    mistake_id: UUID


class ReviewAnswerSubmitRequest(BaseModel):
    answer: Optional[str] = ""  # 答案可选（skip时可为空）
    skip: bool = False  # 是否跳过（不会做）
    is_correct: Optional[bool] = None  # 旧版兼容，可选
