"""
统一API响应格式
提供标准化的API响应格式，确保前后端数据交互一致性

响应格式统一为：
{
    "success": true/false,
    "code": 0/错误码字符串,
    "message": "消息",
    "data": {...},
    "errors": {...}  // 可选，验证错误详情
}

增强特性：
- 支持错误码体系（ErrorCode）
- 集成统一异常类
- 增强的分页响应
"""

from functools import wraps
from rest_framework.response import Response
from rest_framework import status
import logging

from common.constants.error_codes import ErrorCode, get_error_message, get_http_status

logger = logging.getLogger(__name__)


class ResponseCode:
    """
    响应码常量定义（向后兼容）
    """
    SUCCESS = 0
    ERROR = 1
    VALIDATION_ERROR = 400
    UNAUTHORIZED = 401
    FORBIDDEN = 403
    NOT_FOUND = 404
    SERVER_ERROR = 500

    CODE_MESSAGES = {
        0: '操作成功',
        1: '操作失败',
        400: '参数验证失败',
        401: '未授权访问',
        403: '禁止访问',
        404: '资源不存在',
        500: '服务器内部错误'
    }


class UnifiedResponse:
    """
    统一API响应类

    所有API接口应使用此类返回响应，确保格式一致
    """

    @staticmethod
    def success(data=None, message='操作成功', status_code=status.HTTP_200_OK, code=None):
        """
        成功响应

        Args:
            data: 响应数据
            message: 成功消息
            status_code: HTTP状态码
            code: 业务错误码（用于区分不同类型的成功）

        Returns:
            Response: DRF Response对象
        """
        response_data = {
            'success': True,
            'code': code if code is not None else ResponseCode.SUCCESS,
            'message': message,
            'data': data
        }
        return Response(response_data, status=status_code)

    @staticmethod
    def error(message='操作失败', code=None, data=None, status_code=status.HTTP_400_BAD_REQUEST, error_code=None):
        """
        错误响应

        Args:
            message: 错误消息
            code: 业务错误码（数字）
            data: 附加数据
            status_code: HTTP状态码
            error_code: 错误码字符串（如'AUTH_TOKEN_EXPIRED'）

        Returns:
            Response: DRF Response对象
        """
        if error_code:
            resolved_code = error_code
            resolved_message = get_error_message(error_code, message)
            resolved_status = get_http_status(error_code)
        elif code:
            resolved_code = code
            resolved_message = message
            resolved_status = status_code
        else:
            resolved_code = ResponseCode.ERROR
            resolved_message = message
            resolved_status = status_code

        response_data = {
            'success': False,
            'code': resolved_code,
            'message': resolved_message,
            'data': data
        }
        return Response(response_data, status=resolved_status)

    @staticmethod
    def paginated(data, page, page_size, total, message='查询成功', **extra_data):
        """
        分页响应

        Args:
            data: 数据列表
            page: 当前页码
            page_size: 每页数量
            total: 总数量
            message: 响应消息
            **extra_data: 额外的分页字段

        Returns:
            Response: DRF Response对象
        """
        page = int(page) if page else 1
        page_size = int(page_size) if page_size else 20
        total = int(total) if total else 0
        total_pages = (total + page_size - 1) // page_size if page_size > 0 else 0

        pagination_data = {
            'page': page,
            'page_size': page_size,
            'total': total,
            'total_pages': total_pages
        }
        pagination_data.update(extra_data)

        return Response({
            'success': True,
            'code': ResponseCode.SUCCESS,
            'message': message,
            'data': {
                'list': data,
                'pagination': pagination_data
            }
        })

    @staticmethod
    def created(data=None, message='创建成功', **kwargs):
        """创建成功响应"""
        return UnifiedResponse.success(
            data=data,
            message=message,
            status_code=status.HTTP_201_CREATED,
            **kwargs
        )

    @staticmethod
    def updated(data=None, message='更新成功', **kwargs):
        """更新成功响应"""
        return UnifiedResponse.success(
            data=data,
            message=message,
            **kwargs
        )

    @staticmethod
    def deleted(message='删除成功', **kwargs):
        """删除成功响应"""
        return UnifiedResponse.success(
            data=None,
            message=message,
            **kwargs
        )

    @staticmethod
    def not_found(message=None, error_code=None, **kwargs):
        """资源不存在响应"""
        error_code = error_code or 'NOT_FOUND'
        resolved_message = get_error_message(error_code, message) if message else None
        return UnifiedResponse.error(
            message=resolved_message or '资源不存在',
            error_code=error_code,
            status_code=status.HTTP_404_NOT_FOUND,
            **kwargs
        )

    @staticmethod
    def unauthorized(message=None, error_code=None, **kwargs):
        """未授权响应"""
        error_code = error_code or 'AUTH_TOKEN_INVALID'
        resolved_message = get_error_message(error_code, message) if message else None
        return UnifiedResponse.error(
            message=resolved_message or '未授权访问',
            error_code=error_code,
            status_code=status.HTTP_401_UNAUTHORIZED,
            **kwargs
        )

    @staticmethod
    def forbidden(message=None, error_code=None, **kwargs):
        """禁止访问响应"""
        error_code = error_code or 'PERMISSION_DENIED'
        resolved_message = get_error_message(error_code, message) if message else None
        return UnifiedResponse.error(
            message=resolved_message or '禁止访问',
            error_code=error_code,
            status_code=status.HTTP_403_FORBIDDEN,
            **kwargs
        )

    @staticmethod
    def validation_error(errors=None, message=None, error_code=None, **kwargs):
        """参数验证失败响应"""
        error_code = error_code or 'INVALID_PARAMETER'
        resolved_message = get_error_message(error_code, message) if message else None
        return UnifiedResponse.error(
            message=resolved_message or '参数验证失败',
            error_code=error_code,
            data={'errors': errors} if errors else None,
            status_code=status.HTTP_400_BAD_REQUEST,
            **kwargs
        )

    @staticmethod
    def server_error(message=None, error_code=None, **kwargs):
        """服务器错误响应"""
        error_code = error_code or 'INTERNAL_ERROR'
        resolved_message = get_error_message(error_code, message) if message else None
        return UnifiedResponse.error(
            message=resolved_message or '服务器内部错误',
            error_code=error_code,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            **kwargs
        )

    @staticmethod
    def from_error_code(error_code_enum: ErrorCode, message: str = None, **kwargs):
        """
        从ErrorCode枚举创建响应

        Args:
            error_code_enum: ErrorCode枚举值
            message: 自定义消息

        Returns:
            Response: DRF Response对象
        """
        code = error_code_enum.value[0]
        default_message = error_code_enum.value[1]
        http_status = error_code_enum.value[2]

        final_message = message or default_message

        return UnifiedResponse.error(
            message=final_message,
            error_code=code,
            status_code=http_status,
            **kwargs
        )


APIResponse = UnifiedResponse


def api_response(message='操作成功'):
    """
    API响应装饰器
    自动包装函数返回值为统一响应格式

    Args:
        message: 成功消息

    Usage:
        @api_response(message='获取成功')
        def get_data(request):
            return {'key': 'value'}
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                result = func(*args, **kwargs)

                if isinstance(result, Response):
                    return result

                if isinstance(result, dict):
                    if result.get('code') is not None:
                        return Response(result)
                    return APIResponse.success(data=result, message=message)

                if isinstance(result, (list, tuple)):
                    return APIResponse.success(data={'list': result}, message=message)

                return APIResponse.success(data=result, message=message)

            except Exception as e:
                logger.error(f"API响应装饰器捕获异常: {str(e)}", exc_info=True)
                return APIResponse.error(message=str(e))

        return wrapper
    return decorator


def paginated_response(message='查询成功'):
    """
    分页响应装饰器
    自动处理分页逻辑

    Usage:
        @paginated_response()
        def list_items(request):
            queryset = Model.objects.all()
            return queryset, request
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                result = func(*args, **kwargs)

                if isinstance(result, Response):
                    return result

                if isinstance(result, tuple) and len(result) == 2:
                    data, request = result
                    page = request.query_params.get('page', 1)
                    page_size = request.query_params.get('page_size', 20)

                    if hasattr(data, '__iter__') and not isinstance(data, (list, dict)):
                        total = len(data) if hasattr(data, '__len__') else 0
                        start = (int(page) - 1) * int(page_size)
                        end = start + int(page_size)
                        paginated_data = list(data[start:end])
                        return APIResponse.paginated(paginated_data, page, page_size, total, message)

                    return APIResponse.success(data=data, message=message)

                return APIResponse.success(data=result, message=message)

            except Exception as e:
                logger.error(f"分页响应装饰器捕获异常: {str(e)}", exc_info=True)
                return APIResponse.error(message=str(e))

        return wrapper
    return decorator


class ResponseBuilder:
    """
    响应构建器
    用于复杂场景下的响应构建
    """

    def __init__(self):
        self._success = True
        self._code = ResponseCode.SUCCESS
        self._message = '操作成功'
        self._data = None
        self._status_code = status.HTTP_200_OK
        self._error_code = None

    def set_data(self, data):
        """设置响应数据"""
        self._data = data
        return self

    def set_message(self, message):
        """设置响应消息"""
        self._message = message
        return self

    def set_code(self, code):
        """设置业务码"""
        self._code = code
        return self

    def set_error_code(self, error_code: str):
        """设置错误码字符串"""
        self._error_code = error_code
        return self

    def set_status(self, status_code):
        """设置HTTP状态码"""
        self._status_code = status_code
        return self

    def success(self):
        """标记为成功"""
        self._success = True
        self._code = ResponseCode.SUCCESS
        self._status_code = status.HTTP_200_OK
        return self

    def error(self):
        """标记为错误"""
        self._success = False
        self._code = ResponseCode.ERROR
        self._status_code = status.HTTP_400_BAD_REQUEST
        return self

    def build(self):
        """构建响应"""
        response_data = {
            'success': self._success,
            'code': self._error_code or self._code,
            'message': self._message,
            'data': self._data
        }
        return Response(response_data, status=self._status_code)
