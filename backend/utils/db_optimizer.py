"""
数据库连接池和性能优化模块

提供：
1. 连接池配置优化
2. 异步数据库访问
3. 批量操作优化
4. 查询性能分析

使用示例:
```python
from utils.db_optimizer import (
    get_connection_pool,
    async_db_operation,
    batch_operation,
    query_profile,
    DatabasePool,
)

# 连接池统计
stats = get_connection_pool().get_stats()

# 异步数据库操作
result = await async_db_operation(TenderProject.objects.all())

# 批量插入
batch_operation(User, user_list, batch_size=500)

# 查询性能分析
@query_profile
def slow_query():
    return TenderProject.objects.filter(status='open').select_related('source')

# ORM查询优化
query = TenderProject.objects.filter(status='open')
optimized = query.select_related('source').prefetch_related('documents')
```
"""
import asyncio
import functools
import logging
import time
from contextlib import contextmanager
from datetime import datetime
from typing import Any, Callable, Iterable, List, Optional, Type, TypeVar

from django.db import connection, connections
from django.db.models import Model, QuerySet

logger = logging.getLogger(__name__)

T = TypeVar('T')


class DatabasePool:
    """
    数据库连接池管理器

    提供连接池状态监控和配置优化
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
        self._connection_times: List[float] = []
        self._query_times: List[float] = []
        self._max_history = 1000

    @property
    def stats(self) -> dict:
        """获取连接池统计"""
        try:
            conn = connections['default']
            settings_dict = conn.settings_dict

            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT
                        numbackends,
                        xact_commit,
                        xact_rollback,
                        blks_hit,
                        blks_read,
                        queries
                    FROM pg_stat_database
                    WHERE datname = current_database()
                """)
                row = cursor.fetchone()

                cursor.execute("SHOW max_connections")
                max_conn = cursor.fetchone()[0]

            return {
                'active_connections': row[0] if row else 0,
                'max_connections': int(max_conn),
                'transactions_committed': row[2] if row else 0,
                'transactions_rollback': row[3] if row else 0,
                'cache_hit_ratio': (row[4] / (row[4] + row[5]) * 100) if row and (row[4] + row[5]) > 0 else 0,
                'total_queries': row[6] if row else 0,
                'avg_connection_time': sum(self._connection_times) / len(self._connection_times) if self._connection_times else 0,
                'avg_query_time': sum(self._query_times) / len(self._query_times) if self._query_times else 0,
            }
        except Exception as e:
            logger.error(f"Failed to get database pool stats: {e}")
            return {'error': str(e)}

    def get_recommendations(self) -> List[str]:
        """获取优化建议"""
        stats = self.stats
        recommendations = []

        if 'error' in stats:
            return ['无法获取数据库统计信息']

        active_ratio = stats['active_connections'] / stats['max_connections']
        if active_ratio > 0.8:
            recommendations.append({
                'level': 'warning',
                'message': f"活跃连接数比例过高 ({active_ratio:.1%})，建议增加 max_connections 或优化连接使用"
            })

        if stats.get('cache_hit_ratio', 0) < 80:
            recommendations.append({
                'level': 'info',
                'message': f"缓存命中率较低 ({stats['cache_hit_ratio']:.1f}%)，建议优化查询或增加 shared_buffers"
            })

        if stats.get('avg_query_time', 0) > 0.1:
            recommendations.append({
                'level': 'warning',
                'message': f"平均查询时间较长 ({stats['avg_query_time']*1000:.1f}ms)，建议添加索引或优化查询"
            })

        return recommendations

    def reset_stats(self):
        """重置统计"""
        self._connection_times.clear()
        self._query_times.clear()


_database_pool = DatabasePool()


def get_connection_pool() -> DatabasePool:
    """获取数据库连接池实例"""
    return _database_pool


@contextmanager
def query_profile(operation_name: str = None):
    """
    查询性能分析上下文管理器

    Example:
        with query_profile('fetch_tenders'):
            tenders = list(TenderProject.objects.all())
    """
    name = operation_name or 'query'
    start_time = time.time()

    try:
        yield
    finally:
        duration = time.time() - start_time
        _database_pool._query_times.append(duration)
        if len(_database_pool._query_times) > _database_pool._max_history:
            _database_pool._query_times = _database_pool._query_times[-500:]

        if duration > 1.0:
            logger.warning(f"Slow query detected: {name} took {duration:.3f}s")


def query_profile_decorator(func: Callable[..., T]) -> Callable[..., T]:
    """
    查询性能分析装饰器

    Example:
        @query_profile_decorator
        def fetch_tenders():
            return list(TenderProject.objects.all())
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs) -> T:
        start_time = time.time()
        try:
            return func(*args, **kwargs)
        finally:
            duration = time.time() - start_time
            _database_pool._query_times.append(duration)
            if duration > 1.0:
                logger.warning(
                    f"Slow query: {func.__module__}.{func.__qualname__} took {duration:.3f}s"
                )

    @functools.wraps(func)
    async def async_wrapper(*args, **kwargs) -> T:
        start_time = time.time()
        try:
            return await func(*args, **kwargs)
        finally:
            duration = time.time() - start_time
            _database_pool._query_times.append(duration)
            if duration > 1.0:
                logger.warning(
                    f"Slow query: {func.__module__}.{func.__qualname__} took {duration:.3f}s"
                )

    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    return wrapper


async def async_db_operation(operation: Callable, *args, **kwargs) -> Any:
    """
    异步执行数据库操作

    Example:
        result = await async_db_operation(
            lambda: list(TenderProject.objects.all())
        )
    """
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, lambda: operation(*args, **kwargs))


def _batch_create(model: Type[Model], batch: List[dict], ignoreConflicts: bool = False):
    instances = [model(**data) for data in batch]
    if ignoreConflicts:
        model.objects.bulk_create(instances, ignore_conflicts=True)
    else:
        model.objects.bulk_create(instances)


def _batch_upsert(model: Type[Model], batch: List[dict], update_fields: List[str], ignoreConflicts: bool = False):
    pk_name = model._meta.pk.name
    instances = []
    for data in batch:
        pk_value = data.get(pk_name)
        if pk_value:
            try:
                obj = model.objects.get(**{pk_name: pk_value})
                for field in update_fields:
                    if field in data:
                        setattr(obj, field, data[field])
                instances.append(obj)
            except model.DoesNotExist:
                instances.append(model(**data))
        else:
            instances.append(model(**data))

    create_list = [obj for obj in instances if obj.pk is None]
    update_list = [obj for obj in instances if obj.pk is not None]

    if create_list:
        model.objects.bulk_create(create_list, ignore_conflicts=ignoreConflicts)
    if update_list and update_fields:
        model.objects.bulk_update(update_list, update_fields)


def batch_operation(
    model: Type[Model],
    data_list: Iterable[dict],
    batch_size: int = 500,
    update_fields: List[str] = None,
    ignoreConflicts: bool = False,
) -> dict:
    """
    批量操作

    Args:
        model: Django模型类
        data_list: 数据字典列表
        batch_size: 每批数量
        update_fields: 更新字段（用于update_or_create）
        ignoreConflicts: 忽略冲突（PostgreSQL）

    Returns:
        dict: 包含成功数和失败信息

    Example:
        result = batch_operation(
            User,
            [{'username': f'user{i}', 'email': f'user{i}@example.com'} for i in range(1000)],
            batch_size=500
        )
    """
    success_count = 0
    error_count = 0
    errors = []

    data_iter = iter(data_list)
    batch = []

    for data in data_iter:
        batch.append(data)

        if len(batch) >= batch_size:
            try:
                if update_fields:
                    _batch_upsert(model, batch, update_fields, ignoreConflicts)
                else:
                    _batch_create(model, batch, ignoreConflicts)

                success_count += len(batch)
            except Exception as e:
                error_count += len(batch)
                errors.append(str(e))
                logger.error(f"Batch operation error: {e}")

            batch = []

    if batch:
        try:
            if update_fields:
                _batch_upsert(model, batch, update_fields, ignoreConflicts)
            else:
                _batch_create(model, batch, ignoreConflicts)

            success_count += len(batch)
        except Exception as e:
            error_count += len(batch)
            errors.append(str(e))
            logger.error(f"Batch operation error: {e}")

    return {
        'success_count': success_count,
        'error_count': error_count,
        'errors': errors[:10],
    }


def optimize_queryset(queryset: QuerySet, select_fields: list = None, prefetch_fields: list = None) -> QuerySet:
    """
    优化QuerySet

    按需应用优化策略，避免过度查询：
    - select_related for ForeignKey/OneToOne (需显式指定)
    - prefetch_related for ManyToMany (需显式指定)
    - 未指定字段时仅自动添加OneToOne关系（不含M2M）

    Example:
        tenders = optimize_queryset(
            TenderProject.objects.filter(status='open'),
            select_fields=['source'],
            prefetch_fields=['files']
        )
    """
    if select_fields:
        queryset = queryset.select_related(*select_fields)
    else:
        queryset = queryset.select_related(
            *[f.name for f in queryset.model._meta.get_fields() if f.one_to_one]
        )

    if prefetch_fields:
        queryset = queryset.prefetch_related(*prefetch_fields)

    return queryset


class QueryAnalyzer:
    """
    查询分析器

    分析并建议查询优化
    """

    @staticmethod
    def analyze(queryset: QuerySet) -> dict:
        """
        分析QuerySet

        Returns:
            dict: 包含查询信息和优化建议
        """
        query = queryset.query

        suggestions = []

        if 'SELECT' in str(query) and 'JOIN' not in str(query):
            joins = query.get_pending_lookups()
            if joins:
                suggestions.append({
                    'type': 'missing_select_related',
                    'message': f"考虑使用 select_related() 预加载: {', '.join(joins)}"
                })

        if queryset.query.low_mark and queryset.query.high_mark:
            suggested_prefetch = []
            for field in queryset.model._meta.get_fields():
                if field.many_to_many and not field.name.startswith('_'):
                    suggested_prefetch.append(field.name)

            if suggested_prefetch:
                suggestions.append({
                    'type': 'suggest_prefetch_related',
                    'message': f"考虑使用 prefetch_related() 预加载: {', '.join(suggested_prefetch)}"
                })

        select_fields = [f.name for f in queryset.model._meta.get_fields() if not f.many_to_many]
        if len(select_fields) > 10:
            suggestions.append({
                'type': 'too_many_fields',
                'message': "考虑使用 only() 或 defer() 限制字段"
            })

        return {
            'sql': str(query),
            'suggestions': suggestions,
        }


def setup_connection_pool():
    """
    配置数据库连接池优化

    在Django启动时调用
    """
    try:
        from django.conf import settings

        if hasattr(settings, 'DATABASES'):
            for alias, db_settings in settings.DATABASES.items():
                if db_settings.get('ENGINE') == 'django.db.backends.postgresql':
                    conn = connections[alias]
                    conn.ensure_connection()

                    with conn.cursor() as cursor:
                        cursor.execute("""
                            SELECT NAME, SETTING
                            FROM pg_settings
                            WHERE NAME IN ('max_connections', 'shared_buffers')
                            ORDER BY NAME
                        """)
                        results = cursor.fetchall()
                        settings_map = {row[0]: row[1] for row in results}
                        logger.info(
                            f"Database connection pool configured: "
                            f"max_connections={settings_map.get('max_connections', 'N/A')}, "
                            f"shared_buffers={settings_map.get('shared_buffers', 'N/A')}"
                        )

        logger.info("Database connection pool optimization initialized")

    except Exception as e:
        logger.error(f"Failed to setup connection pool: {e}")


def check_connection_health():
    """
    检查数据库连接健康状态

    Returns:
        dict: 包含各数据库连接的健康状态
    """
    from django.conf import settings

    health = {}
    for alias in settings.DATABASES:
        try:
            conn = connections[alias]
            conn.ensure_connection()

            with conn.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()

            health[alias] = {
                'status': 'healthy',
                'vendor': conn.vendor,
            }

            if conn.vendor == 'postgresql':
                with conn.cursor() as cursor:
                    cursor.execute("""
                        SELECT numbackends, pg_database_size(current_database())
                        FROM pg_stat_database WHERE datname = current_database()
                    """)
                    row = cursor.fetchone()
                    if row:
                        health[alias]['active_connections'] = row[0]
                        health[alias]['database_size_bytes'] = row[1]

        except Exception as e:
            health[alias] = {
                'status': 'unhealthy',
                'error': str(e),
            }

    return health


__all__ = [
    'DatabasePool',
    'get_connection_pool',
    'query_profile',
    'query_profile_decorator',
    'async_db_operation',
    'batch_operation',
    'optimize_queryset',
    'QueryAnalyzer',
    'setup_connection_pool',
    'check_connection_health',
]
