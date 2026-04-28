"""
统一异常类定义
基于错误码体系的业务异常

使用方式：
    from common.exceptions import BusinessError, ValidationError, NotFoundError

    raise BusinessError('USER_NOT_FOUND', '用户不存在')
    raise ValidationError('INVALID_PARAMETER', '手机号格式不正确')
    raise NotFoundError('ENTERPRISE_NOT_FOUND')
"""

from rest_framework import status
from rest_framework.exceptions import APIException
from django.utils.translation import gettext_lazy as _

from common.constants.error_codes import ErrorCode, get_error_message, get_http_status


class BaseAPIException(APIException):
    """
    基础API异常
    所有业务异常的基类
    """

    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "操作失败"
    default_code = "error"

    def __init__(self, detail=None, code=None, **kwargs):
        if detail is None:
            detail = self.default_detail

        if code is None:
            code = self.default_code

        self.error_code = code
        self.error_message = detail

        super().__init__(detail=detail, code=code)


class BusinessError(BaseAPIException):
    """
    业务异常
    用于通用业务逻辑错误

    Args:
        error_code: ErrorCode枚举值或错误码字符串
        message: 自定义错误信息
        **kwargs: 其他参数
    """

    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "业务操作失败"
    default_code = "BUSINESS_ERROR"

    def __init__(self, error_code=None, message=None, **kwargs):
        if error_code is None:
            super().__init__(message, self.default_code, **kwargs)
            return

        if isinstance(error_code, ErrorCode):
            self.error_code = error_code.value[0]
            self.status_code = error_code.value[2]
            self.default_detail = error_code.value[1]
        elif isinstance(error_code, str):
            self.error_code = error_code
            http_status = get_http_status(error_code)
            self.status_code = http_status

        final_message = get_error_message(self.error_code, message)

        super().__init__(final_message, self.error_code, **kwargs)


class ValidationError(BaseAPIException):
    """
    参数验证异常
    用于请求参数校验失败
    """

    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "参数校验失败"
    default_code = "VALIDATION_ERROR"


class NotFoundError(BusinessError):
    """
    资源不存在异常
    用于查询不存在的资源
    """

    status_code = status.HTTP_404_NOT_FOUND
    default_detail = "资源不存在"
    default_code = "NOT_FOUND"

    def __init__(self, resource_name=None, resource_id=None, error_code=None):
        if resource_name:
            message = f"{resource_name}不存在"
            if resource_id:
                message = f"{resource_name}(ID: {resource_id})不存在"
        else:
            message = None

        if error_code is None:
            error_code = "NOT_FOUND"

        super().__init__(error_code, message)


class AlreadyExistsError(BusinessError):
    """
    资源已存在异常
    用于创建重复资源
    """

    status_code = status.HTTP_409_CONFLICT
    default_detail = "资源已存在"
    default_code = "ALREADY_EXISTS"

    def __init__(self, resource_name=None, error_code=None):
        if resource_name:
            message = f"{resource_name}已存在"
        else:
            message = None

        if error_code is None:
            error_code = "ALREADY_EXISTS"

        super().__init__(error_code, message)


class PermissionDeniedError(BaseAPIException):
    """
    权限不足异常
    用于权限校验失败
    """

    status_code = status.HTTP_403_FORBIDDEN
    default_detail = "权限不足"
    default_code = "PERMISSION_DENIED"


class AuthenticationError(BaseAPIException):
    """
    认证失败异常
    用于登录认证失败
    """

    status_code = status.HTTP_401_UNAUTHORIZED
    default_detail = "认证失败"
    default_code = "AUTHENTICATION_FAILED"


class TokenExpiredError(AuthenticationError):
    """
    Token过期异常
    """

    status_code = status.HTTP_401_UNAUTHORIZED
    default_detail = "Token已过期"
    default_code = "TOKEN_EXPIRED"


class RateLimitError(BaseAPIException):
    """
    请求频率超限异常
    """

    status_code = status.HTTP_429_TOO_MANY_REQUESTS
    default_detail = "请求过于频繁，请稍后再试"
    default_code = "RATE_LIMITED"


class ServiceUnavailableError(BaseAPIException):
    """
    服务不可用异常
    """

    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    default_detail = "服务暂时不可用"
    default_code = "SERVICE_UNAVAILABLE"


class ExternalServiceError(BaseAPIException):
    """
    外部服务调用异常
    用于调用第三方服务失败
    """

    status_code = status.HTTP_502_BAD_GATEWAY
    default_detail = "外部服务调用失败"
    default_code = "EXTERNAL_SERVICE_ERROR"

    def __init__(self, service_name=None, message=None):
        if service_name and message:
            detail = f"{service_name}服务调用失败: {message}"
        elif service_name:
            detail = f"{service_name}服务不可用"
        else:
            detail = "外部服务调用失败"

        super().__init__(detail, self.default_code)


def convert_django_validation_error(error):
    """
    将Django ValidationError转换为统一的异常格式

    Args:
        error: Django ValidationError

    Returns:
        ValidationError: 转换后的异常
    """
    if hasattr(error, 'message_dict'):
        messages = []
        for field, errors in error.message_dict.items():
            if isinstance(errors, list):
                for msg in errors:
                    messages.append(f"{field}: {msg}")
            else:
                messages.append(f"{field}: {errors}")
        detail = "; ".join(messages)
    elif hasattr(error, 'message'):
        detail = str(error.message)
    else:
        detail = str(error)

    return ValidationError(detail)


def exception_handler(exc, context):
    from rest_framework.views import set_rollback
    from rest_framework.exceptions import (
        ValidationError as DRFValidationError,
        PermissionDenied as DRFPermissionDenied,
        NotAuthenticated,
        AuthenticationFailed,
        NotFound as DRFNotFound,
        Throttled,
    )
    from django.core.exceptions import PermissionDenied as DjangoPermissionDenied
    from django.http import Http404
    from utils.responses import UnifiedResponse
    from common.constants.error_codes import ErrorCode

    if isinstance(exc, NotAuthenticated):
        set_rollback()
        return UnifiedResponse.error(
            message='身份认证信息未提供',
            error_code=ErrorCode.AUTH_TOKEN_MISSING.value[0],
            status_code=status.HTTP_401_UNAUTHORIZED
        )

    if isinstance(exc, AuthenticationFailed):
        set_rollback()
        return UnifiedResponse.error(
            message='认证失败',
            error_code=ErrorCode.AUTH_TOKEN_INVALID.value[0],
            status_code=status.HTTP_401_UNAUTHORIZED
        )

    if isinstance(exc, (DRFPermissionDenied, DjangoPermissionDenied)):
        set_rollback()
        return UnifiedResponse.error(
            message='无权限执行此操作',
            error_code=ErrorCode.PERMISSION_DENIED.value[0],
            status_code=status.HTTP_403_FORBIDDEN
        )

    if isinstance(exc, Http404):
        set_rollback()
        return UnifiedResponse.not_found(message='资源不存在')

    if isinstance(exc, DRFNotFound):
        set_rollback()
        return UnifiedResponse.not_found(message=str(exc.detail) if hasattr(exc, 'detail') else '资源不存在')

    if isinstance(exc, DRFValidationError):
        set_rollback()
        if isinstance(exc.detail, dict):
            errors = []
            for field, messages in exc.detail.items():
                if isinstance(messages, list):
                    errors.append(f"{field}: {', '.join(str(m) for m in messages)}")
                else:
                    errors.append(f"{field}: {messages}")
            message = '; '.join(errors)
        elif isinstance(exc.detail, list):
            message = '; '.join(str(m) for m in exc.detail)
        else:
            message = str(exc.detail)
        return UnifiedResponse.validation_error(message=message)

    if isinstance(exc, Throttled):
        set_rollback()
        wait = exc.wait
        message = f'请求过于频繁，请{"%.0f" % wait}秒后再试' if wait else '请求过于频繁，请稍后再试'
        return UnifiedResponse.error(
            message=message,
            error_code=ErrorCode.RATE_LIMITED.value[0],
            status_code=status.HTTP_429_TOO_MANY_REQUESTS
        )

    if isinstance(exc, BaseAPIException):
        set_rollback()
        error_code = getattr(exc, 'error_code', exc.default_code)
        return UnifiedResponse.error(
            message=str(exc.detail) if hasattr(exc, 'detail') else str(exc),
            error_code=error_code if isinstance(error_code, str) else str(error_code),
            status_code=exc.status_code
        )

    if isinstance(exc, APIException):
        set_rollback()
        return UnifiedResponse.error(
            message=str(exc.detail) if hasattr(exc, 'detail') else str(exc),
            error_code=getattr(exc, 'default_code', 'API_ERROR'),
            status_code=exc.status_code
        )

    import logging
    logging.getLogger(__name__).error(
        f"Unhandled exception: {type(exc).__name__}: {str(exc)}",
        exc_info=True
    )

    from django.conf import settings as django_settings
    if django_settings.DEBUG:
        message = f'{type(exc).__name__}: {str(exc)}'
    else:
        message = '服务器内部错误'

    set_rollback()
    return UnifiedResponse.server_error(message=message)
