"""
统一调度模型
管理所有定时任务的配置和状态
"""
from django.db import models
from django.conf import settings
from django.utils import timezone
from django_celery_beat.models import PeriodicTask


class UnifiedSchedule(models.Model):
    """
    统一调度任务模型
    """
    TASK_TYPE_CHOICES = [
        ('tender_scan', '招标信息扫描'),
        ('bid_auto_submit', '自动投标执行'),
        ('result_check', '中标结果检查'),
        ('vector_cleanup', '向量库维护'),
        ('system_health_check', '系统健康检查'),
        ('daily_summary', '每日汇总报告'),
        ('cleanup_old_tasks', '清理旧任务'),
        ('custom', '自定义任务'),
    ]

    task_id = models.CharField('任务ID', max_length=100, unique=True)
    task_name = models.CharField('任务名称', max_length=200)
    task_type = models.CharField('任务类型', max_length=50, choices=TASK_TYPE_CHOICES)
    description = models.TextField('任务描述', blank=True)

    cron_expression = models.CharField('Cron表达式', max_length=100,
                                       help_text='格式: 分 时 日 月 周')
    is_enabled = models.BooleanField('是否启用', default=True)

    last_run_at = models.DateTimeField('上次执行时间', null=True, blank=True)
    next_run_at = models.DateTimeField('下次执行时间', null=True, blank=True)
    last_run_status = models.CharField('上次执行状态', max_length=20, blank=True)
    last_run_result = models.JSONField('上次执行结果', null=True, blank=True)
    run_count = models.IntegerField('执行次数', default=0)
    error_count = models.IntegerField('错误次数', default=0)
    last_error = models.TextField('上次错误信息', blank=True)

    celery_task = models.ForeignKey(
        PeriodicTask,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Celery定时任务',
        related_name='unified_schedules'
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='创建人'
    )
    created_at = models.DateTimeField('创建时间', default=timezone.now)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        db_table = 'unified_schedules'
        verbose_name = '统一调度任务'
        verbose_name_plural = verbose_name
        ordering = ['task_type', 'task_name']

    def __str__(self):
        return f'{self.task_name} ({self.task_id})'

    def parse_crontab(self):
        """
        解析Cron表达式
        返回: (minute, hour, day_of_month, month_of_year, day_of_week)
        """
        parts = self.cron_expression.strip().split()
        if len(parts) != 5:
            return '0', '0', '*', '*', '*'
        return tuple(parts)

    def create_celery_task(self, task_path: str):
        """
        创建Celery定时任务
        """
        from django_celery_beat.models import PeriodicTask, CrontabSchedule
        import json

        minute, hour, day_of_month, month_of_year, day_of_week = self.parse_crontab()

        schedule, _ = CrontabSchedule.objects.get_or_create(
            minute=minute,
            hour=hour,
            day_of_month=day_of_month,
            month_of_year=month_of_year,
            day_of_week=day_of_week,
            timezone='Asia/Shanghai'
        )

        task, created = PeriodicTask.objects.update_or_create(
            name=f'unified_{self.task_id}',
            defaults={
                'crontab': schedule,
                'task': task_path,
                'kwargs': json.dumps({}),
                'enabled': self.is_enabled,
            }
        )

        self.celery_task = task
        self.save(update_fields=['celery_task'])

        return task

    def update_celery_task(self):
        """
        更新Celery定时任务状态
        """
        if self.celery_task:
            self.celery_task.enabled = self.is_enabled
            self.celery_task.save()
        return self

    def delete_celery_task(self):
        """
        删除Celery定时任务
        """
        if self.celery_task:
            self.celery_task.delete()
            self.celery_task = None
            self.save(update_fields=['celery_task'])
        return self


class ScheduleExecutionLog(models.Model):
    """
    调度任务执行日志
    """
    STATUS_CHOICES = [
        ('running', '执行中'),
        ('success', '成功'),
        ('failed', '失败'),
        ('partial', '部分成功'),
    ]

    schedule = models.ForeignKey(
        UnifiedSchedule,
        on_delete=models.CASCADE,
        verbose_name='调度任务',
        related_name='execution_logs'
    )

    status = models.CharField('状态', max_length=20, choices=STATUS_CHOICES, default='running')
    result = models.JSONField('执行结果', null=True, blank=True)
    error_message = models.TextField('错误信息', blank=True)
    duration = models.IntegerField('耗时(秒)', default=0)

    started_at = models.DateTimeField('开始时间', default=timezone.now)
    finished_at = models.DateTimeField('结束时间', null=True, blank=True)

    class Meta:
        db_table = 'schedule_execution_logs'
        verbose_name = '调度执行日志'
        verbose_name_plural = verbose_name
        ordering = ['-started_at']

    def __str__(self):
        return f'{self.schedule.task_name} - {self.started_at}'

    def finish(self, status: str, result: dict = None, error: str = ''):
        """
        完成执行日志
        """
        self.status = status
        self.result = result
        self.error_message = error
        self.finished_at = timezone.now()
        self.duration = (self.finished_at - self.started_at).seconds
        self.save()

        self.schedule.last_run_at = self.started_at
        self.schedule.last_run_status = status
        self.schedule.last_run_result = result
        self.schedule.run_count += 1

        if status == 'failed':
            self.schedule.error_count += 1
            self.schedule.last_error = error

        self.schedule.save()

        return self
