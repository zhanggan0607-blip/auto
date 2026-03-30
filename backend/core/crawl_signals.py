"""
Django信号处理器
当爬虫任务完成时，自动向FastAPI推送结果
"""
import logging
from django.db.models.signals import post_save
from django.dispatch import receiver

logger = logging.getLogger(__name__)


def register_crawl_signals():
    """
    注册爬虫相关信号
    在Django应用启动时调用
    """
    from apps.crawler.models import CrawlSchedule, CrawlScheduleLog

    @receiver(post_save, sender=CrawlScheduleLog)
    def on_crawl_log_saved(sender, instance, **kwargs):
        """
        当爬虫日志保存时，推送状态更新
        """
        try:
            from core.django_fastapi_bridge import publish_task_status

            status_mapping = {
                'running': 'running',
                'completed': 'completed',
                'failed': 'failed',
            }

            status = status_mapping.get(instance.status, 'unknown')
            progress = 100 if status == 'completed' else (50 if status == 'running' else 0)

            publish_task_status(
                task_id=f"crawl_{instance.id}",
                status=status,
                progress=progress,
                schedule_id=instance.schedule.id if instance.schedule else None,
                items_count=instance.result_count or 0,
            )

        except Exception as e:
            logger.error(f"推送爬虫状态失败: {e}")


# 注册信号
register_crawl_signals()
