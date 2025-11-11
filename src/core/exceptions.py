"""
项目异常处理模块

定义了所有自定义异常类，包括：
- 百炼AI服务相关异常
- 数据库操作异常
- 业务逻辑异常
- API相关异常
"""

from typing import Optional, Dict, Any


class BaseCustomException(Exception):
    """基础自定义异常类"""

    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.details = details or {}
        super().__init__(self.message)

    def to_dict(self) -> Dict[str, Any]:
        """将异常转换为字典格式"""
        return {
            "error_code": self.error_code,
            "message": self.message,
            "details": self.details,
        }


# ============================================================================
# 百炼AI服务相关异常
# ============================================================================


class BailianServiceError(BaseCustomException):
    """百炼服务基础异常"""

    pass


class AIServiceError(BaseCustomException):
    """AI服务相关异常（OCR、文件处理等）"""

    pass


# ============================================================================
# 认证和授权异常
# ============================================================================


class AuthenticationError(BaseCustomException):
    """认证失败异常"""

    def __init__(self, message: str = "认证失败"):
        super().__init__(message=message, error_code="AUTHENTICATION_ERROR")


class AuthorizationError(BaseCustomException):
    """授权失败异常"""

    def __init__(self, message: str = "权限不足"):
        super().__init__(message=message, error_code="AUTHORIZATION_ERROR")


class TokenExpiredError(AuthenticationError):
    """Token过期异常"""

    def __init__(self, message: str = "Token已过期"):
        super().__init__(message)
        self.error_code = "TOKEN_EXPIRED_ERROR"


class InvalidTokenError(AuthenticationError):
    """无效Token异常"""

    def __init__(self, message: str = "无效的Token"):
        super().__init__(message)
        self.error_code = "INVALID_TOKEN_ERROR"


class BailianAuthError(BailianServiceError):
    """百炼服务认证异常"""

    def __init__(self, message: str = "百炼API认证失败"):
        super().__init__(message=message, error_code="BAILIAN_AUTH_ERROR")


class BailianRateLimitError(BailianServiceError):
    """百炼服务限流异常"""

    def __init__(self, message: str = "百炼API调用频率过高", retry_after: int = 60):
        super().__init__(
            message=message,
            error_code="BAILIAN_RATE_LIMIT_ERROR",
            details={"retry_after": retry_after},
        )


class BailianTimeoutError(BailianServiceError):
    """百炼服务超时异常"""

    def __init__(self, message: str = "百炼API调用超时", timeout: int = 30):
        super().__init__(
            message=message,
            error_code="BAILIAN_TIMEOUT_ERROR",
            details={"timeout": timeout},
        )


class BailianQuotaExceededError(BailianServiceError):
    """百炼服务配额超限异常"""

    def __init__(self, message: str = "百炼API调用配额已用完"):
        super().__init__(message=message, error_code="BAILIAN_QUOTA_EXCEEDED_ERROR")


class BailianResponseParseError(BailianServiceError):
    """百炼服务响应解析异常"""

    def __init__(self, message: str = "百炼API响应格式错误", raw_response: str = ""):
        super().__init__(
            message=message,
            error_code="BAILIAN_RESPONSE_PARSE_ERROR",
            details={"raw_response": raw_response},
        )


# ============================================================================
# 作业相关异常
# ============================================================================


class HomeworkError(BaseCustomException):
    """作业相关基础异常"""

    pass


class HomeworkUploadError(HomeworkError):
    """作业上传异常"""

    def __init__(self, message: str = "作业上传失败", file_info: Optional[Dict] = None):
        super().__init__(
            message=message,
            error_code="HOMEWORK_UPLOAD_ERROR",
            details={"file_info": file_info} if file_info else {},
        )


class HomeworkCorrectionError(HomeworkError):
    """作业批改异常"""

    def __init__(
        self, message: str = "作业批改失败", homework_id: Optional[str] = None
    ):
        super().__init__(
            message=message,
            error_code="HOMEWORK_CORRECTION_ERROR",
            details={"homework_id": homework_id} if homework_id else {},
        )


class OCRProcessError(HomeworkError):
    """OCR处理异常"""

    def __init__(
        self, message: str = "图像文字识别失败", image_path: Optional[str] = None
    ):
        super().__init__(
            message=message,
            error_code="OCR_PROCESS_ERROR",
            details={"image_path": image_path} if image_path else {},
        )


# ============================================================================
# 学习问答相关异常
# ============================================================================


class LearningQAError(BaseCustomException):
    """学习问答基础异常"""

    pass


class QuestionProcessError(LearningQAError):
    """问题处理异常"""

    def __init__(self, message: str = "问题处理失败", question: Optional[str] = None):
        super().__init__(
            message=message,
            error_code="QUESTION_PROCESS_ERROR",
            details={"question": question} if question else {},
        )


class ContextLoadError(LearningQAError):
    """上下文加载异常"""

    def __init__(
        self, message: str = "学习上下文加载失败", user_id: Optional[str] = None
    ):
        super().__init__(
            message=message,
            error_code="CONTEXT_LOAD_ERROR",
            details={"user_id": user_id} if user_id else {},
        )


# ============================================================================
# 数据库相关异常
# ============================================================================


class DatabaseError(BaseCustomException):
    """数据库基础异常"""

    pass


class RecordNotFoundError(DatabaseError):
    """记录未找到异常"""

    def __init__(
        self, message: str = "记录未找到", resource: str = "", resource_id: str = ""
    ):
        super().__init__(
            message=message,
            error_code="RECORD_NOT_FOUND_ERROR",
            details={"resource": resource, "resource_id": resource_id},
        )


class RecordAlreadyExistsError(DatabaseError):
    """记录已存在异常"""

    def __init__(
        self, message: str = "记录已存在", resource: str = "", unique_field: str = ""
    ):
        super().__init__(
            message=message,
            error_code="RECORD_ALREADY_EXISTS_ERROR",
            details={"resource": resource, "unique_field": unique_field},
        )


class DatabaseConnectionError(DatabaseError):
    """数据库连接异常"""

    def __init__(self, message: str = "数据库连接失败"):
        super().__init__(message=message, error_code="DATABASE_CONNECTION_ERROR")


# ============================================================================
# 用户相关异常
# ============================================================================


class UserError(BaseCustomException):
    """用户相关基础异常"""

    pass


class UserNotFoundError(UserError):
    """用户未找到异常"""

    def __init__(self, message: str = "用户不存在", user_id: Optional[str] = None):
        super().__init__(
            message=message,
            error_code="USER_NOT_FOUND_ERROR",
            details={"user_id": user_id} if user_id else {},
        )


class UserAuthError(UserError):
    """用户认证异常"""

    def __init__(self, message: str = "用户认证失败"):
        super().__init__(message=message, error_code="USER_AUTH_ERROR")


class UserPermissionError(UserError):
    """用户权限异常"""

    def __init__(
        self, message: str = "用户权限不足", required_permission: Optional[str] = None
    ):
        super().__init__(
            message=message,
            error_code="USER_PERMISSION_ERROR",
            details=(
                {"required_permission": required_permission}
                if required_permission
                else {}
            ),
        )


# ============================================================================
# API相关异常
# ============================================================================


class APIError(BaseCustomException):
    """API基础异常"""

    pass


class ValidationError(APIError):
    """数据验证异常"""

    def __init__(
        self, message: str = "数据验证失败", field_errors: Optional[Dict] = None
    ):
        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            details={"field_errors": field_errors} if field_errors else {},
        )


class RateLimitError(APIError):
    """API限流异常"""

    def __init__(
        self, message: str = "API调用频率过高", limit: int = 100, window: int = 3600
    ):
        super().__init__(
            message=message,
            error_code="RATE_LIMIT_ERROR",
            details={"limit": limit, "window": window},
        )


class FileProcessError(APIError):
    """文件处理异常"""

    def __init__(
        self,
        message: str = "文件处理失败",
        file_name: Optional[str] = None,
        file_size: Optional[int] = None,
    ):
        details = {}
        if file_name:
            details["file_name"] = file_name
        if file_size:
            details["file_size"] = file_size

        super().__init__(
            message=message, error_code="FILE_PROCESS_ERROR", details=details
        )


# ============================================================================
# 配置相关异常
# ============================================================================


class ConfigurationError(BaseCustomException):
    """配置相关异常"""

    def __init__(self, message: str = "配置错误", config_key: Optional[str] = None):
        super().__init__(
            message=message,
            error_code="CONFIGURATION_ERROR",
            details={"config_key": config_key} if config_key else {},
        )


class EnvironmentError(ConfigurationError):
    """环境变量异常"""

    def __init__(self, message: str = "环境变量错误", env_var: Optional[str] = None):
        super().__init__(message=message, config_key=env_var)


# ============================================================================
# 缓存相关异常
# ============================================================================


class CacheError(BaseCustomException):
    """缓存基础异常"""

    pass


class CacheConnectionError(CacheError):
    """缓存连接异常"""

    def __init__(self, message: str = "缓存服务连接失败"):
        super().__init__(message=message, error_code="CACHE_CONNECTION_ERROR")


class CacheKeyNotFoundError(CacheError):
    """缓存键未找到异常"""

    def __init__(self, message: str = "缓存键不存在", cache_key: Optional[str] = None):
        super().__init__(
            message=message,
            error_code="CACHE_KEY_NOT_FOUND_ERROR",
            details={"cache_key": cache_key} if cache_key else {},
        )


# ============================================================================
# 异常映射表（用于错误码到HTTP状态码的映射）
# ============================================================================

EXCEPTION_HTTP_STATUS_MAP = {
    # 百炼服务异常 -> 502 Bad Gateway
    "BAILIAN_AUTH_ERROR": 502,
    "BAILIAN_RATE_LIMIT_ERROR": 503,  # Service Unavailable
    "BAILIAN_TIMEOUT_ERROR": 504,  # Gateway Timeout
    "BAILIAN_QUOTA_EXCEEDED_ERROR": 503,
    "BAILIAN_RESPONSE_PARSE_ERROR": 502,
    # 作业异常 -> 400 Bad Request
    "HOMEWORK_UPLOAD_ERROR": 400,
    "HOMEWORK_CORRECTION_ERROR": 500,
    "OCR_PROCESS_ERROR": 500,
    # 学习问答异常 -> 400 Bad Request
    "QUESTION_PROCESS_ERROR": 400,
    "CONTEXT_LOAD_ERROR": 500,
    # 数据库异常
    "RECORD_NOT_FOUND_ERROR": 404,
    "RECORD_ALREADY_EXISTS_ERROR": 409,  # Conflict
    "DATABASE_CONNECTION_ERROR": 500,
    # 用户异常
    "USER_NOT_FOUND_ERROR": 404,
    "USER_AUTH_ERROR": 401,  # Unauthorized
    "USER_PERMISSION_ERROR": 403,  # Forbidden
    # API异常
    "VALIDATION_ERROR": 400,
    "RATE_LIMIT_ERROR": 429,  # Too Many Requests
    "FILE_PROCESS_ERROR": 400,
    # 配置异常
    "CONFIGURATION_ERROR": 500,
    "ENVIRONMENT_ERROR": 500,
    # 缓存异常
    "CACHE_CONNECTION_ERROR": 500,
    "CACHE_KEY_NOT_FOUND_ERROR": 404,
}


# ============================================================================
# 通用异常别名（为了兼容性）
# ============================================================================

# 认证相关异常 - 使用原有的AuthenticationError类，不创建别名
ConflictError = RecordAlreadyExistsError
NotFoundError = RecordNotFoundError
ServiceError = BaseCustomException


def get_http_status_code(exception: BaseCustomException) -> int:
    """
    根据异常类型获取对应的HTTP状态码

    Args:
        exception: 自定义异常实例

    Returns:
        int: HTTP状态码
    """
    return EXCEPTION_HTTP_STATUS_MAP.get(exception.error_code, 500)
