"""
中间件模块
"""
import time
import logging
import json
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(MiddlewareMixin):
    """
    请求日志中间件
    增强版：支持敏感数据深度过滤、API审计
    """

    SENSITIVE_FIELDS = [
        'password', 'oldPassword', 'newPassword', 'confirmPassword',
        'token', 'accessToken', 'refreshToken', 'apiKey', 'secretKey',
        'secret', 'creditCode', 'bankAccount', 'idCard', 'phone',
        'mobile', 'privateKey', 'authorization'
    ]

    SENSITIVE_PATHS = [
        '/api/v1/auth/login',
        '/api/v1/auth/register',
        '/api/v1/users/password',
    ]

    def process_request(self, request):
        """
        记录请求开始时间
        """
        request.start_time = time.time()

        if request.method in ['POST', 'PUT', 'PATCH']:
            try:
                body = json.loads(request.body.decode('utf-8'))
                request._body_json = self._filter_sensitive_fields(body)
            except Exception:
                request._body_json = {}

    def _filter_sensitive_fields(self, data):
        """
        深度过滤敏感字段

        Args:
            data: 原始数据字典

        Returns:
            dict: 过滤后的数据
        """
        if not isinstance(data, dict):
            return data

        result = {}
        for key, value in data.items():
            key_lower = key.lower()
            if any(sf.lower() in key_lower for sf in self.SENSITIVE_FIELDS):
                result[key] = '***FILTERED***'
            elif isinstance(value, dict):
                result[key] = self._filter_sensitive_fields(value)
            elif isinstance(value, list) and value and isinstance(value[0], dict):
                result[key] = [self._filter_sensitive_fields(item) for item in value]
            else:
                result[key] = value
        return result

    def process_response(self, request, response):
        """
        记录请求日志
        """
        if hasattr(request, 'start_time'):
            duration = time.time() - request.start_time
        else:
            duration = 0

        user_id = None
        username = None
        if hasattr(request, 'user') and request.user.is_authenticated:
            user_id = request.user.id
            username = request.user.username

        ip_address = self.get_client_ip(request)

        log_data = {
            'method': request.method,
            'path': request.path,
            'status': response.status_code,
            'duration': f'{duration:.3f}s',
            'user_id': user_id,
            'username': username,
            'ip': ip_address,
        }

        if request.method in ['POST', 'PUT', 'PATCH'] and hasattr(request, '_body_json'):
            log_data['body'] = request._body_json

        try:
            from utils.audit_logger import audit_logger, AuditEventType, AuditRiskLevel

            if request.method in ['POST', 'PUT', 'PATCH', 'DELETE']:
                risk_level = AuditRiskLevel.WARNING if response.status_code >= 400 else AuditRiskLevel.INFO
                audit_logger.log(
                    event_type=AuditEventType.API_ACCESS,
                    request=request,
                    action=f'{request.method} {request.path}',
                    status='success' if response.status_code < 400 else 'failed',
                    risk_level=risk_level,
                    metadata={'duration': duration, 'status_code': response.status_code}
                )
        except ImportError:
            pass

        if response.status_code >= 400:
            logger.warning(f"API请求失败: {json.dumps(log_data, ensure_ascii=False)}")
        else:
            logger.info(f"API请求: {json.dumps(log_data, ensure_ascii=False)}")

        return response

    def get_client_ip(self, request):
        """
        获取客户端IP
        """
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', '')


class CorsMiddleware(MiddlewareMixin):
    """
    CORS中间件 - 补充处理
    """

    def process_response(self, request, response):
        """
        添加CORS头
        """
        response['Access-Control-Allow-Credentials'] = 'true'
        return response
