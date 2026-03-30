"""
Redis缓存服务扩展（已废弃，请使用 core.cache）

此文件仅用于向后兼容，新代码请直接从 core.cache 导入

已迁移到 core.cache 的功能：
- CacheService 类
- DistributedLock 类
- cache_result 装饰器
- generate_cache_key 函数
- cache_it 装饰器（兼容旧API）
- invalidate_it 装饰器（兼容旧API）
- CacheKeys 类
- cache_service 单例
- warm_up_cache 函数
- clear_user_cache 函数
- clear_enterprise_cache 函数

使用示例：
    # 旧写法（仍可用，但推荐使用新写法）
    from utils.cache_service import cache_service, CacheKeys, DistributedLock

    # 新写法
    from core.cache import cache_service, CacheKeys, DistributedLock
"""

from core.cache import (
    CacheService,
    DistributedLock,
    cache_result,
    generate_cache_key,
    cache_it,
    invalidate_it,
    CacheKeys,
    cache_service,
    warm_up_cache,
    clear_user_cache,
    clear_enterprise_cache,
    clear_tender_cache,
    clear_document_cache,
)

__all__ = [
    'CacheService',
    'DistributedLock',
    'cache_result',
    'generate_cache_key',
    'cache_it',
    'invalidate_it',
    'CacheKeys',
    'cache_service',
    'warm_up_cache',
    'clear_user_cache',
    'clear_enterprise_cache',
    'clear_tender_cache',
    'clear_document_cache',
]
