"""
服务自动重启与告警模块
"""
import logging
import platform
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
        'milvus': ['docker', 'restart', 'bid-milvus'],
        'chroma': ['docker', 'restart', 'bid-chroma'],
        'minio': ['docker', 'restart', 'bid-minio'],
        'ollama': ['systemctl', 'restart', 'ollama'],
    }

    WINDOWS_SERVICE_COMMANDS = {
        'postgresql': {
            'service_pattern': 'postgresql',
            'display_name': 'PostgreSQL',
        },
        'redis': {
            'service_pattern': 'Redis',
            'display_name': 'Redis',
        },
    }

    WINDOWS_PROCESS_COMMANDS = {
        'celery_worker': {
            'process_patterns': ['celery.*worker', 'celery_worker'],
            'start_command': ['celery', '-A', 'config.celery', 'worker', '--loglevel=info', '--pool=solo', '-Q', 'celery,crawler,default', '--hostname=worker1@%h'],
            'display_name': 'Celery Worker',
        },
        'celery_beat': {
            'process_patterns': ['celery.*beat', 'celery_beat'],
            'start_command': ['celery', '-A', 'config.celery', 'beat', '--loglevel=info'],
            'display_name': 'Celery Beat',
        },
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
    def execute_restart(service, action_type: str = 'auto_restart', trigger_condition: str = None) -> Dict[str, Any]:
        """
        执行服务重启
        """
        from apps.monitor.models import ServiceActionLog, ServiceAlert, AlertLevel, AlertStatus

        can_restart, reason = ServiceRestartManager.can_restart(service)
        if not can_restart:
            return {'success': False, 'message': reason}

        if trigger_condition is None:
            trigger_condition = f'连续失败{service.consecutive_failures}次'

        action_log = ServiceActionLog.objects.create(
            service=service,
            action_type=action_type,
            status='started',
            trigger_condition=trigger_condition
        )

        try:
            restart_success, error_msg = ServiceRestartManager._do_restart(service)

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
                action_log.result_message = error_msg or '重启执行返回失败'
                action_log.completed_at = timezone.now()
                action_log.save()

                return {'success': False, 'message': error_msg or '不支持此服务的重启'}

        except Exception as e:
            logger.error(f"重启服务失败 {service.name}: {str(e)}")
            action_log.status = 'failed'
            action_log.error_details = str(e)
            action_log.completed_at = timezone.now()
            action_log.save()

            return {'success': False, 'message': str(e)}

    @staticmethod
    def _do_restart(service) -> tuple[bool, str]:
        """
        执行实际的重启操作
        返回 (success, error_message)
        """
        if platform.system() == 'Windows':
            return ServiceRestartManager._do_restart_windows(service)
        else:
            return ServiceRestartManager._do_restart_linux(service)

    @staticmethod
    def _do_restart_windows(service) -> tuple[bool, str]:
        """
        Windows环境下的服务重启
        使用 sc 命令管理Windows服务，或通过进程管理
        """
        service_name = service.name.lower()

        for key, service_info in ServiceRestartManager.WINDOWS_SERVICE_COMMANDS.items():
            if key in service_name:
                display_name = service_info['display_name']
                service_pattern = service_info['service_pattern']

                windows_service_name = ServiceRestartManager._find_windows_service_name(service_pattern)
                if not windows_service_name:
                    logger.warning(f"未找到包含 '{service_pattern}' 的Windows服务")
                    return False, f"未找到服务: {display_name}"

                try:
                    logger.info(f"Windows服务重启: {display_name} ({windows_service_name})")

                    stop_result = subprocess.run(
                        ['sc', 'stop', windows_service_name],
                        capture_output=True,
                        text=True,
                        timeout=30
                    )
                    logger.info(f"sc stop result: returncode={stop_result.returncode}, stdout={stop_result.stdout}, stderr={stop_result.stderr}")

                    import time
                    time.sleep(2)

                    start_result = subprocess.run(
                        ['sc', 'start', windows_service_name],
                        capture_output=True,
                        text=True,
                        timeout=30
                    )
                    logger.info(f"sc start result: returncode={start_result.returncode}, stdout={start_result.stdout}, stderr={start_result.stderr}")

                    if start_result.returncode in [0, 1056]:
                        return True, ""
                    elif start_result.returncode == 5:
                        logger.error("拒绝访问，需要管理员权限")
                        return False, "需要管理员权限"
                    else:
                        if start_result.stdout and ('state' in start_result.stdout.lower() or 'running' in start_result.stdout.lower()):
                            return True, ""
                        return False, f"重启失败: {start_result.stderr or start_result.stdout}"
                except subprocess.TimeoutExpired:
                    logger.error(f"Windows服务重启命令超时: {display_name}")
                    return False, f"重启超时: {display_name}"
                except Exception as e:
                    logger.error(f"Windows服务重启失败: {str(e)}")
                    return False, f"重启失败: {str(e)}"

        for key, process_info in ServiceRestartManager.WINDOWS_PROCESS_COMMANDS.items():
            if key in service_name:
                display_name = process_info['display_name']
                process_patterns = process_info['process_patterns']
                start_command = process_info['start_command']

                try:
                    logger.info(f"Windows进程重启: {display_name}")

                    killed = ServiceRestartManager._kill_process_by_pattern(process_patterns)
                    logger.info(f"进程终止结果: {killed}")

                    import time
                    time.sleep(2)

                    started, start_msg = ServiceRestartManager._start_process(start_command)
                    logger.info(f"进程启动结果: {started}, {start_msg}")

                    return started, start_msg
                except Exception as e:
                    logger.error(f"Windows进程重启失败: {str(e)}")
                    return False, f"重启失败: {str(e)}"

        if 'docker' in service_name or 'milvus' in service_name or 'chroma' in service_name or 'minio' in service_name:
            try:
                check_docker = subprocess.run(
                    ['docker', 'info'],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                if check_docker.returncode != 0:
                    return False, "Docker未安装或未运行"
            except FileNotFoundError:
                return False, "Docker未安装"
            except Exception as e:
                return False, f"Docker不可用: {str(e)}"

            try:
                container_name = None
                if 'milvus' in service_name:
                    container_name = 'bid-milvus'
                elif 'chroma' in service_name:
                    container_name = 'bid-chroma'
                elif 'minio' in service_name:
                    container_name = 'bid-minio'
                elif 'docker' in service_name:
                    container_name = service_name.replace('docker_', '').replace('_docker', '')

                logger.info(f"Windows Docker容器重启: {container_name}")
                result = subprocess.run(
                    ['docker', 'restart', container_name],
                    capture_output=True,
                    text=True,
                    timeout=60
                )
                logger.info(f"docker restart result: returncode={result.returncode}, stdout={result.stdout}, stderr={result.stderr}")
                if result.returncode == 0:
                    return True, ""
                return False, f"Docker重启失败: {result.stderr or result.stdout}"
            except subprocess.TimeoutExpired:
                logger.error(f"Docker容器重启超时: {container_name}")
                return False, f"Docker重启超时: {container_name}"
            except Exception as e:
                logger.error(f"Docker容器重启失败: {str(e)}")
                return False, f"Docker重启失败: {str(e)}"

        logger.warning(f"未找到服务 {service.name} 的Windows重启方式")
        return False, f"不支持的服务: {service.name}"

    @staticmethod
    def _find_windows_service_name(pattern: str) -> Optional[str]:
        """
        通过服务显示名称查找实际的服务名
        使用 sc query 命令枚举服务
        """
        try:
            result = subprocess.run(
                ['sc', 'query', 'state=', 'all'],
                capture_output=True,
                text=True,
                timeout=30
            )
            if result.returncode != 0:
                return None

            lines = result.stdout.split('\n')
            current_service_name = None
            current_display_name = None

            for line in lines:
                line = line.strip()
                if line.startswith('SERVICE_NAME:'):
                    current_service_name = line.split(':', 1)[1].strip()
                elif line.startswith('DISPLAY_NAME:'):
                    current_display_name = line.split(':', 1)[1].strip()
                    if pattern.lower() in current_display_name.lower():
                        logger.info(f"找到匹配服务: {current_display_name} -> {current_service_name}")
                        return current_service_name

            return None
        except Exception as e:
            logger.error(f"查找Windows服务名失败: {str(e)}")
            return None

    @staticmethod
    def _kill_process_by_pattern(patterns: list) -> bool:
        """
        通过进程名模式终止进程
        使用 taskkill /F /IM 或 wmic 命令
        """
        try:
            import psutil
            killed_any = False

            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    proc_name = proc.info['name'] or ''
                    cmdline = ' '.join(proc.info['cmdline']) if proc.info['cmdline'] else ''

                    for pattern in patterns:
                        import re
                        if re.search(pattern, proc_name, re.IGNORECASE) or re.search(pattern, cmdline, re.IGNORECASE):
                            logger.info(f"终止进程: {proc_name} (PID: {proc.info['pid']})")
                            proc.kill()
                            killed_any = True
                            break
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    pass

            return killed_any
        except Exception as e:
            logger.error(f"终止进程失败: {str(e)}")
            return False

    @staticmethod
    def _start_process(command: list) -> tuple[bool, str]:
        """
        启动一个新进程
        返回 (success, error_message)
        """
        try:
            import subprocess
            import os

            logger.info(f"启动进程: {' '.join(command)}")

            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE

            process = subprocess.Popen(
                command,
                startupinfo=startupinfo,
                cwd=os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            logger.info(f"进程已启动，PID: {process.pid}")
            return True, ""
        except Exception as e:
            logger.error(f"启动进程失败: {str(e)}")
            return False, f"启动进程失败: {str(e)}"

    @staticmethod
    def _do_restart_linux(service) -> tuple[bool, str]:
        """
        Linux环境下的服务重启
        返回 (success, error_message)
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
                    if result.returncode == 0:
                        return True, ""
                    return False, f"重启失败: {result.stderr or result.stdout}"
                except subprocess.TimeoutExpired:
                    logger.error(f"重启命令超时: {key}")
                    return False, f"重启超时: {key}"
                except Exception as e:
                    logger.error(f"执行重启命令失败: {str(e)}")
                    return False, f"重启失败: {str(e)}"

        logger.warning(f"未找到服务 {service.name} 的重启命令")
        return False, f"不支持的服务: {service.name}"

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