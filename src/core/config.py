"""
配置管理模块
基于 Pydantic Settings 的环境配置系统
"""

import secrets
from typing import Any, Dict, List, Optional, Union

from pydantic import AnyHttpUrl, HttpUrl, PostgresDsn, field_validator, model_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """应用程序配置"""

    # 应用基础配置
    PROJECT_NAME: str = "五好伴学"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = secrets.token_urlsafe(32)
    ENVIRONMENT: str = "development"

    # 服务器配置
    HOST: str = "127.0.0.1"
    PORT: int = 8000
    DEBUG: bool = False
    BASE_URL: str = "http://localhost:8000"  # 基础URL，用于生成完整的文件访问链接

    # 安全配置
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8天
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 30  # 30天
    ALGORITHM: str = "HS256"

    # CORS配置
    BACKEND_CORS_ORIGINS: List[str] = []  # 数据库配置
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = ""
    POSTGRES_DB: str = "wuhao_tutor"
    POSTGRES_PORT: str = "5432"
    SQLALCHEMY_DATABASE_URI: Optional[Union[PostgresDsn, str]] = None

    @model_validator(mode="after")
    def assemble_db_connection(self) -> "Settings":
        if isinstance(self.SQLALCHEMY_DATABASE_URI, str):
            return self

        self.SQLALCHEMY_DATABASE_URI = PostgresDsn.build(
            scheme="postgresql+asyncpg",
            username=self.POSTGRES_USER,
            password=self.POSTGRES_PASSWORD,
            host=self.POSTGRES_SERVER,
            port=int(self.POSTGRES_PORT),
            path=f"/{self.POSTGRES_DB or ''}",
        )
        return self

    # Redis配置
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: Optional[str] = None
    REDIS_DB: int = 0

    # 日志配置
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"  # json 或 console

    # 阿里云百炼智能体配置
    BAILIAN_APPLICATION_ID: str = ""
    BAILIAN_API_KEY: str = ""
    BAILIAN_BASE_URL: str = "https://dashscope.aliyuncs.com/api/v1"
    BAILIAN_TIMEOUT: int = 120  # 提高到120秒以支持图片OCR和AI分析
    BAILIAN_MAX_RETRIES: int = 3

    # 阿里云基础配置
    ALICLOUD_ACCESS_KEY_ID: Optional[str] = None
    ALICLOUD_ACCESS_KEY_SECRET: Optional[str] = None
    ALICLOUD_REGION: str = "cn-hangzhou"

    # 语音识别服务配置
    ASR_ENABLED: bool = True
    ASR_APP_KEY: Optional[str] = None  # 语音识别应用Key
    ASR_ACCESS_KEY_ID: Optional[str] = None  # 阿里云AccessKey ID
    ASR_ACCESS_KEY_SECRET: Optional[str] = None  # 阿里云AccessKey Secret
    ASR_ENDPOINT: str = "https://nls-gateway-cn-shanghai.aliyuncs.com/stream/v1/asr"
    ASR_FORMAT: str = "mp3"  # 音频格式
    ASR_SAMPLE_RATE: int = 16000  # 采样率
    ASR_ENABLE_INTERMEDIATE_RESULT: bool = False  # 是否返回中间结果
    ASR_ENABLE_PUNCTUATION_PREDICTION: bool = True  # 是否开启智能断句
    ASR_ENABLE_INVERSE_TEXT_NORMALIZATION: bool = True  # 是否开启ITN
    ASR_MAX_AUDIO_DURATION: int = 60  # 最大音频时长（秒）

    # 文件存储配置
    OSS_BUCKET_NAME: str = "wuhao-tutor-files"
    OSS_ENDPOINT: str = "oss-cn-hangzhou.aliyuncs.com"
    OSS_ACCESS_KEY_ID: Optional[str] = None
    OSS_ACCESS_KEY_SECRET: Optional[str] = None
    UPLOAD_MAX_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_EXTENSIONS: List[str] = [".jpg", ".jpeg", ".png", ".pdf", ".webp"]
    UPLOAD_DIR: str = "./uploads"  # 文件上传目录

    # 短信服务配置
    SMS_ACCESS_KEY_ID: Optional[str] = None
    SMS_ACCESS_KEY_SECRET: Optional[str] = None
    SMS_SIGN_NAME: str = "五好伴学"
    SMS_TEMPLATE_CODE: str = "SMS_123456789"

    # 微信配置
    WECHAT_APP_ID: Optional[str] = None
    WECHAT_APP_SECRET: Optional[str] = None
    WECHAT_MINI_PROGRAM_APP_ID: Optional[str] = None
    WECHAT_MINI_PROGRAM_APP_SECRET: Optional[str] = None

    # 业务配置
    DEFAULT_USER_ROLE: str = "student"
    MAX_RETRY_ATTEMPTS: int = 3
    REVIEW_INTERVALS: List[int] = [1, 1, 2, 4, 7, 15, 30]  # 艾宾浩斯间隔（天）

    # AI服务配置
    AI_CACHE_ENABLED: bool = True
    AI_CACHE_TTL: int = 3600  # 1小时
    AI_MAX_TOKENS: int = 1500
    AI_TEMPERATURE: float = 0.7
    AI_TOP_P: float = 0.8

    # OCR配置
    OCR_ENABLED: bool = True
    OCR_LANGUAGE: str = "chi_sim+eng"  # 中文简体+英文
    OCR_CONFIDENCE_THRESHOLD: float = 0.6

    # 监控配置
    ENABLE_METRICS: bool = True
    METRICS_PORT: int = 9090

    # 性能监控配置
    SLOW_QUERY_THRESHOLD: float = 1.0  # 慢查询阈值（秒）
    MAX_SLOW_QUERIES: int = 100  # 最大慢查询记录数
    QUERY_CACHE_TTL: int = 300  # 查询缓存TTL（秒）
    MAX_CACHE_SIZE: int = 1000  # 最大缓存条目数
    METRICS_COLLECTION_INTERVAL: int = 60  # 指标收集间隔（秒）

    # 限流配置
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_PER_IP: int = 100  # 每IP每分钟请求限制
    RATE_LIMIT_PER_USER: int = 50  # 每用户每分钟请求限制
    RATE_LIMIT_AI_SERVICE: int = 20  # AI服务每分钟请求限制
    RATE_LIMIT_LOGIN: int = 10  # 登录端点每分钟请求限制

    # 缓存配置
    CACHE_ENABLED: bool = True
    CACHE_DEFAULT_TTL: int = 300  # 默认缓存TTL（秒）
    CACHE_MAX_SIZE: int = 10000  # 最大缓存大小

    # 自动错题识别配置
    AUTO_MISTAKE_DETECTION_ENABLED: bool = True  # 是否启用自动错题识别
    AUTO_MISTAKE_MIN_CONFIDENCE: float = (
        0.80  # 🛠️ 提高阈值：自动识别置信度阈值（0.0-1.0）避免误判
    )
    AUTO_MISTAKE_REQUIRE_IMAGE: bool = False  # 是否要求必须有图片才创建错题

    # 加密配置
    ENCRYPTION_KEY: Optional[str] = None  # 对称加密密钥

    class Config:
        env_file = ".env"
        case_sensitive = True


class DevelopmentSettings(Settings):
    """开发环境配置"""

    DEBUG: bool = True
    LOG_LEVEL: str = "DEBUG"
    POSTGRES_DB: str = "wuhao_tutor_dev"

    # 开发环境默认CORS配置（如果.env中没有指定）
    # 注意：.env文件中的配置会覆盖这里的默认值
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",  # Vue.js 开发服务器
        "http://127.0.0.1:3000",
        "http://localhost:5173",  # Vite 开发服务器
        "http://127.0.0.1:5173",
        "http://localhost:8080",  # 其他开发服务器
    ]

    # 开发环境使用SQLite
    SQLALCHEMY_DATABASE_URI: Optional[Union[PostgresDsn, str]] = (
        "sqlite+aiosqlite:///./wuhao_tutor_dev.db"
    )

    # 开发环境宽松的限流配置
    RATE_LIMIT_PER_IP: int = 1000
    RATE_LIMIT_PER_USER: int = 500
    SLOW_QUERY_THRESHOLD: float = 2.0  # 开发环境更宽松的慢查询阈值


class TestingSettings(Settings):
    """测试环境配置"""

    DEBUG: bool = True
    LOG_LEVEL: str = "DEBUG"
    POSTGRES_DB: str = "wuhao_tutor_test"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 5  # 测试用短过期时间

    # 测试环境CORS配置（避免解析.env文件出错）
    BACKEND_CORS_ORIGINS: List[str] = []

    # 测试环境使用内存SQLite
    SQLALCHEMY_DATABASE_URI: Optional[Union[PostgresDsn, str]] = (
        "sqlite+aiosqlite:///:memory:"
    )

    # 测试环境禁用某些功能
    ENABLE_METRICS: bool = False
    RATE_LIMIT_ENABLED: bool = False
    CACHE_ENABLED: bool = False

    model_config = {"env_file": None}  # 测试环境不读取.env文件


class ProductionSettings(Settings):
    """生产环境配置"""

    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    AI_CACHE_ENABLED: bool = True

    # 生产环境严格的性能配置
    SLOW_QUERY_THRESHOLD: float = 0.5  # 更严格的慢查询阈值
    # 🔧 [优化 v2] 再次放宽限流配置，解决小程序并发请求场景
    RATE_LIMIT_PER_IP: int = 500  # 200 → 500（每IP每分钟请求限制）
    RATE_LIMIT_PER_USER: int = 200  # 100 → 200（每用户每分钟请求限制）
    RATE_LIMIT_AI_SERVICE: int = 30  # 10 → 30（AI服务每分钟请求限制，保持不变）

    # 生产环境必需配置验证
    @field_validator("SECRET_KEY", mode="before")
    @classmethod
    def secret_key_must_be_set(cls, v: str) -> str:
        if not v or len(v) < 32:
            raise ValueError("SECRET_KEY must be set and at least 32 characters")
        return v

    @field_validator("BAILIAN_API_KEY", mode="before")
    @classmethod
    def bailian_api_key_must_be_set(cls, v: str) -> str:
        if not v or not v.startswith("sk-"):
            raise ValueError("BAILIAN_API_KEY must be set and start with 'sk-'")
        return v


def get_settings() -> Settings:
    """
    获取配置实例
    根据环境变量 ENVIRONMENT 返回对应配置
    """
    import os

    from dotenv import load_dotenv

    environment = os.getenv("ENVIRONMENT", "development").lower()

    # 根据环境加载对应的 .env 文件
    if environment == "production":
        load_dotenv(".env.production", override=True)
        return ProductionSettings()
    elif environment == "testing":
        load_dotenv(".env.testing", override=True)
        return TestingSettings()
    else:
        load_dotenv(".env", override=False)
        return DevelopmentSettings()


# 全局配置实例
settings = get_settings()
