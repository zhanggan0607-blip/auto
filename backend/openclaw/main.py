"""
OpenCAL 系统启动入口
三层架构 + 多Agent系统启动脚本
"""
import asyncio
import logging
import os
import sys
from pathlib import Path

import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
sys.path.insert(0, str(Path(__file__).parent.parent))

django.setup()

logger = logging.getLogger(__name__)


class OpenCALSystem:
    """
    OpenCAL系统管理器
    统一管理三层架构组件
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
        
        self.gateway = None
        self.pi_layer = None
        self.embedded = None
        
        self._running = False
    
    async def initialize(self):
        """
        初始化系统
        """
        logger.info("=" * 60)
        logger.info("OpenCAL 系统初始化")
        logger.info("架构: Gateway-Pi-Embedded 三层架构")
        logger.info("=" * 60)
        
        from openclaw.architecture.gateway import gateway_manager
        from openclaw.architecture.pi import pi_layer_manager
        from openclaw.architecture.embedded import embedded_executor, sandbox_manager
        
        self.gateway = gateway_manager
        self.pi_layer = pi_layer_manager
        self.embedded = embedded_executor
        
        await self._init_agents()
        
        await self._init_skills()
        
        await self._init_workflows()
        
        logger.info("OpenCAL 系统初始化完成")
    
    async def _init_agents(self):
        """
        初始化Agent注册
        """
        from openclaw.agent_manager import agent_manager
        from openclaw.base_agent import AgentType
        from openclaw.agents.professional_agents import (
            TenderCollectorAgent,
            EnterpriseMatcherAgent,
            BidDocumentGeneratorAgent,
            BidReviewAgent,
            SupervisorAgent
        )
        
        agent_manager.register_agent_class(AgentType.COLLECTOR, TenderCollectorAgent)
        agent_manager.register_agent_class(AgentType.MATCHER, EnterpriseMatcherAgent)
        agent_manager.register_agent_class(AgentType.GENERATOR, BidDocumentGeneratorAgent)
        agent_manager.register_agent_class(AgentType.REVIEWER, BidReviewAgent)
        agent_manager.register_agent_class(AgentType.SUPERVISOR, SupervisorAgent)
        
        logger.info("Agent注册完成")
    
    async def _init_skills(self):
        """
        初始化技能注册
        """
        from openclaw.skill_registry import skill_registry
        
        skills = skill_registry.list_skills()
        logger.info(f"已加载 {len(skills)} 个技能")
    
    async def _init_workflows(self):
        """
        初始化工作流注册
        """
        from openclaw.architecture.pi import agent_orchestrator
        from openclaw.agents.bid_workflow_orchestrator import BidWorkflowOrchestrator
        
        logger.info("工作流注册完成")
    
    async def start_gateway(self, host: str = '127.0.0.1', port: int = 18789):
        """
        启动Gateway服务
        """
        from openclaw.config import OPENCLAW_CONFIG
        
        logger.info(f"启动Gateway服务: ws://{host}:{port}")
        
        try:
            import websockets
            from websockets.server import serve
            
            async with serve(
                self.gateway.handle_connection,
                host,
                port,
                ping_interval=OPENCLAW_CONFIG.gateway.heartbeat_interval,
                ping_timeout=10
            ):
                logger.info(f"Gateway服务已启动: ws://{host}:{port}")
                self._running = True
                await asyncio.Future()
                
        except ImportError:
            logger.warning("websockets未安装，使用Django Channels")
            self._running = True
    
    async def start(self):
        """
        启动完整系统
        """
        await self.initialize()
        
        from openclaw.config import OPENCLAW_CONFIG
        
        await self.start_gateway(
            host=OPENCLAW_CONFIG.gateway.host,
            port=OPENCLAW_CONFIG.gateway.port
        )
    
    async def stop(self):
        """
        停止系统
        """
        self._running = False
        logger.info("OpenCAL 系统已停止")
    
    def get_status(self) -> dict:
        """
        获取系统状态
        """
        return {
            'running': self._running,
            'gateway': self.gateway.get_stats() if self.gateway else None,
            'pi_layer': self.pi_layer.get_stats() if self.pi_layer else None,
            'embedded': self.embedded.get_stats() if self.embedded else None
        }


opencal_system = OpenCALSystem()


async def run_standalone():
    """
    独立运行模式
    """
    system = OpenCALSystem()
    
    try:
        await system.start()
    except KeyboardInterrupt:
        logger.info("收到中断信号，正在停止...")
        await system.stop()


def run_with_django():
    """
    Django集成模式
    """
    import asyncio
    
    system = OpenCALSystem()
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    loop.run_until_complete(system.initialize())
    
    logger.info("OpenCAL系统已初始化，等待Django Channels启动WebSocket服务")
    
    return system


if __name__ == '__main__':
    asyncio.run(run_standalone())
