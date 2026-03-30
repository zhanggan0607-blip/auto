"""
Monitor信号处理器
"""
import logging
from django.db.models.signals import post_save
from django.dispatch import receiver

logger = logging.getLogger(__name__)


@receiver(post_save, sender='monitor.MonitoredService')
def on_service_status_change(sender, instance, created, **kwargs):
    """
    当服务状态发生变化时触发
    可用于发送通知或执行其他操作
    """
    if created:
        logger.info(f"新服务已添加监控: {instance.display_name}")
    else:
        logger.debug(f"服务配置已更新: {instance.display_name}")