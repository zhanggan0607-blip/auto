"""
统一配置管理
提供配置读取、验证、缓存的集中化管理
"""
import os
import logging
from pathlib import Path
from typing import Any, Dict, Optional, Union
from dataclasses import dataclass, field
from functools import lru_cache

logger = logging.getLogger(__name__)


@dataclass
class ConfigSection:
    """配置区块"""
    name: str
    description: str = ""
    readonly: bool = False


class ConfigManager:
    """
    统一配置管理器

    功能：
    1. 集中管理所有配置项
    2. 支持配置验证和默认值
    3. 支持环境变量覆盖
    4. 配置变更监听

    使用示例：
        config = ConfigManager()

        # 获取配置
        debug = config.get('DEBUG')
        db_url = config.get('DATABASE.URL')

        # 获取带默认值
        timeout = config.get('CRAWLER.TIMEOUT', default=30)

        # 验证配置
        config.validate_required(['DATABASE.URL', 'REDIS.HOST'])
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
        self._config_cache: Dict[str, Any] = {}
        self._sections: Dict[str, ConfigSection] = {}
        self._listeners: Dict[str, list] = {}
        self._django_settings = None

        self._init_default_sections()

    def _init_default_sections(self):
        """初始化默认配置区块"""
        self._sections = {
            'database': ConfigSection('database', '数据库配置'),
            'redis': ConfigSection('redis', 'Redis缓存配置'),
            'minio': ConfigSection('minio', 'MinIO对象存储配置'),
            'crawler': ConfigSection('crawler', '爬虫配置'),
            'agent': ConfigSection('agent', 'Agent配置'),
            'llm': ConfigSection('llm', '大模型配置'),
            'dingtalk': ConfigSection('dingtalk', '钉钉配置'),
        }

    def _get_django_settings(self):
        """获取Django settings（延迟加载）"""
        if self._django_settings is None:
            from django.conf import settings
            self._django_settings = settings
        return self._django_settings

    def get(self, key: str, default: Any = None, cast: type = None) -> Any:
        """
        获取配置值

        Args:
            key: 配置键（支持点号分隔，如 'DATABASE.URL'）
            default: 默认值
            cast: 类型转换（如 int, bool, list）

        Returns:
            配置值
        """
        if key in self._config_cache:
            return self._config_cache[key]

        value = self._get_from_django(key)
        if value is None:
            value = self._get_from_env(key)

        if value is None:
            value = default

        if cast and value is not None:
            value = self._cast_value(value, cast)

        self._config_cache[key] = value
        return value

    def _get_from_django(self, key: str) -> Any:
        """从Django settings获取配置"""
        try:
            settings = self._get_django_settings()
            keys = key.split('.')
            value = settings
            for k in keys:
                if hasattr(value, k):
                    value = getattr(value, k)
                else:
                    return None
            return value
        except Exception:
            return None

    def _get_from_env(self, key: str) -> Any:
        """从环境变量获取配置"""
        env_key = key.replace('.', '_').upper()
        return os.environ.get(env_key)

    def _cast_value(self, value: Any, cast_type: type) -> Any:
        """类型转换"""
        try:
            if cast_type == bool:
                if isinstance(value, str):
                    return value.lower() in ('true', '1', 'yes', 'on')
                return bool(value)
            elif cast_type == int:
                return int(value)
            elif cast_type == float:
                return float(value)
            elif cast_type == list:
                if isinstance(value, str):
                    return [item.strip() for item in value.split(',')]
                return list(value)
            elif cast_type == dict:
                if isinstance(value, str):
                    import json
                    return json.loads(value)
                return dict(value)
            return cast_type(value)
        except (ValueError, TypeError) as e:
            logger.warning(f"Failed to cast value '{value}' to {cast_type}: {e}")
            return value

    def set(self, key: str, value: Any, section: str = None):
        """
        设置配置值

        Args:
            key: 配置键
            value: 配置值
            section: 配置区块（可选）
        """
        if section and section in self._sections:
            sec = self._sections[section]
            if sec.readonly:
                raise ValueError(f"Section '{section}' is readonly")

        old_value = self._config_cache.get(key)
        self._config_cache[key] = value

        if old_value != value:
            self._notify_listeners(key, old_value, value)

    def get_section(self, section: str) -> Dict[str, Any]:
        """
        获取配置区块

        Args:
            section: 区块名称

        Returns:
            Dict: 配置字典
        """
        result = {}
        prefix = f"{section.upper()}."

        for key in self._config_cache:
            if key.startswith(prefix):
                result[key[len(prefix):]] = self._config_cache[key]

        settings = self._get_django_settings()
        if hasattr(settings, section.upper()):
            section_config = getattr(settings, section.upper())
            if isinstance(section_config, dict):
                result.update(section_config)

        return result

    def validate_required(self, keys: list) -> bool:
        """
        验证必需配置项

        Args:
            keys: 配置键列表

        Raises:
            ValueError: 缺少必需配置

        Returns:
            bool: 是否通过验证
        """
        missing = []
        for key in keys:
            value = self.get(key)
            if value is None or value == '':
                missing.append(key)

        if missing:
            raise ValueError(f"Missing required config: {missing}")

        return True

    def register_listener(self, key: str, callback):
        """
        注册配置变更监听器

        Args:
            key: 配置键（支持通配符，如 'CRAWLER.*'）
            callback: 回调函数 (key, old_value, new_value)
        """
        if key not in self._listeners:
            self._listeners[key] = []
        self._listeners[key].append(callback)

    def _notify_listeners(self, key: str, old_value: Any, new_value: Any):
        """通知监听器"""
        for pattern, callbacks in self._listeners.items():
            if self._match_key(key, pattern):
                for callback in callbacks:
                    try:
                        callback(key, old_value, new_value)
                    except Exception as e:
                        logger.error(f"Config listener error: {e}")

    def _match_key(self, key: str, pattern: str) -> bool:
        """匹配键"""
        if pattern == key:
            return True
        if pattern.endswith('.*'):
            prefix = pattern[:-2]
            return key.startswith(prefix + '.') or key == prefix
        return False

    def clear_cache(self):
        """清除配置缓存"""
        self._config_cache.clear()
        logger.info("Config cache cleared")

    def get_all_keys(self) -> list:
        """获取所有配置键"""
        return list(self._config_cache.keys())

    def get_stats(self) -> Dict[str, Any]:
        """获取配置统计"""
        return {
            'total_keys': len(self._config_cache),
            'sections': {name: sec.description for name, sec in self._sections.items()},
            'listeners': len(self._listeners)
        }


config_manager = ConfigManager()
