"""
服务自动重启与告警模块
"""
import logging
import subprocess
from datetime import timedelta
from typing import Dict, Any, List, Optional

from django.utils import timezone
from django.conf import settings

logger = logging.getLogger(__name__)


class ServiceRestartManager:
    """
    服务自动重启管理器
    实现冷却策略和多级降级重启
    """

    RESTART_COMMANDS = {
        'celery_worker': ['celery', '-A', 'config', 'worker', '--loglevel=info', '--pool=prefork', '-n', 'worker1@%h'],
        'celery_beat': ['celery', '-A', 'config', 'beat', '--loglevel=info'],
        'redis': ['redis-server'],
        'postgresql': ['pg_ctl', '-D', 'data', 'restart'],
        'milvus': ['docker', 'restart', 'milvus'],
        'chroma': ['docker', 'restart', 'chroma'],
        'minio': ['docker', 'restart', 'minio'],
        'ollama': ['systemctl', 'restart', 'ollama'],
    }

    @staticmethod
    def can_restart(service) -> tuple[bool, str]:
        """
        检查服务是否可以重启（冷却时间检查）
        返回 (是否可以重启, 原因)
        """
        if not service.auto_restart_enabled:
            return False, "自动重启已禁用"

        if service.restart_attempts_today >= service.max_restart_attempts:
            return False, f"今日重启次数已达上限({service.max_restart_attempts})"

        if service.last_restart_time:
            cooldown_seconds = service.restart_cooldown_minutes * 60
            elapsed = (timezone.now() - service.last_restart_time).total_seconds()
            if elapsed < cooldown_seconds:
                remaining = int(cooldown_seconds - elapsed)
                return False, f"冷却中，还需等待 {remaining} 秒"

        return True, "可以重启"

    @staticmethod
    def execute_restart(service) -> Dict[str, Any]:
        """
        执行服务重启
        """
        from apps.monitor.models import ServiceActionLog, ServiceAlert, AlertLevel, AlertStatus

        can_restart, reason = ServiceRestartManager.can_restart(service)
        if not can_restart:
            return {'success': False, 'message': reason}

        action_log = ServiceActionLog.objects.create(
            service=service,
            action_type='auto_restart',
            status='started',
            trigger_condition=f'连续失败{service.consecutive_failures}次'
        )

        try:
            restart_success = ServiceRestartManager._do_restart(service)

            if restart_success:
                service.consecutive_failures = 0
                service.last_restart_time = timezone.now()
                service.restart_attempts_today += 1
                service.save(update_fields=[
                    'consecutive_failures', 'last_restart_time',
                    'restart_attempts_today', 'updated_at'
                ])

                action_log.status = 'success'
                action_log.result_message = f"重启成功"
                action_log.completed_at = timezone.now()
                action_log.save()

                ServiceRestartManager._resolve_existing_alerts(service)

                return {'success': True, 'message': '重启成功'}
            else:
                action_log.status = 'failed'
                action_log.result_message = '重启执行返回失败'
                action_log.completed_at = timezone.now()
                action_log.save()

                return {'success': False, 'message': '重启执行返回失败'}

        except Exception as e:
            logger.error(f"重启服务失败 {service.name}: {str(e)}")
            action_log.status = 'failed'
            action_log.error_details = str(e)
            action_log.completed_at = timezone.now()
            action_log.save()

            return {'success': False, 'message': str(e)}

    @staticmethod
    def _do_restart(service) -> bool:
        """
        执行实际的重启操作
        """
        service_name = service.name.lower()

        for key, command in ServiceRestartManager.RESTART_COMMANDS.items():
            if key in service_name:
                try:
                    logger.info(f"执行重启命令: {' '.join(command)}")
                    result = subprocess.run(
                        command,
                        capture_output=True,
                        text=True,
                        timeout=60
                    )
                    return result.returncode == 0
                except subprocess.TimeoutExpired:
                    logger.error(f"重启命令超时: {key}")
                    return False
                except Exception as e:
                    logger.error(f"执行重启命令失败: {str(e)}")
                    return False

        logger.warning(f"未找到服务 {service.name} 的重启命令")
        return False

    @staticmethod
    def _resolve_existing_alerts(service):
        """解决服务已有的告警"""
        from apps.monitor.models import ServiceAlert, AlertStatus

        ServiceAlert.objects.filter(
            service=service,
            status__in=[AlertStatus.PENDING, AlertStatus.NOTIFIED]
        ).update(
            status=AlertStatus.RESOLVED,
            resolved_at=timezone.now()
        )


class AlertManager:
    """
    告警管理器
    负责告警的创建、通知和升级
    """

    @staticmethod
    def check_and_create_alert(service) -> Optional[Any]:
        """
        检查是否需要创建告警
        """
        from apps.monitor.models import ServiceAlert, AlertLevel, AlertStatus

        if service.consecutive_failures < service.consecutive_failures_to_alert:
            return None

        existing_alert = ServiceAlert.objects.filter(
            service=service,
            status__in=[AlertStatus.PENDING, AlertStatus.NOTIFIED]
        ).first()

        if existing_alert:
            return existing_alert

        level = AlertLevel.CRITICAL if service.is_critical else AlertLevel.ERROR

        alert = ServiceAlert.objects.create(
            service=service,
            level=level,
            status=AlertStatus.PENDING,
            title=f"服务异常: {service.display_name}",
            message=f"服务 {service.display_name} 连续{service.consecutive_failures}次检查失败",
            triggered_by='consecutive_failures',
            consecutive_failures=service.consecutive_failures
        )

        return alert

    @staticmethod
    def send_alert_notification(alert) -> bool:
        """
        发送告警通知
        """
        from apps.monitor.models import ServiceActionLog

        action_log = ServiceActionLog.objects.create(
            service=alert.service,
            action_type='alert_sent',
            status='started',
            trigger_condition=f'告警 #{alert.id}'
        )

        try:
            notification_sent = AlertManager._do_send_notification(alert)

            if notification_sent:
                alert.status = 'NOTIFIED'
                alert.notified_at = timezone.now()
                alert.save(update_fields=['status', 'notified_at', 'updated_at'])

                action_log.status = 'success'
                action_log.result_message = "告警通知已发送"
            else:
                action_log.status = 'failed'
                action_log.result_message = "告警通知发送失败"

            action_log.completed_at = timezone.now()
            action_log.save()

            return notification_sent

        except Exception as e:
            logger.error(f"发送告警通知失败: {str(e)}")
            action_log.status = 'failed'
            action_log.error_details = str(e)
            action_log.completed_at = timezone.now()
            action_log.save()
            return False

    @staticmethod
    def _do_send_notification(alert) -> bool:
        """
        执行实际的通知发送
        支持钉钉、邮件等多种渠道
        """
        try:
            webhook_url = getattr(settings, 'DINGTALK_WEBHOOK_URL', None)

            if webhook_url:
                return AlertManager._send_dingtalk(webhook_url, alert)

            logger.warning("未配置告警通知渠道")
            return True

        except Exception as e:
            logger.error(f"通知发送异常: {str(e)}")
            return False

    @staticmethod
    def _send_dingtalk(webhook_url: str, alert) -> bool:
        """
        发送钉钉通知
        """
        try:
            import json
            import urllib.request
            import urllib.error

            message = {
                'msgtype': 'markdown',
                'markdown': {
                    'title': f"【{alert.get_level_display()}】{alert.title}",
                    'text': f"### 【{alert.get_level_display()}】{alert.title}\n\n"
                           f"**服务**: {alert.service.display_name}\n\n"
                           f"**级别**: {alert.get_level_display()}\n\n"
                           f"**消息**: {alert.message}\n\n"
                           f"**连续失败**: {alert.consecutive_failures}次\n\n"
                           f"**时间**: {alert.created_at.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                           f"**状态**: {alert.get_status_display()}\n\n"
                           f"> 请及时处理！"
                }
            }

            data = json.dumps(message).encode('utf-8')
            req = urllib.request.Request(
                webhook_url,
                data=data,
                headers={'Content-Type': 'application/json'}
            )

            with urllib.request.urlopen(req, timeout=10) as response:
                result = json.loads(response.read().decode('utf-8'))
                return result.get('errcode', 1) == 0

        except Exception as e:
            logger.error(f"钉钉通知发送失败: {str(e)}")
            return False

    @staticmethod
    def get_pending_alerts() -> List[Any]:
        """
        获取所有待处理的告警
        """
        from apps.monitor.models import ServiceAlert, AlertStatus
        return list(ServiceAlert.objects.filter(
            status__in=[AlertStatus.PENDING, AlertStatus.NOTIFIED]
        ).select_related('service').order_by('-created_at'))

    @staticmethod
    def resolve_alert(alert_id: int, resolved_by: str = 'system') -> bool:
        """
        解决告警
        """
        from apps.monitor.models import ServiceAlert, AlertStatus

        try:
            alert = ServiceAlert.objects.get(id=alert_id)
            alert.status = AlertStatus.RESOLVED
            alert.resolved_at = timezone.now()
            alert.save(update_fields=['status', 'resolved_at', 'updated_at'])
            return True
        except ServiceAlert.DoesNotExist:
            return False