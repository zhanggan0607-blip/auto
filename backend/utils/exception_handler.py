"""
统一异常处理模块

提供统一的异常处理机制，包括：
1. API异常处理装饰器 - 自动捕获异常并返回统一格式的API响应
2. 错误记录装饰器 - 自动记录错误到ERROR_LOG.md
3. 上下文管理器 - 用于更细粒度的异常控制

使用示例:
```python
# API视图异常处理
from utils.exception_handler import api_exception_handler

class MyViewSet(viewsets.ModelViewSet):
    @action(detail=True, methods=['post'])
    @api_exception_handler
    def my_action(self, request, pk=None):
        result = do_something()
        return APIResponse.success(data=result)

# 错误记录
from utils.exception_handler import catch_and_log

@catch_and_log(
    scenario="调用用户API时",
    solution="检查用户是否存在"
)
def get_user(user_id):
    return User.objects.get(id=user_id)

# 上下文管理器
from utils.exception_handler import ErrorContext

with ErrorContext("数据库操作", "检查数据库连接"):
    result = User.objects.get(id=1)
```
"""
import logging
import functools
import traceback
from typing import Callable, Optional, List, Any

from rest_framework import status
from django.core.exceptions import PermissionDenied as DjangoPermissionDenied
from rest_framework.exceptions import (
    APIException, ValidationError as DRFValidationError,
    PermissionDenied as DRFPermissionDenied, NotFound as DRFNotFound,
    AuthenticationFailed as DRFAuthenticationFailed
)

from utils.responses import UnifiedResponse

try:
    from utils.error_logger_service import error_logger
    HAS_ERROR_LOGGER = True
except ImportError:
    HAS_ERROR_LOGGER = False


logger = logging.getLogger(__name__)


# ==================== API异常处理 ====================

def api_exception_handler(func):
    """
    API异常处理装饰器
    
    自动捕获异常并返回统一格式的响应
    
    Args:
        func: 被装饰的函数
        
    Returns:
        装饰后的函数
        
    Example:
        @api_exception_handler
        def my_view(request):
            result = do_something()
            return APIResponse.success(data=result)
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            return _handle_api_exception(e, func.__name__)
    return wrapper


def api_exception_handler_async(func):
    """
    异步API异常处理装饰器
    
    用于异步视图方法
    
    Args:
        func: 被装饰的异步函数
        
    Returns:
        装饰后的异步函数
        
    Example:
        @api_exception_handler_async
        async def my_async_view(request):
            result = await do_something_async()
            return APIResponse.success(data=result)
    """
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            return _handle_api_exception(e, func.__name__)
    return wrapper


def _handle_api_exception(e, func_name):
    """
    处理API异常并返回统一格式的响应
    
    Args:
        e: 异常对象
        func_name: 函数名称
        
    Returns:
        APIResponse对象
    """
    error_message = str(e)
    response_status = status.HTTP_400_BAD_REQUEST
    
    if isinstance(e, DRFValidationError):
        error_message = _format_validation_error(e)
        response_status = status.HTTP_400_BAD_REQUEST
        logger.warning(f"[{func_name}] 验证错误: {error_message}")
        
    elif isinstance(e, DRFAuthenticationFailed):
        error_message = '认证失败'
        response_status = status.HTTP_401_UNAUTHORIZED
        logger.warning(f"[{func_name}] 认证失败")
        
    elif isinstance(e, (DRFPermissionDenied, DjangoPermissionDenied)):
        error_message = '无权限执行此操作'
        response_status = status.HTTP_403_FORBIDDEN
        logger.warning(f"[{func_name}] 权限不足")
        
    elif isinstance(e, DRFNotFound):
        error_message = '资源不存在'
        response_status = status.HTTP_404_NOT_FOUND
        logger.warning(f"[{func_name}] 资源不存在")
        
    elif isinstance(e, APIException):
        if hasattr(e, 'detail') and isinstance(e.detail, dict):
            error_message = e.detail.get('message', str(e.detail))
        else:
            error_message = str(e.detail) if hasattr(e, 'detail') else str(e)
        response_status = e.status_code
        logger.warning(f"[{func_name}] API异常: {error_message}")
        
    elif 'DoesNotExist' in type(e).__name__:
        model_name = _extract_model_name(e)
        error_message = f'{model_name}不存在' if model_name else '记录不存在'
        response_status = status.HTTP_404_NOT_FOUND
        logger.warning(f"[{func_name}] {error_message}")
        
    elif 'MultipleObjectsReturned' in type(e).__name__:
        error_message = '找到多条匹配记录'
        response_status = status.HTTP_400_BAD_REQUEST
        logger.warning(f"[{func_name}] {error_message}")
        
    elif 'IntegrityError' in type(e).__name__:
        error_message = '数据完整性错误，可能存在重复数据'
        response_status = status.HTTP_409_CONFLICT
        logger.error(f"[{func_name}] 数据完整性错误: {str(e)}")
        
    elif 'ConnectionError' in type(e).__name__ or 'Timeout' in type(e).__name__:
        error_message = '网络连接失败，请稍后重试'
        response_status = status.HTTP_503_SERVICE_UNAVAILABLE
        logger.error(f"[{func_name}] 网络错误: {str(e)}")
        
    else:
        logger.error(f"[{func_name}] 未处理的异常: {type(e).__name__}: {str(e)}", exc_info=True)
        error_message = f'操作失败: {str(e)}' if str(e) else '操作失败'
        response_status = status.HTTP_500_INTERNAL_SERVER_ERROR
    
    return UnifiedResponse.error(message=error_message, status_code=response_status)


def _format_validation_error(e):
    """
    格式化验证错误信息
    
    Args:
        e: ValidationError异常
        
    Returns:
        格式化后的错误信息字符串
    """
    if isinstance(e.detail, dict):
        errors = []
        for field, messages in e.detail.items():
            if isinstance(messages, list):
                errors.append(f"{field}: {', '.join(str(m) for m in messages)}")
            else:
                errors.append(f"{field}: {messages}")
        return '; '.join(errors)
    elif isinstance(e.detail, list):
        return '; '.join(str(m) for m in e.detail)
    return str(e.detail)


def _extract_model_name(e):
    """
    从DoesNotExist异常中提取模型名称
    
    Args:
        e: DoesNotExist异常
        
    Returns:
        模型名称字符串
    """
    try:
        error_type = type(e).__name__
        if 'DoesNotExist' in error_type:
            model_name = error_type.replace('DoesNotExist', '')
            words = []
            current_word = ''
            for char in model_name:
                if char.isupper() and current_word:
                    words.append(current_word)
                    current_word = char
                else:
                    current_word += char
            if current_word:
                words.append(current_word)
            return ''.join(words)
    except Exception:
        pass
    return None


# ==================== 错误记录装饰器 ====================

def catch_and_log(
    scenario: str = "",
    solution: str = "",
    prevention: str = "",
    related_files: List[str] = None,
    status: str = "已解决",
    reraise: bool = True,
    log_on_success: bool = False,
    return_on_error: Any = None
):
    """
    错误捕获装饰器
    
    自动捕获函数执行中的异常，记录到ERROR_LOG.md
    
    Args:
        scenario: 发生场景描述
        solution: 解决方案
        prevention: 预防措施
        related_files: 相关文件列表
        status: 错误状态（已解决/待解决）
        reraise: 是否重新抛出异常
        log_on_success: 是否在成功时也记录
        return_on_error: 发生错误时的返回值
        
    Returns:
        装饰器函数
        
    Example:
        @catch_and_log(
            scenario="调用用户API时",
            solution="检查用户是否存在",
            related_files=["apps/users/views.py"]
        )
        def get_user(user_id):
            return User.objects.get(id=user_id)
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                result = func(*args, **kwargs)
                if log_on_success and HAS_ERROR_LOGGER:
                    error_logger.log_error(
                        error_type="成功记录",
                        description=f"{func.__name__} 执行成功",
                        scenario=scenario or f"执行函数 {func.__name__}",
                        error_message="无错误",
                        solution=solution or "无需解决",
                        prevention=prevention,
                        related_files=related_files,
                        status=status,
                        check_duplicate=False
                    )
                return result
            except Exception as e:
                _log_exception(e, func, scenario, solution, prevention, related_files, status)
                if reraise:
                    raise
                return return_on_error
        return wrapper
    return decorator


def async_catch_and_log(
    scenario: str = "",
    solution: str = "",
    prevention: str = "",
    related_files: List[str] = None,
    status: str = "已解决",
    reraise: bool = True,
    return_on_error: Any = None
):
    """
    异步错误捕获装饰器
    
    用于异步函数的错误捕获和记录
    
    Args:
        scenario: 发生场景描述
        solution: 解决方案
        prevention: 预防措施
        related_files: 相关文件列表
        status: 错误状态
        reraise: 是否重新抛出异常
        return_on_error: 发生错误时的返回值
        
    Returns:
        装饰器函数
        
    Example:
        @async_catch_and_log(
            scenario="异步调用LLM服务时",
            solution="检查LLM服务配置"
        )
        async def call_llm(prompt):
            return await llm_service.chat(prompt)
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                _log_exception(e, func, scenario, solution, prevention, related_files, status)
                if reraise:
                    raise
                return return_on_error
        return wrapper
    return decorator


def _log_exception(e, func, scenario, solution, prevention, related_files, status):
    """
    记录异常到错误日志
    
    Args:
        e: 异常对象
        func: 函数对象
        scenario: 场景描述
        solution: 解决方案
        prevention: 预防措施
        related_files: 相关文件
        status: 状态
    """
    func_scenario = scenario or f"执行函数 {func.__module__}.{func.__name__}"
    func_files = related_files or []
    
    if not func_files:
        func_files = [func.__module__.replace('.', '/') + '.py']
    
    logger.error(f"[{func.__name__}] 异常: {type(e).__name__}: {str(e)}", exc_info=True)
    
    if HAS_ERROR_LOGGER:
        error_logger.log_exception(
            exception=e,
            scenario=func_scenario,
            solution=solution or "检查错误信息并修复",
            prevention=prevention,
            related_files=func_files,
            status=status
        )


# ==================== 上下文管理器 ====================

class ExceptionHandlerContext:
    """
    API异常处理上下文管理器
    
    用于需要更细粒度控制的API异常处理场景
    
    Example:
        with ExceptionHandlerContext("my_function") as ctx:
            result = do_something()
            return APIResponse.success(data=result)
        
        if ctx.exception:
            return ctx.get_response()
    """
    def __init__(self, func_name='unknown', log_errors=True):
        self.func_name = func_name
        self.log_errors = log_errors
        self.exception = None
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_val is not None:
            self.exception = exc_val
            if self.log_errors:
                logger.error(
                    f"[{self.func_name}] 异常: {type(exc_val).__name__}: {str(exc_val)}",
                    exc_info=True
                )
            return True
        return False
    
    def get_response(self):
        """
        获取异常对应的API响应
        
        Returns:
            APIResponse对象或None
        """
        if self.exception:
            return _handle_api_exception(self.exception, self.func_name)
        return None


class ErrorContext:
    """
    错误上下文管理器
    
    使用with语句自动捕获和记录错误
    
    Example:
        with ErrorContext("数据库操作", "检查数据库连接"):
            result = User.objects.get(id=1)
    """
    
    def __init__(
        self,
        scenario: str,
        solution: str = "",
        prevention: str = "",
        related_files: List[str] = None,
        status: str = "已解决",
        reraise: bool = True
    ):
        self.scenario = scenario
        self.solution = solution
        self.prevention = prevention
        self.related_files = related_files or []
        self.status = status
        self.reraise = reraise
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            from django.conf import settings as django_settings
            if django_settings.DEBUG:
                logger.error(f"[{self.scenario}] 异常: {exc_type.__name__}: {str(exc_val)}", exc_info=True)
            else:
                logger.error(f"[{self.scenario}] 异常: {exc_type.__name__}: {str(exc_val)}")

            if HAS_ERROR_LOGGER:
                error_traceback = ''.join(traceback.format_exception(exc_type, exc_val, exc_tb)) if django_settings.DEBUG else '[生产环境隐藏]'
                error_logger.log_error(
                    error_type=exc_type.__name__,
                    description=str(exc_val),
                    scenario=self.scenario,
                    error_message=error_traceback,
                    solution=self.solution or "检查错误信息并修复",
                    prevention=self.prevention,
                    related_files=self.related_files,
                    status=self.status
                )

            return not self.reraise

        return False


# ==================== Celery任务装饰器 ====================

def log_task_error(task_name: str):
    """
    Celery任务错误记录装饰器
    
    专门用于Celery任务的错误记录
    
    Args:
        task_name: 任务名称
        
    Example:
        @log_task_error("爬虫任务")
        @app.task
        def crawl_task(url):
            return crawler.crawl(url)
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                _log_exception(
                    e, func,
                    scenario=f"Celery任务 {task_name} 执行时",
                    solution="检查任务参数和依赖服务",
                    prevention="添加任务重试机制",
                    related_files=[func.__module__.replace('.', '/') + '.py'],
                    status="待解决"
                )
                raise
        return wrapper
    return decorator


# ==================== 导出 ====================

__all__ = [
    'api_exception_handler',
    'api_exception_handler_async',
    'catch_and_log',
    'async_catch_and_log',
    'ExceptionHandlerContext',
    'ErrorContext',
    'log_task_error',
]
