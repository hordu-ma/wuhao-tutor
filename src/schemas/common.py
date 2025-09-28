"""
通用响应Schema模型
包含API响应的通用数据结构
"""

from typing import Any, Optional, Dict, List, Generic, TypeVar
from datetime import datetime

from pydantic import BaseModel, Field
from pydantic import ConfigDict

T = TypeVar('T')


# ========== 基础响应模型 ==========

class BaseResponse(BaseModel):
    """基础响应模型"""
    success: bool = Field(default=True, description="请求是否成功")
    message: Optional[str] = Field(None, description="响应消息")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="响应时间")

    model_config = ConfigDict(
        json_encoders={
            datetime: lambda v: v.isoformat()
        }
    )


class SuccessResponse(BaseResponse):
    """成功响应模型"""
    success: bool = Field(default=True, description="请求成功")
    message: Optional[str] = Field(default="操作成功", description="成功消息")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": True,
                "message": "操作成功",
                "timestamp": "2024-01-27T10:30:00Z"
            }
        }
    )


class ErrorResponse(BaseResponse):
    """错误响应模型"""
    success: bool = Field(default=False, description="请求失败")
    error_code: Optional[str] = Field(None, description="错误代码")
    error_type: Optional[str] = Field(None, description="错误类型")
    details: Optional[Dict[str, Any]] = Field(None, description="错误详情")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": False,
                "message": "请求参数错误",
                "error_code": "VALIDATION_ERROR",
                "error_type": "ValidationError",
                "details": {"field": "phone", "issue": "格式不正确"},
                "timestamp": "2024-01-27T10:30:00Z"
            }
        }
    )


# ========== 数据响应模型 ==========

class DataResponse(BaseResponse, Generic[T]):
    """带数据的响应模型"""
    data: T = Field(..., description="响应数据")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": True,
                "message": "获取数据成功",
                "data": {"key": "value"},
                "timestamp": "2024-01-27T10:30:00Z"
            }
        }
    )


class ListResponse(BaseResponse, Generic[T]):
    """列表响应模型"""
    data: List[T] = Field(..., description="列表数据")
    total: int = Field(..., description="总数量")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": True,
                "message": "获取列表成功",
                "data": [{"id": 1, "name": "item1"}, {"id": 2, "name": "item2"}],
                "total": 2,
                "timestamp": "2024-01-27T10:30:00Z"
            }
        }
    )


# ========== 分页响应模型 ==========

class PaginationInfo(BaseModel):
    """分页信息"""
    total: int = Field(..., description="总记录数")
    page: int = Field(..., description="当前页码")
    size: int = Field(..., description="每页大小")
    pages: int = Field(..., description="总页数")
    has_prev: bool = Field(..., description="是否有上一页")
    has_next: bool = Field(..., description="是否有下一页")

    @classmethod
    def create(cls, total: int, page: int, size: int) -> 'PaginationInfo':
        """创建分页信息"""
        pages = (total + size - 1) // size if size > 0 else 1
        return cls(
            total=total,
            page=page,
            size=size,
            pages=pages,
            has_prev=page > 1,
            has_next=page < pages
        )


class PaginatedResponse(BaseResponse, Generic[T]):
    """分页响应模型"""
    data: List[T] = Field(..., description="分页数据")
    pagination: PaginationInfo = Field(..., description="分页信息")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": True,
                "message": "获取分页数据成功",
                "data": [{"id": 1, "name": "item1"}],
                "pagination": {
                    "total": 100,
                    "page": 1,
                    "size": 20,
                    "pages": 5,
                    "has_prev": False,
                    "has_next": True
                },
                "timestamp": "2024-01-27T10:30:00Z"
            }
        }
    )


# ========== 文件上传响应模型 ==========

class FileInfo(BaseModel):
    """文件信息"""
    filename: str = Field(..., description="原始文件名")
    file_url: str = Field(..., description="文件访问URL")
    file_size: int = Field(..., description="文件大小(字节)")
    content_type: str = Field(..., description="文件MIME类型")
    upload_time: datetime = Field(default_factory=datetime.utcnow, description="上传时间")

    model_config = ConfigDict(from_attributes=True)


class FileUploadResponse(DataResponse[FileInfo]):
    """文件上传响应"""
    message: Optional[str] = Field(default="文件上传成功", description="上传成功消息")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": True,
                "message": "文件上传成功",
                "data": {
                    "filename": "homework.jpg",
                    "file_url": "https://example.com/files/homework.jpg",
                    "file_size": 1048576,
                    "content_type": "image/jpeg",
                    "upload_time": "2024-01-27T10:30:00Z"
                },
                "timestamp": "2024-01-27T10:30:00Z"
            }
        }
    )


class MultiFileUploadResponse(BaseResponse):
    """多文件上传响应"""
    data: List[FileInfo] = Field(..., description="上传的文件列表")
    success_count: int = Field(..., description="成功上传数量")
    failed_count: int = Field(..., description="失败上传数量")
    failed_files: List[str] = Field(default_factory=list, description="失败的文件名列表")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": True,
                "message": "批量上传完成",
                "data": [
                    {
                        "filename": "file1.jpg",
                        "file_url": "https://example.com/files/file1.jpg",
                        "file_size": 1048576,
                        "content_type": "image/jpeg",
                        "upload_time": "2024-01-27T10:30:00Z"
                    }
                ],
                "success_count": 1,
                "failed_count": 0,
                "failed_files": [],
                "timestamp": "2024-01-27T10:30:00Z"
            }
        }
    )


# ========== 统计响应模型 ==========

class CountStats(BaseModel):
    """计数统计"""
    name: str = Field(..., description="统计项名称")
    count: int = Field(..., description="计数")
    percentage: Optional[float] = Field(None, description="百分比")


class TrendData(BaseModel):
    """趋势数据"""
    date: str = Field(..., description="日期")
    value: float = Field(..., description="数值")
    label: Optional[str] = Field(None, description="标签")


class StatsResponse(BaseResponse):
    """统计响应模型"""
    summary: Dict[str, Any] = Field(..., description="统计摘要")
    counts: List[CountStats] = Field(default_factory=list, description="计数统计")
    trends: List[TrendData] = Field(default_factory=list, description="趋势数据")
    charts: Dict[str, Any] = Field(default_factory=dict, description="图表数据")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": True,
                "message": "获取统计数据成功",
                "summary": {"total_users": 1000, "active_rate": 85.5},
                "counts": [
                    {"name": "学生", "count": 800, "percentage": 80.0},
                    {"name": "教师", "count": 200, "percentage": 20.0}
                ],
                "trends": [
                    {"date": "2024-01-20", "value": 950, "label": "用户数"},
                    {"date": "2024-01-21", "value": 975, "label": "用户数"}
                ],
                "charts": {"user_growth": []},
                "timestamp": "2024-01-27T10:30:00Z"
            }
        }
    )


# ========== 健康检查响应模型 ==========

class HealthStatus(BaseModel):
    """健康状态"""
    service: str = Field(..., description="服务名称")
    status: str = Field(..., description="状态")
    message: Optional[str] = Field(None, description="状态消息")
    response_time: Optional[float] = Field(None, description="响应时间(毫秒)")


class HealthCheckResponse(BaseResponse):
    """健康检查响应"""
    version: str = Field(..., description="应用版本")
    environment: str = Field(..., description="运行环境")
    uptime: float = Field(..., description="运行时长(秒)")
    services: List[HealthStatus] = Field(default_factory=list, description="服务状态列表")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": True,
                "message": "系统运行正常",
                "version": "0.1.0",
                "environment": "development",
                "uptime": 3600.0,
                "services": [
                    {
                        "service": "database",
                        "status": "healthy",
                        "message": "连接正常",
                        "response_time": 5.2
                    },
                    {
                        "service": "redis",
                        "status": "healthy",
                        "message": "连接正常",
                        "response_time": 1.8
                    }
                ],
                "timestamp": "2024-01-27T10:30:00Z"
            }
        }
    )


# ========== 操作结果响应模型 ==========

class OperationResult(BaseModel):
    """操作结果"""
    operation: str = Field(..., description="操作名称")
    success: bool = Field(..., description="是否成功")
    affected_count: int = Field(default=0, description="影响的记录数")
    details: Optional[Dict[str, Any]] = Field(None, description="操作详情")


class BatchOperationResponse(BaseResponse):
    """批量操作响应"""
    results: List[OperationResult] = Field(..., description="操作结果列表")
    success_count: int = Field(..., description="成功操作数")
    failed_count: int = Field(..., description="失败操作数")
    total_count: int = Field(..., description="总操作数")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": True,
                "message": "批量操作完成",
                "results": [
                    {
                        "operation": "create_user",
                        "success": True,
                        "affected_count": 1,
                        "details": {"user_id": "123"}
                    }
                ],
                "success_count": 8,
                "failed_count": 2,
                "total_count": 10,
                "timestamp": "2024-01-27T10:30:00Z"
            }
        }
    )


# ========== 导出响应模型 ==========

class ExportTask(BaseModel):
    """导出任务"""
    task_id: str = Field(..., description="任务ID")
    status: str = Field(..., description="任务状态")
    progress: int = Field(default=0, ge=0, le=100, description="进度百分比")
    download_url: Optional[str] = Field(None, description="下载链接")
    expires_at: Optional[datetime] = Field(None, description="链接过期时间")


class ExportResponse(DataResponse[ExportTask]):
    """导出响应"""
    message: Optional[str] = Field(default="导出任务已创建", description="任务创建消息")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": True,
                "message": "导出任务已创建",
                "data": {
                    "task_id": "export_123",
                    "status": "processing",
                    "progress": 25,
                    "download_url": None,
                    "expires_at": None
                },
                "timestamp": "2024-01-27T10:30:00Z"
            }
        }
    )
