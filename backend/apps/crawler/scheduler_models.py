"""
定时采集任务调度模型
"""
from django.db import models
from django.conf import settings
from django.utils import timezone
from django_celery_beat.models import PeriodicTask, CrontabSchedule
import json

from core.constants import SCHEDULE_STATUS_CHOICES


class CrawlSchedule(models.Model):
    """
    采集计划模型 - 管理定时采集任务
    """

    name = models.CharField('计划名称', max_length=200)
    website_template = models.ForeignKey(
        'crawler.WebsiteTemplate',
        on_delete=models.CASCADE,
        verbose_name='网站模板',
        related_name='crawl_schedules',
        null=True,
        blank=True
    )

    crontab = models.CharField('Cron表达式', max_length=100, default='0 8 * * *',
                               help_text='格式: 分 时 日 月 周，如 "0 8 * * *" 表示每天8点执行')

    is_active = models.BooleanField('是否启用', default=True)
    status = models.CharField('状态', max_length=20, choices=SCHEDULE_STATUS_CHOICES, default='active')

    max_pages = models.IntegerField('最大采集页数', default=5)
    crawl_mode = models.CharField(
        '采集模式',
        max_length=20,
        choices=[
            ('full', '全量采集'),
            ('incremental', '增量采集'),
        ],
        default='full',
        help_text='全量采集：采集所有页面；增量采集：仅采集最新数据'
    )
    keywords = models.JSONField('搜索关键词', default=list, blank=True)
    params = models.JSONField('采集参数', default=dict, blank=True)

    regions = models.JSONField('采集地区', default=list, blank=True,
                               help_text='选择的省/市/区列表，留空则采集全国')
    enterprise_ids = models.JSONField('参与资质匹配的企业ID列表', default=list, blank=True,
                                     help_text='选择参与资质匹配的企业ID')
    exec_datetime = models.DateTimeField('定时执行时间', blank=True, null=True,
                                         help_text='单次执行的指定时间')

    last_run_at = models.DateTimeField('上次执行时间', blank=True, null=True)
    next_run_at = models.DateTimeField('下次执行时间', blank=True, null=True)
    last_result_count = models.IntegerField('上次采集数量', default=0)
    total_result_count = models.IntegerField('累计采集数量', default=0)
    run_count = models.IntegerField('执行次数', default=0)
    error_count = models.IntegerField('错误次数', default=0)
    last_error = models.TextField('上次错误信息', blank=True, null=True)

    auto_match = models.BooleanField('自动匹配企业资质', default=True,
                                     help_text='采集完成后自动进行企业资质匹配')
    auto_delete_unmatched = models.BooleanField('自动删除不匹配项目', default=False,
                                                 help_text='不符合企业要求的项目自动删除')
    match_threshold = models.FloatField('匹配阈值', default=0.6,
                                        help_text='低于此阈值的视为不匹配，范围0-1')

    celery_task = models.ForeignKey(
        PeriodicTask,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Celery定时任务',
        related_name='crawl_schedules'
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
        db_table = 'crawl_schedules'
        verbose_name = '采集计划'
        verbose_name_plural = verbose_name
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    def parse_crontab(self):
        """
        解析Cron表达式
        返回: (minute, hour, day_of_month, month_of_year, day_of_week)
        """
        parts = self.crontab.strip().split()
        if len(parts) != 5:
            return '0', '8', '*', '*', '*'
        return tuple(parts)

    def create_celery_task(self):
        """
        创建Celery定时任务
        """
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
            name=f'crawl_schedule_{self.id}',
            defaults={
                'crontab': schedule,
                'task': 'crawler.tasks.scheduled_crawl_with_match',
                'args': json.dumps([self.id]),
                'enabled': self.is_active and self.status == 'active',
            }
        )

        self.celery_task = task
        self.save(update_fields=['celery_task'])

        return task

    def update_celery_task(self):
        """
        更新Celery定时任务
        """
        if self.celery_task:
            self.celery_task.enabled = self.is_active and self.status == 'active'
            self.celery_task.save()
        else:
            self.create_celery_task()

    def delete_celery_task(self):
        """
        删除Celery定时任务
        """
        if self.celery_task:
            self.celery_task.delete()
            self.celery_task = None
            self.save(update_fields=['celery_task'])


class CrawlScheduleLog(models.Model):
    """
    采集计划执行日志
    """
    LOG_STATUS_CHOICES = [
        ('running', '执行中'),
        ('success', '成功'),
        ('failed', '失败'),
        ('partial', '部分成功'),
    ]

    schedule = models.ForeignKey(
        CrawlSchedule,
        on_delete=models.CASCADE,
        verbose_name='采集计划',
        related_name='logs'
    )
    session = models.ForeignKey(
        'crawler.CrawlSession',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='采集会话',
        related_name='schedule_logs'
    )

    status = models.CharField('状态', max_length=20, choices=LOG_STATUS_CHOICES, default='running')
    result_count = models.IntegerField('采集数量', default=0)
    matched_count = models.IntegerField('匹配数量', default=0)
    deleted_count = models.IntegerField('删除数量', default=0)

    error_message = models.TextField('错误信息', blank=True, null=True)
    details = models.JSONField('详细信息', default=dict, blank=True)

    started_at = models.DateTimeField('开始时间', default=timezone.now)
    finished_at = models.DateTimeField('结束时间', blank=True, null=True)
    duration = models.FloatField('耗时(秒)', default=0.0)

    class Meta:
        db_table = 'crawl_schedule_logs'
        verbose_name = '采集计划日志'
        verbose_name_plural = verbose_name
        ordering = ['-started_at']

    def __str__(self):
        return f'{self.schedule.name} - {self.started_at}'
