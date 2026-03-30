"""
缓存一致性管理模块

提供统一的缓存管理机制，支持：
1. 标签式缓存失效
2. 缓存版本控制
3. 写入时失效（Write-Invalidate）
4. 读取时刷新（Read-Through）
5. 分布式锁
6. 缓存统计和监控

使用示例:
```python
from utils.cache_manager import cache_manager, cached, invalidate_cache

# 基本使用
@cached('user:{user_id}', ttl=300)
def get_user(user_id):
    return User.objects.get(id=user_id)

# 标签失效
@invalidate_cache(tags=['user', 'user:{user_id}'])
def update_user(user_id, data):
    User.objects.filter(id=user_id).update(**data)
    return {'success': True}

# 直接操作
cache_manager.set('key', 'value', ttl=3600, tags=['tag1'])
value = cache_manager.get('key')
cache_manager.invalidate_tags(['tag1'])
```
"""
import functools
import hashlib
import json
import logging
import threading
import time
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional, TypeVar, Union

from django.core.cache import cache
from django.conf import settings

logger = logging.getLogger(__name__)

T = TypeVar('T')


class CacheStats:
    """缓存统计"""

    def __init__(self):
        self.hits = 0
        self.misses = 0
        self.sets = 0
        self.invalidations = 0
        self.errors = 0
        self._lock = threading.Lock()

    def record_hit(self):
        with self._lock:
            self.hits += 1

    def record_miss(self):
        with self._lock:
            self.misses += 1

    def record_set(self):
        with self._lock:
            self.sets += 1

    def record_invalidation(self, count: int = 1):
        with self._lock:
            self.invalidations += count

    def record_error(self):
        with self._lock:
            self.errors += 1

    @property
    def hit_rate(self) -> float:
        total = self.hits + self.misses
        return (self.hits / total * 100) if total > 0 else 0.0

    def to_dict(self) -> Dict[str, Any]:
        with self._lock:
            return {
                'hits': self.hits,
                'misses': self.misses,
                'sets': self.sets,
                'invalidations': self.invalidations,
                'errors': self.errors,
                'hit_rate': self.hit_rate,
            }

    def reset(self):
        with self._lock:
            self.hits = 0
            self.misses = 0
            self.sets = 0
            self.invalidations = 0
            self.errors = 0


class CacheTagRegistry:
    """缓存标签注册表"""

    def __init__(self):
        self._lock = threading.Lock()
        self._tag_to_keys: Dict[str, set] = {}
        self._key_to_tags: Dict[str, set] = {}

    def register(self, key: str, tags: List[str]):
        """注册key和标签的关联"""
        with self._lock:
            for tag in tags:
                if tag not in self._tag_to_keys:
                    self._tag_to_keys[tag] = set()
                self._tag_to_keys[tag].add(key)

            if key not in self._key_to_tags:
                self._key_to_tags[key] = set()
            self._key_to_tags[key].update(tags)

    def get_keys_by_tag(self, tag: str) -> set:
        """获取标签关联的所有key"""
        with self._lock:
            return set(self._tag_to_keys.get(tag, set()))

    def get_tags_by_key(self, key: str) -> set:
        """获取key关联的所有标签"""
        with self._lock:
            return set(self._key_to_tags.get(key, set()))

    def remove_key(self, key: str):
        """移除key"""
        with self._lock:
            tags = self._key_to_tags.pop(key, set())
            for tag in tags:
                self._tag_to_keys.get(tag, set()).discard(key)

    def clear(self):
        """清空注册表"""
        with self._lock:
            self._tag_to_keys.clear()
            self._key_to_tags.clear()


class DistributedLock:
    """分布式锁"""

    LOCK_PREFIX = 'lock:'

    def __init__(self, lock_name: str, timeout: int = 10):
        self.lock_name = lock_name
        self.timeout = timeout
        self._lock = threading.Lock()
        self._acquired = False

    def acquire(self, blocking: bool = True, timeout: float = None) -> bool:
        """
        获取锁

        Args:
            blocking: 是否阻塞等待
            timeout: 阻塞超时时间

        Returns:
            是否成功获取锁
        """
        lock_key = f"{self.LOCK_PREFIX}{self.lock_name}"
        start_time = time.time()

        while True:
            try:
                result = cache.add(lock_key, '1', timeout=self.timeout)
                if result:
                    self._acquired = True
                    logger.debug(f"Lock acquired: {self.lock_name}")
                    return True

                if not blocking:
                    return False

                if timeout and (time.time() - start_time) >= timeout:
                    return False

                time.sleep(0.01)

            except Exception as e:
                logger.error(f"Lock acquire error: {e}")
                return False

    def release(self):
        """释放锁"""
        if self._acquired:
            try:
                lock_key = f"{self.LOCK_PREFIX}{self.lock_name}"
                cache.delete(lock_key)
                self._acquired = False
                logger.debug(f"Lock released: {self.lock_name}")
            except Exception as e:
                logger.error(f"Lock release error: {e}")

    def __enter__(self):
        self.acquire()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.release()
        return False


class CacheManager:
    """
    统一缓存管理器

    提供：
    - 基本缓存操作
    - 标签管理
    - 分布式锁
    - 统计信息
    """

    def __init__(self):
        self._stats = CacheStats()
        self._tag_registry = CacheTagRegistry()
        self._local_cache: Dict[str, tuple] = {}
        self._local_cache_ttl: int = 5
        self._use_local_cache: bool = True
        self._lock = threading.Lock()

    @property
    def stats(self) -> CacheStats:
        """获取统计信息"""
        return self._stats

    def set(
        self,
        key: str,
        value: Any,
        ttl: int = None,
        tags: List[str] = None,
        version: int = None,
    ) -> bool:
        """
        设置缓存

        Args:
            key: 缓存键
            value: 缓存值
            ttl: 过期时间（秒）
            tags: 关联标签
            version: 版本号

        Returns:
            是否成功
        """
        try:
            cache_key = self._make_key(key, version)

            serialized_value = self._serialize(value)

            actual_ttl = ttl if ttl is not None else self._get_default_ttl(key)

            cache.set(cache_key, serialized_value, actual_ttl)

            if tags:
                self._tag_registry.register(cache_key, tags)

            if self._use_local_cache:
                with self._lock:
                    self._local_cache[cache_key] = (serialized_value, time.time() + 1)

            self._stats.record_set()
            logger.debug(f"Cache set: {key}, TTL: {actual_ttl}")
            return True

        except Exception as e:
            logger.error(f"Cache set error: {e}")
            self._stats.record_error()
            return False

    def get(
        self,
        key: str,
        default: Any = None,
        version: int = None,
        refresh: bool = False,
    ) -> Any:
        """
        获取缓存

        Args:
            key: 缓存键
            default: 默认值
            version: 版本号
            refresh: 是否强制刷新本地缓存

        Returns:
            缓存值或默认值
        """
        try:
            cache_key = self._make_key(key, version)

            if self._use_local_cache and not refresh:
                with self._lock:
                    if cache_key in self._local_cache:
                        value, expire_time = self._local_cache[cache_key]
                        if time.time() < expire_time:
                            self._stats.record_hit()
                            return self._deserialize(value)

            serialized_value = cache.get(cache_key)

            if serialized_value is None:
                self._stats.record_miss()
                return default

            if self._use_local_cache:
                with self._lock:
                    self._local_cache[cache_key] = (serialized_value, time.time() + self._local_cache_ttl)

            self._stats.record_hit()
            return self._deserialize(serialized_value)

        except Exception as e:
            logger.error(f"Cache get error: {e}")
            self._stats.record_error()
            return default

    def delete(self, key: str, version: int = None) -> bool:
        """删除缓存"""
        try:
            cache_key = self._make_key(key, version)
            cache.delete(cache_key)
            self._tag_registry.remove_key(cache_key)

            if self._use_local_cache:
                with self._lock:
                    self._local_cache.pop(cache_key, None)

            return True

        except Exception as e:
            logger.error(f"Cache delete error: {e}")
            return False

    def invalidate_tags(self, tags: List[str]):
        """
        根据标签失效缓存

        Args:
            tags: 标签列表
        """
        try:
            keys_to_invalidate = set()
            for tag in tags:
                keys_to_invalidate.update(self._tag_registry.get_keys_by_tag(tag))

            for key in keys_to_invalidate:
                cache.delete(key)
                self._tag_registry.remove_key(key)

                if self._use_local_cache:
                    with self._lock:
                        self._local_cache.pop(key, None)

            self._stats.record_invalidation(len(keys_to_invalidate))
            logger.info(f"Invalidated {len(keys_to_invalidate)} keys for tags: {tags}")

        except Exception as e:
            logger.error(f"Cache invalidate error: {e}")
            self._stats.record_error()

    def invalidate_prefix(self, prefix: str):
        """
        根据前缀失效缓存

        Args:
            prefix: 键前缀
        """
        try:
            pattern = f"{prefix}*"
            keys = cache.keys(pattern)
            for key in keys:
                cache.delete(key)
                self._tag_registry.remove_key(key)

                if self._use_local_cache:
                    with self._lock:
                        self._local_cache.pop(key, None)

            self._stats.record_invalidation(len(keys))
            logger.info(f"Invalidated {len(keys)} keys for prefix: {prefix}")

        except Exception as e:
            logger.error(f"Cache invalidate prefix error: {e}")

    def get_or_set(
        self,
        key: str,
        default: Callable,
        ttl: int = None,
        tags: List[str] = None,
        version: int = None,
    ) -> Any:
        """
        获取缓存，不存在时设置

        Args:
            key: 缓存键
            default: 默认值回调函数
            ttl: 过期时间
            tags: 关联标签
            version: 版本号

        Returns:
            缓存值
        """
        value = self.get(key, version=version)

        if value is None:
            if callable(default):
                value = default()
            else:
                value = default

            self.set(key, value, ttl=ttl, tags=tags, version=version)

        return value

    def clear(self):
        """清空所有缓存"""
        try:
            cache.clear()
            if self._use_local_cache:
                with self._lock:
                    self._local_cache.clear()
            self._tag_registry.clear()
            logger.info("Cache cleared")
        except Exception as e:
            logger.error(f"Cache clear error: {e}")

    def _make_key(self, key: str, version: int = None) -> str:
        """生成缓存键"""
        if version is not None:
            key = f"{key}:v{version}"
        return key

    def _serialize(self, value: Any) -> str:
        """序列化值"""
        return json.dumps(value, default=str)

    def _deserialize(self, value: str) -> Any:
        """反序列化值"""
        return json.loads(value)

    def _get_default_ttl(self, key: str) -> int:
        """获取默认TTL"""
        if hasattr(settings, 'CACHE_TTL'):
            return settings.CACHE_TTL.get('DEFAULT', 300)
        return 300


cache_manager = CacheManager()


def cached(
    key_pattern: str,
    ttl: int = None,
    tags: List[str] = None,
    version: int = None,
):
    """
    缓存装饰器

    Args:
        key_pattern: 缓存键模式，支持 {arg_name} 格式化
        ttl: 过期时间
        tags: 关联标签
        version: 版本号

    Example:
        @cached('user:{user_id}', ttl=300, tags=['user'])
        def get_user(user_id):
            return User.objects.get(id=user_id)
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> T:
            cache_key = _make_cache_key(key_pattern, func, args, kwargs)

            cached_value = cache_manager.get(cache_key, version=version)
            if cached_value is not None:
                return cached_value

            result = func(*args, **kwargs)

            cache_manager.set(cache_key, result, ttl=ttl, tags=tags, version=version)

            return result

        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs) -> T:
            cache_key = _make_cache_key(key_pattern, func, args, kwargs)

            cached_value = cache_manager.get(cache_key, version=version)
            if cached_value is not None:
                return cached_value

            result = await func(*args, **kwargs)

            cache_manager.set(cache_key, result, ttl=ttl, tags=tags, version=version)

            return result

        if functools.iscoroutinefunction(func):
            return async_wrapper
        return wrapper

    return decorator


def invalidate_cache(
    tags: List[str] = None,
    key_pattern: str = None,
    prefix: str = None,
):
    """
    缓存失效装饰器

    Args:
        tags: 要失效的标签列表
        key_pattern: 要失效的键模式
        prefix: 要失效的键前缀

    Example:
        @invalidate_cache(tags=['user'])
        def update_user(user_id, data):
            ...
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> T:
            result = func(*args, **kwargs)

            if tags:
                cache_manager.invalidate_tags(tags)

            if key_pattern:
                cache_key = _make_cache_key(key_pattern, func, args, kwargs)
                cache_manager.delete(cache_key)

            if prefix:
                cache_manager.invalidate_prefix(prefix)

            return result

        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs) -> T:
            result = await func(*args, **kwargs)

            if tags:
                cache_manager.invalidate_tags(tags)

            if key_pattern:
                cache_key = _make_cache_key(key_pattern, func, args, kwargs)
                cache_manager.delete(cache_key)

            if prefix:
                cache_manager.invalidate_prefix(prefix)

            return result

        if functools.iscoroutinefunction(func):
            return async_wrapper
        return wrapper

    return decorator


def _make_cache_key(
    key_pattern: str,
    func: Callable,
    args: tuple,
    kwargs: dict,
) -> str:
    """生成缓存键"""
    import inspect

    sig = inspect.signature(func)
    param_names = list(sig.parameters.keys())

    key = key_pattern

    for i, param_name in enumerate(param_names):
        if i < len(args):
            value = args[i]
        else:
            value = kwargs.get(param_name)

        if value is not None:
            value_str = str(value) if not isinstance(value, (str, int, float)) else value
            key = key.replace(f'{{{param_name}}}', value_str)

    key = key.replace('{', '').replace('}', '')

    key_hash = hashlib.md5(f"{func.__module__}.{func.__qualname__}".encode()).hexdigest()[:8]
    return f"fn:{key_hash}:{key}"


__all__ = [
    'CacheManager',
    'CacheStats',
    'CacheTagRegistry',
    'DistributedLock',
    'cache_manager',
    'cached',
    'invalidate_cache',
]
