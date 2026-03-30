"""
缓存工具模块

使用Redis作为缓存后端，提供统一的缓存操作接口

功能：
- 热点数据缓存
- 分布式锁
- 缓存预热
- 批量操作
- 函数结果缓存装饰器

使用示例：
    from core.cache import cache_service, CacheKeys, DistributedLock, cache_result

    # 基本操作
    cache_service.set('key', 'value', timeout=300)
    value = cache_service.get('key')

    # 分布式锁
    with DistributedLock('task_lock'):
        # 临界区操作
        pass

    # 函数缓存装饰器
    @cache_result('user:{user_id}', timeout=600)
    def get_user_info(user_id):
        return User.objects.get(id=user_id)

    # 缓存键常量
    key = CacheKeys.ENTERPRISE_DETAIL.format(id=1)
"""
import json
import logging
import hashlib
import re
import time
from functools import wraps
from typing import Optional, Any, Callable, List, Dict
from django.core.cache import cache
from django.conf import settings

logger = logging.getLogger(__name__)


class CacheService:
    """
    缓存服务类

    封装Redis缓存操作，提供统一的缓存操作接口
    """

    DEFAULT_TIMEOUT = 300
    LONG_TIMEOUT = 3600
    DAY_TIMEOUT = 86400

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._prefix = getattr(settings, 'CACHE_KEY_PREFIX', 'auto')
        return cls._instance

    def _make_key(self, key: str) -> str:
        """
        生成带前缀的缓存键
        """
        return f"{self._prefix}:{key}"

    def get(self, key: str, default: Any = None) -> Any:
        """
        获取缓存

        Args:
            key: 缓存键
            default: 默认值

        Returns:
            缓存值或默认值
        """
        try:
            return cache.get(self._make_key(key), default)
        except Exception as e:
            logger.warning(f"缓存获取失败: {key} - {str(e)}")
            return default

    def set(self, key: str, value: Any, timeout: int = None) -> bool:
        """
        设置缓存

        Args:
            key: 缓存键
            value: 缓存值
            timeout: 过期时间（秒）

        Returns:
            是否设置成功
        """
        if timeout is None:
            timeout = self.DEFAULT_TIMEOUT
        try:
            return cache.set(self._make_key(key), value, timeout)
        except Exception as e:
            logger.warning(f"缓存设置失败: {key} - {str(e)}")
            return False

    def delete(self, key: str) -> bool:
        """
        删除缓存

        Args:
            key: 缓存键

        Returns:
            是否删除成功
        """
        try:
            return cache.delete(self._make_key(key))
        except Exception as e:
            logger.warning(f"缓存删除失败: {key} - {str(e)}")
            return False

    def delete_pattern(self, pattern: str) -> int:
        """
        按模式删除缓存

        Args:
            pattern: 缓存键模式（不含前缀）

        Returns:
            删除的键数量
        """
        try:
            keys = cache.keys(f"*{pattern}*")
            if keys:
                cache.delete_many(keys)
                logger.info(f"批量删除缓存: {len(keys)}个, 模式: {pattern}")
                return len(keys)
            return 0
        except Exception as e:
            logger.warning(f"按模式删除缓存失败: {pattern} - {str(e)}")
            return 0

    def exists(self, key: str) -> bool:
        """
        检查缓存是否存在

        Args:
            key: 缓存键

        Returns:
            是否存在
        """
        try:
            return cache.get(self._make_key(key)) is not None
        except Exception as e:
            logger.warning(f"检查缓存存在失败: {key} - {str(e)}")
            return False

    def get_or_set(
        self,
        key: str,
        callable_or_value: Any,
        timeout: int = None
    ) -> Any:
        """
        获取缓存，不存在则设置

        Args:
            key: 缓存键
            callable_or_value: 当缓存不存在时的值或返回值的函数
            timeout: 过期时间

        Returns:
            缓存值
        """
        full_key = self._make_key(key)
        value = cache.get(full_key)

        if value is None:
            if callable(callable_or_value):
                value = callable_or_value()
            else:
                value = callable_or_value
            cache.set(full_key, value, timeout or self.DEFAULT_TIMEOUT)

        return value

    def get_many(self, keys: List[str]) -> Dict[str, Any]:
        """
        批量获取缓存

        Args:
            keys: 缓存键列表

        Returns:
            键值对字典
        """
        try:
            full_keys = [self._make_key(k) for k in keys]
            result = cache.get_many(full_keys)

            return {
                k.replace(f"{self._prefix}:", ''): v
                for k, v in result.items()
            }
        except Exception as e:
            logger.warning(f"批量获取缓存失败 - {str(e)}")
            return {}

    def set_many(self, mapping: Dict[str, Any], timeout: int = None) -> bool:
        """
        批量设置缓存

        Args:
            mapping: 键值对字典
            timeout: 过期时间

        Returns:
            是否设置成功
        """
        if timeout is None:
            timeout = self.DEFAULT_TIMEOUT
        try:
            full_mapping = {
                self._make_key(k): v
                for k, v in mapping.items()
            }
            return cache.set_many(full_mapping, timeout)
        except Exception as e:
            logger.warning(f"批量设置缓存失败 - {str(e)}")
            return False

    def delete_many(self, keys: List[str]) -> bool:
        """
        批量删除缓存

        Args:
            keys: 缓存键列表

        Returns:
            是否删除成功
        """
        try:
            full_keys = [self._make_key(k) for k in keys]
            return cache.delete_many(full_keys)
        except Exception as e:
            logger.warning(f"批量删除缓存失败 - {str(e)}")
            return False

    def incr(self, key: str, delta: int = 1) -> int:
        """
        递增缓存值

        Args:
            key: 缓存键
            delta: 递增量

        Returns:
            递增后的值
        """
        try:
            return cache.incr(self._make_key(key), delta)
        except Exception as e:
            logger.warning(f"缓存递增失败: {key} - {str(e)}")
            return None

    def decr(self, key: str, delta: int = 1) -> int:
        """
        递减缓存值

        Args:
            key: 缓存键
            delta: 递减量

        Returns:
            递减后的值
        """
        try:
            return cache.decr(self._make_key(key), delta)
        except Exception as e:
            logger.warning(f"缓存递减失败: {key} - {str(e)}")
            return None

    def ttl(self, key: str) -> Optional[int]:
        """
        获取剩余过期时间

        Args:
            key: 缓存键

        Returns:
            剩余秒数
        """
        try:
            return cache.ttl(self._make_key(key))
        except AttributeError:
            return None

    def clear_all(self) -> bool:
        """
        清除所有缓存（谨慎使用）

        Returns:
            是否清除成功
        """
        try:
            cache.clear()
            logger.warning("已清除所有缓存")
            return True
        except Exception as e:
            logger.warning(f"清除所有缓存失败 - {str(e)}")
            return False


class DistributedLock:
    """
    分布式锁

    使用Redis实现分布式锁，防止并发操作

    使用示例：
        with DistributedLock('task_lock'):
            # 临界区操作
            pass
    """

    DEFAULT_TIMEOUT = 30

    def __init__(self, lock_name: str, timeout: int = None):
        """
        初始化分布式锁

        Args:
            lock_name: 锁名称
            timeout: 锁过期时间（秒）
        """
        self.lock_name = f"lock:{lock_name}"
        self.timeout = timeout or self.DEFAULT_TIMEOUT
        self._locked = False

    def acquire(self, blocking: bool = True, timeout: float = None) -> bool:
        """
        获取锁

        Args:
            blocking: 是否阻塞等待
            timeout: 阻塞超时时间（秒）

        Returns:
            是否成功获取锁
        """
        start_time = time.time()

        while True:
            if cache.add(self.lock_name, 'locked', self.timeout):
                self._locked = True
                return True

            if not blocking:
                return False

            if timeout and (time.time() - start_time) >= timeout:
                return False

            time.sleep(0.1)

    def release(self):
        """
        释放锁
        """
        if self._locked:
            try:
                cache.delete(self.lock_name)
            except Exception as e:
                logger.warning(f"释放锁失败: {self.lock_name} - {str(e)}")
            self._locked = False

    def __enter__(self):
        self.acquire()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.release()
        return False

    def locked(self) -> bool:
        """
        检查是否已锁定

        Returns:
            是否已锁定
        """
        return self._locked


def cache_result(key_pattern: str, timeout: int = 300):
    """
    缓存函数结果装饰器

    Args:
        key_pattern: 缓存键模式，支持 {arg} 占位符
        timeout: 缓存超时时间

    Example:
        @cache_result('user:{user_id}', timeout=600)
        def get_user_info(user_id):
            return User.objects.get(id=user_id)
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache_key = key_pattern

            placeholders = re.findall(r'\{(\w+)\}', key_pattern)

            import inspect
            sig = inspect.signature(func)
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()

            for placeholder in placeholders:
                value = bound_args.arguments.get(placeholder, '')
                if value:
                    cache_key = cache_key.replace(f'{{{placeholder}}}', str(value))

            cache_key = hashlib.md5(cache_key.encode()).hexdigest()
            cache_key = f"func:{func.__module__}.{func.__name__}:{cache_key}"

            result = cache.get(cache_key)

            if result is None:
                result = func(*args, **kwargs)
                cache.set(cache_key, result, timeout)

            return result

        return wrapper
    return decorator


def generate_cache_key(*args, **kwargs):
    """
    生成缓存键

    Args:
        *args: 位置参数
        **kwargs: 关键字参数

    Returns:
        MD5哈希后的缓存键
    """
    key_parts = [str(arg) for arg in args]
    key_parts.extend(f"{k}:{v}" for k, v in sorted(kwargs.items()))
    key_string = ":".join(key_parts)
    return hashlib.md5(key_string.encode()).hexdigest()


def cache_it(key_prefix, timeout=None, key_params=None):
    """
    缓存装饰器（兼容旧API）

    Args:
        key_prefix: 缓存key前缀
        timeout: 缓存过期时间(秒)
        key_params: 用于生成缓存key的参数名列表

    Example:
        @cache_it('user_info', timeout=60, key_params=['user_id'])
        def get_user_info(user_id):
            return User.objects.get(id=user_id)
    """
    if timeout is None:
        timeout = getattr(settings, 'CACHE_TTL', {}).get('DEFAULT', 300)

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache_key_parts = [key_prefix]

            if key_params:
                for param in key_params:
                    if param in kwargs:
                        cache_key_parts.append(f"{param}:{kwargs[param]}")

            cache_key = ":".join(cache_key_parts)

            try:
                cached_result = cache.get(cache_key)
                if cached_result is not None:
                    logger.debug(f"缓存命中: {cache_key}")
                    return cached_result
            except Exception as e:
                logger.warning(f"缓存读取失败: {cache_key} - {str(e)}")

            result = func(*args, **kwargs)

            try:
                cache.set(cache_key, result, timeout)
                logger.debug(f"缓存设置: {cache_key}, TTL: {timeout}s")
            except Exception as e:
                logger.warning(f"缓存设置失败: {cache_key} - {str(e)}")

            return result
        return wrapper
    return decorator


def invalidate_it(key_pattern):
    """
    清除缓存装饰器（兼容旧API）
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)

            try:
                keys = cache.keys(f"*{key_pattern}*")
                if keys:
                    cache.delete_many(keys)
                    logger.debug(f"清除缓存: {keys}")
            except Exception as e:
                logger.warning(f"清除缓存失败: {key_pattern} - {str(e)}")

            return result
        return wrapper
    return decorator


class CacheKeys:
    """
    缓存键常量

    定义系统中常用的缓存键模式
    """
    ENTERPRISE_DETAIL = 'enterprise:detail:{id}'
    ENTERPRISE_LIST = 'enterprise:list:{page}:{size}'
    ENTERPRISE_SEARCH = 'enterprise:search:{query}:{page}'
    TENDER_DETAIL = 'tender:detail:{id}'
    TENDER_LIST = 'tender:list:{status}:{page}'
    TENDER_SEARCH = 'tender:search:{query}:{page}'
    BID_DETAIL = 'bid:detail:{id}'
    BID_LIST = 'bid:list:{status}:{page}'
    USER_PERMISSIONS = 'user:permissions:{user_id}'
    USER_SETTINGS = 'user:settings:{user_id}'
    USER_PROFILE = 'user:profile:{user_id}'
    CRAWLER_STATUS = 'crawler:status:{session_id}'
    CRAWLER_PROGRESS = 'crawler:progress:{session_id}'
    MATCH_RESULT = 'match:result:{tender_id}'
    MATCH_ENTERPRISE = 'match:enterprise:{enterprise_id}'
    DOCUMENT_CONTENT = 'document:content:{doc_id}'
    DOCUMENT_LIST = 'document:list:{type}:{page}'
    VECTOR_SEARCH = 'vector:search:{query_hash}'
    STATISTICS_DAILY = 'stats:daily:{date}'
    STATISTICS_MONTHLY = 'stats:monthly:{year}:{month}'
    SCHEDULE_STATUS = 'schedule:status:{schedule_id}'
    AGENT_SESSION = 'agent:session:{session_id}'
    LLM_PROVIDER_CONFIG = 'llm:provider:{provider_id}'
    CONSTANTS_ALL = 'constants:all'
    CONSTANTS_BY_TYPE = 'constants:type:{type}'

    @classmethod
    def format(cls, key_name: str, **kwargs) -> str:
        """
        格式化缓存键

        Args:
            key_name: 缓存键名称
            **kwargs: 格式化参数

        Returns:
            格式化后的缓存键
        """
        key = getattr(cls, key_name, key_name)
        try:
            return key.format(**kwargs)
        except KeyError:
            return key


cache_service = CacheService()


def warm_up_cache():
    """
    缓存预热

    在系统启动时预热热点数据
    """
    logger.info("开始缓存预热...")

    try:
        from apps.enterprise.models import Enterprise

        enterprises = Enterprise.objects.filter(is_active=True).only(
            'id', 'name', 'credit_code', 'legal_person'
        )[:100]

        for enterprise in enterprises:
            key = CacheKeys.ENTERPRISE_DETAIL.format(id=enterprise.id)
            cache_service.set(key, {
                'id': enterprise.id,
                'name': enterprise.name,
                'credit_code': enterprise.credit_code,
                'legal_person': enterprise.legal_person,
            }, timeout=CacheService.LONG_TIMEOUT)

        logger.info(f"缓存预热完成，预热了 {len(enterprises)} 条企业数据")

    except Exception as e:
        logger.error(f"缓存预热失败: {str(e)}")


def clear_user_cache(user_id: int):
    """
    清除用户相关缓存

    Args:
        user_id: 用户ID
    """
    keys = [
        CacheKeys.USER_PERMISSIONS.format(user_id=user_id),
        CacheKeys.USER_SETTINGS.format(user_id=user_id),
        CacheKeys.USER_PROFILE.format(user_id=user_id),
    ]
    cache_service.delete_many(keys)
    logger.info(f"清除用户缓存: user_id={user_id}")


def clear_enterprise_cache(enterprise_id: int):
    """
    清除企业相关缓存

    Args:
        enterprise_id: 企业ID
    """
    key = CacheKeys.ENTERPRISE_DETAIL.format(id=enterprise_id)
    cache_service.delete(key)
    cache_service.delete_pattern('enterprise:list:*')
    cache_service.delete_pattern('enterprise:search:*')
    cache_service.delete_pattern(f'match:enterprise:{enterprise_id}')
    logger.info(f"清除企业缓存: enterprise_id={enterprise_id}")


def clear_tender_cache(tender_id: int):
    """
    清除招标相关缓存

    Args:
        tender_id: 招标ID
    """
    key = CacheKeys.TENDER_DETAIL.format(id=tender_id)
    cache_service.delete(key)
    cache_service.delete_pattern('tender:list:*')
    cache_service.delete_pattern('tender:search:*')
    cache_service.delete_pattern(f'match:result:{tender_id}')
    logger.info(f"清除招标缓存: tender_id={tender_id}")


def clear_document_cache(doc_id: int = None):
    """
    清除文档相关缓存

    Args:
        doc_id: 文档ID，如果为None则清除所有文档缓存
    """
    if doc_id:
        key = CacheKeys.DOCUMENT_CONTENT.format(doc_id=doc_id)
        cache_service.delete(key)
    cache_service.delete_pattern('document:list:*')
    logger.info(f"清除文档缓存: doc_id={doc_id}")
