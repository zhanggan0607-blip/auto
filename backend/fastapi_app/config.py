"""
FastAPI配置文件
"""
from functools import lru_cache
from pydantic_settings import BaseSettings
from pydantic import ConfigDict
from typing import List


class Settings(BaseSettings):
    """
    FastAPI配置类
    从环境变量读取配置
    """
    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # FastAPI服务配置
    APP_NAME: str = "投标自动化系统-FastAPI"
    DEBUG: bool = False
    API_V1_PREFIX: str = "/api/v1"

    # CORS配置
    CORS_ORIGINS: List[str] = [
        "http://localhost:8080",
        "http://localhost:3000",
        "http://127.0.0.1:8080",
    ]

    # Redis配置
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: str = ""

    # Celery配置
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/1"

    # Milvus配置
    MILVUS_HOST: str = "localhost"
    MILVUS_PORT: int = 19530

    # Django密钥
    DJANGO_SECRET_KEY: str = ""


@lru_cache()
def get_settings() -> Settings:
    """
    获取配置单例
    """
    return Settings()
