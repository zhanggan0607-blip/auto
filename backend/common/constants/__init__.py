"""
公共常量模块
统一导出所有常量
"""

from .error_codes import (
    ErrorCode,
    get_error_by_code,
    get_error_message,
    get_http_status,
)

from .http_status import (
    HttpStatus,
    http_status_messages,
    get_status_text,
)

__all__ = [
    # 错误码
    'ErrorCode',
    'get_error_by_code',
    'get_error_message',
    'get_http_status',
    # HTTP状态码
    'HttpStatus',
    'http_status_messages',
    'get_status_text',
]
