"""
OpenClaw配置模块
支持三层架构 + 多Agent系统
"""
import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from pathlib import Path


@dataclass
class GatewayConfig:
    """
    Gateway网关配置
    """
    host: str = '127.0.0.1'
    port: int = 18789
    max_connections: int = 1000
    heartbeat_interval: int = 30
    message_timeout: int = 300
    cors_origins: List[str] = field(default_factory=lambda: ['*'])
    
    message_queue_size: int = 1000
    broadcast_enabled: bool = True
    event_retention_seconds: int = 3600


@dataclass
class PiLayerConfig:
    """
    Pi层配置
    """
    max_agents: int = 100
    session_timeout: int = 3600
    max_retries: int = 3
    retry_delay: float = 1.0
    task_timeout: int = 600
    
    workflow_max_concurrent: int = 10
    workflow_timeout: int = 3600
    
    memory_max_entries: int = 10000
    memory_ttl: int = 86400


@dataclass
class EmbeddedConfig:
    """
    Embedded层配置
    """
    sandbox_enabled: bool = True
    sandbox_memory_limit: int = 512
    sandbox_cpu_limit: float = 1.0
    sandbox_timeout: int = 60
    sandbox_max_output_size: int = 1048576
    
    allowed_modules: List[str] = field(default_factory=lambda: [
        'json', 'math', 're', 'datetime', 'collections', 'itertools',
        'functools', 'typing', 'copy', 'decimal', 'fractions', 'random',
        'string', 'textwrap', 'pathlib'
    ])
    blocked_modules: List[str] = field(default_factory=lambda: [
        'subprocess', 'socket', 'multiprocessing', 'threading',
        'ctypes', 'pickle', 'shelve', 'marshal', 'imp'
    ])
    
    network_enabled: bool = False
    file_access_enabled: bool = False


@dataclass
class AgentConfig:
    """
    Agent配置
    """
    max_agents: int = 100
    session_timeout: int = 3600
    max_retries: int = 3
    retry_delay: float = 1.0
    task_timeout: int = 600
    
    default_llm_model: str = 'qwen2.5:14b'
    default_temperature: float = 0.7
    default_max_tokens: int = 4096
    
    enable_memory: bool = True
    enable_tools: bool = True


@dataclass
class SkillConfig:
    """
    Skill技能配置
    """
    skills_dir: str = ''
    auto_reload: bool = True
    cache_enabled: bool = True
    cache_ttl: int = 3600
    max_concurrent_skills: int = 10


@dataclass
class LLMConfig:
    """
    本地大模型配置
    """
    provider: str = 'ollama'
    base_url: str = 'http://localhost:11434'
    
    main_model: str = 'qwen2.5:14b'
    main_model_temperature: float = 0.7
    main_model_max_tokens: int = 4096
    
    code_model: str = 'deepseek-coder-v2:lite'
    code_model_temperature: float = 0.3
    
    vision_model: str = 'qwen2.5-vl:7b'
    
    embedding_model: str = 'bge-m3'
    embedding_dimension: int = 1024
    
    api_key: str = ''
    timeout: int = 120


@dataclass
class OpenClawConfig:
    """
    OpenClaw主配置
    三层架构 + 多Agent系统
    """
    gateway: GatewayConfig = field(default_factory=GatewayConfig)
    pi_layer: PiLayerConfig = field(default_factory=PiLayerConfig)
    embedded: EmbeddedConfig = field(default_factory=EmbeddedConfig)
    agent: AgentConfig = field(default_factory=AgentConfig)
    skill: SkillConfig = field(default_factory=SkillConfig)
    llm: LLMConfig = field(default_factory=LLMConfig)
    
    debug: bool = False
    log_level: str = 'INFO'
    
    @classmethod
    def from_env(cls) -> 'OpenClawConfig':
        """
        从环境变量加载配置
        """
        config = cls()
        
        config.gateway.host = os.getenv('OPENCLAW_GATEWAY_HOST', config.gateway.host)
        config.gateway.port = int(os.getenv('OPENCLAW_GATEWAY_PORT', config.gateway.port))
        config.gateway.max_connections = int(os.getenv('OPENCLAW_MAX_CONNECTIONS', config.gateway.max_connections))
        
        config.pi_layer.max_agents = int(os.getenv('OPENCLAW_MAX_AGENTS', config.pi_layer.max_agents))
        config.pi_layer.session_timeout = int(os.getenv('OPENCLAW_SESSION_TIMEOUT', config.pi_layer.session_timeout))
        
        config.llm.provider = os.getenv('OPENCLAW_LLM_PROVIDER', config.llm.provider)
        config.llm.base_url = os.getenv('OPENCLAW_LLM_BASE_URL', config.llm.base_url)
        config.llm.main_model = os.getenv('OPENCLAW_MAIN_MODEL', config.llm.main_model)
        config.llm.code_model = os.getenv('OPENCLAW_CODE_MODEL', config.llm.code_model)
        config.llm.vision_model = os.getenv('OPENCLAW_VISION_MODEL', config.llm.vision_model)
        config.llm.embedding_model = os.getenv('OPENCLAW_EMBEDDING_MODEL', config.llm.embedding_model)
        config.llm.api_key = os.getenv('OPENCLAW_API_KEY', '')
        
        config.debug = os.getenv('OPENCLAW_DEBUG', 'false').lower() == 'true'
        config.log_level = os.getenv('OPENCLAW_LOG_LEVEL', config.log_level)
        
        base_dir = Path(__file__).parent
        config.skill.skills_dir = str(base_dir / 'skills')
        
        return config
    
    def to_dict(self) -> Dict:
        """
        转换为字典
        """
        return {
            'gateway': {
                'host': self.gateway.host,
                'port': self.gateway.port,
                'max_connections': self.gateway.max_connections
            },
            'pi_layer': {
                'max_agents': self.pi_layer.max_agents,
                'session_timeout': self.pi_layer.session_timeout
            },
            'embedded': {
                'sandbox_enabled': self.embedded.sandbox_enabled,
                'sandbox_timeout': self.embedded.sandbox_timeout
            },
            'agent': {
                'max_agents': self.agent.max_agents,
                'default_llm_model': self.agent.default_llm_model
            },
            'llm': {
                'provider': self.llm.provider,
                'base_url': self.llm.base_url,
                'main_model': self.llm.main_model
            },
            'debug': self.debug,
            'log_level': self.log_level
        }


OPENCLAW_CONFIG = OpenClawConfig.from_env()
