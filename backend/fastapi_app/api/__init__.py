"""
API路由模块
"""
from fastapi import APIRouter

from .crawler import router as crawler_router
from .tasks import router as task_router
from .websocket_proxy import router as websocket_proxy_router
from .embedding import router as embedding_router
from core.streaming import router as stream_router

__all__ = [
    "crawler_router",
    "task_router",
    "websocket_proxy_router",
    "embedding_router",
    "stream_router",
]
