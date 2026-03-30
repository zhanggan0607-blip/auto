"""
核心模块

职责：
- 中间件（RequestLoggingMiddleware等）
- 缓存工具（CacheService, cache_result装饰器）
- 分页器（StandardPagination）
- 异常处理（custom_exception_handler）
- 限流器（RateThrottle）
- 验证器（Validators）
- 三层架构基础类（Repository, Service, ViewSet）
- API版本控制

使用示例：
```python
# 缓存
from core.cache import cache_service, cache_result

@cache_result('user_info', timeout=60, key_params=['user_id'])
def get_user_info(user_id):
    return User.objects.get(id=user_id)

# 分页
from core.pagination import StandardPagination

# 异常处理
from core.exceptions import custom_exception_handler

# 三层架构
from core.repository import BaseRepository
from core.service import BaseService, ServiceResult
from core.viewset import ModelViewSet, ReadOnlyViewSet, ActionViewSet

# API版本控制
from core.versioning import APIVersion, FeatureFlags
```

注意：
- 此目录只包含Django核心功能扩展
- 业务逻辑放在 services/ 目录
- 应用相关代码放在 apps/ 目录

警告：
- 此模块的导入应在Django setup()之后进行
- 避免在模块级别导入可能导致循环依赖的类
"""