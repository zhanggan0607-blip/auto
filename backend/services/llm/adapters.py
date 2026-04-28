"""
LLM适配器模块
通过适配器模式统一不同Provider的调用方式

此模块作为代理，将调用转发到 services.llm_adapters
保持向后兼容性
"""
from services.llm_adapters import (
    BaseLLMAdapter,
    OpenAICompatibleAdapter,
    OllamaAdapter,
    QwenAdapter,
    WenxinAdapter,
    ADAPTER_REGISTRY,
    get_adapter,
)

__all__ = [
    'BaseLLMAdapter',
    'OpenAICompatibleAdapter',
    'OllamaAdapter',
    'QwenAdapter',
    'WenxinAdapter',
    'ADAPTER_REGISTRY',
    'get_adapter',
]