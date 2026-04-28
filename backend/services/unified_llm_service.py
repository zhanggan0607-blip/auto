"""
统一大模型服务
支持多模型切换，为不同Agent提供模型服务

使用适配器模式，通过 services.llm.adapters 统一接口调用
"""
import hashlib
import json
import logging
import time
from typing import Any, Dict, List, Optional

from django.core.cache import cache
from apps.openclaw.models import LLMProvider, LLMModel, AgentModelConfig, LLMUsageLog
from services.llm.adapters import get_adapter
from asgiref.sync import sync_to_async


logger = logging.getLogger(__name__)

_USAGE_LOG_BUFFER = []
_USAGE_LOG_BUFFER_SIZE = 20


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
        actual_model_id = model_id
        actual_temperature = temperature
        actual_max_tokens = max_tokens
        actual_system_prompt = system_prompt

        if agent_type:
            def get_config():
                cfg = self.get_model_config(agent_type)
                if cfg:
                    result = {
                        'chat_model_model_id': getattr(cfg.chat_model, 'model_id', None) if cfg.chat_model_id else None,
                        'chat_model_provider': getattr(cfg.chat_model, 'provider', None) if cfg.chat_model_id else None,
                        'temperature': cfg.temperature,
                        'max_tokens': cfg.max_tokens,
                        'system_prompt': cfg.system_prompt,
                    }
                    return result
                return None

            config_data = await sync_to_async(get_config)()
            if config_data:
                if config_data['chat_model_model_id']:
                    actual_model_id = config_data['chat_model_model_id']
                    provider = config_data['chat_model_provider']
                if actual_temperature is None:
                    actual_temperature = config_data['temperature']
                if actual_max_tokens is None:
                    actual_max_tokens = config_data['max_tokens']
                if actual_system_prompt is None:
                    actual_system_prompt = config_data['system_prompt']

        if actual_model_id is None:
            actual_model_id = provider.default_model
        if actual_temperature is None:
            actual_temperature = provider.temperature or 0.7
        if actual_max_tokens is None:
            actual_max_tokens = provider.max_tokens or 4096

        messages = []
        if actual_system_prompt:
            messages.append({'role': 'system', 'content': actual_system_prompt})
        if history:
            messages.extend(history)
        messages.append({'role': 'user', 'content': message})

        cache_key = None
        if actual_temperature is not None and actual_temperature < 0.01:
            cache_key = self._build_cache_key(actual_model_id, messages, actual_max_tokens)
            cached = cache.get(cache_key)
            if cached:
                logger.debug(f"LLM缓存命中: {cache_key[:16]}...")
                return cached

        try:
            adapter = get_adapter(provider)
            content, usage = await adapter.chat(
                model_id=actual_model_id,
                messages=messages,
                temperature=actual_temperature,
                max_tokens=actual_max_tokens
            )

            latency = time.time() - start_time

            await self._log_usage_async(
                provider=provider,
                model=actual_model_id,
                agent_type=agent_type,
                session_id=session_id,
                input_tokens=usage.get('input_tokens', 0),
                output_tokens=usage.get('output_tokens', 0),
                latency=latency,
                success=True
            )

            result = {
                'content': content,
                'input_tokens': usage.get('input_tokens', 0),
                'output_tokens': usage.get('output_tokens', 0),
                'total_tokens': usage.get('total_tokens', 0),
                'latency': latency,
                'model': actual_model_id,
                'provider': provider.name
            }

            if cache_key:
                cache.set(cache_key, result, 3600)

            return result

        except Exception as e:
            latency = time.time() - start_time
            await self._log_usage_async(
                provider=provider,
                model=actual_model_id,
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
        异步记录使用日志（缓冲批量写入）
        """
        global _USAGE_LOG_BUFFER

        log_entry = {
            'provider_id': provider.id if provider else None,
            'model': model,
            'agent_type': agent_type,
            'session_id': session_id,
            'input_tokens': input_tokens,
            'output_tokens': output_tokens,
            'total_tokens': input_tokens + output_tokens,
            'latency': latency,
            'success': success,
            'error_message': error_message
        }

        _USAGE_LOG_BUFFER.append(log_entry)

        if len(_USAGE_LOG_BUFFER) >= _USAGE_LOG_BUFFER_SIZE:
            await self._flush_usage_log_buffer()

    async def _flush_usage_log_buffer(self):
        """
        刷新使用日志缓冲区到数据库
        """
        global _USAGE_LOG_BUFFER

        if not _USAGE_LOG_BUFFER:
            return

        logs_to_write = _USAGE_LOG_BUFFER[:]
        _USAGE_LOG_BUFFER = []

        try:
            def _bulk_create():
                log_objects = []
                for entry in logs_to_write:
                    try:
                        provider = LLMProvider.objects.get(id=entry['provider_id']) if entry['provider_id'] else None
                        log_objects.append(LLMUsageLog(
                            provider=provider,
                            model=entry['model'],
                            agent_type=entry['agent_type'],
                            session_id=entry['session_id'],
                            input_tokens=entry['input_tokens'],
                            output_tokens=entry['output_tokens'],
                            total_tokens=entry['total_tokens'],
                            latency=entry['latency'],
                            success=entry['success'],
                            error_message=entry['error_message']
                        ))
                    except Exception:
                        pass
                if log_objects:
                    LLMUsageLog.objects.bulk_create(log_objects, ignore_conflicts=True)

            await sync_to_async(_bulk_create)()
        except Exception as e:
            logger.error(f"批量写入使用日志失败: {str(e)}")

    @staticmethod
    def _build_cache_key(model_id: str, messages: List[Dict], max_tokens: int) -> str:
        """
        构建LLM响应缓存键
        """
        content = json.dumps(messages, ensure_ascii=False, sort_keys=True)
        content_hash = hashlib.md5(content.encode()).hexdigest()
        return f"llm:cache:{model_id}:{content_hash}:{max_tokens}"

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

    async def analyze_image(
        self,
        image_base64: str,
        prompt: str,
        model_id: str = 'qwen3-vl:8b',
        agent_type: str = 'vision',
        max_tokens: int = 8192
    ) -> Dict[str, Any]:
        """
        使用视觉模型分析图片（异步版本）
        """
        import httpx
        import json
        from django.conf import settings

        base_url = getattr(settings, 'OLLAMA_BASE_URL', 'http://localhost:11434')
        url = f"{base_url}/api/generate"

        payload = {
            'model': model_id,
            'prompt': prompt,
            'images': [image_base64],
            'stream': False,
            'thinking': False,
            'options': {
                'temperature': 0.1,
                'num_predict': max_tokens
            }
        }

        try:
            async with httpx.AsyncClient(timeout=600) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                data = response.json()
                content = data.get('response', '')
                return {
                    'content': content,
                    'success': True,
                    'model': model_id
                }
        except Exception as e:
            logger.error(f"视觉分析失败: {str(e)}")
            return {
                'content': '',
                'success': False,
                'error': str(e),
                'model': model_id
            }


unified_llm_service = UnifiedLLMService()
