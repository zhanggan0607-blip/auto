"""
自定义异常处理器
统一API错误响应格式
"""
import logging
import traceback
from rest_framework.views import exception_handler
from rest_framework.exceptions import (
    APIException, ValidationError, AuthenticationFailed,
    PermissionDenied, NotFound, Throttled
)
from rest_framework.response import Response
from rest_framework import status
from django.db import DatabaseError, OperationalError
from django.core.exceptions import PermissionDenied as DjangoPermissionDenied

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    """
    自定义异常处理器
    
    统一错误响应格式:
    {
        "success": false,
        "code": "ERROR_CODE",
        "message": "错误消息",
        "data": null,
        "errors": {...}  # 可选，详细错误信息
    }
    """
    response = exception_handler(exc, context)
    
    if response is not None:
        error_code = get_error_code(exc)
        error_message = get_error_message(exc)
        errors = get_error_details(exc)
        
        custom_response = {
            'success': False,
            'code': error_code,
            'message': error_message,
            'data': None,
        }
        
        if errors:
            custom_response['errors'] = errors
        
        response.data = custom_response
        response.status_code = get_http_status(exc, response.status_code)
        
        log_exception(exc, context, response.status_code)
        
    else:
        if isinstance(exc, DatabaseError):
            response = handle_database_error(exc, context)
        elif isinstance(exc, OperationalError):
            response = handle_operational_error(exc, context)
        elif isinstance(exc, DjangoPermissionDenied):
            response = handle_permission_denied(exc, context)
        else:
            response = handle_unexpected_error(exc, context)
    
    return response


def get_error_code(exc) -> str:
    """
    获取错误代码
    """
    error_codes = {
        ValidationError: 'VALIDATION_ERROR',
        AuthenticationFailed: 'AUTHENTICATION_FAILED',
        PermissionDenied: 'PERMISSION_DENIED',
        NotFound: 'NOT_FOUND',
        Throttled: 'RATE_LIMIT_EXCEEDED',
        DatabaseError: 'DATABASE_ERROR',
        OperationalError: 'SERVICE_UNAVAILABLE',
    }
    
    for exc_class, code in error_codes.items():
        if isinstance(exc, exc_class):
            return code
    
    if hasattr(exc, 'code'):
        return str(exc.code)
    
    return 'INTERNAL_ERROR'


def get_error_message(exc) -> str:
    """
    获取用户友好的错误消息
    """
    if isinstance(exc, ValidationError):
        if hasattr(exc, 'detail'):
            if isinstance(exc.detail, dict):
                return '数据验证失败'
            elif isinstance(exc.detail, list):
                return exc.detail[0] if exc.detail else '数据验证失败'
        return '数据验证失败'
    
    if isinstance(exc, AuthenticationFailed):
        return '认证失败，请重新登录'
    
    if isinstance(exc, PermissionDenied):
        return '您没有权限执行此操作'
    
    if isinstance(exc, NotFound):
        return '请求的资源不存在'
    
    if isinstance(exc, Throttled):
        wait_time = getattr(exc, 'wait', None)
        if wait_time:
            return f'请求过于频繁，请 {wait_time} 秒后再试'
        return '请求过于频繁，请稍后再试'
    
    if isinstance(exc, DatabaseError):
        return '数据库错误，请稍后再试'
    
    if isinstance(exc, OperationalError):
        return '服务暂时不可用，请稍后再试'
    
    if hasattr(exc, 'detail'):
        return str(exc.detail)
    
    if hasattr(exc, 'message'):
        return str(exc.message)
    
    return '服务器内部错误'


def get_error_details(exc) -> dict:
    """
    获取详细错误信息
    """
    if isinstance(exc, ValidationError):
        if hasattr(exc, 'detail'):
            if isinstance(exc.detail, dict):
                return {k: str(v[0]) if isinstance(v, list) else str(v) 
                        for k, v in exc.detail.items()}
            elif isinstance(exc.detail, list):
                return {'detail': exc.detail}
    
    return None


def get_http_status(exc, default_status: int) -> int:
    """
    获取HTTP状态码
    """
    if isinstance(exc, DatabaseError):
        return status.HTTP_503_SERVICE_UNAVAILABLE
    
    if isinstance(exc, OperationalError):
        return status.HTTP_503_SERVICE_UNAVAILABLE
    
    return default_status


def log_exception(exc, context, status_code: int):
    """
    记录异常日志
    安全改进：生产环境禁止输出完整堆栈信息
    """
    from django.conf import settings

    view = context.get('view')
    request = context.get('request')

    view_name = view.__class__.__name__ if view else 'Unknown'
    request_path = request.path if request else 'Unknown'
    request_method = request.method if request else 'Unknown'

    if status_code >= 500:
        if settings.DEBUG:
            logger.error(
                f"[{view_name}] {request_method} {request_path} - "
                f"Status: {status_code}, Error: {str(exc)}\n"
                f"Traceback: {traceback.format_exc()}"
            )
        else:
            logger.error(
                f"[{view_name}] {request_method} {request_path} - "
                f"Status: {status_code}, Error: {str(exc)} [堆栈信息已隐藏，生产环境禁止输出]"
            )
    elif status_code >= 400:
        logger.warning(
            f"[{view_name}] {request_method} {request_path} - "
            f"Status: {status_code}, Error: {str(exc)}"
        )


def handle_database_error(exc, context) -> Response:
    """
    处理数据库错误
    """
    log_exception(exc, context, status.HTTP_503_SERVICE_UNAVAILABLE)
    
    return Response({
        'success': False,
        'code': 'DATABASE_ERROR',
        'message': '数据库服务暂时不可用，请稍后再试',
        'data': None,
    }, status=status.HTTP_503_SERVICE_UNAVAILABLE)


def handle_operational_error(exc, context) -> Response:
    """
    处理服务不可用错误
    """
    log_exception(exc, context, status.HTTP_503_SERVICE_UNAVAILABLE)
    
    return Response({
        'success': False,
        'code': 'SERVICE_UNAVAILABLE',
        'message': '服务暂时不可用，请稍后再试',
        'data': None,
    }, status=status.HTTP_503_SERVICE_UNAVAILABLE)


def handle_permission_denied(exc, context) -> Response:
    """
    处理权限拒绝
    """
    return Response({
        'success': False,
        'code': 'PERMISSION_DENIED',
        'message': '您没有权限执行此操作',
        'data': None,
    }, status=status.HTTP_403_FORBIDDEN)


def handle_unexpected_error(exc, context) -> Response:
    """
    处理未预期的错误
    """
    log_exception(exc, context, status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    return Response({
        'success': False,
        'code': 'INTERNAL_ERROR',
        'message': '服务器内部错误，请稍后再试',
        'data': None,
    }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class BusinessException(APIException):
    """
    业务异常基类
    用于业务逻辑中的预期错误
    """
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = '业务处理失败'
    default_code = 'BUSINESS_ERROR'
    
    def __init__(self, message=None, code=None, data=None):
        self.detail = message or self.default_detail
        self.code = code or self.default_code
        self.data = data


class ResourceNotFoundException(BusinessException):
    """
    资源未找到异常
    """
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = '资源不存在'
    default_code = 'RESOURCE_NOT_FOUND'


class DuplicateException(BusinessException):
    """
    重复数据异常
    """
    status_code = status.HTTP_409_CONFLICT
    default_detail = '数据已存在'
    default_code = 'DUPLICATE_ERROR'


class WorkflowException(BusinessException):
    """
    工作流异常
    """
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = '工作流执行失败'
    default_code = 'WORKFLOW_ERROR'


class CrawlerException(BusinessException):
    """
    爬虫异常
    """
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_detail = '数据采集失败'
    default_code = 'CRAWLER_ERROR'


class VectorDBException(BusinessException):
    """
    向量库异常
    """
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_detail = '向量检索失败'
    default_code = 'VECTOR_DB_ERROR'


class LLMException(BusinessException):
    """
    LLM服务异常
    """
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    default_detail = 'AI服务暂时不可用'
    default_code = 'LLM_ERROR'
