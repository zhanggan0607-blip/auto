"""
Agent双向流式通信模块
支持WebSocket和SSE两种流式通信方式
实现OpenClaw流式推理
"""
import asyncio
import json
import logging
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, AsyncGenerator
from starlette.responses import StreamingResponse
from starlette.requests import Request
import sse_starlette.sse as sse

logger = logging.getLogger(__name__)


class StreamEventType(str, Enum):
    """流式事件类型"""
    THOUGHTS = "thoughts"
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"
    MESSAGE = "message"
    ERROR = "error"
    COMPLETE = "complete"
    HEARTBEAT = "heartbeat"
    STATUS_UPDATE = "status_update"


class StreamProtocol(str, Enum):
    """流式通信协议"""
    WEBSOCKET = "websocket"
    SSE = "sse"
    ServerStreaming = "server_streaming"


@dataclass
class StreamMessage:
    """流式消息"""
    event_type: StreamEventType
    data: Any
    timestamp: datetime = field(default_factory=datetime.now)
    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event": self.event_type.value,
            "data": self.data,
            "timestamp": self.timestamp.isoformat(),
            "message_id": self.message_id,
            "metadata": self.metadata,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False)

    @classmethod
    def from_dict(cls, data: Dict) -> "StreamMessage":
        return cls(
            event_type=StreamEventType(data.get("event", "message")),
            data=data.get("data"),
            timestamp=datetime.fromisoformat(data.get("timestamp", datetime.now().isoformat())),
            message_id=data.get("message_id", str(uuid.uuid4())),
            metadata=data.get("metadata", {}),
        )


@dataclass
class StreamSession:
    """流式会话"""
    session_id: str
    agent_id: str
    user_id: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    context: Dict[str, Any] = field(default_factory=dict)
    message_history: List[StreamMessage] = field(default_factory=list)

    def add_message(self, message: StreamMessage):
        self.message_history.append(message)

    def get_history(self, limit: int = 50) -> List[StreamMessage]:
        return self.message_history[-limit:]


class StreamHandler(ABC):
    """流式处理器基类"""

    @abstractmethod
    async def send(self, message: StreamMessage):
        pass

    @abstractmethod
    async def receive(self) -> Optional[StreamMessage]:
        pass

    @abstractmethod
    async def close(self):
        pass

    @abstractmethod
    async def is_connected(self) -> bool:
        pass


class WebSocketStreamHandler(StreamHandler):
    """WebSocket流式处理器"""

    def __init__(self, websocket):
        self.websocket = websocket
        self._connected = True

    async def send(self, message: StreamMessage):
        if self._connected:
            try:
                await self.websocket.send_text(message.to_json())
            except Exception as e:
                logger.error(f"WebSocket send error: {e}")
                self._connected = False

    async def receive(self) -> Optional[StreamMessage]:
        try:
            data = await self.websocket.receive_text()
            return StreamMessage.from_dict(json.loads(data))
        except Exception as e:
            logger.error(f"WebSocket receive error: {e}")
            return None

    async def close(self):
        if self._connected:
            try:
                await self.websocket.close()
            except Exception:
                pass
            self._connected = False

    async def is_connected(self) -> bool:
        return self._connected


class SSEStreamHandler(StreamHandler):
    """SSE流式处理器"""

    def __init__(self, request: Request):
        self.request = request
        self._connected = True
        self._queue: asyncio.Queue = asyncio.Queue()

    async def send(self, message: StreamMessage):
        if self._connected:
            await self._queue.put(message)

    async def receive(self) -> Optional[StreamMessage]:
        try:
            return await asyncio.wait_for(self._queue.get(), timeout=30)
        except asyncio.TimeoutError:
            return None

    async def close(self):
        self._connected = False
        while not self._queue.empty():
            try:
                self._queue.get_nowait()
            except asyncio.QueueEmpty:
                break

    async def is_connected(self) -> bool:
        return self._connected

    async def event_generator(self) -> AsyncGenerator[Dict, None]:
        """生成SSE事件流"""
        while self._connected:
            try:
                message = await asyncio.wait_for(self._queue.get(), timeout=30)
                yield {
                    "event": message.event_type.value,
                    "data": json.dumps(message.data, ensure_ascii=False),
                }
            except asyncio.TimeoutError:
                yield {"event": "heartbeat", "data": "{}"}
                continue
            except Exception as e:
                logger.error(f"SSE event generator error: {e}")
                break


class BidirectionalStreamManager:
    """双向流式通信管理器"""

    _instance = None
    _sessions: Dict[str, StreamSession] = {}
    _handlers: Dict[str, StreamHandler] = {}
    _locks: Dict[str, asyncio.Lock] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, "_initialized"):
            self._initialized = True
            self._sessions = {}
            self._handlers = {}
            self._locks = {}

    def _get_lock(self, session_id: str) -> asyncio.Lock:
        if session_id not in self._locks:
            self._locks[session_id] = asyncio.Lock()
        return self._locks[session_id]

    async def create_session(
        self,
        agent_id: str,
        user_id: Optional[str] = None,
        context: Dict[str, Any] = None,
    ) -> StreamSession:
        session_id = str(uuid.uuid4())
        session = StreamSession(
            session_id=session_id,
            agent_id=agent_id,
            user_id=user_id,
            context=context or {},
        )
        self._sessions[session_id] = session
        self._locks[session_id] = asyncio.Lock()
        logger.info(f"Created stream session: {session_id} for agent: {agent_id}")
        return session

    async def register_handler(self, session_id: str, handler: StreamHandler):
        self._handlers[session_id] = handler

    async def unregister_handler(self, session_id: str):
        if session_id in self._handlers:
            await self._handlers[session_id].close()
            del self._handlers[session_id]

    async def send_to_session(
        self,
        session_id: str,
        event_type: StreamEventType,
        data: Any,
        metadata: Dict[str, Any] = None,
    ) -> bool:
        if session_id not in self._sessions:
            logger.warning(f"Session not found: {session_id}")
            return False

        message = StreamMessage(
            event_type=event_type,
            data=data,
            metadata=metadata or {},
        )

        self._sessions[session_id].add_message(message)

        if session_id in self._handlers:
            await self._handlers[session_id].send(message)
            return True

        return False

    async def broadcast_to_agent(
        self,
        agent_id: str,
        event_type: StreamEventType,
        data: Any,
        metadata: Dict[str, Any] = None,
    ) -> int:
        count = 0
        for session_id, session in self._sessions.items():
            if session.agent_id == agent_id:
                if await self.send_to_session(session_id, event_type, data, metadata):
                    count += 1
        return count

    async def stream_thoughts(
        self,
        session_id: str,
        thoughts: AsyncGenerator[str, None],
    ):
        """流式输出思考过程"""
        async for thought in thoughts:
            await self.send_to_session(
                session_id,
                StreamEventType.THOUGHTS,
                {"content": thought, "type": "reasoning"},
            )

    async def stream_tool_calls(
        self,
        session_id: str,
        tool_calls: AsyncGenerator[Dict, None],
    ):
        """流式输出工具调用"""
        async for tool_call in tool_calls:
            await self.send_to_session(
                session_id,
                StreamEventType.TOOL_CALL,
                tool_call,
            )

    async def stream_agent_response(
        self,
        session_id: str,
        response_generator: AsyncGenerator[Dict, None],
    ):
        """流式输出Agent响应"""
        async for chunk in response_generator:
            event_type = StreamEventType(chunk.get("type", "message"))
            await self.send_to_session(session_id, event_type, chunk.get("data", chunk))

    async def close_session(self, session_id: str):
        if session_id in self._sessions:
            if session_id in self._handlers:
                await self.unregister_handler(session_id)
            del self._sessions[session_id]
            if session_id in self._locks:
                del self._locks[session_id]
            logger.info(f"Closed stream session: {session_id}")

    def get_session(self, session_id: str) -> Optional[StreamSession]:
        return self._sessions.get(session_id)

    def get_active_sessions(self, agent_id: str = None) -> List[StreamSession]:
        if agent_id:
            return [s for s in self._sessions.values() if s.agent_id == agent_id]
        return list(self._sessions.values())


stream_manager = BidirectionalStreamManager()


class StreamingAgentMixin:
    """流式Agent混入类
    让Agent支持双向流式通信
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._stream_session: Optional[StreamSession] = None
        self._stream_handlers: List[StreamHandler] = []

    async def set_stream_session(self, session: StreamSession):
        self._stream_session = session

    async def send_stream_message(
        self,
        event_type: StreamEventType,
        data: Any,
        metadata: Dict[str, Any] = None,
    ):
        if self._stream_session:
            await stream_manager.send_to_session(
                self._stream_session.session_id,
                event_type,
                data,
                metadata,
            )

    async def stream_think(self, prompt: str, context: Dict = None) -> str:
        """流式思考"""
        thoughts = await self.think_streaming(prompt, context)
        result = ""
        async for thought in thoughts:
            result += thought
            await self.send_stream_message(
                StreamEventType.THOUGHTS,
                {"content": thought, "partial": True},
            )
        return result

    async def think_streaming(self, prompt: str, context: Dict = None) -> AsyncGenerator[str, None]:
        """流式思考生成器 - 子类可重写"""
        result = await self.think(prompt, context)
        for char in result:
            yield char
            await asyncio.sleep(0.01)

    async def execute_with_stream(self, task: Dict[str, Any]) -> Dict:
        """带流式输出的任务执行"""
        if not self._stream_session:
            return await self.execute(task)

        await self.send_stream_message(
            StreamEventType.STATUS_UPDATE,
            {"status": "started", "agent_id": self.agent_id},
        )

        try:
            result = await self.execute(task)

            await self.send_stream_message(
                StreamEventType.STATUS_UPDATE,
                {"status": "completed", "success": result.success},
            )

            if result.data:
                await self.send_stream_message(
                    StreamEventType.MESSAGE,
                    {"content": result.data, "type": "result"},
                )

            return result.to_dict()

        except Exception as e:
            await self.send_stream_message(
                StreamEventType.ERROR,
                {"error": str(e), "type": "execution_error"},
            )
            raise


async def create_sse_response(request: Request, session_id: str) -> StreamingResponse:
    """创建SSE响应"""
    session = stream_manager.get_session(session_id)
    if not session:
        raise ValueError(f"Session not found: {session_id}")

    handler = SSEStreamHandler(request)
    await stream_manager.register_handler(session_id, handler)

    async def event_generator():
        async for event in handler.event_generator():
            yield event

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


class RedisStreamAdapter:
    """Redis适配器 - 支持跨进程流式通信"""

    def __init__(self):
        self._redis = None
        self._pubsub = None

    async def connect(self):
        try:
            import os
            import redis.asyncio as aioredis

            redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/1')
            self._redis = await aioredis.from_url(redis_url, decode_responses=True)
            self._pubsub = self._redis.pubsub()
            logger.info("Redis stream adapter connected")

        except Exception as e:
            logger.warning(f"Redis stream adapter not available: {e}")

    async def disconnect(self):
        if self._pubsub:
            await self._pubsub.close()
        if self._redis:
            await self._redis.close()

    async def publish(self, channel: str, message: StreamMessage):
        if self._redis:
            await self._redis.publish(channel, message.to_json())

    async def subscribe(self, channel: str):
        if self._pubsub:
            await self._pubsub.subscribe(channel)

    async def listen(self, channel: str) -> AsyncGenerator[StreamMessage, None]:
        if self._pubsub:
            async for message in self._pubsub.listen():
                if message["type"] == "message":
                    yield StreamMessage.from_dict(json.loads(message["data"]))


redis_stream_adapter = RedisStreamAdapter()


from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

router = APIRouter()


class CreateSessionRequest(BaseModel):
    agent_id: str
    user_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None


class SendMessageRequest(BaseModel):
    session_id: str
    event_type: str
    data: Any
    metadata: Optional[Dict[str, Any]] = None


@router.post("/sessions/")
async def create_stream_session(request: CreateSessionRequest):
    """创建流式会话"""
    session = await stream_manager.create_session(
        agent_id=request.agent_id,
        user_id=request.user_id,
        context=request.context,
    )
    return {
        "session_id": session.session_id,
        "agent_id": session.agent_id,
        "created_at": session.created_at.isoformat(),
    }


@router.get("/sessions/{session_id}")
async def get_stream_session(session_id: str):
    """获取流式会话信息"""
    session = stream_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return {
        "session_id": session.session_id,
        "agent_id": session.agent_id,
        "user_id": session.user_id,
        "created_at": session.created_at.isoformat(),
        "message_count": len(session.message_history),
    }


@router.delete("/sessions/{session_id}")
async def close_stream_session(session_id: str):
    """关闭流式会话"""
    await stream_manager.close_session(session_id)
    return {"status": "closed", "session_id": session_id}


@router.post("/send/")
async def send_stream_message(request: SendMessageRequest):
    """发送流式消息"""
    success = await stream_manager.send_to_session(
        session_id=request.session_id,
        event_type=StreamEventType(request.event_type),
        data=request.data,
        metadata=request.metadata,
    )
    return {"success": success}


@router.get("/sessions/{session_id}/history")
async def get_session_history(
    session_id: str,
    limit: int = Query(default=50, ge=1, le=100),
):
    """获取会话历史消息"""
    session = stream_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    history = session.get_history(limit=limit)
    return {
        "session_id": session_id,
        "messages": [
            {
                "event": msg.event_type.value,
                "data": msg.data,
                "timestamp": msg.timestamp.isoformat(),
                "message_id": msg.message_id,
            }
            for msg in history
        ],
    }


@router.get("/agents/{agent_id}/sessions")
async def get_agent_sessions(agent_id: str):
    """获取Agent的所有活动会话"""
    sessions = stream_manager.get_active_sessions(agent_id=agent_id)
    return {
        "agent_id": agent_id,
        "active_sessions": len(sessions),
        "sessions": [
            {
                "session_id": s.session_id,
                "user_id": s.user_id,
                "created_at": s.created_at.isoformat(),
                "message_count": len(s.message_history),
            }
            for s in sessions
        ],
    }


@router.get("/stats/")
async def get_stream_stats():
    """获取流式通信统计"""
    all_sessions = stream_manager.get_active_sessions()
    agent_sessions: Dict[str, int] = {}
    for session in all_sessions:
        agent_sessions[session.agent_id] = agent_sessions.get(session.agent_id, 0) + 1

    return {
        "total_active_sessions": len(all_sessions),
        "sessions_by_agent": agent_sessions,
    }
