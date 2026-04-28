"""
Monitor Celery定时任务
"""
import logging
from celery import shared_task
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task(name='monitor.tasks.check_all_services_health')
def check_all_services_health():
    """
    定时任务：检查所有服务健康状态
    默认每30秒执行一次
    """
    from .health_checker import ServiceHealthMonitor
    from .restart_manager import AlertManager, PostgresGuardian
    from .models import MonitoredService

    logger.info("开始执行定时健康检查...")

    try:
        pg_ok, pg_msg = PostgresGuardian.ensure_postgres_running()
        if not pg_ok:
            logger.warning(f"PostgreSQL守护检查失败: {pg_msg}")
        else:
            logger.info(f"PostgreSQL守护检查成功: {pg_msg}")

        result = ServiceHealthMonitor.check_all_services()
        logger.info(f"健康检查完成: {result['healthy']}/{result['total']} 服务正常")

        for service_result in result.get('results', []):
            if not service_result.get('is_healthy', True):
                service = MonitoredService.objects.filter(id=service_result['service_id']).first()
                if service:
                    alert = AlertManager.check_and_create_alert(service)
                    if alert:
                        logger.warning(f"服务 {service.name} 创建告警: {alert.title}")
                        AlertManager.send_alert_notification(alert)

        return result

    except Exception as e:
        logger.error(f"健康检查任务执行失败: {str(e)}")
        raise


@shared_task(name='monitor.tasks.auto_recover_unhealthy_services')
def auto_recover_unhealthy_services():
    """
    定时任务：自动恢复异常服务
    在健康检查之后执行
    """
    from django.db import models
    from .restart_manager import ServiceRestartManager, AlertManager
    from .models import MonitoredService

    logger.info("开始执行自动恢复任务...")

    try:
        services = MonitoredService.objects.filter(
            is_enabled=True,
            auto_restart_enabled=True
        ).annotate(
            restart_threshold=models.F('consecutive_failures_to_restart')
        ).filter(
            consecutive_failures__gte=models.F('restart_threshold')
        )

        results = []
        for service in services:
            can_restart, reason = ServiceRestartManager.can_restart(service)
            if can_restart:
                logger.info(f"尝试重启服务: {service.name}")
                result = ServiceRestartManager.execute_restart(service)
                results.append({
                    'service_id': service.id,
                    'service_name': service.name,
                    'result': result
                })

                alert = AlertManager.check_and_create_alert(service)
                if alert and service.consecutive_failures >= service.consecutive_failures_to_alert:
                    AlertManager.send_alert_notification(alert)

        logger.info(f"自动恢复完成: 处理了 {len(results)} 个服务")
        return results

    except Exception as e:
        logger.error(f"自动恢复任务执行失败: {str(e)}")
        raise


@shared_task(name='monitor.tasks.reset_daily_restart_counts')
def reset_daily_restart_counts():
    """
    定时任务：每日重置重启计数
    每天凌晨0点执行
    """
    from .models import MonitoredService

    logger.info("重置每日重启计数...")

    try:
        updated = MonitoredService.objects.filter(
            restart_attempts_today__gt=0
        ).update(restart_attempts_today=0)

        logger.info(f"已重置 {updated} 个服务的每日重启计数")
        return {'reset_count': updated}

    except Exception as e:
        logger.error(f"重置每日重启计数失败: {str(e)}")
        raise


@shared_task(name='monitor.tasks.cleanup_old_health_records')
def cleanup_old_health_records():
    """
    定时任务：清理过期的健康检查记录
    保留最近7天的记录
    """
    from .models import ServiceHealthRecord

    logger.info("清理过期的健康检查记录...")

    try:
        cutoff_date = timezone.now() - timezone.timedelta(days=7)
        deleted, _ = ServiceHealthRecord.objects.filter(
            timestamp__lt=cutoff_date
        ).delete()

        logger.info(f"已删除 {deleted} 条过期健康检查记录")
        return {'deleted_count': deleted}

    except Exception as e:
        logger.error(f"清理健康检查记录失败: {str(e)}")
        raise


@shared_task(name='monitor.tasks.cleanup_old_action_logs')
def cleanup_old_action_logs():
    """
    定时任务：清理过期的操作日志
    保留最近30天的记录
    """
    from .models import ServiceActionLog

    logger.info("清理过期的操作日志...")

    try:
        cutoff_date = timezone.now() - timezone.timedelta(days=30)
        deleted, _ = ServiceActionLog.objects.filter(
            started_at__lt=cutoff_date
        ).delete()

        logger.info(f"已删除 {deleted} 条过期操作日志")
        return {'deleted_count': deleted}

    except Exception as e:
        logger.error(f"清理操作日志失败: {str(e)}")
        raise


@shared_task(name='monitor.tasks.check_single_service', bind=True)
def check_single_service(self, service_id: int):
    """
    检查单个服务的健康状态
    """
    from .health_checker import ServiceHealthMonitor

    logger.info(f"检查单个服务: {service_id}")

    try:
        result = ServiceHealthMonitor.check_single_service(service_id)
        return result
    except Exception as e:
        logger.error(f"检查服务失败: {str(e)}")
        raise


@shared_task(name='monitor.tasks.send_pending_alerts')
def send_pending_alerts():
    """
    定时任务：发送待处理的告警通知
    每分钟执行一次
    """
    from .restart_manager import AlertManager
    from .models import ServiceAlert, AlertStatus

    logger.info("发送待处理的告警通知...")

    try:
        pending_alerts = ServiceAlert.objects.filter(
            status=AlertStatus.PENDING
        )

        sent_count = 0
        for alert in pending_alerts:
            if AlertManager.send_alert_notification(alert):
                sent_count += 1

        logger.info(f"已发送 {sent_count} 个告警通知")
        return {'sent_count': sent_count}

    except Exception as e:
        logger.error(f"发送告警通知失败: {str(e)}")
        raise