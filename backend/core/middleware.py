"""
中间件模块
"""
import re
import threading
import time
import uuid
from django.utils.deprecation import MiddlewareMixin

_thread_local = threading.local()

API_VERSION_PATTERN = re.compile(r'^/api/(v\d+)/')
API_VERSION_HEADER = 'HTTP_ACCEPT'
API_VERSION_HEADER_PATTERN = re.compile(r'application/vnd\.bid-auto\.(v\d+)\+json')
CURRENT_API_VERSION = 'v1'
SUPPORTED_VERSIONS = ['v1']


class ApiVersionMiddleware(MiddlewareMixin):
    def process_request(self, request):
        request.api_version = self._resolve_version(request)

    def process_response(self, request, response):
        if hasattr(request, 'api_version'):
            response['X-API-Version'] = request.api_version
        return response

    def _resolve_version(self, request):
        path_match = API_VERSION_PATTERN.match(request.path)
        if path_match:
            version = path_match.group(1)
            if version in SUPPORTED_VERSIONS:
                return version
            return CURRENT_API_VERSION

        accept = request.META.get(API_VERSION_HEADER, '')
        header_match = API_VERSION_HEADER_PATTERN.search(accept)
        if header_match:
            version = header_match.group(1)
            if version in SUPPORTED_VERSIONS:
                return version

        return CURRENT_API_VERSION


class TraceIdMiddleware(MiddlewareMixin):
    """
    追踪ID中间件
    为每个请求生成唯一追踪ID，便于日志关联
    """

    def process_request(self, request):
        trace_id = request.META.get('HTTP_X_TRACE_ID')
        if not trace_id:
            trace_id = str(uuid.uuid4())[:16]
        request.trace_id = trace_id
        _thread_local.request = request

    def process_response(self, request, response):
        if hasattr(request, 'trace_id'):
            response['X-Trace-Id'] = request.trace_id
        if hasattr(_thread_local, 'request'):
            try:
                del _thread_local.request
            except Exception:
                pass
        return response


class RequestLoggingMiddleware(MiddlewareMixin):
    """
    请求日志中间件
    轻量版：仅记录请求信息，敏感字段过滤由 logging_config 处理
    """

    def process_request(self, request):
        request.start_time = time.time()

    def process_response(self, request, response):
        if hasattr(request, 'start_time'):
            duration = time.time() - request.start_time
        else:
            duration = 0

        user_id = None
        username = None
        if hasattr(request, 'user') and request.user.is_authenticated:
            user_id = request.user.id
            username = request.user.username

        import logging
        logger = logging.getLogger('api_request')

        log_data = {
            'method': request.method,
            'path': request.path,
            'status': response.status_code,
            'duration': f'{duration:.3f}s',
            'user_id': user_id,
            'username': username,
        }

        if hasattr(request, 'trace_id'):
            log_data['trace_id'] = request.trace_id

        if response.status_code >= 400:
            logger.warning(f"API请求失败: {log_data}")
        else:
            logger.info(f"API请求: {log_data}")

        return response
