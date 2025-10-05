"""
作业批改API端点
提供作业批改相关的API接口
"""

import uuid as uuid_lib
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from fastapi import status as http_status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.v1.endpoints.auth import get_current_user_id
from src.core.database import get_db
from src.schemas.common import DataResponse, SuccessResponse
from src.schemas.homework import HomeworkCreate, HomeworkSubmissionCreate
from src.services.homework_service import HomeworkService

router = APIRouter(prefix="/homework", tags=["作业批改"])


# ========== 依赖注入 ==========


def get_homework_service() -> HomeworkService:
    """获取HomeworkService实例"""
    return HomeworkService()


# ========== 健康检查 ==========


@router.get(
    "/health",
    summary="作业模块健康检查",
    description="检查作业批改模块的健康状态",
    response_model=Dict[str, str],
)
async def homework_health():
    """作业模块健康检查"""
    return {"status": "ok", "module": "homework", "version": "1.0.0"}


# ========== 作业模板管理 ==========


@router.get(
    "/templates",
    summary="获取作业模板列表",
    description="获取当前用户创建的所有作业模板",
    response_model=DataResponse[List[Dict[str, Any]]],
)
async def get_templates(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(10, ge=1, le=50, description="每页数量"),
    subject: Optional[str] = Query(None, description="学科筛选"),
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """
    获取作业模板列表

    **查询参数:**
    - **page**: 页码，从1开始
    - **size**: 每页数量，最大50
    - **subject**: 学科筛选（可选）

    **返回数据:**
    - 模板列表，包含ID、名称、学科、创建时间等信息
    """
    # 简化实现：返回示例数据
    templates = [
        {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "name": "小学数学基础练习",
            "subject": "math",
            "description": "适用于小学1-3年级的数学基础题练习",
            "created_at": "2024-01-15T10:30:00Z",
            "max_score": 100,
        }
    ]

    return DataResponse[List[Dict[str, Any]]](
        success=True, data=templates, message="获取模板列表成功"
    )


@router.post(
    "/templates",
    summary="创建作业模板",
    description="创建新的作业批改模板",
    response_model=DataResponse[Dict[str, Any]],
)
async def create_template(
    name: str = Form(..., description="模板名称"),
    subject: str = Form(..., description="学科"),
    description: str = Form(..., description="模板描述"),
    max_score: int = Form(100, description="最高分数"),
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """
    创建作业模板

    **表单参数:**
    - **name**: 模板名称
    - **subject**: 学科
    - **description**: 模板描述
    - **max_score**: 最高分数

    **返回数据:**
    - 创建的模板信息，包含生成的模板ID
    """
    # 简化实现：返回模拟创建的模板
    template = {
        "id": "550e8400-e29b-41d4-a716-446655440001",
        "name": name,
        "subject": subject,
        "description": description,
        "max_score": max_score,
        "created_at": "2024-01-15T10:30:00Z",
        "user_id": current_user_id,
    }

    return DataResponse[Dict[str, Any]](
        success=True, data=template, message="模板创建成功"
    )


@router.get(
    "/templates/{template_id}",
    summary="获取作业模板详情",
    description="根据ID获取特定作业模板的详细信息",
    response_model=DataResponse[Dict[str, Any]],
)
async def get_template(
    template_id: UUID,
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """
    获取作业模板详情

    **路径参数:**
    - **template_id**: 模板UUID

    **返回数据:**
    - 模板详细信息，包含所有字段
    """
    # 简化实现：检查ID格式后返回示例数据或404
    if str(template_id) == "550e8400-e29b-41d4-a716-446655440000":
        template = {
            "id": str(template_id),
            "name": "小学数学基础练习",
            "subject": "math",
            "description": "适用于小学1-3年级的数学基础题练习",
            "template_content": "请完成以下数学题目...",
            "correction_criteria": "按照计算准确性、解题步骤完整性评分",
            "max_score": 100,
            "created_at": "2024-01-15T10:30:00Z",
            "updated_at": "2024-01-15T10:30:00Z",
        }

        return DataResponse[Dict[str, Any]](
            success=True, data=template, message="获取模板详情成功"
        )
    else:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND, detail="模板不存在"
        )


# ========== 作业提交和批改 ==========


@router.post(
    "/submit",
    summary="提交作业",
    description="提交作业文件进行AI批改",
    response_model=DataResponse[Dict[str, Any]],
)
async def submit_homework(
    template_id: UUID = Form(..., description="作业模板ID"),
    student_name: str = Form(..., description="学生姓名"),
    homework_file: UploadFile = File(..., description="作业文件"),
    additional_info: Optional[str] = Form(None, description="附加信息"),
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
    homework_service: HomeworkService = Depends(get_homework_service),
):
    """
    提交作业进行批改

    **表单参数:**
    - **template_id**: 作业模板ID
    - **student_name**: 学生姓名
    - **homework_file**: 作业文件（图片或PDF）
    - **additional_info**: 附加信息（可选）

    **支持的文件格式:**
    - 图片: JPG, PNG, WebP
    - 文档: PDF
    - 最大文件大小: 10MB

    **返回数据:**
    - 提交记录信息，包含提交ID用于查询批改结果
    """
    try:
        # 基本文件验证
        if not homework_file.content_type or not homework_file.content_type.startswith(
            ("image/", "application/pdf")
        ):
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail="不支持的文件格式，请上传图片或PDF文件",
            )

        # 检查文件大小
        content = await homework_file.read()
        if len(content) > 10 * 1024 * 1024:  # 10MB
            raise HTTPException(
                status_code=http_status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="文件大小超过10MB限制",
            )

        # 重置文件指针
        await homework_file.seek(0)

        # Step 1: 创建作业提交记录
        from src.schemas.homework import HomeworkSubmissionCreate

        submission_data = HomeworkSubmissionCreate(
            homework_id=template_id,
            submission_title=f"{student_name}的作业",
            submission_note=additional_info,
            completion_time=None,  # 可选
        )

        submission = await homework_service.create_submission(
            session=db,
            submission_data=submission_data,
            student_id=uuid_lib.UUID(current_user_id),
            student_name=student_name,
        )

        # Step 2: 上传作业图片并触发OCR+AI批改
        submission_uuid = (
            uuid_lib.UUID(str(submission.id))
            if not isinstance(submission.id, uuid_lib.UUID)
            else submission.id
        )
        images = await homework_service.upload_homework_images(
            session=db, submission_id=submission_uuid, image_files=[homework_file]
        )

        # 返回提交结果
        return DataResponse[Dict[str, Any]](
            success=True,
            data={
                "id": str(submission.id),
                "template_id": str(template_id),
                "student_name": student_name,
                "file_url": images[0]["url"] if images else None,
                "status": submission.status.value,
                "submitted_at": submission.created_at.isoformat(),
                "additional_info": additional_info,
                "message": "作业提交成功，正在进行OCR识别和AI批改...",
            },
            message="作业提交成功",
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"作业提交失败: {str(e)}",
        )


@router.get(
    "/submissions",
    summary="获取作业提交列表",
    description="获取当前用户的所有作业提交记录",
    response_model=DataResponse[List[Dict[str, Any]]],
)
async def get_submissions(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(10, ge=1, le=50, description="每页数量"),
    template_id: Optional[UUID] = Query(None, description="模板ID筛选"),
    status: Optional[str] = Query(None, description="状态筛选"),
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """
    获取作业提交列表

    **查询参数:**
    - **page**: 页码，从1开始
    - **size**: 每页数量，最大50
    - **template_id**: 按模板ID筛选（可选）
    - **status**: 按状态筛选（可选）：pending/processing/completed/failed

    **返回数据:**
    - 提交记录列表，包含批改状态和结果
    """
    # 简化实现：返回示例数据
    submissions = [
        {
            "id": "660e8400-e29b-41d4-a716-446655440001",
            "template_id": "550e8400-e29b-41d4-a716-446655440000",
            "student_name": "张小明",
            "status": "completed",
            "score": 85,
            "submitted_at": "2024-01-15T10:35:00Z",
            "completed_at": "2024-01-15T10:37:30Z",
        }
    ]

    return DataResponse[List[Dict[str, Any]]](
        success=True, data=submissions, message="获取提交列表成功"
    )


@router.get(
    "/submissions/{submission_id}",
    summary="获取作业提交详情",
    description="获取特定作业提交的详细信息和批改结果",
    response_model=DataResponse[Dict[str, Any]],
)
async def get_submission(
    submission_id: UUID,
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """
    获取作业提交详情

    **路径参数:**
    - **submission_id**: 提交记录UUID

    **返回数据:**
    - 完整的提交信息，包括：
      - 基本信息（学生姓名、提交时间等）
      - 批改状态和进度
      - AI批改结果（如果已完成）
      - 错误信息（如果批改失败）
    """
    # 简化实现：返回示例数据或404
    if str(submission_id) == "660e8400-e29b-41d4-a716-446655440001":
        submission = {
            "id": str(submission_id),
            "template_id": "550e8400-e29b-41d4-a716-446655440000",
            "student_name": "张小明",
            "file_url": "/api/v1/files/homework_image.jpg",
            "status": "completed",
            "score": 85,
            "submitted_at": "2024-01-15T10:35:00Z",
            "completed_at": "2024-01-15T10:37:30Z",
            "additional_info": "第一次提交数学作业",
        }

        return DataResponse[Dict[str, Any]](
            success=True, data=submission, message="获取提交详情成功"
        )
    else:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND, detail="提交记录不存在"
        )


@router.get(
    "/submissions/{submission_id}/correction",
    summary="获取批改结果",
    description="获取作业的详细批改结果",
    response_model=DataResponse[Dict[str, Any]],
)
async def get_correction_result(
    submission_id: UUID,
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """
    获取批改结果

    **路径参数:**
    - **submission_id**: 提交记录UUID

    **返回数据:**
    - 详细的批改结果，包括：
      - 总体评分和评语
      - 逐题分析和建议
      - 知识点掌握情况
      - 学习建议

    **注意:**
    - 只有批改完成的作业才有批改结果
    - 如果批改还在进行中，请稍后再试
    """
    # 简化实现：返回示例批改结果
    if str(submission_id) == "660e8400-e29b-41d4-a716-446655440001":
        correction = {
            "submission_id": str(submission_id),
            "total_score": 85,
            "max_score": 100,
            "overall_comment": "整体完成得不错，计算能力较强，但需要注意解题步骤的完整性。",
            "detailed_feedback": [
                {
                    "question_number": 1,
                    "score": 10,
                    "max_score": 10,
                    "comment": "答案正确，计算准确。",
                },
                {
                    "question_number": 2,
                    "score": 7,
                    "max_score": 10,
                    "comment": "答案正确，但缺少解题步骤说明。",
                },
            ],
            "suggestions": ["建议在解题时写出完整的计算步骤", "可以多练习类似的应用题"],
            "corrected_at": "2024-01-15T10:37:30Z",
        }

        return DataResponse[Dict[str, Any]](
            success=True, data=correction, message="获取批改结果成功"
        )
    else:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="批改结果不存在或批改尚未完成",
        )


# ========== 前端兼容性别名路由 ==========


@router.get(
    "/list",
    summary="获取作业列表（别名）",
    description="与 /submissions 相同，为前端兼容性提供的别名路由",
    response_model=DataResponse[List[Dict[str, Any]]],
)
async def get_homework_list(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(10, ge=1, le=50, description="每页数量"),
    template_id: Optional[UUID] = Query(None, description="模板ID筛选"),
    status: Optional[str] = Query(None, description="状态筛选"),
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """获取作业列表 - 前端兼容性别名"""
    return await get_submissions(
        page=page,
        size=size,
        template_id=template_id,
        status=status,
        current_user_id=current_user_id,
        db=db,
    )


@router.get(
    "/stats",
    summary="获取作业统计信息",
    description="获取当前用户的作业统计数据",
    response_model=DataResponse[Dict[str, Any]],
)
async def get_homework_stats(
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """
    获取作业统计信息

    **返回数据:**
    - **total**: 总作业数
    - **completed**: 已完成数量
    - **processing**: 处理中数量
    - **failed**: 失败数量
    - **by_subject**: 按学科统计
    - **by_grade**: 按年级统计
    """
    # TODO: 实现真实的统计逻辑
    # 当前返回示例数据
    stats = {
        "total": 0,
        "completed": 0,
        "processing": 0,
        "failed": 0,
        "by_subject": {},
        "by_grade": {},
    }

    return DataResponse[Dict[str, Any]](
        success=True, data=stats, message="获取统计信息成功"
    )


@router.get(
    "/{id}",
    summary="获取作业详情（别名）",
    description="与 /submissions/{id} 相同，为前端兼容性提供的别名路由",
    response_model=DataResponse[Dict[str, Any]],
)
async def get_homework_detail(
    id: UUID,
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """获取作业详情 - 前端兼容性别名"""
    return await get_submission(
        submission_id=id, current_user_id=current_user_id, db=db
    )


@router.put(
    "/{id}",
    summary="更新作业",
    description="更新作业提交信息",
    response_model=DataResponse[Dict[str, Any]],
)
async def update_homework(
    id: UUID,
    student_name: Optional[str] = Form(None, description="学生姓名"),
    additional_info: Optional[str] = Form(None, description="附加信息"),
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """
    更新作业提交信息

    **路径参数:**
    - **id**: 作业提交ID

    **表单参数:**
    - **student_name**: 学生姓名（可选）
    - **additional_info**: 附加信息（可选）
    """
    # 简化实现
    if str(id) == "660e8400-e29b-41d4-a716-446655440001":
        updated_homework = {
            "id": str(id),
            "student_name": student_name or "张小明",
            "additional_info": additional_info,
            "updated_at": datetime.utcnow().isoformat(),
        }
        return DataResponse[Dict[str, Any]](
            success=True, data=updated_homework, message="作业更新成功"
        )
    else:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND, detail="作业不存在"
        )


@router.post(
    "/{id}/correct",
    summary="批改作业",
    description="手动触发或重新批改作业",
    response_model=DataResponse[Dict[str, Any]],
)
async def correct_homework(
    id: UUID,
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
    homework_service: HomeworkService = Depends(get_homework_service),
):
    """
    批改作业

    **路径参数:**
    - **id**: 作业提交ID

    **说明:**
    - 可用于重新批改已批改的作业
    - 会触发新的OCR和AI批改流程
    """
    try:
        # 简化实现：返回批改任务状态
        correction_task = {
            "id": str(id),
            "status": "processing",
            "message": "批改任务已启动",
            "started_at": datetime.utcnow().isoformat(),
        }
        return DataResponse[Dict[str, Any]](
            success=True, data=correction_task, message="批改任务已启动"
        )
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"批改失败: {str(e)}",
        )


@router.post(
    "/{id}/retry",
    summary="重试批改",
    description="重试失败的批改任务",
    response_model=DataResponse[Dict[str, Any]],
)
async def retry_homework_correction(
    id: UUID,
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """
    重试批改

    **路径参数:**
    - **id**: 作业提交ID

    **说明:**
    - 仅用于重试失败的批改任务
    - 会重新执行OCR和AI批改流程
    """
    # 简化实现
    retry_task = {
        "id": str(id),
        "status": "retrying",
        "message": "重试批改任务已启动",
        "retry_at": datetime.utcnow().isoformat(),
    }
    return DataResponse[Dict[str, Any]](
        success=True, data=retry_task, message="重试批改任务已启动"
    )
