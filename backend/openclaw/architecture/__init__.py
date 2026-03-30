"""
OpenCAL 三层架构核心模块
Gateway-Pi-Embedded 架构实现

架构说明:
- Gateway层: WebSocket控制平面 + RESTful辅助接口
- Pi层: Agent管理 + 工作流编排 + 技能注册
- Embedded层: 沙箱执行 + 技能执行 + 外部API调用
"""
from .gateway import GatewayManager, MessageRouter
from .pi import PiLayerManager, AgentOrchestrator
from .embedded import EmbeddedExecutor, SandboxManager

__all__ = [
    'GatewayManager',
    'MessageRouter',
    'PiLayerManager',
    'AgentOrchestrator',
    'EmbeddedExecutor',
    'SandboxManager',
]
