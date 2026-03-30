"""
统一大模型服务
支持多模型切换，为不同Agent提供模型服务

使用适配器模式，核心调用逻辑下沉到 llm_adapters.py
"""
import logging
import time
from typing import Any, Dict, List, Optional

from apps.openclaw.models import LLMProvider, LLMModel, AgentModelConfig, LLMUsageLog
from .llm_adapters import get_adapter
from asgiref.sync import sync_to_async


logger = logging.getLogger(__name__)


class UnifiedLLMService:
    """
    统一大模型服务
    支持多提供商、多模型切换
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
        self._default_provider = None
        self._load_default_provider()

    def _load_default_provider(self):
        """
        加载默认提供商
        """
        try:
            self._default_provider = LLMProvider.objects.filter(
                is_active=True,
                is_default=True
            ).first()

            if not self._default_provider:
                self._default_provider = LLMProvider.objects.filter(is_active=True).first()
        except Exception as e:
            logger.warning(f"加载默认提供商失败: {str(e)}")

    async def get_provider_async(self, provider_id: int = None) -> Optional[LLMProvider]:
        """
        异步获取提供商
        """
        if provider_id:
            return await sync_to_async(
                lambda: LLMProvider.objects.filter(id=provider_id, is_active=True).first()
            )()
        return self._default_provider

    def get_provider(self, provider_id: int = None) -> Optional[LLMProvider]:
        """
        获取提供商（同步版本）
        """
        if provider_id:
            return LLMProvider.objects.filter(id=provider_id, is_active=True).first()
        return self._default_provider

    def get_model_config(self, agent_type: str) -> Optional[AgentModelConfig]:
        """
        获取Agent模型配置
        """
        return AgentModelConfig.objects.filter(
            agent_type=agent_type,
            is_active=True
        ).first()

    async def chat(
        self,
        message: str,
        provider_id: int = None,
        model_id: str = None,
        agent_type: str = None,
        temperature: float = None,
        max_tokens: int = None,
        system_prompt: str = None,
        history: List[Dict] = None,
        session_id: str = None
    ) -> Dict[str, Any]:
        """
        统一聊天接口

        Args:
            message: 用户消息
            provider_id: 提供商ID
            model_id: 模型ID
            agent_type: Agent类型（自动选择模型）
            temperature: 温度参数
            max_tokens: 最大Token数
            system_prompt: 系统提示词
            history: 历史对话
            session_id: 会话ID

        Returns:
            dict: {content, tokens, latency, model}
        """
        start_time = time.time()

        provider = await self.get_provider_async(provider_id)
        if not provider:
            raise ValueError("没有可用的模型提供商")

        model_config = None
        if agent_type:
            model_config = self.get_model_config(agent_type)
            if model_config:
                if model_config.chat_model:
                    model_id = model_config.chat_model.model_id
                    provider = model_config.chat_model.provider
                if temperature is None:
                    temperature = model_config.temperature
                if max_tokens is None:
                    max_tokens = model_config.max_tokens
                if system_prompt is None and model_config.system_prompt:
                    system_prompt = model_config.system_prompt

        if model_id is None:
            model_id = provider.default_model
        if temperature is None:
            temperature = provider.temperature or 0.7
        if max_tokens is None:
            max_tokens = provider.max_tokens or 4096

        messages = []
        if system_prompt:
            messages.append({'role': 'system', 'content': system_prompt})
        if history:
            messages.extend(history)
        messages.append({'role': 'user', 'content': message})

        try:
            adapter = get_adapter(provider)
            content, usage = await adapter.chat(
                model_id=model_id,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )

            latency = time.time() - start_time

            await self._log_usage_async(
                provider=provider,
                model=model_id,
                agent_type=agent_type,
                session_id=session_id,
                input_tokens=usage.get('input_tokens', 0),
                output_tokens=usage.get('output_tokens', 0),
                latency=latency,
                success=True
            )

            return {
                'content': content,
                'input_tokens': usage.get('input_tokens', 0),
                'output_tokens': usage.get('output_tokens', 0),
                'total_tokens': usage.get('total_tokens', 0),
                'latency': latency,
                'model': model_id,
                'provider': provider.name
            }

        except Exception as e:
            latency = time.time() - start_time
            await self._log_usage_async(
                provider=provider,
                model=model_id,
                agent_type=agent_type,
                session_id=session_id,
                latency=latency,
                success=False,
                error_message=str(e)
            )
            raise

    def _log_usage(
        self,
        provider: LLMProvider,
        model: str,
        agent_type: str,
        session_id: str,
        input_tokens: int = 0,
        output_tokens: int = 0,
        latency: float = 0,
        success: bool = True,
        error_message: str = None
    ):
        """
        记录使用日志
        """
        try:
            LLMUsageLog.objects.create(
                provider=provider,
                model=model,
                agent_type=agent_type,
                session_id=session_id,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                total_tokens=input_tokens + output_tokens,
                latency=latency,
                success=success,
                error_message=error_message
            )
        except Exception as e:
            logger.error(f"记录使用日志失败: {str(e)}")

    async def _log_usage_async(
        self,
        provider: LLMProvider,
        model: str,
        agent_type: str,
        session_id: str,
        input_tokens: int = 0,
        output_tokens: int = 0,
        latency: float = 0,
        success: bool = True,
        error_message: str = None
    ):
        """
        异步记录使用日志
        """
        try:
            await sync_to_async(LLMUsageLog.objects.create)(
                provider=provider,
                model=model,
                agent_type=agent_type,
                session_id=session_id,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                total_tokens=input_tokens + output_tokens,
                latency=latency,
                success=success,
                error_message=error_message
            )
        except Exception as e:
            logger.error(f"异步记录使用日志失败: {str(e)}")

    async def reasoning(
        self,
        question: str,
        context: str = None,
        agent_type: str = None,
        session_id: str = None
    ) -> Dict[str, Any]:
        """
        推理接口
        用于复杂决策和分析
        """
        model_config = self.get_model_config(agent_type)
        reasoning_model = None

        if model_config and model_config.reasoning_model:
            reasoning_model = model_config.reasoning_model

        system_prompt = """你是一个专业的招投标分析专家。请基于提供的信息进行深入分析，给出详细的推理过程和结论。

分析要求：
1. 仔细分析问题背景和关键信息
2. 列出分析步骤和推理过程
3. 给出明确的结论和建议
4. 如有风险，请明确指出

请以结构化的方式输出分析结果。"""

        if context:
            message = f"背景信息：\n{context}\n\n问题：\n{question}"
        else:
            message = question

        provider_id = reasoning_model.provider_id if reasoning_model else None
        model_id = reasoning_model.model_id if reasoning_model else None

        return await self.chat(
            message=message,
            provider_id=provider_id,
            model_id=model_id,
            agent_type=agent_type,
            system_prompt=system_prompt,
            session_id=session_id
        )


unified_llm_service = UnifiedLLMService()
