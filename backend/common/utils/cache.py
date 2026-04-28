"""
统一缓存管理模块

整合 core.cache 和 utils.cache_manager 的功能，提供统一的缓存接口

职责：
- 基本缓存操作 (get, set, delete)
- 分布式锁
- 缓存键常量
- 函数结果缓存装饰器
- 标签式缓存失效
- 缓存统计

使用示例：
    from common.utils.cache import cache_service, CacheKeys, DistributedLock

    # 基本操作
    cache_service.set('key', 'value', timeout=300)
    value = cache_service.get('key')

    # 分布式锁
    with DistributedLock('task_lock'):
        # 临界区操作
        pass

    # 缓存装饰器
    @cached('user:{user_id}', ttl=600)
    def get_user(user_id):
        return User.objects.get(id=user_id)

迁移指南：
    # 旧代码
    from core.cache import cache_service, CacheKeys, DistributedLock
    from utils.cache_manager import cache_manager, cached, invalidate_cache

    # 新代码（统一入口）
    from common.utils.cache import (
        cache_service,      # 来自 core.cache
        CacheKeys,          # 来自 core.cache
        DistributedLock,    # 来自 core.cache
        cache_manager,      # 来自 utils.cache_manager
        cached,             # 来自 utils.cache_manager
        invalidate_cache,   # 来自 utils.cache_manager
        CacheStats,         # 来自 utils.cache_manager
    )
"""
from core.cache import (
    CacheService,
    DistributedLock,
    cache_result,
    generate_cache_key,
    CacheKeys,
    cache_service,
    warm_up_cache,
    clear_user_cache,
    clear_enterprise_cache,
    clear_tender_cache,
    clear_document_cache,
)

from utils.cache_manager import (
    CacheManager,
    CacheStats,
    CacheTagRegistry,
    cache_manager,
    cached,
    invalidate_cache,
)

__all__ = [
    # core.cache 导出
    'CacheService',
    'DistributedLock',
    'cache_result',
    'generate_cache_key',
    'CacheKeys',
    'cache_service',
    'warm_up_cache',
    'clear_user_cache',
    'clear_enterprise_cache',
    'clear_tender_cache',
    'clear_document_cache',
    # utils.cache_manager 导出
    'CacheManager',
    'CacheStats',
    'CacheTagRegistry',
    'cache_manager',
    'cached',
    'invalidate_cache',
]
