"""
作业API兼容性端点
为保持与前端的兼容性，提供前端期望的API路径
"""

from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi import status as http_status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.v1.endpoints.auth import get_current_user_id
from src.core.database import get_db
from src.core.logging import get_logger
from src.schemas.common import DataResponse
from src.services.homework_service import HomeworkService, get_homework_service

logger = get_logger(__name__)

router = APIRouter(prefix="/homework", tags=["homework-compatibility"])


@router.get(
    "/list",
    summary="获取作业列表 (兼容性端点)",
    description="前端兼容性端点，重定向到submissions",
    response_model=DataResponse[Dict[str, Any]],
)
async def get_homework_list_compatibility(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页大小"),
    subject: Optional[str] = Query(None, description="学科过滤"),
    grade_level: Optional[str] = Query(None, description="年级过滤"),
    status: Optional[str] = Query(None, description="状态过滤"),
    start_date: Optional[str] = Query(None, description="开始日期"),
    end_date: Optional[str] = Query(None, description="结束日期"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
    homework_service: HomeworkService = Depends(get_homework_service),
):
    """
    前端兼容性端点：获取作业列表

    **兼容性说明:**
    - 此端点保持与前端期望的API路径一致
    - 内部调用真实的submissions端点
    - 数据格式转换为前端期望的格式
    """
    try:
        # 调用真实的服务获取数据
        from src.api.v1.endpoints.homework import get_submissions

        # 重新包装参数为真实端点期望的格式
        result = await get_submissions(
            page=page,
            size=page_size,
            status=status,
            subject=subject,
            homework_type=None,  # 前端兼容性映射
            current_user_id=current_user_id,
            db=db,
            homework_service=homework_service,
        )

        # 转换为前端期望的格式
        if result.success and result.data:
            converted_data = {
                "items": result.data.get("items", []),
                "total": result.data.get("total", 0),
                "page": result.data.get("page", page),
                "page_size": result.data.get("size", page_size),
                "total_pages": result.data.get("total_pages", 1),
            }

            return DataResponse[Dict[str, Any]](
                success=True, data=converted_data, message=result.message
            )
        else:
            return result

    except Exception as e:
        logger.error(f"获取作业列表失败 (兼容性端点): {e}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取作业列表失败: {str(e)}",
        )


@router.get(
    "/{homework_id}",
    summary="获取作业详情 (兼容性端点)",
    description="前端兼容性端点，重定向到submissions/{id}",
    response_model=DataResponse[Dict[str, Any]],
)
async def get_homework_compatibility(
    homework_id: str,
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
    homework_service: HomeworkService = Depends(get_homework_service),
):
    """
    前端兼容性端点：获取作业详情

    **兼容性说明:**
    - 此端点保持与前端期望的API路径一致
    - 内部调用真实的submission详情端点
    """
    try:
        # 调用真实的服务获取数据
        from src.api.v1.endpoints.homework import get_submission

        # 转换ID参数
        try:
            submission_id = UUID(homework_id)
        except ValueError:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST, detail="无效的作业ID格式"
            )

        result = await get_submission(
            submission_id=submission_id,
            current_user_id=current_user_id,
            db=db,
            homework_service=homework_service,
        )

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取作业详情失败 (兼容性端点): {e}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取作业详情失败: {str(e)}",
        )


@router.post(
    "/{homework_id}/correct",
    summary="开始批改作业 (兼容性端点)",
    description="前端兼容性端点，触发作业批改",
    response_model=DataResponse[Dict[str, Any]],
)
async def correct_homework_compatibility(
    homework_id: str,
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
    homework_service: HomeworkService = Depends(get_homework_service),
):
    """
    前端兼容性端点：开始批改作业

    **兼容性说明:**
    - 此端点保持与前端期望的API路径一致
    - 内部可能需要调用批改服务或返回批改结果
    """
    try:
        # 转换ID参数
        try:
            submission_id = UUID(homework_id)
        except ValueError:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST, detail="无效的作业ID格式"
            )

        # 首先检查作业是否存在
        submission = await homework_service.get_submission_with_details(
            session=db, submission_id=submission_id
        )

        if not submission:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND, detail="作业不存在"
            )

        # 权限验证
        if str(getattr(submission, "student_id", "")) != current_user_id:
            raise HTTPException(
                status_code=http_status.HTTP_403_FORBIDDEN, detail="无权批改该作业"
            )

        # 检查是否已经有批改结果
        from src.api.v1.endpoints.homework import get_correction_result

        try:
            correction_result = await get_correction_result(
                submission_id=submission_id,
                format_type="json",
                current_user_id=current_user_id,
                db=db,
                homework_service=homework_service,
            )

            if correction_result.success:
                return DataResponse[Dict[str, Any]](
                    success=True, data=correction_result.data, message="批改已完成"
                )
        except:
            pass

        # 如果没有批改结果，返回处理中状态
        return DataResponse[Dict[str, Any]](
            success=True,
            data={
                "status": "processing",
                "message": "作业正在批改中，请稍后查看结果",
                "submission_id": homework_id,
            },
            message="批改请求已提交",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"批改作业失败 (兼容性端点): {e}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"批改作业失败: {str(e)}",
        )


@router.get(
    "/{homework_id}/ocr",
    summary="获取OCR识别结果 (兼容性端点)",
    description="前端兼容性端点，获取OCR结果",
    response_model=DataResponse[Dict[str, Any]],
)
async def get_ocr_result_compatibility(
    homework_id: str,
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
    homework_service: HomeworkService = Depends(get_homework_service),
):
    """
    前端兼容性端点：获取OCR识别结果
    """
    try:
        # 转换ID参数
        try:
            submission_id = UUID(homework_id)
        except ValueError:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST, detail="无效的作业ID格式"
            )

        # 获取提交详情
        submission = await homework_service.get_submission_with_details(
            session=db, submission_id=submission_id
        )

        if not submission:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND, detail="作业不存在"
            )

        # 权限验证
        if str(getattr(submission, "student_id", "")) != current_user_id:
            raise HTTPException(
                status_code=http_status.HTTP_403_FORBIDDEN,
                detail="无权访问该作业的OCR结果",
            )

        # 从AI批改数据中提取OCR结果
        ai_review_data = getattr(submission, "ai_review_data", {})
        ocr_data = ai_review_data.get("ocr_result", {})

        return DataResponse[Dict[str, Any]](
            success=True,
            data={
                "ocr_text": ocr_data.get("text", ""),
                "confidence": ocr_data.get("confidence", 0.0),
                "processing_time": ocr_data.get("processing_time", 0),
                "detected_language": ocr_data.get("language", "zh"),
                "word_count": (
                    len(ocr_data.get("text", "").split()) if ocr_data.get("text") else 0
                ),
            },
            message="获取OCR结果成功",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取OCR结果失败 (兼容性端点): {e}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取OCR结果失败: {str(e)}",
        )
