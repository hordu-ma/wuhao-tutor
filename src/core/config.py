"""
配置管理模块
基于 Pydantic Settings 的环境配置系统
"""

import secrets
from typing import Any, Dict, List, Optional, Union

from pydantic import AnyHttpUrl, field_validator, model_validator, HttpUrl, PostgresDsn
from pydantic_settings import BaseSettings
from typing import Union


class Settings(BaseSettings):
    """应用程序配置"""
    
    # 应用基础配置
    PROJECT_NAME: str = "五好伴学"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = secrets.token_urlsafe(32)
    
    # 服务器配置
    HOST: str = "127.0.0.1"
    PORT: int = 8000
    DEBUG: bool = False
    
    # 安全配置
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8天
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 30  # 30天
    ALGORITHM: str = "HS256"
    
    # CORS配置
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = []
    
    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)
    
    # 数据库配置
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = ""
    POSTGRES_DB: str = "wuhao_tutor"
    POSTGRES_PORT: str = "5432"
    SQLALCHEMY_DATABASE_URI: Optional[PostgresDsn] = None
    
    @model_validator(mode="after")
    def assemble_db_connection(self) -> 'Settings':
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
    
    # AI服务配置
    ALICLOUD_ACCESS_KEY_ID: Optional[str] = None
    ALICLOUD_ACCESS_KEY_SECRET: Optional[str] = None
    ALICLOUD_REGION: str = "cn-hangzhou"
    
    # 文件存储配置
    OSS_BUCKET_NAME: Optional[str] = None
    OSS_ENDPOINT: Optional[str] = None
    UPLOAD_MAX_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_EXTENSIONS: List[str] = [".jpg", ".jpeg", ".png", ".pdf"]
    
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
    
    # 监控配置
    ENABLE_METRICS: bool = True
    METRICS_PORT: int = 9090
    
    class Config:
        env_file = ".env"
        case_sensitive = True


class DevelopmentSettings(Settings):
    """开发环境配置"""
    DEBUG: bool = True
    LOG_LEVEL: str = "DEBUG"
    POSTGRES_DB: str = "wuhao_tutor_dev"


class TestingSettings(Settings):
    """测试环境配置"""
    DEBUG: bool = True
    LOG_LEVEL: str = "DEBUG"
    POSTGRES_DB: str = "wuhao_tutor_test"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 5  # 测试用短过期时间
    

class ProductionSettings(Settings):
    """生产环境配置"""
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    
    # 生产环境必需配置验证
    @field_validator("SECRET_KEY", mode="before")
    @classmethod
    def secret_key_must_be_set(cls, v: str) -> str:
        if not v or len(v) < 32:
            raise ValueError("SECRET_KEY must be set and at least 32 characters")
        return v


def get_settings() -> Settings:
    """
    获取配置实例
    根据环境变量 ENVIRONMENT 返回对应配置
    """
    import os
    
    environment = os.getenv("ENVIRONMENT", "development").lower()
    
    if environment == "production":
        return ProductionSettings()
    elif environment == "testing":
        return TestingSettings()
    else:
        return DevelopmentSettings()


# 全局配置实例
settings = get_settings()