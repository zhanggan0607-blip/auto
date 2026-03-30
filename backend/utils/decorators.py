"""
API异常处理装饰器

已迁移到 utils/exception_handler.py
此文件保留用于向后兼容，建议直接使用新模块

使用示例:
```python
from utils.decorators import api_exception_handler

class MyViewSet(viewsets.ModelViewSet):
    @action(detail=True, methods=['post'])
    @api_exception_handler
    def my_action(self, request, pk=None):
        result = do_something()
        return APIResponse.success(data=result)
```
"""
from utils.exception_handler import (
    api_exception_handler,
    api_exception_handler_async,
    ExceptionHandlerContext,
)

__all__ = [
    'api_exception_handler',
    'api_exception_handler_async',
    'ExceptionHandlerContext',
]
