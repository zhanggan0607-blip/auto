from django.db import models
from django.conf import settings
from django.utils import timezone

from core.constants import (
    ASSURANCE_CHECK_STATUS_CHOICES,
    ASSURANCE_REPORT_STATUS_CHOICES,
    OPTIMIZATION_TYPE_CHOICES,
)


class CrawlHealthCheck(models.Model):
    network_connectivity = models.CharField('网络连通性', max_length=20, choices=ASSURANCE_CHECK_STATUS_CHOICES, default='pending')
    network_details = models.JSONField('网络检查详情', default=dict, blank=True)

    http_status = models.CharField('HTTP状态码', max_length=20, choices=ASSURANCE_CHECK_STATUS_CHOICES, default='pending')
    http_status_code = models.IntegerField('响应状态码', null=True, blank=True)
    http_details = models.JSONField('HTTP检查详情', default=dict, blank=True)

    page_structure = models.CharField('页面结构', max_length=20, choices=ASSURANCE_CHECK_STATUS_CHOICES, default='pending')
    page_structure_diff = models.JSONField('页面结构差异', default=dict, blank=True)
    page_structure_details = models.JSONField('页面结构检查详情', default=dict, blank=True)

    anti_crawl = models.CharField('反爬检测', max_length=20, choices=ASSURANCE_CHECK_STATUS_CHOICES, default='pending')
    anti_crawl_indicators = models.JSONField('反爬指标', default=dict, blank=True)
    anti_crawl_details = models.JSONField('反爬检查详情', default=dict, blank=True)

    extraction_rules = models.CharField('提取规则', max_length=20, choices=ASSURANCE_CHECK_STATUS_CHOICES, default='pending')
    extraction_rules_invalid = models.JSONField('失效的提取规则', default=list, blank=True)
    extraction_rules_details = models.JSONField('提取规则检查详情', default=dict, blank=True)

    overall_status = models.CharField('总体状态', max_length=20, choices=ASSURANCE_CHECK_STATUS_CHOICES, default='pending')
    failure_summary = models.TextField('失败原因汇总', blank=True, default='')

    website_template = models.ForeignKey(
        'crawler.WebsiteTemplate',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='网站模板',
        related_name='health_checks'
    )
    target_url = models.URLField('目标URL', max_length=1000)

    checked_at = models.DateTimeField('检查时间', default=timezone.now)
    duration = models.FloatField('检查耗时(秒)', default=0)

    class Meta:
        db_table = 'crawl_health_checks'
        verbose_name = '采集健康检查'
        verbose_name_plural = verbose_name
        ordering = ['-checked_at']

    def __str__(self):
        return f'健康检查 {self.target_url[:50]} - {self.overall_status}'


class CrawlOptimizationPlan(models.Model):
    optimization_type = models.CharField('优化类型', max_length=30, choices=OPTIMIZATION_TYPE_CHOICES)
    description = models.TextField('优化描述')
    parameters_before = models.JSONField('优化前参数', default=dict, blank=True)
    parameters_after = models.JSONField('优化后参数', default=dict, blank=True)
    is_applied = models.BooleanField('已应用', default=False)
    applied_at = models.DateTimeField('应用时间', null=True, blank=True)
    apply_result = models.CharField('应用结果', max_length=20, default='pending')
    apply_details = models.TextField('应用详情', blank=True, default='')

    health_check = models.ForeignKey(
        CrawlHealthCheck,
        on_delete=models.CASCADE,
        verbose_name='健康检查',
        related_name='optimization_plans'
    )

    created_at = models.DateTimeField('创建时间', default=timezone.now)

    class Meta:
        db_table = 'crawl_optimization_plans'
        verbose_name = '采集优化方案'
        verbose_name_plural = verbose_name
        ordering = ['created_at']

    def __str__(self):
        return f'{self.get_optimization_type_display()} - {self.description[:50]}'


class CrawlAssuranceReport(models.Model):
    website_template = models.ForeignKey(
        'crawler.WebsiteTemplate',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='网站模板',
        related_name='assurance_reports'
    )
    target_url = models.URLField('目标URL', max_length=1000)
    consecutive_failures = models.IntegerField('连续失败次数', default=0)
    trigger_reason = models.TextField('触发原因', blank=True, default='')

    status = models.CharField('状态', max_length=20, choices=ASSURANCE_REPORT_STATUS_CHOICES, default='running')
    attempt_count = models.IntegerField('尝试次数', default=0)
    max_attempts = models.IntegerField('最大尝试次数', default=5)

    current_health_check = models.ForeignKey(
        CrawlHealthCheck,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='当前健康检查',
        related_name='+'
    )

    failure_analysis = models.TextField('失败原因分析', blank=True, default='')
    optimization_summary = models.TextField('优化措施汇总', blank=True, default='')
    parameters_comparison = models.JSONField('修复前后参数对比', default=dict, blank=True)
    crawl_result_stats = models.JSONField('爬取结果统计', default=dict, blank=True)

    notification_sent = models.BooleanField('已发送通知', default=False)
    notification_channels = models.JSONField('通知渠道', default=list, blank=True)
    notification_details = models.JSONField('通知详情', default=dict, blank=True)

    final_result = models.TextField('最终结果', blank=True, default='')
    data_collected = models.IntegerField('最终采集数据量', default=0)

    started_at = models.DateTimeField('开始时间', default=timezone.now)
    finished_at = models.DateTimeField('结束时间', null=True, blank=True)
    duration = models.FloatField('总耗时(秒)', default=0)

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
        db_table = 'crawl_assurance_reports'
        verbose_name = '采集保障报告'
        verbose_name_plural = verbose_name
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['website_template', '-created_at']),
        ]

    def __str__(self):
        return f'保障报告 {self.target_url[:50]} - {self.status} (尝试{self.attempt_count}/{self.max_attempts})'
