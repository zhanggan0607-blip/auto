"""
LLM Provider适配器模块
通过适配器模式统一不同Provider的调用方式，消除重复代码
"""
import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Tuple, Any, Optional

logger = logging.getLogger(__name__)


class BaseLLMAdapter(ABC):
    """
    LLM适配器基类
    所有Provider适配器必须继承此类并实现抽象方法
    """

    provider_type: str = None

    def __init__(self, provider):
        """
        初始化适配器

        Args:
            provider: LLMProvider模型实例
        """
        self.provider = provider
        self._session = None

    def get_session(self):
        """
        获取HTTP会话（延迟初始化，会话复用）
        """
        if self._session is None:
            import requests
            self._session = requests.Session()
            self._session.headers.update({'Content-Type': 'application/json'})
            if self.provider.api_key:
                self._session.headers.update({
                    'Authorization': f'Bearer {self.provider.api_key}'
                })
        return self._session

    @abstractmethod
    def build_url(self, model_id: str) -> str:
        """
        构建API请求URL

        Args:
            model_id: 模型ID

        Returns:
            str: 完整的API URL
        """
        pass

    @abstractmethod
    def build_payload(
        self,
        model_id: str,
        messages: List[Dict],
        temperature: float,
        max_tokens: int
    ) -> dict:
        """
        构建请求Payload

        Args:
            model_id: 模型ID
            messages: 消息列表
            temperature: 温度参数
            max_tokens: 最大Token数

        Returns:
            dict: 请求体
        """
        pass

    @abstractmethod
    def parse_response(self, response: dict) -> Tuple[str, dict]:
        """
        解析响应数据

        Args:
            response: API响应字典

        Returns:
            Tuple[str, dict]: (内容, 使用量信息)
        """
        pass

    def get_headers(self) -> dict:
        """
        获取请求头（可被子类重写）
        """
        return {}

    async def chat(
        self,
        model_id: str,
        messages: List[Dict],
        temperature: float,
        max_tokens: int
    ) -> Tuple[str, dict]:
        """
        统一聊天接口

        Args:
            model_id: 模型ID
            messages: 消息列表
            temperature: 温度参数
            max_tokens: 最大Token数

        Returns:
            Tuple[str, dict]: (内容, 使用量信息)
        """
        url = self.build_url(model_id)
        payload = self.build_payload(model_id, messages, temperature, max_tokens)
        headers = self.get_headers()

        loop = asyncio.get_event_loop()

        def sync_request():
            session = self.get_session()
            timeout = getattr(self.provider, 'timeout', 60) or 60
            if headers:
                response = session.post(url, json=payload, headers=headers, timeout=timeout)
            else:
                response = session.post(url, json=payload, timeout=timeout)
            response.raise_for_status()
            return response.json()

        result = await loop.run_in_executor(None, sync_request)
        return self.parse_response(result)


class OpenAICompatibleAdapter(BaseLLMAdapter):
    """
    OpenAI兼容API适配器
    适用于: OpenAI, vLLM, DeepSeek, Kimi, 智谱AI 等
    """

    provider_type = 'openai_compatible'

    def build_url(self, model_id: str) -> str:
        base_url = getattr(self.provider, 'base_url', '').rstrip('/')
        return f"{base_url}/v1/chat/completions"

    def build_payload(
        self,
        model_id: str,
        messages: List[Dict],
        temperature: float,
        max_tokens: int
    ) -> dict:
        return {
            'model': model_id,
            'messages': messages,
            'temperature': temperature,
            'max_tokens': max_tokens
        }

    def parse_response(self, response: dict) -> Tuple[str, dict]:
        choices = response.get('choices', [])
        content = choices[0].get('message', {}).get('content', '') if choices else ''
        usage = response.get('usage', {})
        return content, {
            'input_tokens': usage.get('prompt_tokens', 0),
            'output_tokens': usage.get('completion_tokens', 0),
            'total_tokens': usage.get('total_tokens', 0)
        }


class OllamaAdapter(BaseLLMAdapter):
    """
    Ollama本地模型适配器
    API格式与OpenAI略有不同
    """

    provider_type = 'ollama'

    def build_url(self, model_id: str) -> str:
        base_url = getattr(self.provider, 'base_url', '').rstrip('/')
        return f"{base_url}/api/chat"

    def build_payload(
        self,
        model_id: str,
        messages: List[Dict],
        temperature: float,
        max_tokens: int
    ) -> dict:
        return {
            'model': model_id,
            'messages': messages,
            'temperature': temperature,
            'stream': False
        }

    def chat_stream(
        self,
        model_id: str,
        messages: List[Dict],
        temperature: float,
        max_tokens: int
    ):
        """
        流式聊天接口，返回 generator
        Ollama 使用 application/x-ndjson 格式（非SSE）
        使用同步 httpx.Session 避免缓冲问题
        """
        import httpx
        import json
        base_url = getattr(self.provider, 'base_url', '').rstrip('/')
        url = f"{base_url}/api/chat"
        payload = {
            'model': model_id,
            'messages': messages,
            'temperature': temperature,
            'stream': True
        }

        accumulated_content = ''
        line_buffer = ''

        with httpx.Client(timeout=300, headers={'Accept': 'application/x-ndjson'}) as client:
            with client.stream('POST', url, json=payload) as response:
                response.raise_for_status()
                for chunk in response.iter_bytes():
                    chunk_str = chunk.decode('utf-8')
                    line_buffer += chunk_str

                    while '\n' in line_buffer:
                        line, line_buffer = line_buffer.split('\n', 1)
                        if not line:
                            continue
                        try:
                            data = json.loads(line)
                            content = data.get('message', {}).get('content', '')
                            if content:
                                accumulated_content += content
                                yield content
                        except json.JSONDecodeError:
                            pass

        yield '__COMPLETE__', {'content': accumulated_content}

    def parse_response(self, response: dict) -> Tuple[str, dict]:
        content = response.get('message', {}).get('content', '')
        eval_count = response.get('eval_count', 0)
        prompt_eval_count = response.get('prompt_eval_count', 0)
        return content, {
            'input_tokens': prompt_eval_count,
            'output_tokens': eval_count,
            'total_tokens': prompt_eval_count + eval_count
        }


class QwenAdapter(BaseLLMAdapter):
    """
    通义千问API适配器
    请求格式与其他Provider不同
    """

    provider_type = 'qwen'

    def build_url(self, model_id: str) -> str:
        return "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"

    def build_payload(
        self,
        model_id: str,
        messages: List[Dict],
        temperature: float,
        max_tokens: int
    ) -> dict:
        return {
            'model': model_id,
            'input': {
                'messages': messages
            },
            'parameters': {
                'temperature': temperature,
                'max_tokens': max_tokens
            }
        }

    def parse_response(self, response: dict) -> Tuple[str, dict]:
        output = response.get('output', {})
        content = output.get('text', '')
        usage = response.get('usage', {})
        return content, {
            'input_tokens': usage.get('input_tokens', 0),
            'output_tokens': usage.get('output_tokens', 0),
            'total_tokens': usage.get('input_tokens', 0) + usage.get('output_tokens', 0)
        }


class WenxinAdapter(BaseLLMAdapter):
    """
    百度文心一言API适配器
    需要特殊的认证方式
    """

    provider_type = 'wenxin'

    def build_url(self, model_id: str) -> str:
        return "https://qianfan.baidubce.com/v2/chat/completions"

    def get_headers(self) -> dict:
        access_token = self.provider.api_key
        if access_token:
            return {'Authorization': f'Bearer {access_token}'}
        return {}

    def build_payload(
        self,
        model_id: str,
        messages: List[Dict],
        temperature: float,
        max_tokens: int
    ) -> dict:
        return {
            'model': model_id,
            'messages': messages,
            'temperature': temperature,
            'max_tokens': max_tokens
        }

    def parse_response(self, response: dict) -> Tuple[str, dict]:
        choices = response.get('choices', [])
        content = choices[0].get('message', {}).get('content', '') if choices else ''
        usage = response.get('usage', {})
        return content, {
            'input_tokens': usage.get('prompt_tokens', 0),
            'output_tokens': usage.get('completion_tokens', 0),
            'total_tokens': usage.get('total_tokens', 0)
        }


ADAPTER_REGISTRY: Dict[str, type] = {
    'ollama': OllamaAdapter,
    'vllm': OpenAICompatibleAdapter,
    'openai': OpenAICompatibleAdapter,
    'zhipu': OpenAICompatibleAdapter,
    'qwen': QwenAdapter,
    'deepseek': OpenAICompatibleAdapter,
    'kimi': OpenAICompatibleAdapter,
    'wenxin': WenxinAdapter,
}


def get_adapter(provider) -> BaseLLMAdapter:
    """
    根据Provider类型获取对应的适配器

    Args:
        provider: LLMProvider模型实例

    Returns:
        BaseLLMAdapter: 适配器实例
    """
    provider_type = getattr(provider, 'provider_type', 'openai')

    adapter_class = ADAPTER_REGISTRY.get(provider_type)
    if adapter_class is None:
        logger.warning(f"未知的Provider类型: {provider_type}，使用OpenAI兼容适配器")
        adapter_class = OpenAICompatibleAdapter

    return adapter_class(provider)
