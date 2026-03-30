"""
公共Serializer模块
统一导出所有公共Serializer组件
"""

from .base import (
    BaseSerializer,
    BaseModelSerializer,
    ListSerializer,
    NestedListSerializer,
    SummarySerializer,
    DetailSerializer,
    CreateSerializer,
    UpdateSerializer,
    PaginatedSerializer,
)

from .fields import (
    TimestampField,
    FileUrlField,
    FileSizeField,
    FlexibleDateField,
    JSONField,
    CreatedAtField,
    UpdatedAtField,
    ObjectIdField,
    UserIdField,
)

from .validators import (
    validate_phone,
    validate_credit_code,
    validate_url,
    validate_date_range,
    validate_positive_integer,
    validate_percentage,
    DateRangeValidator,
)

__all__ = [
    # 基类
    'BaseSerializer',
    'BaseModelSerializer',
    'ListSerializer',
    'NestedListSerializer',
    'SummarySerializer',
    'DetailSerializer',
    'CreateSerializer',
    'UpdateSerializer',
    'PaginatedSerializer',
    # 字段
    'TimestampField',
    'FileUrlField',
    'FileSizeField',
    'FlexibleDateField',
    'JSONField',
    'CreatedAtField',
    'UpdatedAtField',
    'ObjectIdField',
    'UserIdField',
    # 验证器
    'validate_phone',
    'validate_credit_code',
    'validate_url',
    'validate_date_range',
    'validate_positive_integer',
    'validate_percentage',
    'DateRangeValidator',
]
