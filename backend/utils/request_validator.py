"""
请求参数验证模块

提供统一的请求参数验证机制，包括：
1. 参数必填验证
2. 参数类型验证
3. 参数格式验证（正则表达式）
4. 参数范围验证
5. 自定义验证规则

使用示例:
```python
from utils.request_validator import validate_params, Required, Optional, Type, Range

# 基本验证
@validate_params([
    Required('id', int, description='用户ID'),
    Required('name', str, description='用户名'),
])
def get_user(request):
    ...

# 带格式验证
@validate_params([
    Required('email', str, pattern=r'^[\w\.-]+@[\w\.-]+\.\w+$', description='邮箱'),
    Required('phone', str, pattern=r'^1[3-9]\d{9}$', description='手机号'),
])
def create_user(request):
    ...

# 带范围验证
@validate_params([
    Required('page', int, min_value=1, max_value=100, description='页码'),
    Optional('page_size', int, default=20, min_value=1, max_value=100),
])
def list_users(request):
    ...

# 自定义验证
@validate_params([
    Required('code', str, custom=lambda x: len(x) == 6, custom_msg='验证码必须为6位'),
])
def verify_code(request):
    ...
```
"""
import functools
import re
from typing import Any, Callable, Dict, List, Optional, Union

from rest_framework import status

from utils.responses import UnifiedResponse


class ValidationError(Exception):
    """参数验证错误异常"""

    def __init__(self, field: str, message: str):
        self.field = field
        self.message = message
        super().__init__(message)


class Required:
    """必填参数定义"""

    def __init__(
        self,
        name: str,
        param_type: type = str,
        pattern: str = None,
        min_value: Union[int, float] = None,
        max_value: Union[int, float] = None,
        allowed_values: List[Any] = None,
        custom: Callable[[Any], bool] = None,
        custom_msg: str = None,
        description: str = None,
        error_code: str = None,
    ):
        self.name = name
        self.param_type = param_type
        self.pattern = pattern
        self.min_value = min_value
        self.max_value = max_value
        self.allowed_values = allowed_values
        self.custom = custom
        self.custom_msg = custom_msg
        self.description = description or name
        self.error_code = error_code or 'INVALID_PARAMETER'


class Optional:
    """可选参数定义"""

    def __init__(
        self,
        name: str,
        param_type: type = str,
        default: Any = None,
        pattern: str = None,
        min_value: Union[int, float] = None,
        max_value: Union[int, float] = None,
        allowed_values: List[Any] = None,
        custom: Callable[[Any], bool] = None,
        custom_msg: str = None,
        description: str = None,
        error_code: str = None,
    ):
        self.name = name
        self.param_type = param_type
        self.default = default
        self.pattern = pattern
        self.min_value = min_value
        self.max_value = max_value
        self.allowed_values = allowed_values
        self.custom = custom
        self.custom_msg = custom_msg
        self.description = description or name
        self.error_code = error_code or 'INVALID_PARAMETER'


def validate_params(params: List[Union[Required, Optional]]):
    """
    请求参数验证装饰器

    Args:
        params: 参数定义列表

    Returns:
        装饰器函数

    Example:
        @validate_params([
            Required('id', int, description='用户ID'),
            Optional('name', str, default='匿名'),
        ])
        def get_user(request):
            ...
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            errors = []
            validated_data = {}

            request = None
            for arg in args:
                if hasattr(arg, 'query_params'):
                    request = arg
                    break

            if request is None:
                return func(*args, **kwargs)

            for param_def in params:
                name = param_def.name
                value = request.query_params.get(name) or request.data.get(name)

                if isinstance(param_def, Required):
                    if value is None or value == '':
                        errors.append({
                            'field': name,
                            'message': f'{param_def.description}不能为空',
                            'code': 'REQUIRED_FIELD_MISSING'
                        })
                        continue

                    try:
                        validated_value = _validate_and_convert(
                            value, param_def, name
                        )
                        if validated_value is not None:
                            validated_data[name] = validated_value
                    except ValidationError as e:
                        errors.append({
                            'field': e.field,
                            'message': e.message,
                            'code': param_def.error_code
                        })

                elif isinstance(param_def, Optional):
                    if value is None or value == '':
                        if param_def.default is not None:
                            validated_data[name] = param_def.default
                    else:
                        try:
                            validated_value = _validate_and_convert(
                                value, param_def, name
                            )
                            if validated_value is not None:
                                validated_data[name] = validated_value
                        except ValidationError as e:
                            errors.append({
                                'field': e.field,
                                'message': e.message,
                                'code': param_def.error_code
                            })

            if errors:
                return UnifiedResponse.error(
                    message='参数验证失败',
                    code=400,
                    data={'errors': errors},
                    status_code=status.HTTP_400_BAD_REQUEST
                )

            request.validated_data = validated_data
            return func(*args, **kwargs)

        return wrapper

    return decorator


def _validate_and_convert(value: Any, param_def, field_name: str) -> Any:
    """
    验证并转换参数值

    Args:
        value: 参数原始值
        param_def: 参数定义对象
        field_name: 字段名称

    Returns:
        验证并转换后的值

    Raises:
        ValidationError: 验证失败时抛出
    """
    original_value = value

    if param_def.param_type in (int, 'int'):
        try:
            value = int(value)
        except (ValueError, TypeError):
            raise ValidationError(field_name, f'{param_def.description}必须为整数')

    elif param_def.param_type in (float, 'float'):
        try:
            value = float(value)
        except (ValueError, TypeError):
            raise ValidationError(field_name, f'{param_def.description}必须为数字')

    elif param_def.param_type == bool and isinstance(value, str):
        value = value.lower() in ('true', '1', 'yes', 'on')

    if param_def.pattern is not None:
        pattern = param_def.pattern
        if isinstance(pattern, str):
            pattern = re.compile(pattern)
        if not pattern.match(str(value)):
            raise ValidationError(field_name, f'{param_def.description}格式不正确')

    if param_def.min_value is not None and isinstance(value, (int, float)):
        if value < param_def.min_value:
            raise ValidationError(
                field_name,
                f'{param_def.description}不能小于{param_def.min_value}'
            )

    if param_def.max_value is not None and isinstance(value, (int, float)):
        if value > param_def.max_value:
            raise ValidationError(
                field_name,
                f'{param_def.description}不能大于{param_def.max_value}'
            )

    if param_def.allowed_values is not None:
        if value not in param_def.allowed_values:
            allowed_str = ', '.join(str(v) for v in param_def.allowed_values)
            raise ValidationError(
                field_name,
                f'{param_def.description}必须是以下值之一: {allowed_str}'
            )

    if param_def.custom is not None:
        try:
            if not param_def.custom(value):
                raise ValidationError(
                    field_name,
                    param_def.custom_msg or f'{param_def.description}验证失败'
                )
        except Exception as e:
            if isinstance(e, ValidationError):
                raise
            raise ValidationError(field_name, str(e))

    return value


def validate_pagination(func: Callable) -> Callable:
    """
    分页参数验证装饰器

    自动验证并转换 page 和 page_size 参数

    Example:
        @validate_pagination
        def list_view(request):
            page = request.validated_pagination.get('page', 1)
            page_size = request.validated_pagination.get('page_size', 20)
            ...
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        request = None
        for arg in args:
            if hasattr(arg, 'query_params'):
                request = arg
                break

        if request is None:
            return func(*args, **kwargs)

        try:
            page = int(request.query_params.get('page', 1))
            if page < 1:
                page = 1
        except (ValueError, TypeError):
            page = 1

        try:
            page_size = int(request.query_params.get('page_size', 20))
            if page_size < 1:
                page_size = 20
            elif page_size > 100:
                page_size = 100
        except (ValueError, TypeError):
            page_size = 20

        request.validated_pagination = {'page': page, 'page_size': page_size}
        return func(*args, **kwargs)

    return wrapper


def validate_date_range(func: Callable) -> Callable:
    """
    日期范围验证装饰器

    自动验证 start_date 和 end_date 参数

    Example:
        @validate_date_range
        def list_view(request):
            start_date = request.validated_date_range.get('start_date')
            end_date = request.validated_date_range.get('end_date')
            ...
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        from datetime import datetime

        request = None
        for arg in args:
            if hasattr(arg, 'query_params'):
                request = arg
                break

        if request is None:
            return func(*args, **kwargs)

        date_format = '%Y-%m-%d'
        validated_dates = {}

        start_date_str = request.query_params.get('start_date')
        if start_date_str:
            try:
                validated_dates['start_date'] = datetime.strptime(
                    start_date_str, date_format
                ).date()
            except ValueError:
                return UnifiedResponse.error(
                    message='start_date格式不正确，应为YYYY-MM-DD',
                    code=400,
                    status_code=status.HTTP_400_BAD_REQUEST
                )

        end_date_str = request.query_params.get('end_date')
        if end_date_str:
            try:
                validated_dates['end_date'] = datetime.strptime(
                    end_date_str, date_format
                ).date()
            except ValueError:
                return UnifiedResponse.error(
                    message='end_date格式不正确，应为YYYY-MM-DD',
                    code=400,
                    status_code=status.HTTP_400_BAD_REQUEST
                )

        if 'start_date' in validated_dates and 'end_date' in validated_dates:
            if validated_dates['start_date'] > validated_dates['end_date']:
                return UnifiedResponse.error(
                    message='start_date不能大于end_date',
                    code=400,
                    status_code=status.HTTP_400_BAD_REQUEST
                )

        request.validated_date_range = validated_dates
        return func(*args, **kwargs)

    return wrapper


__all__ = [
    'validate_params',
    'validate_pagination',
    'validate_date_range',
    'Required',
    'Optional',
    'ValidationError',
]