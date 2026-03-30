"""
Agent消息协议模块
统一Multi-Agent之间的通信格式和路由机制
安全改进：添加HMAC签名验证，防止恶意Agent注入伪造消息
"""
import asyncio
import hashlib
import hmac
import json
import logging
import os
import secrets
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Callable
from collections import defaultdict

logger = logging.getLogger(__name__)


class MessageType(Enum):
    """
    消息类型枚举
    """
    TASK = "task"
    RESULT = "result"
    ERROR = "error"
    HEARTBEAT = "heartbeat"
    EVENT = "event"
    BROADCAST = "broadcast"


class MessagePriority(Enum):
    """
    消息优先级
    """
    LOW = 1
    NORMAL = 5
    HIGH = 10
    URGENT = 20


@dataclass
class AgentMessage:
    """
    Agent消息 - 统一的通信协议

    Attributes:
        msg_id: 消息唯一标识
        msg_type: 消息类型
        sender_id: 发送方Agent ID
        receiver_id: 接收方Agent ID（单播时）
        content: 消息内容
        metadata: 元数据
        timestamp: 时间戳
        priority: 优先级
        reply_to: 回复的消息ID
        correlation_id: 关联ID（用于追踪）
        signature: 消息签名（用于验证发送者身份和消息完整性）
        nonce: 随机数（用于防止重放攻击）
    """
    msg_type: MessageType
    sender_id: str
    content: Any
    receiver_id: str = ""
    msg_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    priority: MessagePriority = MessagePriority.NORMAL
    reply_to: str = ""
    correlation_id: str = ""
    signature: str = ""
    nonce: str = field(default_factory=lambda: secrets.token_hex(16))

    def __post_init__(self):
        if isinstance(self.msg_type, str):
            self.msg_type = MessageType(self.msg_type)
        if isinstance(self.priority, int):
            self.priority = MessagePriority(self.priority)

    def compute_signature(self, secret_key: str) -> str:
        """
        计算消息签名
        使用HMAC-SHA256，签名内容包含：msg_id + nonce + timestamp + content

        Args:
            secret_key: 共享密钥

        Returns:
            str: 签名字符串
        """
        content_str = json.dumps(self.content, sort_keys=True, default=str) if self.content else ''
        sign_data = f"{self.msg_id}{self.nonce}{self.timestamp.isoformat()}{content_str}"
        signature = hmac.new(
            secret_key.encode('utf-8'),
            sign_data.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        return signature

    def verify_signature(self, secret_key: str) -> bool:
        """
        验证消息签名

        Args:
            secret_key: 共享密钥

        Returns:
            bool: 签名是否有效
        """
        if not self.signature:
            return False
        expected = self.compute_signature(secret_key)
        return hmac.compare_digest(expected, self.signature)

    def sign(self, secret_key: str):
        """
        对消息进行签名

        Args:
            secret_key: 共享密钥
        """
        self.signature = self.compute_signature(secret_key)

    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典格式
        """
        result = {
            'msg_id': self.msg_id,
            'type': self.msg_type.value,
            'from': self.sender_id,
            'to': self.receiver_id,
            'content': self.content,
            'meta': self.metadata,
            'ts': self.timestamp.isoformat(),
            'priority': self.priority.value,
            'nonce': self.nonce,
            'signature': self.signature
        }
        if self.reply_to:
            result['reply_to'] = self.reply_to
        if self.correlation_id:
            result['correlation_id'] = self.correlation_id
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AgentMessage':
        """
        从字典创建消息
        """
        msg_type = MessageType(data.get('type', 'task'))
        priority = MessagePriority(data.get('priority', 5))

        timestamp = data.get('timestamp') or data.get('ts')
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp)
        elif timestamp is None:
            timestamp = datetime.now()

        return cls(
            msg_id=data.get('msg_id', str(uuid.uuid4())),
            msg_type=msg_type,
            sender_id=data.get('from', ''),
            receiver_id=data.get('to', ''),
            content=data.get('content'),
            metadata=data.get('meta', {}),
            timestamp=timestamp,
            priority=priority,
            reply_to=data.get('reply_to', ''),
            correlation_id=data.get('correlation_id', ''),
            signature=data.get('signature', ''),
            nonce=data.get('nonce', secrets.token_hex(16))
        )

    def create_reply(self, content: Any, **kwargs) -> 'AgentMessage':
        """
        创建回复消息
        """
        return AgentMessage(
            msg_type=MessageType.RESULT,
            sender_id=self.receiver_id,
            receiver_id=self.sender_id,
            content=content,
            correlation_id=self.correlation_id or self.msg_id,
            reply_to=self.msg_id,
            metadata=kwargs
        )

    def create_error_reply(self, error: str, **kwargs) -> 'AgentMessage':
        """
        创建错误回复消息
        """
        return AgentMessage(
            msg_type=MessageType.ERROR,
            sender_id=self.receiver_id,
            receiver_id=self.sender_id,
            content={'error': error},
            correlation_id=self.correlation_id or self.msg_id,
            reply_to=self.msg_id,
            metadata=kwargs
        )


class AgentRouter:
    """
    Agent消息路由器
    统一管理Agent间的消息传递
    安全改进：支持签名验证和消息新鲜度检查
    """

    _instance = None
    MESSAGE_FRESHNESS_SECONDS = 300

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._initialized = True
        self._agents: Dict[str, Any] = {}
        self._handlers: Dict[str, List[Callable]] = defaultdict(list)
        self._middlewares: List[Callable] = []
        self._message_queue: asyncio.Queue = asyncio.Queue()
        self._running = False
        self._agent_secrets: Dict[str, str] = {}
        self._shared_secret: str = os.getenv('AGENT_MESSAGE_SECRET', secrets.token_hex(32))

    def set_shared_secret(self, secret: str):
        """
        设置Agent间通信的共享密钥

        Args:
            secret: 共享密钥
        """
        self._shared_secret = secret
        logger.warning("Agent共享密钥已更新")

    def register_agent(self, agent_id: str, agent_instance: Any, secret: str = None):
        """
        注册Agent到路由器

        Args:
            agent_id: Agent唯一标识
            agent_instance: Agent实例
            secret: Agent专用密钥（可选）
        """
        self._agents[agent_id] = agent_instance
        if secret:
            self._agent_secrets[agent_id] = secret
        logger.info(f"Agent注册到路由器: {agent_id}")

    def get_agent_secret(self, agent_id: str) -> str:
        """
        获取Agent的专用密钥

        Args:
            agent_id: Agent ID

        Returns:
            str: 密钥，如果没有专用密钥则返回共享密钥
        """
        return self._agent_secrets.get(agent_id, self._shared_secret)

    def _verify_message(self, message: AgentMessage) -> tuple:
        """
        验证消息签名和时间新鲜度

        Args:
            message: 消息对象

        Returns:
            tuple: (is_valid, error_reason)
        """
        if not message.signature:
            return False, "消息缺少签名"

        secret = self.get_agent_secret(message.sender_id)
        if not message.verify_signature(secret):
            return False, "签名验证失败"

        age = (datetime.now() - message.timestamp).total_seconds()
        if abs(age) > self.MESSAGE_FRESHNESS_SECONDS:
            return False, f"消息已过期(age={age:.0f}s)"

        return True, ""

    def _security_middleware(self, message: AgentMessage) -> Optional[AgentMessage]:
        """
        安全中间件：验证消息签名和时间新鲜度

        Args:
            message: 消息对象

        Returns:
            AgentMessage: 验证通过返回原消息，失败返回None
        """
        is_valid, reason = self._verify_message(message)
        if not is_valid:
            logger.warning(f"消息安全验证失败 [{message.sender_id}]: {reason}")
            logger.debug(f"验证失败的消息: msg_id={message.msg_id}, signature={message.signature[:16]}...")
            return None
        return message

    def unregister_agent(self, agent_id: str):
        """
        注销Agent
        """
        if agent_id in self._agents:
            del self._agents[agent_id]
        if agent_id in self._agent_secrets:
            del self._agent_secrets[agent_id]
        logger.info(f"Agent从路由器注销: {agent_id}")

    def get_agent(self, agent_id: str) -> Optional[Any]:
        """
        获取Agent实例
        """
        return self._agents.get(agent_id)

    def add_middleware(self, middleware: Callable):
        """
        添加消息中间件
        """
        self._middlewares.append(middleware)
        logger.info(f"添加消息中间件: {middleware.__name__}")

    def route_message(self, message: AgentMessage) -> bool:
        """
        路由单条消息（同步模式）
        安全：自动进行签名验证

        Args:
            message: 消息对象

        Returns:
            bool: 是否成功路由
        """
        if not self._security_middleware(message):
            return False

        for middleware in self._middlewares:
            message = middleware(message)
            if message is None:
                return False

        if message.receiver_id:
            return self._route_to_agent(message)
        elif message.msg_type == MessageType.BROADCAST:
            return self._broadcast(message)
        else:
            logger.warning(f"消息缺少接收者: {message.msg_id}")
            return False

    def _route_to_agent(self, message: AgentMessage) -> bool:
        """
        路由消息到指定Agent
        """
        agent = self._agents.get(message.receiver_id)
        if not agent:
            logger.error(f"Agent不存在: {message.receiver_id}")
            return False

        try:
            if hasattr(agent, 'handle_message'):
                agent.handle_message(message)
            else:
                logger.warning(f"Agent没有handle_message方法: {message.receiver_id}")
            return True
        except Exception as e:
            logger.error(f"路由消息到Agent失败: {e}")
            return False

    def _broadcast(self, message: AgentMessage) -> int:
        """
        广播消息到所有Agent

        Returns:
            int: 成功接收消息的Agent数量
        """
        count = 0
        for agent_id, agent in self._agents.items():
            if agent_id != message.sender_id:
                msg_copy = AgentMessage.from_dict(message.to_dict())
                msg_copy.receiver_id = agent_id
                try:
                    if hasattr(agent, 'handle_message'):
                        agent.handle_message(msg_copy)
                    count += 1
                except Exception as e:
                    logger.error(f"广播消息到Agent失败 {agent_id}: {e}")
        return count

    async def send_async(self, message: AgentMessage) -> Any:
        """
        异步发送消息

        Args:
            message: 消息对象

        Returns:
            Any: 处理结果
        """
        if not self._security_middleware(message):
            return None

        for middleware in self._middlewares:
            message = middleware(message)
            if message is None:
                return None

        agent = self._agents.get(message.receiver_id)
        if not agent:
            logger.error(f"Agent不存在: {message.receiver_id}")
            return None

        if hasattr(agent, 'handle_message_async'):
            return await agent.handle_message_async(message)
        elif asyncio.iscoroutinefunction(agent.handle_message):
            return await agent.handle_message(message)
        else:
            return agent.handle_message(message)

    async def broadcast_async(self, message: AgentMessage) -> List[Any]:
        """
        异步广播消息

        Returns:
            List[Any]: 所有Agent的处理结果
        """
        results = []
        tasks = []

        for agent_id, agent in self._agents.items():
            if agent_id != message.sender_id:
                msg_copy = AgentMessage.from_dict(message.to_dict())
                msg_copy.receiver_id = agent_id

                if hasattr(agent, 'handle_message_async'):
                    tasks.append(agent.handle_message_async(msg_copy))
                elif asyncio.iscoroutinefunction(agent.handle_message):
                    tasks.append(agent.handle_message(msg_copy))
                else:
                    tasks.append(asyncio.create_task(
                        asyncio.to_thread(agent.handle_message, msg_copy)
                    ))

        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)

        return results

    def send_signed_message(self, message: AgentMessage) -> bool:
        """
        发送已签名的消息（自动签名后再发送）

        Args:
            message: 消息对象

        Returns:
            bool: 是否成功
        """
        message.sign(self._shared_secret)
        return self.route_message(message)

    async def send_signed_message_async(self, message: AgentMessage) -> Any:
        """
        异步发送已签名的消息（自动签名后再发送）

        Args:
            message: 消息对象

        Returns:
            Any: 处理结果
        """
        message.sign(self._shared_secret)
        return await self.send_async(message)

    def subscribe(self, event_type: str, handler: Callable):
        """
        订阅事件
        """
        self._handlers[event_type].append(handler)

    def unsubscribe(self, event_type: str, handler: Callable):
        """
        取消订阅
        """
        if event_type in self._handlers:
            self._handlers[event_type].remove(handler)

    def publish_event(self, event_type: str, message: AgentMessage):
        """
        发布事件
        """
        for handler in self._handlers.get(event_type, []):
            try:
                handler(message)
            except Exception as e:
                logger.error(f"事件处理器执行失败: {e}")


agent_router = AgentRouter()
