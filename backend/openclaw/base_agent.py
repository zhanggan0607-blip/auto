"""
OpenClaw Agent基类 (增强版)
实现基于agentId的会话隔离机制 + 三层架构集成
安全改进：添加Agent调度结构化审计日志
"""
import asyncio
import json
import logging
import time
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

from core.constants import AgentStatus, AgentType, AgentCapability


logger = logging.getLogger(__name__)


def _log_agent_audit(
    event_type: str,
    agent_id: str,
    action: str,
    resource_type: str = None,
    resource_id: str = None,
    metadata: Dict = None,
    success: bool = True,
    error: str = None
):
    """
    Agent操作审计日志（结构化）

    Args:
        event_type: 事件类型
        agent_id: Agent ID
        action: 操作描述
        resource_type: 资源类型
        resource_id: 资源ID
        metadata: 额外元数据
        success: 是否成功
        error: 错误信息
    """
    audit_data = {
        'event_type': event_type,
        'agent_id': agent_id,
        'action': action,
        'resource_type': resource_type,
        'resource_id': resource_id,
        'success': success,
        'timestamp': datetime.now().isoformat(),
    }
    if metadata:
        safe_metadata = {}
        for k, v in metadata.items():
            if k.lower() not in ['password', 'token', 'secret', 'key', 'credential']:
                safe_metadata[k] = str(v)[:200]
        audit_data['metadata'] = safe_metadata
    if error:
        audit_data['error'] = str(error)[:200]

    if success:
        logger.info(f"Agent审计: {audit_data}")
    else:
        logger.warning(f"Agent审计[失败]: {audit_data}")


@dataclass
class AgentContext:
    """
    Agent上下文 - 实现会话隔离
    """
    agent_id: str
    agent_type: AgentType
    session_id: str
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    state: Dict[str, Any] = field(default_factory=dict)
    memory: Dict[str, Any] = field(default_factory=dict)
    messages: List[Dict[str, Any]] = field(default_factory=list)
    
    parent_agent_id: Optional[str] = None
    child_agent_ids: List[str] = field(default_factory=list)
    
    capabilities: List[AgentCapability] = field(default_factory=list)
    tools: List[str] = field(default_factory=list)
    
    def update_state(self, key: str, value: Any):
        """
        更新状态
        """
        self.state[key] = value
        self.updated_at = datetime.now()
    
    def get_state(self, key: str, default: Any = None) -> Any:
        """
        获取状态
        """
        return self.state.get(key, default)
    
    def add_message(self, role: str, content: Any, metadata: Dict = None):
        """
        添加消息到上下文
        """
        self.messages.append({
            'role': role,
            'content': content,
            'timestamp': datetime.now().isoformat(),
            'metadata': metadata or {}
        })
        self.updated_at = datetime.now()
    
    def get_recent_messages(self, limit: int = 10) -> List[Dict]:
        """
        获取最近的消息
        """
        return self.messages[-limit:] if self.messages else []
    
    def clear_messages(self):
        """
        清除消息
        """
        self.messages.clear()
        self.updated_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典
        """
        return {
            'agent_id': self.agent_id,
            'agent_type': self.agent_type.value,
            'session_id': self.session_id,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'state': self.state,
            'memory_keys': list(self.memory.keys()),
            'messages_count': len(self.messages),
            'parent_agent_id': self.parent_agent_id,
            'child_agent_ids': self.child_agent_ids,
            'capabilities': [c.value for c in self.capabilities],
            'tools': self.tools
        }


@dataclass
class TaskResult:
    """
    任务执行结果
    """
    success: bool
    data: Any = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    execution_time: float = 0.0
    agent_id: str = ''
    
    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典
        """
        return {
            'success': self.success,
            'data': self.data,
            'error': self.error,
            'metadata': self.metadata,
            'execution_time': self.execution_time,
            'agent_id': self.agent_id
        }


@dataclass
class AgentConfig:
    """
    Agent配置
    """
    max_retries: int = 3
    retry_delay: float = 1.0
    timeout: int = 300
    enable_memory: bool = True
    enable_tools: bool = True
    llm_model: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 4096


class BaseAgent(ABC):
    """
    Agent基类 (增强版)
    所有Agent必须继承此类并实现execute方法
    
    特性:
    - 会话隔离
    - 状态管理
    - 记忆系统
    - 工具调用
    - 事件驱动
    - 三层架构集成
    """
    
    agent_type: AgentType = None
    capabilities: List[AgentCapability] = []
    default_tools: List[str] = []
    
    def __init__(
        self,
        agent_id: str = None,
        session_id: str = None,
        config: AgentConfig = None
    ):
        """
        初始化Agent
        
        Args:
            agent_id: Agent唯一标识，不提供则自动生成
            session_id: 会话ID，用于隔离不同会话的数据
            config: Agent配置
        """
        self.agent_id = agent_id or self._generate_agent_id()
        self.session_id = session_id or str(uuid.uuid4())
        self.config = config or AgentConfig()
        
        self.context = AgentContext(
            agent_id=self.agent_id,
            agent_type=self.agent_type or AgentType.ORCHESTRATOR,
            session_id=self.session_id,
            capabilities=self.capabilities,
            tools=self.default_tools.copy()
        )
        
        self.status = AgentStatus.IDLE
        self._skills: Dict[str, Callable] = {}
        self._event_handlers: Dict[str, List[Callable]] = {}
        self._tools: Dict[str, Callable] = {}
        
        self._setup()
        self._register_default_tools()
    
    def _generate_agent_id(self) -> str:
        """
        生成唯一的agentId（小写）
        """
        prefix = self.agent_type.value if self.agent_type else 'agent'
        unique_id = str(uuid.uuid4())[:8]
        return f"{prefix}_{unique_id}".lower()
    
    def _setup(self):
        """
        初始化设置，子类可重写
        """
        pass
    
    def _register_default_tools(self):
        """
        注册默认工具
        """
        for tool_name in self.default_tools:
            self._register_tool_internal(tool_name)
    
    def _register_tool_internal(self, tool_name: str):
        """
        内部工具注册
        """
        if tool_name == 'llm_chat':
            self._tools[tool_name] = self._tool_llm_chat
        elif tool_name == 'execute_code':
            self._tools[tool_name] = self._tool_execute_code
        elif tool_name == 'http_request':
            self._tools[tool_name] = self._tool_http_request
        elif tool_name == 'read_memory':
            self._tools[tool_name] = self._tool_read_memory
        elif tool_name == 'write_memory':
            self._tools[tool_name] = self._tool_write_memory
    
    def register_skill(self, name: str, handler: Callable):
        """
        注册技能
        """
        self._skills[name] = handler
        logger.info(f"Agent {self.agent_id} registered skill: {name}")
    
    def register_tool(self, name: str, handler: Callable):
        """
        注册工具
        """
        self._tools[name] = handler
        if name not in self.context.tools:
            self.context.tools.append(name)
        logger.info(f"Agent {self.agent_id} registered tool: {name}")
    
    def on(self, event: str, handler: Callable):
        """
        注册事件处理器
        """
        if event not in self._event_handlers:
            self._event_handlers[event] = []
        self._event_handlers[event].append(handler)
    
    def emit(self, event: str, data: Any = None):
        """
        触发事件
        """
        handlers = self._event_handlers.get(event, [])
        for handler in handlers:
            try:
                handler(data)
            except Exception as e:
                logger.error(f"Event handler error: {event}, {str(e)}")
    
    async def execute_skill(self, skill_name: str, *args, **kwargs) -> Any:
        """
        执行技能
        """
        if skill_name not in self._skills:
            raise ValueError(f"Skill not found: {skill_name}")
        
        self.emit('skill_start', {'skill': skill_name})
        
        try:
            handler = self._skills[skill_name]
            if asyncio.iscoroutinefunction(handler):
                result = await handler(*args, **kwargs)
            else:
                result = handler(*args, **kwargs)
            
            self.emit('skill_complete', {'skill': skill_name, 'result': result})
            return result
            
        except Exception as e:
            self.emit('skill_error', {'skill': skill_name, 'error': str(e)})
            raise
    
    async def use_tool(self, tool_name: str, **kwargs) -> Any:
        """
        使用工具
        """
        if tool_name not in self._tools:
            raise ValueError(f"Tool not found: {tool_name}")
        
        self.emit('tool_start', {'tool': tool_name, 'params': kwargs})
        
        try:
            handler = self._tools[tool_name]
            if asyncio.iscoroutinefunction(handler):
                result = await handler(**kwargs)
            else:
                result = handler(**kwargs)
            
            self.emit('tool_complete', {'tool': tool_name, 'result': result})
            return result
            
        except Exception as e:
            self.emit('tool_error', {'tool': tool_name, 'error': str(e)})
            raise
    
    async def _tool_llm_chat(
        self,
        message: str,
        system_prompt: str = None,
        history: List[Dict] = None,
        model: str = None,
        temperature: float = None
    ) -> str:
        """
        LLM聊天工具
        """
        from services.unified_llm_service import unified_llm_service
        
        messages = []
        if system_prompt:
            messages.append({'role': 'system', 'content': system_prompt})
        if history:
            messages.extend(history)
        messages.append({'role': 'user', 'content': message})
        
        response = await unified_llm_service.chat(
            messages=messages,
            model=model or self.config.llm_model,
            temperature=temperature or self.config.temperature
        )
        
        return response
    
    async def _tool_execute_code(
        self,
        code: str,
        language: str = 'python',
        timeout: int = 60
    ) -> Dict:
        """
        代码执行工具
        """
        from openclaw.architecture.embedded import embedded_executor
        
        result = await embedded_executor.execute_code(code, language, timeout)
        return result
    
    async def _tool_http_request(
        self,
        method: str,
        url: str,
        headers: Dict = None,
        data: Dict = None,
        timeout: int = 30
    ) -> Dict:
        from common.utils.http_client import async_http_request
        resp = await async_http_request(
            method, url, headers=headers, data=data, timeout=timeout
        )
        return resp.to_dict()
    
    def _tool_read_memory(self, key: str = None) -> Any:
        """
        读取记忆工具
        """
        if key:
            return self.context.memory.get(key)
        return self.context.memory
    
    def _tool_write_memory(self, key: str, value: Any):
        """
        写入记忆工具
        """
        self.context.memory[key] = value
        self.context.updated_at = datetime.now()
    
    def update_context(self, key: str, value: Any):
        """
        更新上下文状态
        """
        self.context.update_state(key, value)
    
    def get_context(self, key: str, default: Any = None) -> Any:
        """
        获取上下文状态
        """
        return self.context.get_state(key, default)
    
    def add_memory(self, key: str, value: Any):
        """
        添加到记忆（同时持久化）
        """
        self.context.memory[key] = value
        self.context.updated_at = datetime.now()
        self._persist_memory(key, value)

    def get_memory(self, key: str, default: Any = None) -> Any:
        """
        从记忆获取（先查内存，再查持久化）
        """
        if key in self.context.memory:
            return self.context.memory[key]

        persisted = self._load_persisted_memory(key)
        if persisted is not None:
            self.context.memory[key] = persisted
            return persisted

        return default

    def _persist_memory(self, key: str, value: Any):
        """
        持久化记忆到数据库
        """
        try:
            from openclaw.persistent_memory import persistent_memory_service
            persistent_memory_service.save_memory(
                agent_id=self.agent_id,
                agent_type=self.agent_type.value if self.agent_type else 'unknown',
                key=key,
                value=value,
                session_id=self.session_id,
                scope='session',
            )
        except Exception as e:
            logger.debug(f"记忆持久化失败(非致命): {str(e)}")

    def _load_persisted_memory(self, key: str) -> Any:
        """
        从数据库加载持久化记忆
        """
        try:
            from openclaw.persistent_memory import persistent_memory_service
            return persistent_memory_service.load_memory(
                agent_type=self.agent_type.value if self.agent_type else 'unknown',
                key=key,
                session_id=self.session_id,
            )
        except Exception as e:
            logger.debug(f"加载持久化记忆失败(非致命): {str(e)}")
            return None
    
    def add_message(self, role: str, content: Any, metadata: Dict = None):
        """
        添加消息
        """
        self.context.add_message(role, content, metadata)
    
    def get_messages(self, limit: int = None) -> List[Dict]:
        """
        获取消息列表
        """
        messages = self.context.messages
        if limit:
            return messages[-limit:]
        return messages
    
    def set_status(self, status: AgentStatus):
        """
        设置状态
        """
        old_status = self.status
        self.status = status
        self.emit('status_change', {
            'old_status': old_status.value,
            'new_status': status.value
        })
        logger.info(f"Agent {self.agent_id} status: {old_status.value} -> {status.value}")
    
    async def think(self, prompt: str, context: Dict = None) -> str:
        """
        思考方法 - 使用LLM进行推理
        """
        system_prompt = f"""你是一个{self.agent_type.value if self.agent_type else '通用'}类型的智能Agent。
你的ID是: {self.agent_id}
你的能力包括: {', '.join([c.value for c in self.capabilities]) if self.capabilities else '通用'}

请根据上下文进行思考和推理，给出你的分析和建议。"""
        
        full_prompt = prompt
        if context:
            full_prompt = f"上下文信息:\n{json.dumps(context, ensure_ascii=False, indent=2)}\n\n问题:\n{prompt}"
        
        return await self._tool_llm_chat(
            message=full_prompt,
            system_prompt=system_prompt
        )
    
    async def act(self, action: str, params: Dict = None) -> Any:
        """
        行动方法 - 执行具体操作
        """
        params = params or {}
        
        if action in self._tools:
            return await self.use_tool(action, **params)
        elif action in self._skills:
            return await self.execute_skill(action, **params)
        else:
            raise ValueError(f"Unknown action: {action}")
    
    @abstractmethod
    async def execute(self, task: Dict[str, Any]) -> TaskResult:
        """
        执行任务（抽象方法，子类必须实现）
        
        Args:
            task: 任务数据
            
        Returns:
            TaskResult: 执行结果
        """
        pass
    
    async def run(self, task: Dict[str, Any]) -> TaskResult:
        """
        运行Agent（入口方法）
        安全：添加结构化审计日志
        """
        start_time = time.time()

        self.set_status(AgentStatus.RUNNING)
        self.emit('task_start', {'task': task})

        task_id = task.get('task_id', task.get('id', 'unknown'))
        _log_agent_audit(
            event_type='AGENT_TASK_START',
            agent_id=self.agent_id,
            action=f'Agent执行任务',
            resource_type='task',
            resource_id=task_id,
            metadata={'task_type': task.get('type'), 'session_id': self.session_id}
        )

        try:
            result = await self.execute(task)
            result.agent_id = self.agent_id
            result.execution_time = time.time() - start_time

            if result.success:
                self.set_status(AgentStatus.IDLE)
                _log_agent_audit(
                    event_type='AGENT_TASK_COMPLETE',
                    agent_id=self.agent_id,
                    action='Agent任务执行成功',
                    resource_type='task',
                    resource_id=task_id,
                    metadata={'execution_time': result.execution_time}
                )
            else:
                self.set_status(AgentStatus.ERROR)
                _log_agent_audit(
                    event_type='AGENT_TASK_FAILED',
                    agent_id=self.agent_id,
                    action='Agent任务执行失败',
                    resource_type='task',
                    resource_id=task_id,
                    success=False,
                    error=result.error
                )

            self.emit('task_complete', {'result': result.to_dict()})
            return result

        except Exception as e:
            self.set_status(AgentStatus.ERROR)
            error_result = TaskResult(
                success=False,
                error=str(e),
                metadata={'agent_id': self.agent_id},
                execution_time=time.time() - start_time,
                agent_id=self.agent_id
            )
            self.emit('task_error', {'error': str(e)})
            _log_agent_audit(
                event_type='AGENT_TASK_ERROR',
                agent_id=self.agent_id,
                action='Agent任务异常',
                resource_type='task',
                resource_id=task_id,
                success=False,
                error=str(e)
            )
            return error_result

    def handle_message(self, message) -> Any:
        """
        处理收到的消息（支持AgentRouter协议）

        Args:
            message: AgentMessage消息对象

        Returns:
            Any: 处理结果
        """
        from openclaw.messaging.protocol import AgentMessage, MessageType

        if isinstance(message, dict):
            message = AgentMessage.from_dict(message)

        logger.info(f"Agent {self.agent_id} 收到消息: type={message.msg_type.value}, from={message.sender_id}")

        if message.msg_type == MessageType.TASK:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                task_result = loop.run_until_complete(self.run(message.content))
            finally:
                loop.close()
            return task_result.to_dict() if hasattr(task_result, 'to_dict') else task_result

        elif message.msg_type == MessageType.EVENT:
            self.emit(message.content.get('event'), message.content.get('data'))
            return {'status': 'event_processed'}

        elif message.msg_type == MessageType.HEARTBEAT:
            return {
                'status': 'alive',
                'agent_id': self.agent_id,
                'agent_type': self.agent_type.value if self.agent_type else None,
                'current_status': self.status.value
            }

        else:
            return {'status': 'unknown_message_type'}

    async def handle_message_async(self, message) -> Any:
        """
        异步处理收到的消息（支持AgentRouter协议）

        Args:
            message: AgentMessage消息对象

        Returns:
            Any: 处理结果
        """
        from openclaw.messaging.protocol import AgentMessage, MessageType

        if isinstance(message, dict):
            message = AgentMessage.from_dict(message)

        logger.info(f"Agent {self.agent_id} 异步收到消息: type={message.msg_type.value}, from={message.sender_id}")

        if message.msg_type == MessageType.TASK:
            result = await self.run(message.content)
            return result.to_dict() if hasattr(result, 'to_dict') else result

        elif message.msg_type == MessageType.EVENT:
            self.emit(message.content.get('event'), message.content.get('data'))
            return {'status': 'event_processed'}

        elif message.msg_type == MessageType.HEARTBEAT:
            return {
                'status': 'alive',
                'agent_id': self.agent_id,
                'agent_type': self.agent_type.value if self.agent_type else None,
                'current_status': self.status.value
            }

        else:
            return {'status': 'unknown_message_type'}

    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典
        """
        return {
            'agent_id': self.agent_id,
            'agent_type': self.agent_type.value if self.agent_type else None,
            'session_id': self.session_id,
            'status': self.status.value,
            'context': self.context.to_dict(),
            'config': {
                'max_retries': self.config.max_retries,
                'timeout': self.config.timeout,
                'llm_model': self.config.llm_model
            }
        }
    
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} id={self.agent_id} type={self.agent_type.value if self.agent_type else 'unknown'} status={self.status.value}>"
