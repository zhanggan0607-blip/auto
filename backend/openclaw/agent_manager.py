"""
OpenClaw Agent管理器
管理多Agent协同和会话隔离
"""
import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Type
from .base_agent import BaseAgent, AgentStatus, AgentType, TaskResult
from .config import OPENCLAW_CONFIG


logger = logging.getLogger(__name__)


class AgentManager:
    """
    Agent管理器
    负责Agent的创建、销毁、调度和协同
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
        self.config = OPENCLAW_CONFIG.pi_layer
        
        self._agents: Dict[str, BaseAgent] = {}
        self._sessions: Dict[str, Dict[str, BaseAgent]] = {}
        self._agent_classes: Dict[AgentType, Type[BaseAgent]] = {}
        
        self._task_queue: asyncio.Queue = None
        self._running = False
        self._lock = asyncio.Lock()
    
    def register_agent_class(self, agent_type: AgentType, agent_class: Type[BaseAgent]):
        """
        注册Agent类
        
        Args:
            agent_type: Agent类型
            agent_class: Agent类
        """
        self._agent_classes[agent_type] = agent_class
        logger.info(f"Registered agent class: {agent_type.value}")
    
    def get_agent_class(self, agent_type: AgentType) -> Optional[Type[BaseAgent]]:
        """
        获取Agent类
        """
        return self._agent_classes.get(agent_type)
    
    async def create_agent(
        self,
        agent_type: AgentType,
        agent_id: str = None,
        session_id: str = None,
        **kwargs
    ) -> BaseAgent:
        """
        创建Agent
        
        Args:
            agent_type: Agent类型
            agent_id: 指定Agent ID
            session_id: 会话ID
            **kwargs: 其他参数
            
        Returns:
            BaseAgent: 创建的Agent实例
        """
        agent_class = self.get_agent_class(agent_type)
        if not agent_class:
            raise ValueError(f"Agent type not registered: {agent_type.value}")
        
        if len(self._agents) >= self.config.max_agents:
            raise RuntimeError(f"Max agents limit reached: {self.config.max_agents}")
        
        agent = agent_class(agent_id=agent_id, session_id=session_id, **kwargs)
        
        async with self._lock:
            self._agents[agent.agent_id] = agent
            
            if session_id:
                if session_id not in self._sessions:
                    self._sessions[session_id] = {}
                self._sessions[session_id][agent.agent_id] = agent
        
        logger.info(f"Created agent: {agent.agent_id}, type: {agent_type.value}")
        return agent
    
    async def get_agent(self, agent_id: str) -> Optional[BaseAgent]:
        """
        获取Agent
        """
        return self._agents.get(agent_id)
    
    async def get_session_agents(self, session_id: str) -> Dict[str, BaseAgent]:
        """
        获取会话中的所有Agent
        """
        return self._sessions.get(session_id, {})
    
    async def destroy_agent(self, agent_id: str):
        """
        销毁Agent
        """
        async with self._lock:
            agent = self._agents.pop(agent_id, None)
            if agent:
                session_id = agent.session_id
                if session_id in self._sessions:
                    self._sessions[session_id].pop(agent_id, None)
                    if not self._sessions[session_id]:
                        del self._sessions[session_id]
                
                agent.set_status(AgentStatus.STOPPED)
                logger.info(f"Destroyed agent: {agent_id}")
    
    async def destroy_session(self, session_id: str):
        """
        销毁会话及其所有Agent
        """
        async with self._lock:
            session_agents = self._sessions.pop(session_id, {})
            for agent_id in list(session_agents.keys()):
                agent = self._agents.pop(agent_id, None)
                if agent:
                    agent.set_status(AgentStatus.STOPPED)
            
            logger.info(f"Destroyed session: {session_id}, agents: {len(session_agents)}")
    
    async def execute_agent_task(
        self,
        agent_id: str,
        task: Dict[str, Any]
    ) -> TaskResult:
        """
        执行Agent任务
        """
        agent = await self.get_agent(agent_id)
        if not agent:
            return TaskResult(
                success=False,
                error=f"Agent not found: {agent_id}"
            )
        
        return await agent.run(task)
    
    async def broadcast_to_session(
        self,
        session_id: str,
        message: Dict[str, Any],
        exclude_agent_id: str = None
    ):
        """
        向会话中的所有Agent广播消息
        """
        session_agents = await self.get_session_agents(session_id)
        for agent_id, agent in session_agents.items():
            if agent_id != exclude_agent_id:
                agent.add_message('system', message)
    
    async def create_child_agent(
        self,
        parent_agent_id: str,
        agent_type: AgentType,
        **kwargs
    ) -> BaseAgent:
        """
        创建子Agent
        """
        parent = await self.get_agent(parent_agent_id)
        if not parent:
            raise ValueError(f"Parent agent not found: {parent_agent_id}")
        
        child = await self.create_agent(
            agent_type=agent_type,
            session_id=parent.session_id,
            **kwargs
        )
        
        parent.context.child_agent_ids.append(child.agent_id)
        child.context.parent_agent_id = parent_agent_id
        
        logger.info(f"Created child agent: {child.agent_id}, parent: {parent_agent_id}")
        return child
    
    async def get_agent_status(self, agent_id: str) -> Optional[Dict]:
        """
        获取Agent状态
        """
        agent = await self.get_agent(agent_id)
        if agent:
            return agent.to_dict()
        return None
    
    async def list_agents(
        self,
        session_id: str = None,
        agent_type: AgentType = None,
        status: AgentStatus = None
    ) -> List[Dict]:
        """
        列出Agent
        """
        agents = []
        
        if session_id:
            agent_dict = self._sessions.get(session_id, {})
            agent_list = agent_dict.values()
        else:
            agent_list = self._agents.values()
        
        for agent in agent_list:
            if agent_type and agent.agent_type != agent_type:
                continue
            if status and agent.status != status:
                continue
            agents.append(agent.to_dict())
        
        return agents
    
    async def cleanup_idle_agents(self, timeout_seconds: int = None):
        """
        清理空闲Agent
        """
        timeout = timeout_seconds or self.config.session_timeout
        now = datetime.now()
        
        to_remove = []
        for agent_id, agent in self._agents.items():
            if agent.status == AgentStatus.IDLE:
                idle_time = (now - agent.context.updated_at).total_seconds()
                if idle_time > timeout:
                    to_remove.append(agent_id)
        
        for agent_id in to_remove:
            await self.destroy_agent(agent_id)
        
        if to_remove:
            logger.info(f"Cleaned up {len(to_remove)} idle agents")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        获取统计信息
        """
        status_counts = {}
        for agent in self._agents.values():
            status = agent.status.value
            status_counts[status] = status_counts.get(status, 0) + 1
        
        return {
            'total_agents': len(self._agents),
            'total_sessions': len(self._sessions),
            'status_distribution': status_counts,
            'max_agents': self.config.max_agents
        }


agent_manager = AgentManager()
