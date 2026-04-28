"""
统一日志配置模块
为整个项目提供结构化日志、日志脱敏、上下文追踪能力

功能：
- 统一日志格式
- 敏感字段脱敏
- 请求追踪ID
- 分层日志级别
- 多输出目标

配置方式：
    from core.logging_config import setup_logging
    setup_logging()

    # 或在 settings.py 中使用
    LOGGING = get_logging_config()
"""

import os
import re
import logging
import traceback
from datetime import datetime
from typing import Any, Dict, Optional
from logging.handlers import RotatingFileHandler


SENSITIVE_FIELDS = [
    'password', 'oldPassword', 'newPassword', 'confirmPassword',
    'token', 'accessToken', 'refreshToken', 'apiKey', 'secretKey',
    'secret', 'creditCode', 'bankAccount', 'idCard', 'phone', 'mobile',
    'privateKey', 'authorization', 'cookie', 'sessionId',
    'old_password', 'new_password', 'confirm_password',
    'api_key', 'secret_key', 'private_key',
    'redis_password', 'celery_broker_url', 'broker_url',
]

TRACE_ID_HEADER = 'HTTP_X_TRACE_ID'
TRACE_ID_CONTEXTVar = 'trace_id'


class SensitiveFilter(logging.Filter):
    """
    日志敏感字段过滤器
    自动将敏感字段替换为 ***FILTERED***
    """

    SENSITIVE_PATTERNS = [
        re.compile(r'"(?:' + '|'.join(SENSITIVE_FIELDS) + r')"\s*:\s*"[^"]*"', re.IGNORECASE),
        re.compile(r"'(?:" + '|'.join(SENSITIVE_FIELDS) + r")'\s*:\s*'[^']*'", re.IGNORECASE),
        re.compile(r'(?:' + '|'.join(SENSITIVE_FIELDS) + r')=([^&\s]+)', re.IGNORECASE),
    ]

    def filter(self, record: logging.LogRecord) -> bool:
        if hasattr(record, 'msg') and isinstance(record.msg, str):
            record.msg = self._filter_message(record.msg)

        if hasattr(record, 'args') and record.args:
            record.args = tuple(
                self._filter_message(str(arg)) if isinstance(arg, str) else arg
                for arg in record.args
            )

        return True

    def _filter_message(self, message: str) -> str:
        for pattern in self.SENSITIVE_PATTERNS:
            message = pattern.sub(lambda m: f'"{m.group(1).split("=")[0]}":"***FILTERED***"', message)

        for field in SENSITIVE_FIELDS:
            field_pattern = re.compile(
                rf'({field}\s*[=:]\s*)([^\s,}}]+)',
                re.IGNORECASE
            )
            message = field_pattern.sub(rf'\1***FILTERED***', message)

        return message


class TraceIdFilter(logging.Filter):
    """
    日志追踪ID过滤器
    为每条日志添加追踪ID
    从 _thread_local.request.trace_id 读取（由 TraceIdMiddleware 设置）
    """

    def filter(self, record: logging.LogRecord) -> bool:
        try:
            from core.middleware import _thread_local

            request = getattr(_thread_local, 'request', None)
            if request and hasattr(request, 'trace_id'):
                record.trace_id = request.trace_id
            else:
                record.trace_id = '-'
        except Exception:
            record.trace_id = '-'

        return True


class SafeVerboseFormatter(logging.Formatter):
    def format(self, record):
        if not hasattr(record, 'trace_id'):
            record.trace_id = '-'
        return super().format(record)


class StructuredLogger:
    """
    结构化日志记录器
    提供 JSON 格式的结构化日志输出

    使用示例：
        from core.logging_config import get_structured_logger

        logger = get_structured_logger('workflow')
        logger.info('Workflow started', workflow_id='wf-123', stage='collect')
    """

    def __init__(self, name: str):
        self.logger = logging.getLogger(name)

    def _format_struct(self, message: str, **kwargs) -> str:
        """格式化结构化日志"""
        parts = [f"[{message}]"]
        for key, value in kwargs.items():
            if value is not None:
                if isinstance(value, (dict, list)):
                    import json
                    value = json.dumps(value, ensure_ascii=False)[:500]
                parts.append(f"{key}={value}")
        return ' '.join(parts)

    def debug(self, message: str, **kwargs):
        self.logger.debug(self._format_struct(message, **kwargs))

    def info(self, message: str, **kwargs):
        self.logger.info(self._format_struct(message, **kwargs))

    def warning(self, message: str, **kwargs):
        self.logger.warning(self._format_struct(message, **kwargs))

    def error(self, message: str, **kwargs):
        self.logger.error(self._format_struct(message, **kwargs))

    def critical(self, message: str, **kwargs):
        self.logger.critical(self._format_struct(message, **kwargs))


def get_structured_logger(name: str) -> StructuredLogger:
    """获取结构化日志记录器"""
    return StructuredLogger(name)


class RequestLogger:
    """
    HTTP 请求日志记录器
    用于记录 API 请求的详细信息

    使用示例：
        from core.logging_config import get_request_logger

        logger = get_request_logger()
        logger.log_request(
            request=request,
            status_code=200,
            duration=0.123,
            user_id=1
        )
    """

    def __init__(self):
        self.logger = logging.getLogger('api_request')

    def log_request(
        self,
        request,
        status_code: int,
        duration: float,
        user_id: Optional[int] = None,
        error: Optional[str] = None
    ):
        """记录请求日志"""
        log_data = {
            'method': request.method,
            'path': request.path,
            'status': status_code,
            'duration': f'{duration:.3f}s',
        }

        if user_id:
            log_data['user_id'] = user_id

        if error:
            log_data['error'] = error

        if status_code >= 400:
            self.logger.warning(self._format(**log_data))
        else:
            self.logger.info(self._format(**log_data))

    def _format(self, **kwargs) -> str:
        parts = []
        for key, value in kwargs.items():
            parts.append(f"{key}={value}")
        return ' '.join(parts)


def get_request_logger() -> RequestLogger:
    """获取请求日志记录器"""
    return RequestLogger()


def setup_logging():
    """
    设置项目日志配置
    在 Django 启动时调用（如 settings.py 或 manage.py）
    """
    import os
    from django.conf import settings

    log_dir = getattr(settings, 'LOG_DIR', os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'logs'))
    os.makedirs(log_dir, exist_ok=True)

    LOGGING_CONFIG = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'verbose': {
                '()': 'core.logging_config.SafeVerboseFormatter',
                'format': '[{asctime}] [{levelname}] [{name}] [{trace_id}] {message}',
                'style': '{',
            },
            'simple': {
                'format': '[{levelname}] {message}',
                'style': '{',
            },
            'json': {
                'format': '{"time":"%(asctime)s","level":"%(levelname)s","logger":"%(name)s","trace_id":"%(trace_id)s","message":"%(message)s"}',
            },
        },
        'filters': {
            'sensitive_filter': {
                '()': SensitiveFilter,
            },
            'trace_id_filter': {
                '()': TraceIdFilter,
            },
        },
        'handlers': {
            'console': {
                'level': 'DEBUG',
                'class': 'logging.StreamHandler',
                'formatter': 'simple',
                'filters': ['sensitive_filter'],
            },
            'file': {
                'level': 'INFO',
                'class': 'logging.handlers.RotatingFileHandler',
                'filename': os.path.join(log_dir, 'app.log'),
                'maxBytes': 10 * 1024 * 1024,
                'backupCount': 10,
                'formatter': 'verbose',
                'filters': ['sensitive_filter', 'trace_id_filter'],
            },
            'error_file': {
                'level': 'ERROR',
                'class': 'logging.handlers.RotatingFileHandler',
                'filename': os.path.join(log_dir, 'error.log'),
                'maxBytes': 10 * 1024 * 1024,
                'backupCount': 10,
                'formatter': 'verbose',
                'filters': ['sensitive_filter', 'trace_id_filter'],
            },
            'api_file': {
                'level': 'INFO',
                'class': 'logging.handlers.RotatingFileHandler',
                'filename': os.path.join(log_dir, 'api.log'),
                'maxBytes': 10 * 1024 * 1024,
                'backupCount': 20,
                'formatter': 'verbose',
                'filters': ['sensitive_filter', 'trace_id_filter'],
            },
        },
        'loggers': {
            'django': {
                'handlers': ['console', 'file'],
                'level': 'INFO',
                'propagate': False,
            },
            'django.request': {
                'handlers': ['api_file', 'error_file'],
                'level': 'INFO',
                'propagate': False,
            },
            'django.db.backends': {
                'handlers': ['file'],
                'level': 'WARNING',
                'propagate': False,
            },
            'apps': {
                'handlers': ['console', 'file'],
                'level': 'INFO',
                'propagate': False,
            },
            'api_request': {
                'handlers': ['api_file'],
                'level': 'INFO',
                'propagate': False,
            },
            '': {
                'handlers': ['console', 'file', 'error_file'],
                'level': 'INFO',
                'propagate': False,
            },
        },
    }

    logging.config.dictConfig(LOGGING_CONFIG)


def get_logging_config():
    """
    获取日志配置字典
    用于在 settings.py 中配置

    使用方式：
        from core.logging_config import get_logging_config

        LOGGING = get_logging_config()
    """
    import os

    log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'logs')
    os.makedirs(log_dir, exist_ok=True)

    return {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'verbose': {
                '()': 'core.logging_config.SafeVerboseFormatter',
                'format': '[{asctime}] [{levelname}] [{name}] [{trace_id}] {message}',
                'style': '{',
            },
            'simple': {
                'format': '[{levelname}] {message}',
                'style': '{',
            },
        },
        'filters': {
            'sensitive_filter': {
                '()': SensitiveFilter,
            },
            'trace_id_filter': {
                '()': TraceIdFilter,
            },
        },
        'handlers': {
            'console': {
                'level': 'DEBUG',
                'class': 'logging.StreamHandler',
                'formatter': 'simple',
                'filters': ['sensitive_filter'],
            },
            'file': {
                'level': 'INFO',
                'class': 'logging.handlers.RotatingFileHandler',
                'filename': os.path.join(log_dir, 'app.log'),
                'maxBytes': 10 * 1024 * 1024,
                'backupCount': 10,
                'formatter': 'verbose',
                'filters': ['sensitive_filter', 'trace_id_filter'],
            },
            'error_file': {
                'level': 'ERROR',
                'class': 'logging.handlers.RotatingFileHandler',
                'filename': os.path.join(log_dir, 'error.log'),
                'maxBytes': 10 * 1024 * 1024,
                'backupCount': 10,
                'formatter': 'verbose',
                'filters': ['sensitive_filter', 'trace_id_filter'],
            },
            'api_file': {
                'level': 'INFO',
                'class': 'logging.handlers.RotatingFileHandler',
                'filename': os.path.join(log_dir, 'api.log'),
                'maxBytes': 10 * 1024 * 1024,
                'backupCount': 20,
                'formatter': 'verbose',
                'filters': ['sensitive_filter', 'trace_id_filter'],
            },
        },
        'loggers': {
            'django': {
                'handlers': ['console', 'file'],
                'level': 'INFO',
                'propagate': False,
            },
            'django.request': {
                'handlers': ['api_file', 'error_file'],
                'level': 'INFO',
                'propagate': False,
            },
            'django.db.backends': {
                'handlers': ['file'],
                'level': 'WARNING',
                'propagate': False,
            },
            'apps': {
                'handlers': ['console', 'file'],
                'level': 'INFO',
                'propagate': False,
            },
            'api_request': {
                'handlers': ['api_file'],
                'level': 'INFO',
                'propagate': False,
            },
            '': {
                'handlers': ['console', 'file', 'error_file'],
                'level': 'INFO',
                'propagate': False,
            },
        },
    }
