"""
LLM适配器模块
通过适配器模式统一不同Provider的调用方式
"""
from .base import BaseLLMAdapter
from .openai_compatible import OpenAICompatibleAdapter
from .ollama import OllamaAdapter
from .qwen import QwenAdapter
from .wenxin import WenxinAdapter
from .registry import ADAPTER_REGISTRY, get_adapter

__all__ = [
    'BaseLLMAdapter',
    'OpenAICompatibleAdapter',
    'OllamaAdapter',
    'QwenAdapter',
    'WenxinAdapter',
    'ADAPTER_REGISTRY',
    'get_adapter',
]