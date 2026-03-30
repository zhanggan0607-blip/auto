"""
服务健康检查模块
"""
import time
import psutil
import socket
import logging
import subprocess
from typing import Dict, Any, Optional, Tuple
from datetime import datetime
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError

logger = logging.getLogger(__name__)


class CeleryHealthChecker:
    """
    Celery服务专用健康检查器
    提供详细的Worker状态检测
    """

    @staticmethod
    def check_celery_worker() -> Dict[str, Any]:
        """
        检查Celery Worker状态
        """
        try:
            from config.celery import app as celery_app
            inspect = celery_app.control.inspect()

            stats = inspect.stats()
            active = inspect.active()
            registered = inspect.registered()

            if not stats:
                return {
                    'is_healthy': False,
                    'error_message': '无Worker运行',
                    'worker_count': 0,
                    'active_tasks': [],
                    'queue_name': None
                }

            worker_count = len(stats)
            active_tasks = []
            queues = set()

            for worker_name, worker_stats in stats.items():
                if 'pool' in worker_stats:
                    queues.add(worker_stats['pool'].get('queues', ['default']))

            if active:
                for worker_name, tasks in active.items():
                    for task in tasks:
                        active_tasks.append({
                            'worker': worker_name,
                            'task_name': task.get('name', 'unknown'),
                            'time_active': task.get('time_active', 0)
                        })

            return {
                'is_healthy': worker_count > 0,
                'worker_count': worker_count,
                'active_tasks': active_tasks[:10],
                'active_task_count': len(active_tasks),
                'registered_tasks': len(registered) if registered else 0,
                'queues': list(queues) if queues else ['default'],
                'error_message': '' if worker_count > 0 else '无Worker运行'
            }

        except Exception as e:
            logger.error(f"Celery Worker检查失败: {str(e)}")
            return {
                'is_healthy': False,
                'error_message': f'检查失败: {str(e)}',
                'worker_count': 0
            }

    @staticmethod
    def check_celery_beat() -> Dict[str, Any]:
        """
        检查Celery Beat调度器状态
        """
        try:
            from django_celery_beat.models import PeriodicTask, IntervalSchedule
            from django.utils import timezone

            active_tasks = PeriodicTask.objects.filter(enabled=True).count()

            schedules = IntervalSchedule.objects.count()

            return {
                'is_healthy': True,
                'active_tasks': active_tasks,
                'schedules': schedules,
                'error_message': ''
            }

        except Exception as e:
            logger.error(f"Celery Beat检查失败: {str(e)}")
            return {
                'is_healthy': False,
                'error_message': f'检查失败: {str(e)}',
                'active_tasks': 0
            }

    @staticmethod
    def check_celery_tasks() -> Dict[str, Any]:
        """
        检查待执行任务队列
        """
        try:
            from config.celery import app as celery_app

            inspect = celery_app.control.inspect()
            reserved = inspect.reserved()
            scheduled = inspect.scheduled()

            pending_count = 0
            if reserved:
                for worker_tasks in reserved.values():
                    pending_count += len(worker_tasks)
            if scheduled:
                for worker_tasks in scheduled.values():
                    pending_count += len(worker_tasks)

            return {
                'pending_tasks': pending_count,
                'is_healthy': True
            }

        except Exception as e:
            return {
                'pending_tasks': 0,
                'is_healthy': True,
                'error': str(e)
            }


class HealthChecker:
    """
    服务健康检查器
    支持HTTP/TCP/进程等多种检查方式
    """

    def __init__(self, service):
        from apps.monitor.models import MonitoredService
        self.service = service if isinstance(service, MonitoredService) else service

    def check_health(self) -> Dict[str, Any]:
        """
        执行健康检查并返回结果
        """
        start_time = time.time()

        check_type = self.service.health_check_type
        try:
            if check_type == 'http':
                result = self._check_http()
            elif check_type == 'tcp':
                result = self._check_tcp()
            elif check_type == 'process':
                result = self._check_process()
            elif check_type == 'celery':
                result = self._check_celery()
            else:
                result = self._check_custom()
        except Exception as e:
            logger.error(f"健康检查异常 {self.service.name}: {str(e)}")
            result = {
                'is_healthy': False,
                'error_message': str(e),
                'response_time_ms': 0
            }

        result['check_duration_ms'] = int((time.time() - start_time) * 1000)
        return result

    def _check_celery(self) -> Dict[str, Any]:
        """Celery服务健康检查"""
        service_name = self.service.name.lower()

        if 'worker' in service_name:
            return CeleryHealthChecker.check_celery_worker()
        elif 'beat' in service_name:
            return CeleryHealthChecker.check_celery_beat()
        else:
            return CeleryHealthChecker.check_celery_worker()

    def _check_http(self) -> Dict[str, Any]:
        """HTTP健康检查"""
        url = self.service.health_check_url
        if not url:
            return {'is_healthy': False, 'error_message': '未配置健康检查URL'}

        try:
            timeout = self.service.health_check_timeout or 10
            req = Request(url, headers={'User-Agent': 'HealthChecker/1.0'})
            start = time.time()
            with urlopen(req, timeout=timeout) as response:
                content = response.read()
                response_time = int((time.time() - start) * 1000)

            return {
                'is_healthy': response.status == 200,
                'response_time_ms': response_time,
                'status_code': response.status,
                'response_size': len(content),
                'error_message': '' if response.status == 200 else f'HTTP {response.status}'
            }
        except HTTPError as e:
            return {
                'is_healthy': False,
                'response_time_ms': int((time.time() - start) * 1000) if 'start' in locals() else 0,
                'error_message': f'HTTP错误: {e.code} {e.reason}'
            }
        except URLError as e:
            return {
                'is_healthy': False,
                'response_time_ms': 0,
                'error_message': f'连接失败: {str(e)}'
            }
        except Exception as e:
            return {
                'is_healthy': False,
                'response_time_ms': 0,
                'error_message': str(e)
            }

    def _check_tcp(self) -> Dict[str, Any]:
        """TCP端口健康检查"""
        port = self.service.health_check_port
        host = self.service.health_check_url or 'localhost'

        if not port:
            return {'is_healthy': False, 'error_message': '未配置端口'}

        try:
            start = time.time()
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.service.health_check_timeout or 5)
            result = sock.connect_ex((host, port))
            sock.close()
            response_time = int((time.time() - start) * 1000)

            return {
                'is_healthy': result == 0,
                'response_time_ms': response_time,
                'error_message': '' if result == 0 else f'端口 {port} 无法连接'
            }
        except Exception as e:
            return {
                'is_healthy': False,
                'response_time_ms': 0,
                'error_message': str(e)
            }

    def _check_process(self) -> Dict[str, Any]:
        """进程健康检查"""
        process_name = self.service.health_check_url

        if not process_name:
            return {'is_healthy': False, 'error_message': '未配置进程名'}

        try:
            cpu_usage, memory_usage = self._get_system_usage()
            is_running = self._is_process_running(process_name)

            return {
                'is_healthy': is_running,
                'response_time_ms': 0,
                'cpu_usage': cpu_usage,
                'memory_usage': memory_usage,
                'error_message': '' if is_running else f'进程 {process_name} 未运行'
            }
        except Exception as e:
            return {
                'is_healthy': False,
                'response_time_ms': 0,
                'error_message': str(e)
            }

    def _check_custom(self) -> Dict[str, Any]:
        """自定义健康检查"""
        return {'is_healthy': True, 'response_time_ms': 0, 'error_message': ''}

    def _is_process_running(self, process_name: str) -> bool:
        """检查进程是否运行"""
        try:
            for proc in psutil.process_iter(['name']):
                if process_name.lower() in proc.info['name'].lower():
                    return True
            return False
        except Exception:
            return False

    def _get_system_usage(self) -> Tuple[Optional[float], Optional[float]]:
        """获取系统CPU和内存使用率"""
        try:
            cpu = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory().percent
            return cpu, memory
        except Exception:
            return None, None


class ServiceHealthMonitor:
    """
    服务健康监控管理器
    负责协调多个服务的健康检查
    """

    @staticmethod
    def check_single_service(service_id: int) -> Dict[str, Any]:
        """
        检查单个服务的健康状态
        """
        from apps.monitor.models import MonitoredService, ServiceHealthRecord, ServiceActionLog
        from django.utils import timezone

        try:
            service = MonitoredService.objects.get(id=service_id)
        except MonitoredService.DoesNotExist:
            return {'error': '服务不存在'}

        if not service.is_enabled:
            return {'status': 'disabled', 'message': '服务监控已禁用'}

        action_log = ServiceActionLog.objects.create(
            service=service,
            action_type='health_check',
            status='started',
            trigger_condition=f'定期检查 @ {timezone.now()}'
        )

        checker = HealthChecker(service)
        result = checker.check_health()

        try:
            cpu_usage, memory_usage = None, None
            if result.get('cpu_usage') is not None:
                cpu_usage = result['cpu_usage']
            if result.get('memory_usage') is not None:
                memory_usage = result['memory_usage']

            ServiceHealthRecord.objects.create(
                service=service,
                is_healthy=result['is_healthy'],
                response_time_ms=result.get('response_time_ms'),
                cpu_usage=cpu_usage,
                memory_usage=memory_usage,
                error_message=result.get('error_message', ''),
                details=result
            )

            if result['is_healthy']:
                service.consecutive_failures = 0
                service.last_health_check = timezone.now()
                service.save(update_fields=['consecutive_failures', 'last_health_check', 'updated_at'])

                action_log.status = 'success'
                action_log.result_message = f"检查成功，响应时间: {result.get('response_time_ms', 0)}ms"
            else:
                service.consecutive_failures += 1
                service.last_health_check = timezone.now()
                service.save(update_fields=['consecutive_failures', 'last_health_check', 'updated_at'])

                action_log.status = 'failed'
                action_log.result_message = result.get('error_message', '检查失败')

            action_log.completed_at = timezone.now()
            action_log.save()

        except Exception as e:
            logger.error(f"保存健康检查记录失败: {str(e)}")
            action_log.status = 'failed'
            action_log.error_details = str(e)
            action_log.completed_at = timezone.now()
            action_log.save()

        return {
            'service_id': service_id,
            'service_name': service.name,
            'is_healthy': result['is_healthy'],
            'response_time_ms': result.get('response_time_ms'),
            'consecutive_failures': service.consecutive_failures,
            'error_message': result.get('error_message', '')
        }

    @staticmethod
    def check_all_services() -> Dict[str, Any]:
        """
        检查所有已启用的服务
        """
        from apps.monitor.models import MonitoredService

        services = MonitoredService.objects.filter(is_enabled=True)
        results = []

        for service in services:
            result = ServiceHealthMonitor.check_single_service(service.id)
            results.append(result)

        healthy_count = sum(1 for r in results if r.get('is_healthy', False))
        unhealthy_count = len(results) - healthy_count

        return {
            'total': len(results),
            'healthy': healthy_count,
            'unhealthy': unhealthy_count,
            'results': results,
            'timestamp': timezone.now().isoformat() if hasattr(timezone, 'now') else datetime.now().isoformat()
        }