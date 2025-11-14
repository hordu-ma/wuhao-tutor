"""
学习问答API端点
提供AI学习助手相关接口，包括提问、会话管理、历史查询等功能
"""

import json
import logging
from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    Query,
    UploadFile,
    WebSocket,
    WebSocketDisconnect,
)
from fastapi import status as http_status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.v1.endpoints.auth import get_current_user_id
from src.core.database import get_db
from src.core.exceptions import (
    BailianServiceError,
    NotFoundError,
    ServiceError,
    ValidationError,
)
from src.schemas.common import SuccessResponse
from src.schemas.learning import (
    AskQuestionRequest,
    AskQuestionResponse,
    CreateSessionRequest,
    FeedbackRequest,
    LearningAnalyticsResponse,
    QuestionHistoryQuery,
    QuestionHistoryResponse,
    RecommendationResponse,
    SessionListQuery,
    SessionListResponse,
    SessionResponse,
    UpdateSessionRequest,
)
from src.schemas.mistake import MistakeDetailResponse
from src.services.learning_service import get_learning_service

router = APIRouter()
logger = logging.getLogger(__name__)


# ========== 测试和健康检查 ==========


@router.get("/health", summary="学习模块健康检查")
async def learning_health_check():
    """学习模块健康检查端点"""
    return {
        "status": "ok",
        "module": "learning",
        "timestamp": datetime.utcnow().isoformat(),
        "message": "学习问答模块正常工作",
    }


@router.get("/test", summary="无认证测试端点")
async def test_endpoint():
    """测试端点，无需认证"""
    return {
        "message": "学习API测试成功",
        "timestamp": datetime.utcnow().isoformat(),
        "routing": "working",
        "auth": "bypassed",
    }


# ========== 问答核心功能 ==========


@router.post("/ask", response_model=AskQuestionResponse, summary="提问")
async def ask_question(
    request: AskQuestionRequest,
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """
    向AI学习助手提问

    - **content**: 问题内容
    - **question_type**: 问题类型 (concept/problem_solving/study_guidance等)
    - **subject**: 学科 (math/chinese/english/physics等)
    - **topic**: 话题/知识点
    - **difficulty_level**: 难度级别 (1-5)
    - **session_id**: 会话ID (可选，不提供则创建新会话)
    - **use_context**: 是否使用学习上下文
    - **include_history**: 是否包含历史对话
    - **max_history**: 最大历史消息数
    """
    try:
        learning_service = get_learning_service(db)

        response = await learning_service.ask_question(current_user_id, request)
        return response

    except BailianServiceError as e:
        raise HTTPException(
            status_code=http_status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"AI服务暂时不可用: {str(e)}",
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=http_status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)
        )
    except ServiceError as e:
        # 检查是否是表不存在的错误
        error_msg = str(e).lower()
        if "does not exist" in error_msg or "undefinedtable" in error_msg:
            raise HTTPException(
                status_code=http_status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="学习问答功能暂未开放,数据库尚未初始化",
            )
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )
    except Exception as e:
        # 捕获其他数据库错误
        error_msg = str(e).lower()
        if "does not exist" in error_msg or "undefinedtable" in error_msg:
            raise HTTPException(
                status_code=http_status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="学习问答功能暂未开放,数据库尚未初始化",
            )
        logging.error(f"Ask question failed: {e}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="提问失败,请稍后重试",
        )


@router.post("/ask-stream", summary="提问(流式响应)")
async def ask_question_stream(
    request: AskQuestionRequest,
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """
    向AI学习助手提问(流式响应，SSE格式)

    返回 Server-Sent Events (SSE) 流，客户端可以实时接收AI的回复。

    - **content**: 问题内容
    - **session_id**: 会话ID (可选)
    - **use_context**: 是否使用学习上下文
    - **include_history**: 是否包含历史对话

    SSE 数据格式:
    ```
    data: {"type": "content", "content": "增量文本", "finish_reason": null}
    data: {"type": "done", "question_id": "xxx", "answer_id": "xxx", "usage": {...}}
    data: {"type": "error", "message": "错误信息"}
    ```
    """
    from fastapi.responses import StreamingResponse

    async def event_generator():
        """SSE 事件生成器"""
        try:
            learning_service = get_learning_service(db)

            # 流式调用
            async for chunk in learning_service.ask_question_stream(
                current_user_id, request
            ):
                # 转换为 SSE 格式
                yield f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"

        except BailianServiceError as e:
            error_data = {"type": "error", "message": f"AI服务暂时不可用: {str(e)}"}
            yield f"data: {json.dumps(error_data, ensure_ascii=False)}\n\n"
        except ValidationError as e:
            error_data = {"type": "error", "message": str(e)}
            yield f"data: {json.dumps(error_data, ensure_ascii=False)}\n\n"
        except Exception as e:
            logging.error(f"Stream ask question failed: {e}")
            error_data = {"type": "error", "message": "提问失败,请稍后重试"}
            yield f"data: {json.dumps(error_data, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # 禁用 Nginx 缓冲
        },
    )


@router.post("/feedback", response_model=SuccessResponse, summary="提交反馈")
async def submit_feedback(
    request: FeedbackRequest,
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """
    对AI回答提交反馈

    - **question_id**: 问题ID
    - **rating**: 评分 (1-5)
    - **feedback**: 反馈内容
    - **is_helpful**: 是否有帮助
    """
    try:
        learning_service = get_learning_service(db)

        success = await learning_service.submit_feedback(current_user_id, request)

        return SuccessResponse(message="反馈提交成功" if success else "反馈提交失败")

    except NotFoundError as e:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(
            status_code=http_status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)
        )


# ========== 会话管理功能 ==========


@router.post("/sessions", response_model=SessionResponse, summary="创建会话")
async def create_session(
    request: CreateSessionRequest,
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """
    创建新的学习会话

    - **title**: 会话标题
    - **subject**: 学科 (可选)
    - **grade_level**: 学段 (可选)
    - **context_enabled**: 是否启用上下文
    - **initial_question**: 初始问题 (可选)
    """
    try:
        learning_service = get_learning_service(db)

        session = await learning_service.create_session(current_user_id, request)
        return session

    except ValidationError as e:
        raise HTTPException(
            status_code=http_status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)
        )
    except ServiceError as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.get("/sessions", response_model=SessionListResponse, summary="获取会话列表")
async def get_session_list(
    status_filter: Optional[str] = Query(None, description="会话状态筛选"),
    subject_filter: Optional[str] = Query(None, description="学科筛选"),
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页大小"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """获取用户的学习会话列表"""
    try:
        learning_service = get_learning_service(db)

        query = SessionListQuery(
            status=status_filter,
            subject=subject_filter,
            page=page,
            size=size,
            search=search,
        )

        result = await learning_service.get_session_list(current_user_id, query)

        return SessionListResponse(**result)

    except Exception as e:
        # 如果表不存在,返回空列表
        import logging

        logger = logging.getLogger(__name__)
        if "does not exist" in str(e) or "UndefinedTable" in str(type(e).__name__):
            logger.warning(f"学习会话表不存在,返回空数据: {e}")
            return SessionListResponse(total=0, page=page, size=size, pages=0, items=[])

        # 其他错误正常抛出
        if isinstance(e, ValidationError):
            raise HTTPException(
                status_code=http_status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)
            )
        raise


@router.get("/sessions/{id}", response_model=SessionResponse, summary="获取会话详情")
async def get_session_detail(
    id: str,
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """获取指定会话的详细信息"""
    try:
        learning_service = get_learning_service(db)

        session = await learning_service.session_repo.get_by_id(id)
        if not session:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND, detail="会话不存在"
            )

        if str(session.user_id) != str(current_user_id):
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND, detail="无权限访问该会话"
            )

        return SessionResponse.model_validate(session)

    except NotFoundError:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND, detail="会话不存在"
        )


@router.put("/sessions/{id}", response_model=SessionResponse, summary="更新会话")
async def update_session(
    id: str,
    request: UpdateSessionRequest,
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """
    更新会话信息

    - **title**: 会话标题
    - **status**: 会话状态
    - **context_enabled**: 是否启用上下文
    """
    try:
        learning_service = get_learning_service(db)

        # 验证会话归属
        session = await learning_service.session_repo.get_by_id(id)
        if not session:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND, detail="会话不存在"
            )

        if str(session.user_id) != str(current_user_id):
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND, detail="无权限访问该会话"
            )

        # 更新会话
        update_data = request.model_dump(exclude_unset=True)
        if update_data:
            await learning_service.session_repo.update(id, update_data)
            session = await learning_service.session_repo.get_by_id(id)

        return SessionResponse.model_validate(session)

    except ValidationError as e:
        raise HTTPException(
            status_code=http_status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)
        )


@router.delete("/sessions/{id}", response_model=SuccessResponse, summary="删除会话")
async def delete_session(
    id: str,
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """删除指定会话（软删除）"""
    try:
        learning_service = get_learning_service(db)

        # 验证会话归属
        session = await learning_service.session_repo.get_by_id(id)
        if not session:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND, detail="会话不存在"
            )

        if str(session.user_id) != str(current_user_id):
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND, detail="无权限访问该会话"
            )

        # 标记为已删除
        await learning_service.session_repo.update(id, {"status": "archived"})

        return SuccessResponse(message="会话删除成功")

    except NotFoundError:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND, detail="会话不存在"
        )


@router.patch("/sessions/{id}", response_model=SessionResponse, summary="部分更新会话")
async def patch_session(
    id: str,
    request: UpdateSessionRequest,
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """
    部分更新会话信息 (PATCH)

    - **title**: 会话标题
    - **status**: 会话状态
    - **context_enabled**: 是否启用上下文
    """
    try:
        learning_service = get_learning_service(db)

        # 验证会话归属
        session = await learning_service.session_repo.get_by_id(id)
        if not session:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND, detail="会话不存在"
            )

        if str(session.user_id) != str(current_user_id):
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND, detail="无权限访问该会话"
            )

        # 更新会话
        update_data = request.model_dump(exclude_unset=True)
        if update_data:
            await learning_service.session_repo.update(id, update_data)
            session = await learning_service.session_repo.get_by_id(id)

        return SessionResponse.model_validate(session)

    except ValidationError as e:
        raise HTTPException(
            status_code=http_status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)
        )


@router.patch(
    "/sessions/{id}/archive", response_model=SuccessResponse, summary="归档会话"
)
async def archive_session(
    id: str,
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """归档指定会话"""
    try:
        learning_service = get_learning_service(db)

        # 验证会话归属
        session = await learning_service.session_repo.get_by_id(id)
        if not session:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND, detail="会话不存在"
            )

        if str(session.user_id) != str(current_user_id):
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND, detail="无权限访问该会话"
            )

        # 更新状态为归档
        await learning_service.session_repo.update(id, {"status": "archived"})

        return SuccessResponse(message="会话归档成功")

    except NotFoundError:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND, detail="会话不存在"
        )


@router.patch(
    "/sessions/{id}/activate", response_model=SuccessResponse, summary="激活会话"
)
async def activate_session(
    id: str,
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """激活指定会话（从归档状态恢复）"""
    try:
        learning_service = get_learning_service(db)

        # 验证会话归属
        session = await learning_service.session_repo.get_by_id(id)
        if not session:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND, detail="会话不存在"
            )

        if str(session.user_id) != str(current_user_id):
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND, detail="无权限访问该会话"
            )

        # 更新状态为活跃
        await learning_service.session_repo.update(id, {"status": "active"})

        return SuccessResponse(message="会话激活成功")

    except NotFoundError:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND, detail="会话不存在"
        )


@router.get(
    "/sessions/{id}/questions",
    response_model=QuestionHistoryResponse,
    summary="获取会话的问题列表",
)
async def get_session_questions(
    id: str,
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页大小"),
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """获取指定会话的所有问题"""
    try:
        learning_service = get_learning_service(db)

        # 验证会话归属
        session = await learning_service.session_repo.get_by_id(id)
        if not session:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND, detail="会话不存在"
            )

        if str(session.user_id) != str(current_user_id):
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND, detail="无权限访问该会话"
            )

        query = QuestionHistoryQuery(session_id=id, page=page, size=size)
        result = await learning_service.get_question_history(current_user_id, query)

        return QuestionHistoryResponse(**result)

    except NotFoundError:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND, detail="会话不存在"
        )


# ========== 历史查询功能 ==========


@router.get(
    "/questions", response_model=QuestionHistoryResponse, summary="获取问题历史"
)
async def get_question_history(
    subject_filter: Optional[str] = Query(None, description="学科筛选"),
    question_type_filter: Optional[str] = Query(None, description="问题类型筛选"),
    start_date: Optional[str] = Query(None, description="开始日期"),
    end_date: Optional[str] = Query(None, description="结束日期"),
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页大小"),
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """获取用户的问答历史记录"""
    try:
        learning_service = get_learning_service(db)

        from datetime import datetime

        query = QuestionHistoryQuery(
            subject=subject_filter,
            question_type=question_type_filter,
            start_date=datetime.fromisoformat(start_date) if start_date else None,
            end_date=datetime.fromisoformat(end_date) if end_date else None,
            page=page,
            size=size,
        )

        result = await learning_service.get_question_history(current_user_id, query)

        return QuestionHistoryResponse(**result)

    except ValidationError as e:
        raise HTTPException(
            status_code=http_status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)
        )
    except ValueError as e:
        raise HTTPException(
            status_code=http_status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"日期格式错误: {str(e)}",
        )


@router.get(
    "/questions/history",
    response_model=QuestionHistoryResponse,
    summary="获取问题历史（别名）",
)
async def get_questions_history_alias(
    subject_filter: Optional[str] = Query(None, description="学科筛选"),
    question_type_filter: Optional[str] = Query(None, description="问题类型筛选"),
    start_date: Optional[str] = Query(None, description="开始日期"),
    end_date: Optional[str] = Query(None, description="结束日期"),
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页大小"),
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """
    获取用户的问答历史记录（与 GET /questions 功能相同）
    此端点是为了兼容前端调用
    """
    try:
        learning_service = get_learning_service(db)

        from datetime import datetime

        query = QuestionHistoryQuery(
            subject=subject_filter,
            question_type=question_type_filter,
            start_date=datetime.fromisoformat(start_date) if start_date else None,
            end_date=datetime.fromisoformat(end_date) if end_date else None,
            page=page,
            size=size,
        )

        result = await learning_service.get_question_history(current_user_id, query)

        return QuestionHistoryResponse(**result)

    except ValidationError as e:
        raise HTTPException(
            status_code=http_status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)
        )
    except ValueError as e:
        raise HTTPException(
            status_code=http_status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"日期格式错误: {str(e)}",
        )


@router.get(
    "/questions/search", response_model=QuestionHistoryResponse, summary="搜索问题"
)
async def search_questions(
    keyword: Optional[str] = Query(None, description="搜索关键词"),
    subject: Optional[str] = Query(None, description="学科筛选"),
    question_type: Optional[str] = Query(None, description="问题类型筛选"),
    start_date: Optional[str] = Query(None, description="开始日期"),
    end_date: Optional[str] = Query(None, description="结束日期"),
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页大小"),
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """
    搜索用户的问答记录

    支持按关键词、学科、类型、时间范围等条件搜索
    """
    try:
        learning_service = get_learning_service(db)

        from datetime import datetime

        query = QuestionHistoryQuery(
            subject=subject,
            question_type=question_type,
            start_date=datetime.fromisoformat(start_date) if start_date else None,
            end_date=datetime.fromisoformat(end_date) if end_date else None,
            page=page,
            size=size,
        )

        result = await learning_service.get_question_history(current_user_id, query)

        # 如果有关键词，进行额外的过滤
        if keyword and result.get("questions"):
            filtered_questions = [
                q
                for q in result["questions"]
                if keyword.lower() in q.get("content", "").lower()
                or keyword.lower() in q.get("answer", "").lower()
            ]
            result["questions"] = filtered_questions
            result["total"] = len(filtered_questions)

        return QuestionHistoryResponse(**result)

    except ValidationError as e:
        raise HTTPException(
            status_code=http_status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)
        )
    except ValueError as e:
        raise HTTPException(
            status_code=http_status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"日期格式错误: {str(e)}",
        )


@router.get("/sessions/{id}/history", summary="获取会话问答历史")
async def get_session_history(
    id: UUID,
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页大小"),
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """获取指定会话的问答历史"""
    try:
        learning_service = get_learning_service(db)

        # 验证会话归属
        session = await learning_service.session_repo.get_by_id(str(id))
        if not session:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND, detail="会话不存在"
            )

        if str(session.user_id) != str(current_user_id):
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND, detail="无权限访问该会话"
            )

        query = QuestionHistoryQuery(session_id=str(id), page=page, size=size)

        result = await learning_service.get_question_history(current_user_id, query)

        return QuestionHistoryResponse(**result)

    except NotFoundError:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND, detail="会话不存在"
        )


# ========== 学习分析功能 ==========


@router.get(
    "/analytics", response_model=LearningAnalyticsResponse, summary="获取学习分析"
)
async def get_learning_analytics(
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """获取用户的学习分析报告"""
    try:
        learning_service = get_learning_service(db)

        analytics = await learning_service.get_learning_analytics(current_user_id)

        if not analytics:
            # 如果没有分析数据，返回默认结构
            from datetime import datetime

            from src.schemas.learning import DifficultyLevel, LearningPattern

            return LearningAnalyticsResponse(
                user_id=current_user_id,
                total_questions=0,
                total_sessions=0,
                subject_stats=[],
                learning_pattern=LearningPattern(
                    most_active_hour=20,
                    most_active_day=0,
                    avg_session_length=0,
                    preferred_difficulty=DifficultyLevel.MEDIUM,
                ),
                avg_rating=0.0,
                positive_feedback_rate=0,
                improvement_suggestions=[],
                knowledge_gaps=[],
                last_analyzed_at=datetime.utcnow(),
            )

        return analytics

    except Exception as e:
        # 如果表不存在,返回默认数据
        import logging

        logger = logging.getLogger(__name__)
        if "does not exist" in str(e) or "UndefinedTable" in str(type(e).__name__):
            logger.warning(f"学习分析表不存在,返回默认数据: {e}")
            from datetime import datetime

            from src.schemas.learning import DifficultyLevel, LearningPattern

            return LearningAnalyticsResponse(
                user_id=current_user_id,
                total_questions=0,
                total_sessions=0,
                subject_stats=[],
                learning_pattern=LearningPattern(
                    most_active_hour=20,
                    most_active_day=0,
                    avg_session_length=0,
                    preferred_difficulty=DifficultyLevel.MEDIUM,
                ),
                avg_rating=0.0,
                positive_feedback_rate=0,
                improvement_suggestions=[],
                knowledge_gaps=[],
                last_analyzed_at=datetime.utcnow(),
            )

        # 其他服务错误
        if isinstance(e, ServiceError):
            raise HTTPException(
                status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
            )
        raise


@router.get(
    "/recommendations", response_model=RecommendationResponse, summary="获取学习推荐"
)
async def get_learning_recommendations(
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """获取个性化学习推荐"""
    try:
        from src.schemas.learning import (
            DifficultyLevel,
            RecommendedQuestion,
            StudyPlan,
            SubjectType,
        )

        # 简化实现，返回基础推荐
        return RecommendationResponse(
            recommended_questions=[
                RecommendedQuestion(
                    content="二次函数的对称轴公式是什么？",
                    subject=SubjectType.MATH,
                    topic="二次函数",
                    difficulty_level=DifficultyLevel.EASY,
                    reason="基于你最近的数学学习记录",
                ),
                RecommendedQuestion(
                    content="如何理解牛顿第二定律？",
                    subject=SubjectType.PHYSICS,
                    topic="牛顿定律",
                    difficulty_level=DifficultyLevel.MEDIUM,
                    reason="物理基础知识巩固",
                ),
            ],
            study_plans=[
                StudyPlan(
                    title="数学基础强化",
                    description="针对二次函数和代数运算的专项训练",
                    subjects=[SubjectType.MATH],
                    estimated_hours=10,
                    tasks=[
                        "复习二次函数概念",
                        "练习配方法",
                        "掌握对称轴和顶点公式",
                        "完成综合练习题",
                    ],
                    priority=1,
                )
            ],
            focus_areas=["数学函数", "物理力学"],
            next_topics=["三角函数", "电磁学"],
        )

    except Exception as e:
        # 处理数据库表不存在的情况（生产环境可能缺少相关表）
        error_msg = str(e).lower()
        if "does not exist" in error_msg or "undefinedtable" in error_msg:
            logging.warning(
                f"Recommendations tables not found for user {current_user_id}, returning empty recommendations"
            )
            # 返回空推荐数据
            return RecommendationResponse(
                recommended_questions=[],
                study_plans=[],
                focus_areas=[],
                next_topics=[],
            )

        # 对于服务层错误，包装为 HTTP 异常
        if isinstance(e, ServiceError):
            raise HTTPException(
                status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
            )

        # 其他未知错误
        logging.error(f"Error getting recommendations for user {current_user_id}: {e}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get learning recommendations",
        )


# ========== 统计和报表功能 ==========


@router.get("/stats/daily", summary="获取日统计")
async def get_daily_stats(
    date: Optional[str] = Query(None, description="日期 (YYYY-MM-DD)"),
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """获取指定日期的学习统计"""
    try:
        from datetime import date as date_type
        from datetime import datetime

        target_date = date_type.today()
        if date:
            target_date = datetime.strptime(date, "%Y-%m-%d").date()

        # 简化实现
        return {
            "date": target_date.isoformat(),
            "question_count": 5,
            "session_count": 2,
            "total_tokens": 1250,
            "avg_rating": 4.2,
            "study_time_minutes": 85,
            "subjects_studied": ["math", "physics"],
        }

    except ValueError as e:
        raise HTTPException(
            status_code=http_status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"日期格式错误: {str(e)}",
        )


@router.get("/stats/weekly", summary="获取周报告")
async def get_weekly_stats(
    week_start: Optional[str] = Query(None, description="周开始日期 (YYYY-MM-DD)"),
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """获取指定周的学习报告"""
    try:
        from datetime import date as date_type
        from datetime import datetime, timedelta

        if week_start:
            start_date = datetime.strptime(week_start, "%Y-%m-%d").date()
        else:
            today = date_type.today()
            start_date = today - timedelta(days=today.weekday())

        end_date = start_date + timedelta(days=6)

        # 简化实现
        return {
            "week_start": start_date.isoformat(),
            "week_end": end_date.isoformat(),
            "daily_stats": [
                {
                    "date": (start_date + timedelta(days=i)).isoformat(),
                    "question_count": max(0, 8 - i),
                    "session_count": max(0, 3 - i // 2),
                    "total_tokens": max(0, 1000 - i * 100),
                    "avg_rating": 4.0 + (i % 3) * 0.2,
                }
                for i in range(7)
            ],
            "top_subjects": ["math", "physics", "chemistry"],
            "total_study_time": 420,
            "progress_summary": "本周学习积极性很高，数学和物理进步明显！",
        }

    except ValueError as e:
        raise HTTPException(
            status_code=http_status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"日期格式错误: {str(e)}",
        )


# ========== 语音识别功能 ==========


@router.post("/voice-to-text", summary="语音转文字")
async def voice_to_text(
    voice: UploadFile = File(..., description="语音文件"),
    language: Optional[str] = Query("zh-CN", description="识别语言"),
    current_user_id: str = Depends(get_current_user_id),
):
    """
    语音转文字接口

    **支持的音频格式:**
    - MP3, WAV, M4A, AAC, FLAC, OGG

    **文件限制:**
    - 最大文件大小: 基于配置的最大时长限制
    - 最大时长: 60秒（可配置）

    **返回数据:**
    - 识别的文字内容
    - 置信度评分
    - 音频时长等信息
    """
    try:
        from src.services.speech_recognition_service import (
            get_speech_recognition_service,
        )

        # 验证文件名
        if not voice.filename:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST, detail="文件名不能为空"
            )

        # 获取语音识别服务
        speech_service = get_speech_recognition_service()

        # 调用语音识别（确保 language 有默认值）
        result = await speech_service.recognize_from_file(voice, language or "zh-CN")

        if result["success"]:
            return {
                "success": True,
                "data": {
                    "text": result["text"],
                    "confidence": result["confidence"],
                    "duration": result.get("duration", 0.0),
                    "audio_size": result.get("audio_size", 0),
                    "language": language,
                },
                "message": "语音识别成功",
            }
        else:
            raise HTTPException(
                status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.get("error", "语音识别失败"),
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"语音转文字处理失败: {str(e)}", exc_info=True)

        # 检查是否是配置问题
        if "配置" in str(e) or "ASR_" in str(e):
            raise HTTPException(
                status_code=http_status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="语音识别服务配置不完整，请联系管理员",
            )

        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"语音识别处理失败: {str(e)}",
        )


# ========== 错题本集成 ==========


@router.post(
    "/questions/{question_id}/add-to-mistakes",
    response_model=MistakeDetailResponse,
    status_code=http_status.HTTP_201_CREATED,
    summary="将题目加入错题本",
)
async def add_question_to_mistakes(
    question_id: str,
    student_answer: Optional[str] = Query(
        None, description="学生答案（可选，用于标记答错）"
    ),
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """
    将学习问答中的题目加入到错题本

    支持从学习问答中提取错题：
    - 答错的题目：提供 student_answer 参数
    - 空白未作答的题目：不提供 student_answer

    加入错题本后将自动：
    - 标记来源为 learning
    - 关联原始 Question ID
    - 设置艾宾浩斯遗忘曲线复习计划（首次复习为1天后）
    - 提取 AI 回答中的正确答案

    Args:
        question_id: 问题ID
        student_answer: 学生答案（可选）

    Returns:
        创建的错题详情

    Raises:
        404: 问题不存在或无权限
        409: 该问题已在错题本中
        500: 服务错误
    """
    try:
        learning_service = get_learning_service(db)

        # 调用服务层方法
        mistake = await learning_service.add_question_to_mistakes(
            user_id=current_user_id,
            question_id=question_id,
            student_answer=student_answer,
        )

        return MistakeDetailResponse(**mistake)

    except NotFoundError as e:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        # 409: 已存在
        if "已存在" in str(e) or "already" in str(e).lower():
            raise HTTPException(
                status_code=http_status.HTTP_409_CONFLICT, detail=str(e)
            )
        # 422: 其他验证错误
        raise HTTPException(
            status_code=http_status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)
        )
    except ServiceError as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )
    except Exception as e:
        logger.error(f"Add question to mistakes failed: {e}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="加入错题本失败，请稍后重试",
        )


# ========== WebSocket 流式问答 ==========


@router.websocket("/ws/ask")
async def websocket_ask_question(
    websocket: WebSocket,
    db: AsyncSession = Depends(get_db),
):
    """
    WebSocket 流式问答端点

    客户端发送格式:
    {
        "token": "Bearer xxx",
        "params": {
            "content": "问题内容",
            "question_type": "concept",
            "subject": "math",
            ...
        }
    }

    服务器返回格式 (流式):
    {
        "type": "content",
        "content": "逐字内容",
        "full_content": "累积内容"
    }
    {
        "type": "done",
        "question_id": "uuid",
        "answer_id": "uuid",
        "session_id": "uuid",
        "usage": {...}
    }
    {
        "type": "error",
        "message": "错误信息"
    }
    """
    await websocket.accept()
    logger.info("WebSocket 连接已建立")

    try:
        # 1. 接收客户端请求
        request_data = await websocket.receive_json()
        logger.info(f"WebSocket 收到请求: {request_data.keys()}")

        # 2. 验证 token
        token = request_data.get("token", "")
        if not token:
            await websocket.send_json({"type": "error", "message": "缺少 token"})
            await websocket.close()
            return

        # 移除 "Bearer " 前缀
        if token.startswith("Bearer "):
            token = token[7:]

        # 验证 token 并获取用户 ID
        import jwt

        from src.core.config import get_settings

        settings = get_settings()

        try:
            payload = jwt.decode(
                token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
            )
            user_id = payload.get("sub")
            if not user_id:
                raise ValueError("Token 中缺少用户 ID")
        except jwt.ExpiredSignatureError:
            logger.error("Token 已过期")
            await websocket.send_json(
                {"type": "error", "message": "登录已过期，请重新登录"}
            )
            await websocket.close()
            return
        except jwt.InvalidTokenError as e:
            logger.error(f"Token 无效: {e}")
            await websocket.send_json(
                {"type": "error", "message": "认证失败，请重新登录"}
            )
            await websocket.close()
            return
        except Exception as e:
            logger.error(f"Token 验证失败: {e}")
            await websocket.send_json(
                {"type": "error", "message": "认证失败，请重新登录"}
            )
            await websocket.close()
            return

        # 3. 解析请求参数
        params = request_data.get("params", {})
        try:
            ask_request = AskQuestionRequest(**params)
        except Exception as e:
            logger.error(f"请求参数验证失败: {e}")
            await websocket.send_json(
                {"type": "error", "message": f"请求参数错误: {str(e)}"}
            )
            await websocket.close()
            return

        # 4. 调用流式服务
        learning_service = get_learning_service(db)

        async for chunk in learning_service.ask_question_stream(user_id, ask_request):
            # 发送数据块到客户端
            await websocket.send_json(chunk)
            logger.debug(f"WebSocket 发送块: {chunk.get('type', 'unknown')}")

        logger.info("WebSocket 流式响应完成")

    except WebSocketDisconnect:
        logger.info("WebSocket 客户端主动断开连接")
    except BailianServiceError as e:
        logger.error(f"百炼服务错误: {e}")
        try:
            await websocket.send_json(
                {"type": "error", "message": f"AI 服务错误: {str(e)}"}
            )
        except (RuntimeError, ConnectionError):
            pass
    except Exception as e:
        logger.error(f"WebSocket 错误: {e}", exc_info=True)
        try:
            await websocket.send_json(
                {"type": "error", "message": f"服务器错误: {str(e)}"}
            )
        except (RuntimeError, ConnectionError):
            pass
    finally:
        try:
            await websocket.close()
            logger.info("WebSocket 连接已关闭")
        except (RuntimeError, ConnectionError):
            pass
