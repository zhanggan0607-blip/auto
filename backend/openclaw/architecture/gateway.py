"""
Gateway层 - 网关层
WebSocket控制平面 + RESTful辅助接口 + 消息路由
"""
import asyncio
import json
import logging
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set


logger = logging.getLogger(__name__)


class MessageType(Enum):
    """
    消息类型枚举
    """
    PING = 'ping'
    PONG = 'pong'
    CREATE_AGENT = 'create_agent'
    EXECUTE_AGENT = 'execute_agent'
    EXECUTE_SKILL = 'execute_skill'
    EXECUTE_WORKFLOW = 'execute_workflow'
    GET_STATUS = 'get_status'
    LIST_AGENTS = 'list_agents'
    LIST_SKILLS = 'list_skills'
    CHAT = 'chat'
    BROADCAST = 'broadcast'
    ERROR = 'error'
    EVENT = 'event'


@dataclass
class GatewayConnection:
    """
    Gateway连接信息
    """
    connection_id: str
    websocket: Any
    session_id: Optional[str] = None
    agent_id: Optional[str] = None
    user_id: Optional[int] = None
    created_at: datetime = field(default_factory=datetime.now)
    last_ping: float = field(default_factory=time.time)
    metadata: Dict = field(default_factory=dict)
    subscriptions: Set[str] = field(default_factory=set)
    
    def to_dict(self) -> Dict:
        return {
            'connection_id': self.connection_id,
            'session_id': self.session_id,
            'agent_id': self.agent_id,
            'user_id': self.user_id,
            'created_at': self.created_at.isoformat(),
            'last_ping': self.last_ping,
            'subscriptions': list(self.subscriptions)
        }


@dataclass
class GatewayMessage:
    """
    Gateway消息结构
    """
    type: MessageType
    payload: Dict[str, Any]
    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.now)
    source: Optional[str] = None
    target: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            'type': self.type.value,
            'payload': self.payload,
            'message_id': self.message_id,
            'timestamp': self.timestamp.isoformat(),
            'source': self.source,
            'target': self.target
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'GatewayMessage':
        return cls(
            type=MessageType(data.get('type', 'ping')),
            payload=data.get('payload', {}),
            message_id=data.get('message_id', str(uuid.uuid4())),
            source=data.get('source'),
            target=data.get('target')
        )


class MessageRouter:
    """
    消息路由器
    负责消息分发和路由
    """
    
    def __init__(self):
        self._handlers: Dict[MessageType, Callable] = {}
        self._middlewares: List[Callable] = []
        self._event_subscribers: Dict[str, Set[str]] = {}
    
    def register_handler(self, msg_type: MessageType, handler: Callable):
        """
        注册消息处理器
        """
        self._handlers[msg_type] = handler
        logger.info(f"Registered handler for message type: {msg_type.value}")
    
    def add_middleware(self, middleware: Callable):
        """
        添加中间件
        """
        self._middlewares.append(middleware)
    
    async def route(self, message: GatewayMessage, connection: GatewayConnection) -> Optional[Dict]:
        """
        路由消息到对应处理器
        """
        for middleware in self._middlewares:
            message = await middleware(message, connection)
            if message is None:
                return None
        
        handler = self._handlers.get(message.type)
        if handler:
            try:
                return await handler(message, connection)
            except Exception as e:
                logger.error(f"Handler error for {message.type.value}: {str(e)}")
                return {
                    'type': 'error',
                    'error': str(e),
                    'original_type': message.type.value
                }
        
        return {
            'type': 'error',
            'error': f"No handler for message type: {message.type.value}"
        }
    
    def subscribe(self, event: str, connection_id: str):
        """
        订阅事件
        """
        if event not in self._event_subscribers:
            self._event_subscribers[event] = set()
        self._event_subscribers[event].add(connection_id)
    
    def unsubscribe(self, event: str, connection_id: str):
        """
        取消订阅
        """
        if event in self._event_subscribers:
            self._event_subscribers[event].discard(connection_id)
    
    def get_subscribers(self, event: str) -> Set[str]:
        """
        获取事件订阅者
        """
        return self._event_subscribers.get(event, set())


class GatewayManager:
    """
    Gateway管理器
    管理连接、消息路由、会话
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._initialized = True
        
        self._connections: Dict[str, GatewayConnection] = {}
        self._session_connections: Dict[str, Set[str]] = {}
        self._user_connections: Dict[int, Set[str]] = {}
        
        self._router = MessageRouter()
        self._running = False
        
        self._register_default_handlers()
    
    def _register_default_handlers(self):
        """
        注册默认消息处理器
        """
        self._router.register_handler(MessageType.PING, self._handle_ping)
        self._router.register_handler(MessageType.CREATE_AGENT, self._handle_create_agent)
        self._router.register_handler(MessageType.EXECUTE_AGENT, self._handle_execute_agent)
        self._router.register_handler(MessageType.EXECUTE_SKILL, self._handle_execute_skill)
        self._router.register_handler(MessageType.EXECUTE_WORKFLOW, self._handle_execute_workflow)
        self._router.register_handler(MessageType.GET_STATUS, self._handle_get_status)
        self._router.register_handler(MessageType.LIST_AGENTS, self._handle_list_agents)
        self._router.register_handler(MessageType.LIST_SKILLS, self._handle_list_skills)
        self._router.register_handler(MessageType.CHAT, self._handle_chat)
    
    async def handle_connection(self, websocket, user_id: int = None):
        """
        处理WebSocket连接
        """
        connection_id = str(uuid.uuid4())
        connection = GatewayConnection(
            connection_id=connection_id,
            websocket=websocket,
            user_id=user_id
        )
        
        self._connections[connection_id] = connection
        
        if user_id:
            if user_id not in self._user_connections:
                self._user_connections[user_id] = set()
            self._user_connections[user_id].add(connection_id)
        
        logger.info(f"New connection: {connection_id}, user: {user_id}")
        
        try:
            async for message in websocket:
                try:
                    data = json.loads(message)
                    gateway_msg = GatewayMessage.from_dict(data)
                    gateway_msg.source = connection_id
                    
                    response = await self._router.route(gateway_msg, connection)
                    
                    if response:
                        await self._send_response(connection, gateway_msg, response)
                        
                except json.JSONDecodeError:
                    await self._send_error(connection, "Invalid JSON format")
                except Exception as e:
                    logger.error(f"Message handling error: {str(e)}")
                    await self._send_error(connection, str(e))
                    
        except Exception as e:
            logger.error(f"Connection error: {str(e)}")
        
        finally:
            await self._cleanup_connection(connection)
    
    async def _handle_ping(self, message: GatewayMessage, connection: GatewayConnection) -> Dict:
        """
        处理心跳
        """
        connection.last_ping = time.time()
        return {'pong': True, 'timestamp': datetime.now().isoformat()}
    
    async def _handle_create_agent(self, message: GatewayMessage, connection: GatewayConnection) -> Dict:
        """
        创建Agent
        """
        from openclaw.agent_manager import agent_manager
        from openclaw.base_agent import AgentType
        
        payload = message.payload
        agent_type_str = payload.get('agent_type', 'orchestrator')
        session_id = payload.get('session_id') or connection.session_id or str(uuid.uuid4())
        
        try:
            agent_type = AgentType(agent_type_str)
        except ValueError:
            agent_type = AgentType.ORCHESTRATOR
        
        agent = await agent_manager.create_agent(
            agent_type=agent_type,
            session_id=session_id
        )
        
        connection.agent_id = agent.agent_id
        connection.session_id = session_id
        
        if session_id not in self._session_connections:
            self._session_connections[session_id] = set()
        self._session_connections[session_id].add(connection.connection_id)
        
        return agent.to_dict()
    
    async def _handle_execute_agent(self, message: GatewayMessage, connection: GatewayConnection) -> Dict:
        """
        执行Agent任务
        """
        from openclaw.agent_manager import agent_manager
        
        payload = message.payload
        agent_id = payload.get('agent_id') or connection.agent_id
        task = payload.get('task', {})
        
        if not agent_id:
            return {'error': 'No agent specified'}
        
        result = await agent_manager.execute_agent_task(agent_id, task)
        
        return result.to_dict()
    
    async def _handle_execute_skill(self, message: GatewayMessage, connection: GatewayConnection) -> Dict:
        """
        执行技能
        """
        from openclaw.skill_registry import skill_registry
        
        payload = message.payload
        skill_name = payload.get('skill')
        params = payload.get('params', {})
        
        if not skill_name:
            return {'error': 'No skill specified'}
        
        result = await skill_registry.execute_skill(skill_name, **params)
        
        return result.to_dict()
    
    async def _handle_execute_workflow(self, message: GatewayMessage, connection: GatewayConnection) -> Dict:
        """
        执行工作流
        """
        from openclaw.agents.bid_workflow_orchestrator import bid_workflow_orchestrator
        
        payload = message.payload
        tender_id = payload.get('tender_id')
        enterprise_id = payload.get('enterprise_id')
        config = payload.get('config', {})
        
        if not tender_id:
            return {'error': 'No tender_id specified'}
        
        result = await bid_workflow_orchestrator.start_workflow(
            tender_id=tender_id,
            enterprise_id=enterprise_id,
            config=config
        )
        
        return result
    
    async def _handle_get_status(self, message: GatewayMessage, connection: GatewayConnection) -> Dict:
        """
        获取状态
        """
        from openclaw.agent_manager import agent_manager
        from openclaw.skill_registry import skill_registry
        
        return {
            'gateway': {
                'connections': len(self._connections),
                'sessions': len(self._session_connections)
            },
            'agents': agent_manager.get_stats(),
            'skills': skill_registry.get_stats()
        }
    
    async def _handle_list_agents(self, message: GatewayMessage, connection: GatewayConnection) -> List[Dict]:
        """
        列出Agent
        """
        from openclaw.agent_manager import agent_manager
        from openclaw.base_agent import AgentType, AgentStatus
        
        payload = message.payload
        session_id = payload.get('session_id')
        agent_type_str = payload.get('agent_type')
        status_str = payload.get('status')
        
        agent_type = AgentType(agent_type_str) if agent_type_str else None
        status = AgentStatus(status_str) if status_str else None
        
        return await agent_manager.list_agents(
            session_id=session_id,
            agent_type=agent_type,
            status=status
        )
    
    async def _handle_list_skills(self, message: GatewayMessage, connection: GatewayConnection) -> List[Dict]:
        """
        列出技能
        """
        from openclaw.skill_registry import skill_registry
        
        payload = message.payload
        category = payload.get('category')
        tag = payload.get('tag')
        
        skills = skill_registry.list_skills(category=category, tag=tag)
        
        return [
            {
                'name': s.name,
                'description': s.description,
                'category': s.category,
                'tags': s.tags
            }
            for s in skills
        ]
    
    async def _handle_chat(self, message: GatewayMessage, connection: GatewayConnection) -> Dict:
        """
        聊天接口
        """
        from services.unified_llm_service import unified_llm_service
        
        payload = message.payload
        user_message = payload.get('message')
        model = payload.get('model')
        temperature = payload.get('temperature')
        system_prompt = payload.get('system_prompt')
        history = payload.get('history', [])
        
        if not user_message:
            return {'error': 'No message provided'}
        
        messages = []
        if system_prompt:
            messages.append({'role': 'system', 'content': system_prompt})
        messages.extend(history)
        messages.append({'role': 'user', 'content': user_message})
        
        response = await unified_llm_service.chat(
            messages=messages,
            model=model,
            temperature=temperature
        )
        
        return {'response': response}
    
    async def _send_response(self, connection: GatewayConnection, message: GatewayMessage, response: Dict):
        """
        发送响应
        """
        response_msg = {
            'type': f'{message.type.value}_response',
            'message_id': message.message_id,
            'payload': response,
            'timestamp': datetime.now().isoformat()
        }
        
        try:
            await connection.websocket.send(json.dumps(response_msg, ensure_ascii=False))
        except Exception as e:
            logger.error(f"Failed to send response: {str(e)}")
    
    async def _send_error(self, connection: GatewayConnection, error: str, msg_type: str = None):
        """
        发送错误
        """
        message = json.dumps({
            'type': 'error',
            'error': error,
            'original_type': msg_type,
            'timestamp': datetime.now().isoformat()
        }, ensure_ascii=False)
        
        try:
            await connection.websocket.send(message)
        except Exception as e:
            logger.error(f"Failed to send error: {str(e)}")
    
    async def _cleanup_connection(self, connection: GatewayConnection):
        """
        清理连接
        """
        conn_id = connection.connection_id
        
        if conn_id in self._connections:
            del self._connections[conn_id]
        
        session_id = connection.session_id
        if session_id and session_id in self._session_connections:
            self._session_connections[session_id].discard(conn_id)
            if not self._session_connections[session_id]:
                del self._session_connections[session_id]
        
        user_id = connection.user_id
        if user_id and user_id in self._user_connections:
            self._user_connections[user_id].discard(conn_id)
            if not self._user_connections[user_id]:
                del self._user_connections[user_id]
        
        logger.info(f"Connection closed: {conn_id}")
    
    async def broadcast_to_session(self, session_id: str, message: Dict):
        """
        向会话广播消息
        """
        conn_ids = self._session_connections.get(session_id, set())
        
        for conn_id in conn_ids:
            conn = self._connections.get(conn_id)
            if conn:
                try:
                    await conn.websocket.send(json.dumps(message, ensure_ascii=False))
                except Exception:
                    pass
    
    async def broadcast_to_user(self, user_id: int, message: Dict):
        """
        向用户广播消息
        """
        conn_ids = self._user_connections.get(user_id, set())
        
        for conn_id in conn_ids:
            conn = self._connections.get(conn_id)
            if conn:
                try:
                    await conn.websocket.send(json.dumps(message, ensure_ascii=False))
                except Exception:
                    pass
    
    async def emit_event(self, event: str, data: Dict):
        """
        发送事件到订阅者
        """
        subscribers = self._router.get_subscribers(event)
        
        message = {
            'type': 'event',
            'event': event,
            'data': data,
            'timestamp': datetime.now().isoformat()
        }
        
        for conn_id in subscribers:
            conn = self._connections.get(conn_id)
            if conn:
                try:
                    await conn.websocket.send(json.dumps(message, ensure_ascii=False))
                except Exception:
                    pass
    
    def get_stats(self) -> Dict:
        """
        获取统计信息
        """
        return {
            'running': self._running,
            'connections': len(self._connections),
            'sessions': len(self._session_connections),
            'users': len(self._user_connections)
        }


gateway_manager = GatewayManager()
