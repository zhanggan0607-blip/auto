"""
WebSocket代理接口
为前端提供WebSocket连接代理
解决前端直接连接后端WebSocket的跨域和安全性问题
"""
import asyncio
import json
import logging
from typing import Optional, Dict, Any
from datetime import datetime

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, HTTPException
from starlette.websockets import WebSocketState

from fastapi_app.services.redis_pubsub import pubsub_manager

logger = logging.getLogger(__name__)
router = APIRouter()


class ConnectionManager:
    """
    WebSocket连接管理器
    """

    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.user_connections: Dict[int, set] = {}

    async def connect(self, websocket: WebSocket, client_id: str, user_id: Optional[int] = None):
        """接受WebSocket连接"""
        await websocket.accept()
        self.active_connections[client_id] = websocket

        if user_id:
            if user_id not in self.user_connections:
                self.user_connections[user_id] = set()
            self.user_connections[user_id].add(client_id)

        logger.info(f"WebSocket connected: {client_id}, user_id={user_id}")

    def disconnect(self, client_id: str, user_id: Optional[int] = None):
        """断开WebSocket连接"""
        if client_id in self.active_connections:
            del self.active_connections[client_id]

        if user_id and user_id in self.user_connections:
            self.user_connections[user_id].discard(client_id)
            if not self.user_connections[user_id]:
                del self.user_connections[user_id]

        logger.info(f"WebSocket disconnected: {client_id}")

    async def send_message(self, client_id: str, message: dict):
        """发送消息到指定客户端"""
        if client_id in self.active_connections:
            websocket = self.active_connections[client_id]
            if websocket.client_state == WebSocketState.CONNECTED:
                await websocket.send_json(message)

    async def broadcast(self, message: dict, user_filter: Optional[set] = None):
        """广播消息"""
        for client_id, websocket in self.active_connections.items():
            if websocket.client_state == WebSocketState.CONNECTED:
                if user_filter is None or client_id in user_filter:
                    try:
                        await websocket.send_json(message)
                    except Exception as e:
                        logger.error(f"发送消息失败 {client_id}: {e}")


manager = ConnectionManager()


@router.websocket("/crawl/{task_id}/")
async def websocket_crawl_progress(
    websocket: WebSocket,
    task_id: str,
    token: Optional[str] = Query(None),
):
    """
    爬虫进度WebSocket连接
    前端通过此接口获取爬虫实时进度
    """
    client_id = f"crawl_{task_id}_{id(websocket)}"

    try:
        # 验证token（如果提供）
        user_id = None
        if token:
            user_id = await verify_ws_token(token)
            if not user_id:
                await websocket.close(code=4001, reason="Invalid token")
                return

        await manager.connect(websocket, client_id, user_id)

        # 订阅爬虫进度频道
        channel = f"crawl_progress:{task_id}"
        pubsub = await pubsub_manager.subscribe(channel)

        try:
            # 发送连接成功消息
            await websocket.send_json({
                "type": "connected",
                "task_id": task_id,
                "timestamp": datetime.now().isoformat(),
            })

            # 持续接收并转发消息
            while True:
                message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=30)

                if message:
                    data = json.loads(message["data"])
                    await websocket.send_json(data)

                # 检查客户端连接状态
                if websocket.client_state != WebSocketState.CONNECTED:
                    break

        finally:
            await pubsub_manager.unsubscribe(channel)
            manager.disconnect(client_id, user_id)

    except WebSocketDisconnect:
        logger.info(f"Client disconnected: {client_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        manager.disconnect(client_id, user_id)


@router.websocket("/agent/{session_id}/")
async def websocket_agent_session(
    websocket: WebSocket,
    session_id: str,
    token: Optional[str] = Query(None),
):
    """
    Agent会话WebSocket连接
    用于OpenClaw Gateway的WebSocket代理
    """
    client_id = f"agent_{session_id}_{id(websocket)}"

    try:
        user_id = None
        if token:
            user_id = await verify_ws_token(token)
            if not user_id:
                await websocket.close(code=4001, reason="Invalid token")
                return

        await manager.connect(websocket, client_id, user_id)

        # 订阅Agent会话频道
        channel = f"agent_session:{session_id}"
        pubsub = await pubsub_manager.subscribe(channel)

        # 获取Django配置的Gateway地址
        from django.conf import settings
        gateway_host = settings.OPENCLAW_CONFIG.get("GATEWAY_HOST", "127.0.0.1")
        gateway_port = settings.OPENCLAW_CONFIG.get("GATEWAY_PORT", 18789)

        # 建立到Gateway的连接
        gateway_ws = None
        try:
            import websockets
            gateway_url = f"ws://{gateway_host}:{gateway_port}/agent/{session_id}"
            gateway_ws = await websockets.connect(gateway_url)

            # 双向转发
            async def forward_to_gateway():
                try:
                    while True:
                        data = await websocket.receive_json()
                        await gateway_ws.send_json(data)
                except Exception:
                    pass

            async def forward_to_client():
                try:
                    while True:
                        data = await gateway_ws.recv()
                        if isinstance(data, str):
                            await websocket.send_text(data)
                        else:
                            await websocket.send_bytes(data)
                except Exception:
                    pass

            # 并发执行两个转发任务
            await asyncio.gather(
                forward_to_gateway(),
                forward_to_client(),
            )

        except Exception as e:
            logger.error(f"Gateway connection failed: {e}")
            await websocket.send_json({
                "type": "error",
                "message": f"Gateway连接失败: {e}",
            })
        finally:
            if gateway_ws:
                await gateway_ws.close()
            await pubsub_manager.unsubscribe(channel)
            manager.disconnect(client_id, user_id)

    except WebSocketDisconnect:
        logger.info(f"Agent client disconnected: {client_id}")
    except Exception as e:
        logger.error(f"Agent WebSocket error: {e}")
    finally:
        manager.disconnect(client_id, user_id)


@router.get("/connections/")
async def list_active_connections():
    """
    获取当前活跃连接数
    (仅管理员)
    """
    return {
        "total": len(manager.active_connections),
        "by_user": {str(k): len(v) for k, v in manager.user_connections.items()},
    }


async def verify_ws_token(token: str) -> Optional[int]:
    """
    验证WebSocket Token
    返回user_id或None
    """
    try:
        from utils.authentication import decode_token
        payload = decode_token(token)
        if payload:
            return payload.get("user_id")
    except Exception:
        pass
    return None
