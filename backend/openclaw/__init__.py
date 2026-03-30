"""
OpenCAL Agent引擎模块
Gateway-Pi-Embedded 三层架构 + 多Agent系统

架构说明:
- Gateway层: WebSocket控制平面 + RESTful辅助接口 + 消息路由
- Pi层: Agent管理 + 工作流编排 + 技能注册 + 记忆系统
- Embedded层: 沙箱执行 + 技能执行 + 外部API调用

目录结构：
openclaw/
├── architecture/            # 三层架构核心
│   ├── __init__.py
│   ├── gateway.py          # Gateway层实现
│   ├── pi.py               # Pi层实现
│   └── embedded.py         # Embedded层实现
├── base_agent.py           # Agent基类
├── agent_manager.py        # Agent管理器
├── skill_registry.py       # 技能注册表
├── config.py               # 配置
├── main.py                 # 系统启动入口
├── agents/                 # Agent实现
│   ├── professional_agents.py  # 专业Agent
│   ├── bid_collector_agent.py
│   ├── bid_document_agents.py
│   ├── bid_tracker_agents.py
│   └── bid_workflow_orchestrator.py
├── skills/                 # 技能实现
│   ├── collector/
│   ├── generator/
│   ├── parser/
│   └── uploader/

注意：
- Django模型在 apps/openclaw/ 目录
- 此目录只包含Agent引擎实现代码
- LLM服务请使用 services.unified_llm_service.UnifiedLLMService
"""

from openclaw.architecture import (
    GatewayManager,
    MessageRouter,
    PiLayerManager,
    AgentOrchestrator,
    EmbeddedExecutor,
    SandboxManager,
)
from openclaw.architecture.gateway import gateway_manager
from openclaw.architecture.pi import pi_layer_manager, agent_orchestrator
from openclaw.architecture.embedded import embedded_executor, sandbox_manager


__all__ = [
    'GatewayManager',
    'MessageRouter',
    'PiLayerManager',
    'AgentOrchestrator',
    'EmbeddedExecutor',
    'SandboxManager',
    'gateway_manager',
    'pi_layer_manager',
    'agent_orchestrator',
    'embedded_executor',
    'sandbox_manager',
]
