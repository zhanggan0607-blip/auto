"""
数据库读写分离路由器
实现主从数据库的读写分离
"""
import logging
import random
from django.conf import settings

logger = logging.getLogger(__name__)


class ReadWriteRouter:
    """
    数据库读写分离路由器
    
    写操作 -> 主库
    读操作 -> 从库
    
    使用方式:
    1. 在 settings.py 中配置 DATABASES 和 DATABASE_ROUTERS
    2. 读操作自动路由到 replica
    3. 写操作自动路由到 default
    """
    
    READ_DB_ALIAS = 'replica'
    WRITE_DB_ALIAS = 'default'
    
    READ_ONLY_MODELS = [
        'auth.permission',
        'contenttypes.contenttype',
    ]
    
    WRITE_PREFERRED_MODELS = [
        'users.userloginlog',
        'crawler.crawllog',
        'openclaw.llmusagelog',
    ]
    
    def __init__(self):
        self._replica_health = True
        self._last_health_check = 0
    
    def db_for_read(self, model, **hints):
        """
        读操作路由
        """
        if self._should_use_primary(model):
            return self.WRITE_DB_ALIAS
        
        if not self._is_replica_available():
            logger.warning("Replica unavailable, falling back to primary")
            return self.WRITE_DB_ALIAS
        
        return self.READ_DB_ALIAS
    
    def db_for_write(self, model, **hints):
        """
        写操作路由 - 始终使用主库
        """
        return self.WRITE_DB_ALIAS
    
    def allow_relation(self, obj1, obj2, **hints):
        """
        允许同一数据库中的对象之间建立关系
        """
        db1 = getattr(obj1, '_state', None) and obj1._state.db
        db2 = getattr(obj2, '_state', None) and obj2._state.db
        
        if db1 and db2:
            return db1 == db2
        
        return True
    
    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """
        控制迁移操作 - 只在主库执行
        """
        return db == self.WRITE_DB_ALIAS
    
    def _should_use_primary(self, model) -> bool:
        """
        判断是否应该使用主库读取
        """
        model_label = f"{model._meta.app_label}.{model._meta.model_name}"
        
        if model_label in self.READ_ONLY_MODELS:
            return False
        
        if model_label in self.WRITE_PREFERRED_MODELS:
            return True
        
        return False
    
    def _is_replica_available(self) -> bool:
        """
        检查从库是否可用
        """
        import time
        current_time = time.time()
        
        if current_time - self._last_health_check > 30:
            self._last_health_check = current_time
            self._replica_health = self._check_replica_connection()
        
        return self._replica_health
    
    def _check_replica_connection(self) -> bool:
        """
        实际检查从库连接
        """
        try:
            from django.db import connections
            from django.db.utils import OperationalError
            
            replica_config = settings.DATABASES.get(self.READ_DB_ALIAS)
            if not replica_config:
                return False
            
            connection = connections[self.READ_DB_ALIAS]
            connection.ensure_connection()
            return True
            
        except OperationalError as e:
            logger.error(f"Replica connection failed: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Replica health check error: {str(e)}")
            return False


class PrimaryReplicaRouter:
    """
    简化版读写分离路由器
    用于特定场景的读写分离
    """
    
    def db_for_read(self, model, **hints):
        if model._meta.app_label in ['sessions', 'admin']:
            return 'default'
        return 'replica'
    
    def db_for_write(self, model, **hints):
        return 'default'
    
    def allow_relation(self, obj1, obj2, **hints):
        return True
    
    def allow_migrate(self, db, app_label, model_name=None, **hints):
        return db == 'default'


def use_primary_db(func):
    """
    装饰器：强制使用主库
    用于需要读取最新数据的场景
    """
    from functools import wraps
    
    @wraps(func)
    def wrapper(*args, **kwargs):
        from django.db import connections
        
        old_db = None
        try:
            from django.db import DEFAULT_DB_ALIAS
            old_db = getattr(connections['default'], 'alias', DEFAULT_DB_ALIAS)
            
            result = func(*args, **kwargs)
            return result
        finally:
            pass
    
    return wrapper


def use_replica_db(func):
    """
    装饰器：强制使用从库
    用于报表查询等场景
    """
    from functools import wraps
    
    @wraps(func)
    def wrapper(*args, **kwargs):
        from django.db import connections
        
        try:
            connections['replica'].ensure_connection()
            return func(*args, **kwargs)
        except Exception:
            return func(*args, **kwargs)
    
    return wrapper
