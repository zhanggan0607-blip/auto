"""
FastAPI主应用入口
异步高性能接口层 - Django + FastAPI双轨制
"""
import json
import logging
import os
import sys
from contextlib import asynccontextmanager
from pathlib import Path

import django
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)

backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')
django.setup()

from fastapi_app.api import (
    crawler_router,
    task_router,
    websocket_proxy_router,
    embedding_router,
)
from fastapi_app.middleware.django_auth import DjangoAuthMiddleware
from fastapi_app.middleware.logging import RequestLoggingMiddleware
from fastapi_app.config import get_settings
from fastapi_app.services.redis_pubsub import RedisPubSubManager
from fastapi_app.services.celery_proxy import CeleryTaskProxy
from core.streaming import (
    stream_manager,
    BidirectionalStreamManager,
    StreamingAgentMixin,
    StreamEventType,
    router as stream_router,
)


settings = get_settings()
pubsub_manager = RedisPubSubManager()
celery_proxy = CeleryTaskProxy()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await pubsub_manager.connect()
    yield
    await pubsub_manager.disconnect()


app = FastAPI(
    title="投标自动化系统 - FastAPI异步接口",
    description="""
## FastAPI异步接口层

提供高性能异步接口，包括：
- **爬虫状态实时推送**：WebSocket支持
- **AI推理流式输出**：SSE支持
- **批量任务触发**：异步Celery任务
- **向量检索加速**：Milvus分布式集群直连
- **Agent双向流式通信**：支持流式推理和工具调用

## 架构说明
- Django处理复杂业务逻辑（ORM事务、复杂查询）
- FastAPI处理高频异步场景（实时推送、流式响应）
- 任务队列使用Celery+Redis Cluster
- 实时消息使用Redis Pub/Sub
- 向量库使用Milvus分布式集群
    """,
    version="3.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(DjangoAuthMiddleware)

app.include_router(crawler_router, prefix="/api/v1/crawler", tags=["爬虫接口"])
app.include_router(task_router, prefix="/api/v1/tasks", tags=["任务接口"])
app.include_router(websocket_proxy_router, prefix="/api/v1/ws", tags=["WebSocket代理"])
app.include_router(embedding_router, prefix="/api/v1/embedding", tags=["向量接口"])
app.include_router(stream_router, prefix="/api/v1/stream", tags=["流式通信"])


@app.websocket("/ws/stream/{agent_id}")
async def websocket_stream_endpoint(websocket: WebSocket, agent_id: str):
    await websocket.accept()

    user_id = None
    if hasattr(websocket, 'user') and websocket.user and hasattr(websocket.user, 'id'):
        user_id = websocket.user.id

    session = await stream_manager.create_session(
        agent_id=agent_id,
        user_id=user_id,
    )

    from core.streaming import WebSocketStreamHandler
    handler = WebSocketStreamHandler(websocket)
    await stream_manager.register_handler(session.session_id, handler)

    try:
        await websocket.send_json({
            "event": "session_established",
            "session_id": session.session_id,
            "agent_id": agent_id,
        })

        while True:
            data = await websocket.receive_text()
            message = json.loads(data)

            event_type = message.get("type", "message")
            if event_type == "ping":
                await websocket.send_json({"event": "pong"})
            else:
                await stream_manager.send_to_session(
                    session.session_id,
                    StreamEventType(event_type),
                    message.get("data", message),
                )

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: session={session.session_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        await stream_manager.close_session(session.session_id)


@app.get("/health/", tags=["健康检查"])
async def health_check():
    return {
        "status": "healthy",
        "service": "fastapi-app",
        "version": "3.0.0",
    }


@app.get("/ready/", tags=["健康检查"])
async def readiness_check():
    try:
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        redis_ok = await pubsub_manager.ping()
        return {
            "status": "ready",
            "database": "connected",
            "redis": "connected" if redis_ok else "disconnected",
        }
    except Exception:
        return JSONResponse(
            status_code=503,
            content={
                "status": "not_ready",
            }
        )


@app.get("/api/v1/status/", tags=["系统状态"])
async def system_status(request: Request):
    if not hasattr(request, 'user') or not request.user or not request.user.is_staff:
        return JSONResponse(status_code=403, content={"detail": "Forbidden"})

    return {
        "celery": {
            "broker_configured": bool(os.getenv('CELERY_BROKER_URL') or os.getenv('REDIS_HOST')),
        },
        "vector": {
            "type": os.getenv('VECTOR_DB_TYPE', 'chroma'),
        },
        "stream": {
            "active_sessions": len(stream_manager.get_active_sessions()),
        },
    }


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"FastAPI全局异常: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
        }
    )
