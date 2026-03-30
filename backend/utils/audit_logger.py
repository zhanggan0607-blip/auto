"""
审计日志模块
记录所有敏感操作，支持数据库存储和查询
"""
import json
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any
from django.utils import timezone

logger = logging.getLogger(__name__)


class AuditEventType:
    """审计事件类型"""
    LOGIN = 'login'
    LOGOUT = 'logout'
    LOGIN_FAILED = 'login_failed'
    PASSWORD_CHANGE = 'password_change'
    USER_CREATE = 'user_create'
    USER_UPDATE = 'user_update'
    USER_DELETE = 'user_delete'
    PERMISSION_CHANGE = 'permission_change'
    ENTERPRISE_CREATE = 'enterprise_create'
    ENTERPRISE_UPDATE = 'enterprise_update'
    ENTERPRISE_DELETE = 'enterprise_delete'
    DATA_EXPORT = 'data_export'
    DATA_IMPORT = 'data_import'
    API_ACCESS = 'api_access'
    SECURITY_ALERT = 'security_alert'
    CRAWL_START = 'crawl_start'
    CRAWL_COMPLETE = 'crawl_complete'
    CRAWL_FAILED = 'crawl_failed'
    AGENT_EXECUTE = 'agent_execute'
    DOCUMENT_UPLOAD = 'document_upload'
    DOCUMENT_DOWNLOAD = 'document_download'
    VECTOR_SEARCH = 'vector_search'
    SETTINGS_CHANGE = 'settings_change'


class AuditRiskLevel:
    """风险等级"""
    INFO = 'info'
    WARNING = 'warning'
    CRITICAL = 'critical'


class AuditLogger:
    """
    审计日志记录器
    支持控制台输出、文件存储、数据库存储
    """

    SENSITIVE_FIELDS = [
        'password',
        'oldPassword',
        'newPassword',
        'confirmPassword',
        'token',
        'accessToken',
        'refreshToken',
        'apiKey',
        'secretKey',
        'creditCode',
        'bankAccount',
        'idCard',
        'phone',
        'mobile',
        'privateKey',
        'secret',
    ]

    SENSITIVE_PATHS = [
        '/api/v1/auth/login',
        '/api/v1/auth/register',
        '/api/v1/users/password',
        '/api/v1/admin/',
    ]

    def __init__(self):
        self._buffer = []
        self._buffer_size = 100
        self._async_save = True

    def _filter_sensitive_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        过滤敏感数据

        Args:
            data: 原始数据

        Returns:
            Dict: 过滤后的数据
        """
        if not data:
            return {}

        result = {}
        for key, value in data.items():
            if key.lower() in [f.lower() for f in self.SENSITIVE_FIELDS]:
                result[key] = '***FILTERED***'
            elif isinstance(value, dict):
                result[key] = self._filter_sensitive_data(value)
            elif isinstance(value, list) and len(value) > 0:
                if isinstance(value[0], dict):
                    result[key] = [self._filter_sensitive_data(item) for item in value]
                else:
                    result[key] = value
            else:
                result[key] = value
        return result

    def _create_log_entry(
        self,
        event_type: str,
        user_id: Optional[int],
        username: Optional[str],
        ip_address: str,
        user_agent: str,
        action: str,
        resource_type: str = None,
        resource_id: str = None,
        status: str = 'success',
        request_data: Dict = None,
        response_data: Dict = None,
        error_message: str = None,
        risk_level: str = AuditRiskLevel.INFO,
        metadata: Dict = None
    ) -> Dict[str, Any]:
        """
        创建日志条目

        Args:
            event_type: 事件类型
            user_id: 用户ID
            username: 用户名
            ip_address: IP地址
            user_agent: 用户代理
            action: 操作描述
            resource_type: 资源类型
            resource_id: 资源ID
            status: 状态
            request_data: 请求数据
            response_data: 响应数据
            error_message: 错误信息
            risk_level: 风险等级
            metadata: 额外元数据

        Returns:
            Dict: 日志条目
        """
        return {
            'timestamp': timezone.now().isoformat(),
            'event_type': event_type,
            'user_id': user_id,
            'username': username,
            'ip_address': ip_address,
            'user_agent': user_agent,
            'action': action,
            'resource_type': resource_type,
            'resource_id': resource_id,
            'status': status,
            'request_data': self._filter_sensitive_data(request_data) if request_data else None,
            'response_data': self._filter_sensitive_data(response_data) if response_data else None,
            'error_message': error_message,
            'risk_level': risk_level,
            'metadata': metadata or {}
        }

    def log(
        self,
        event_type: str,
        request=None,
        action: str = None,
        resource_type: str = None,
        resource_id: str = None,
        status: str = 'success',
        request_data: Dict = None,
        response_data: Dict = None,
        error_message: str = None,
        risk_level: str = AuditRiskLevel.INFO,
        metadata: Dict = None,
        user_id: int = None,
        username: str = None,
        ip_address: str = None,
        user_agent: str = None
    ):
        """
        记录审计日志

        Args:
            event_type: 事件类型
            request: Django请求对象
            action: 操作描述
            resource_type: 资源类型
            resource_id: 资源ID
            status: 状态
            request_data: 请求数据
            response_data: 响应数据
            error_message: 错误信息
            risk_level: 风险等级
            metadata: 额外元数据
            user_id: 用户ID
            username: 用户名
            ip_address: IP地址
            user_agent: 用户代理
        """
        if request:
            user_id = user_id or (request.user.id if hasattr(request, 'user') and request.user.is_authenticated else None)
            username = username or (request.user.username if hasattr(request, 'user') and request.user.is_authenticated else 'anonymous')
            ip_address = ip_address or self._get_client_ip(request)
            user_agent = user_agent or request.META.get('HTTP_USER_AGENT', '')
            if request_data is None and request.method in ['POST', 'PUT', 'PATCH']:
                try:
                    if hasattr(request, '_body_json'):
                        request_data = request._body_json
                    else:
                        request_data = json.loads(request.body.decode('utf-8'))
                except Exception:
                    request_data = {}

        log_entry = self._create_log_entry(
            event_type=event_type,
            user_id=user_id,
            username=username,
            ip_address=ip_address or '',
            user_agent=user_agent or '',
            action=action or event_type,
            resource_type=resource_type,
            resource_id=resource_id,
            status=status,
            request_data=request_data,
            response_data=response_data,
            error_message=error_message,
            risk_level=risk_level,
            metadata=metadata
        )

        self._save_log(log_entry)

        if risk_level in [AuditRiskLevel.CRITICAL, AuditRiskLevel.WARNING]:
            logger.warning(f"审计日志 [{risk_level}]: {json.dumps(log_entry, ensure_ascii=False)}")
        else:
            logger.info(f"审计日志: {json.dumps(log_entry, ensure_ascii=False)}")

    def _save_log(self, log_entry: Dict[str, Any]):
        """
        保存日志条目

        Args:
            log_entry: 日志条目
        """
        self._buffer.append(log_entry)

        if len(self._buffer) >= self._buffer_size:
            self._flush_buffer()

    def _flush_buffer(self):
        """刷新缓冲区，将日志写入存储"""
        if not self._buffer:
            return

        try:
            self._save_to_database(self._buffer)
            self._buffer = []
        except Exception as e:
            logger.error(f"保存审计日志失败: {str(e)}")

    def _save_to_database(self, log_entries: List[Dict[str, Any]]):
        """
        保存日志到数据库

        Args:
            log_entries: 日志条目列表
        """
        try:
            from apps.core.models import AuditLog
            models_to_create = []
            for entry in log_entries:
                models_to_create.append(AuditLog(
                    event_type=entry['event_type'],
                    user_id=entry.get('user_id'),
                    username=entry.get('username'),
                    ip_address=entry.get('ip_address', ''),
                    user_agent=entry.get('user_agent', ''),
                    action=entry.get('action', ''),
                    resource_type=entry.get('resource_type'),
                    resource_id=entry.get('resource_id'),
                    status=entry.get('status', 'success'),
                    request_data=json.dumps(entry.get('request_data')) if entry.get('request_data') else None,
                    response_data=json.dumps(entry.get('response_data')) if entry.get('response_data') else None,
                    error_message=entry.get('error_message'),
                    risk_level=entry.get('risk_level', 'info'),
                    metadata=json.dumps(entry.get('metadata')) if entry.get('metadata') else None
                ))
            AuditLog.objects.bulk_create(models_to_create)
        except ImportError:
            logger.debug("AuditLog模型未定义，跳过数据库存储")
        except Exception as e:
            logger.error(f"数据库存储审计日志失败: {str(e)}")

    def _get_client_ip(self, request) -> str:
        """获取客户端IP"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', '')

    def log_login(self, request, status: str = 'success', error_message: str = None):
        """记录登录事件"""
        self.log(
            event_type=AuditEventType.LOGIN if status == 'success' else AuditEventType.LOGIN_FAILED,
            request=request,
            action='用户登录' if status == 'success' else '登录失败',
            resource_type='auth',
            status=status,
            risk_level=AuditRiskLevel.WARNING if status != 'success' else AuditRiskLevel.INFO,
            error_message=error_message
        )

    def log_logout(self, request):
        """记录登出事件"""
        self.log(
            event_type=AuditEventType.LOGOUT,
            request=request,
            action='用户登出',
            resource_type='auth',
            status='success'
        )

    def log_enterprise_operation(
        self,
        request,
        operation: str,
        enterprise_id: str,
        status: str = 'success',
        error_message: str = None
    ):
        """记录企业操作事件"""
        event_type_map = {
            'create': AuditEventType.ENTERPRISE_CREATE,
            'update': AuditEventType.ENTERPRISE_UPDATE,
            'delete': AuditEventType.ENTERPRISE_DELETE
        }
        self.log(
            event_type=event_type_map.get(operation, AuditEventType.ENTERPRISE_UPDATE),
            request=request,
            action=f'企业{operation}',
            resource_type='enterprise',
            resource_id=str(enterprise_id),
            status=status,
            risk_level=AuditRiskLevel.WARNING if operation == 'delete' else AuditRiskLevel.INFO,
            error_message=error_message
        )

    def log_crawl_operation(
        self,
        request,
        operation: str,
        crawl_id: str = None,
        status: str = 'success',
        error_message: str = None,
        metadata: Dict = None
    ):
        """记录爬虫操作事件"""
        event_type_map = {
            'start': AuditEventType.CRAWL_START,
            'complete': AuditEventType.CRAWL_COMPLETE,
            'failed': AuditEventType.CRAWL_FAILED
        }
        self.log(
            event_type=event_type_map.get(operation, AuditEventType.CRAWL_START),
            request=request,
            action=f'采集{operation}',
            resource_type='crawl',
            resource_id=str(crawl_id) if crawl_id else None,
            status=status,
            risk_level=AuditRiskLevel.WARNING if operation == 'failed' else AuditRiskLevel.INFO,
            error_message=error_message,
            metadata=metadata
        )

    def log_security_alert(
        self,
        request,
        alert_type: str,
        description: str,
        details: Dict = None
    ):
        """记录安全告警"""
        self.log(
            event_type=AuditEventType.SECURITY_ALERT,
            request=request,
            action=f'安全告警: {alert_type}',
            resource_type='security',
            status='alert',
            risk_level=AuditRiskLevel.CRITICAL,
            metadata={'alert_type': alert_type, 'description': description, 'details': details}
        )

    def flush(self):
        """强制刷新缓冲区"""
        self._flush_buffer()


audit_logger = AuditLogger()


def get_audit_logger() -> AuditLogger:
    """
    获取审计日志记录器实例

    Returns:
        AuditLogger: 审计日志记录器
    """
    return audit_logger


def log_audit_event(
    event_type: str,
    request=None,
    action: str = None,
    resource_type: str = None,
    resource_id: str = None,
    status: str = 'success',
    request_data: Dict = None,
    response_data: Dict = None,
    error_message: str = None,
    risk_level: str = AuditRiskLevel.INFO,
    metadata: Dict = None
):
    """
    记录审计事件的便捷函数

    Args:
        event_type: 事件类型
        request: Django请求对象
        action: 操作描述
        resource_type: 资源类型
        resource_id: 资源ID
        status: 状态
        request_data: 请求数据
        response_data: 响应数据
        error_message: 错误信息
        risk_level: 风险等级
        metadata: 额外元数据
    """
    audit_logger.log(
        event_type=event_type,
        request=request,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        status=status,
        request_data=request_data,
        response_data=response_data,
        error_message=error_message,
        risk_level=risk_level,
        metadata=metadata
    )