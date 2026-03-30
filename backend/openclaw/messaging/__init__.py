"""
Agent消息通信模块
"""
from .protocol import (
    AgentMessage,
    AgentRouter,
    MessageType,
    MessagePriority,
    agent_router
)

__all__ = [
    'AgentMessage',
    'AgentRouter',
    'MessageType',
    'MessagePriority',
    'agent_router'
]
