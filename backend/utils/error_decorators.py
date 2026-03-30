"""
错误捕获装饰器模块

已迁移到 utils/exception_handler.py
此文件保留用于向后兼容，建议直接使用新模块

使用示例:
```python
from utils.error_decorators import catch_and_log

@catch_and_log(
    scenario="调用用户API时",
    solution="检查用户是否存在"
)
def get_user(user_id):
    return User.objects.get(id=user_id)
```
"""
from utils.exception_handler import (
    catch_and_log,
    async_catch_and_log,
    ErrorContext,
    log_task_error,
)

__all__ = [
    'catch_and_log',
    'async_catch_and_log',
    'ErrorContext',
    'log_task_error',
]
