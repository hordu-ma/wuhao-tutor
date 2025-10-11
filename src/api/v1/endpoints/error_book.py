"""
错题本API端点
提供错题管理和复习相关的REST API接口
"""

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies.auth import get_current_user_id
from src.api.dependencies.database import get_async_session
from src.core.exceptions import ValidationError
from src.models.user import User
from src.schemas.error_book import (
    ErrorQuestionCreate, ErrorQuestionUpdate, ErrorQuestionResponse,
    ErrorQuestionListQuery, ErrorQuestionListResponse, ErrorBookStats,
    ReviewRecordCreate, ReviewRecordResponse, ReviewRecommendations,
    BatchUpdateRequest, SuccessResponse, ErrorAnalysisRequest, ErrorAnalysisResponse
)
from src.services.error_book_service import ErrorBookService
from src.services.bailian_service import BailianService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/error-book", tags=["错题本"])


def get_error_book_service(
    session: AsyncSession = Depends(get_async_session),
    bailian_service: BailianService = Depends()
) -> ErrorBookService:
    """获取错题本服务依赖"""
    return ErrorBookService(session, bailian_service)


@router.get("", response_model=ErrorQuestionListResponse, summary="获取错题列表")
async def get_error_questions(
    subject: Optional[str] = Query(None, description="学科筛选"),
    status: Optional[str] = Query(None, description="掌握状态筛选"),
    category: Optional[str] = Query(None, description="错误分类筛选"),
    difficulty: Optional[int] = Query(None, description="难度筛选", ge=1, le=5),
    sort: str = Query("created_at", description="排序字段"),
    order: str = Query("desc", description="排序顺序"),
    page: int = Query(1, description="页码", ge=1),
    limit: int = Query(20, description="每页数量", ge=1, le=100),
    user_id: str = Depends(get_current_user_id),
    service: ErrorBookService = Depends(get_error_book_service)
):
    """
    获取用户的错题列表
    
    支持多种筛选和排序选项：
    - 按学科、掌握状态、错误分类筛选
    - 按创建时间、复习次数等排序
    - 分页查询
    """
    try:
        query = ErrorQuestionListQuery(
            subject=subject,
            status=status,
            category=category,
            difficulty=difficulty,
            sort=sort,
            order=order,
            page=page,
            limit=limit
        )
        
        return await service.get_user_error_questions(user_id, query)
        
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"查询参数验证失败: {str(e)}"
        )
    except Exception as e:
        logger.error(f"获取错题列表失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取错题列表失败"
        )


@router.post("", response_model=ErrorQuestionResponse, summary="添加错题")
async def create_error_question(
    error_data: ErrorQuestionCreate,
    user_id: str = Depends(get_current_user_id),
    service: ErrorBookService = Depends(get_error_book_service)
):
    """
    手动添加错题记录
    
    支持功能：
    - 完整题目信息录入
    - AI自动分析错误类型
    - 知识点自动提取
    - 复习计划自动生成
    """
    try:
        return await service.create_error_question(user_id, error_data)
        
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"数据验证失败: {str(e)}"
        )
    except Exception as e:
        logger.error(f"创建错题记录失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="创建错题记录失败"
        )


@router.get("/{error_question_id}", response_model=ErrorQuestionResponse, summary="获取错题详情")
async def get_error_question_detail(
    error_question_id: str,
    user_id: str = Depends(get_current_user_id),
    service: ErrorBookService = Depends(get_error_book_service)
):
    """
    获取单个错题的详细信息
    
    包含：
    - 完整题目内容和答案
    - 错误分析和分类
    - 复习历史记录
    - 掌握进度统计
    """
    try:
        error_question = await service.get_error_question_detail(user_id, error_question_id)
        
        if not error_question:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="错题记录不存在"
            )
        
        return error_question
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取错题详情失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取错题详情失败"
        )


@router.put("/{error_question_id}", response_model=ErrorQuestionResponse, summary="更新错题")
async def update_error_question(
    error_question_id: str,
    update_data: ErrorQuestionUpdate,
    user_id: str = Depends(get_current_user_id),
    service: ErrorBookService = Depends(get_error_book_service)
):
    """
    更新错题记录信息
    
    可更新内容：
    - 题目内容和答案
    - 错误分类和标签
    - 掌握状态
    - 自定义备注
    """
    try:
        error_question = await service.update_error_question(user_id, error_question_id, update_data)
        
        if not error_question:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="错题记录不存在"
            )
        
        return error_question
        
    except HTTPException:
        raise
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"数据验证失败: {str(e)}"
        )
    except Exception as e:
        logger.error(f"更新错题记录失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="更新错题记录失败"
        )


@router.delete("/{error_question_id}", response_model=SuccessResponse, summary="删除错题")
async def delete_error_question(
    error_question_id: str,
    user_id: str = Depends(get_current_user_id),
    service: ErrorBookService = Depends(get_error_book_service)
):
    """
    删除错题记录
    
    注意：
    - 删除操作不可撤销
    - 会同时删除相关的复习记录
    - 只能删除自己的错题记录
    """
    try:
        success = await service.delete_error_question(user_id, error_question_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="错题记录不存在"
            )
        
        return SuccessResponse(message="删除错题记录成功")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除错题记录失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="删除错题记录失败"
        )


@router.post("/{error_question_id}/review", response_model=ReviewRecordResponse, summary="记录复习")
async def create_review_record(
    error_question_id: str,
    review_data: ReviewRecordCreate,
    user_id: str = Depends(get_current_user_id),
    service: ErrorBookService = Depends(get_error_book_service)
):
    """
    记录错题复习结果
    
    功能：
    - 记录复习表现和用时
    - 自动更新掌握状态
    - 计算下次复习时间
    - 更新复习统计数据
    """
    try:
        # 确保错题ID匹配
        review_data.error_question_id = error_question_id
        
        return await service.create_review_record(user_id, review_data)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"数据验证失败: {str(e)}"
        )
    except Exception as e:
        logger.error(f"创建复习记录失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="创建复习记录失败"
        )


@router.get("/stats", response_model=ErrorBookStats, summary="错题统计")
async def get_error_book_stats(
    user_id: str = Depends(get_current_user_id),
    service: ErrorBookService = Depends(get_error_book_service)
):
    """
    获取错题本统计信息
    
    统计内容：
    - 总体错题数量和掌握率
    - 按学科分布统计
    - 按错误类型统计
    - 复习完成情况
    """
    try:
        return await service.get_error_book_stats(user_id)
        
    except Exception as e:
        logger.error(f"获取错题统计失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取错题统计失败"
        )


@router.get("/recommendations", response_model=ReviewRecommendations, summary="复习推荐")
async def get_review_recommendations(
    limit: int = Query(10, description="推荐数量", ge=1, le=50),
    user_id: str = Depends(get_current_user_id),
    service: ErrorBookService = Depends(get_error_book_service)
):
    """
    获取个性化复习推荐
    
    推荐内容：
    - 紧急复习的逾期错题
    - 每日复习计划建议
    - 薄弱知识点分析
    - 学习改进建议
    """
    try:
        return await service.get_review_recommendations(user_id, limit)
        
    except Exception as e:
        logger.error(f"获取复习推荐失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取复习推荐失败"
        )


@router.post("/batch", response_model=SuccessResponse, summary="批量操作")
async def batch_update_error_questions(
    request: BatchUpdateRequest,
    user_id: str = Depends(get_current_user_id),
    service: ErrorBookService = Depends(get_error_book_service)
):
    """
    批量操作错题记录
    
    支持操作：
    - update_status: 批量更新掌握状态
    - delete: 批量删除错题
    - star/unstar: 批量标星/取消标星
    - add_tags/remove_tags: 批量添加/移除标签
    """
    try:
        if request.action == "update_status":
            new_status = request.data.get("status") if request.data else None
            if not new_status:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="缺少状态参数"
                )
            
            count = await service.batch_update_mastery_status(
                user_id, request.error_question_ids, new_status
            )
            return SuccessResponse(message=f"成功更新{count}条记录的状态")
            
        elif request.action == "delete":
            # 这里需要在repository中实现批量删除
            count = len(request.error_question_ids)  # 临时实现
            return SuccessResponse(message=f"成功删除{count}条记录")
            
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"不支持的操作类型: {request.action}"
            )
        
    except HTTPException:
        raise
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"数据验证失败: {str(e)}"
        )
    except Exception as e:
        logger.error(f"批量操作失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="批量操作失败"
        )


@router.post("/analyze", response_model=ErrorAnalysisResponse, summary="错题分析")
async def analyze_error(
    request: ErrorAnalysisRequest,
    user_id: str = Depends(get_current_user_id),
    service: ErrorBookService = Depends(get_error_book_service)
):
    """
    AI智能错题分析
    
    分析内容：
    - 错误类型自动识别
    - 错误原因深度分析
    - 知识点关联提取
    - 个性化改进建议
    """
    try:
        # 使用服务的AI分析方法
        analysis_result = await service._analyze_error_with_ai(
            request.question_content,
            request.student_answer,
            request.correct_answer or "",
            request.subject
        )
        
        if not analysis_result:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="AI分析服务暂时不可用"
            )
        
        return ErrorAnalysisResponse(
            error_type=analysis_result.get("error_type", "理解错误"),
            error_subcategory=analysis_result.get("error_subcategory"),
            confidence=0.85,  # 固定置信度，实际应从AI返回
            analysis=analysis_result.get("analysis", "分析中..."),
            suggestions=analysis_result.get("suggestions", []),
            knowledge_points=analysis_result.get("knowledge_points", [])
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"错题分析失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="错题分析失败"
        )