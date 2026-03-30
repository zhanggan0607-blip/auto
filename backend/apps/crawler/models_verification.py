"""
采集验证报告模型
用于存储数据源验证报告和采集工作流记录
"""
from django.db import models
from django.contrib.auth import get_user_model


class DataSourceVerification(models.Model):
    """
    数据源验证记录
    存储数据源的验证状态和报告
    """

    STATUS_CHOICES = [
        ('pending', '待验证'),
        ('validating', '验证中'),
        ('passed', '验证通过'),
        ('failed', '验证失败'),
        ('requires_review', '需人工审核'),
    ]

    source_name = models.CharField('数据源名称', max_length=200)
    source_url = models.URLField('数据源URL', max_length=1000)
    source_type = models.CharField('数据源类型', max_length=50, default='unknown')

    status = models.CharField('验证状态', max_length=20, choices=STATUS_CHOICES, default='pending')

    compliance_passed = models.BooleanField('合规性验证', default=False)
    technical_passed = models.BooleanField('技术可行性验证', default=False)
    quality_passed = models.BooleanField('数据质量验证', default=False)

    validation_report = models.JSONField('验证报告', default=dict, blank=True)

    warnings = models.JSONField('警告信息', default=list, blank=True)
    recommendations = models.JSONField('建议', default=list, blank=True)

    can_proceed = models.BooleanField('是否可以继续', default=False)
    requires_manual_review = models.BooleanField('需人工审核', default=False)

    validated_by = models.ForeignKey(
        get_user_model(),
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='验证人'
    )

    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)
    validated_at = models.DateTimeField('验证时间', null=True, blank=True)

    class Meta:
        db_table = 'data_source_verification'
        verbose_name = '数据源验证'
        verbose_name_plural = '数据源验证'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.source_name} - {self.get_status_display()}"


class CollectionWorkflow(models.Model):
    """
    采集工作流记录
    存储采集工作流的执行状态和结果
    """

    STAGE_CHOICES = [
        ('pending', '待处理'),
        ('validation', '验证阶段'),
        ('validation_passed', '验证通过'),
        ('validation_failed', '验证失败'),
        ('collection', '采集中'),
        ('collection_passed', '采集完成'),
        ('collection_failed', '采集失败'),
        ('completed', '已完成'),
    ]

    STATUS_CHOICES = [
        ('pending', '待处理'),
        ('running', '运行中'),
        ('paused', '暂停'),
        ('completed', '已完成'),
        ('failed', '失败'),
        ('cancelled', '已取消'),
    ]

    workflow_id = models.CharField('工作流ID', max_length=100, unique=True, db_index=True)
    source_name = models.CharField('数据源名称', max_length=200)
    source_url = models.URLField('数据源URL', max_length=1000)
    source_type = models.CharField('数据源类型', max_length=50, default='unknown')

    current_stage = models.CharField('当前阶段', max_length=20, choices=STAGE_CHOICES, default='pending')
    overall_status = models.CharField('整体状态', max_length=20, choices=STATUS_CHOICES, default='pending')

    can_proceed = models.BooleanField('是否可以继续', default=False)
    requires_manual_review = models.BooleanField('需人工审核', default=False)

    validation_result = models.JSONField('验证结果', default=dict, blank=True)
    collection_result = models.JSONField('采集结果', default=dict, blank=True)

    metadata = models.JSONField('元数据', default=dict, blank=True)

    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)
    completed_at = models.DateTimeField('完成时间', null=True, blank=True)

    class Meta:
        db_table = 'collection_workflow'
        verbose_name = '采集工作流'
        verbose_name_plural = '采集工作流'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.workflow_id} - {self.get_overall_status_display()}"


class CrawlerSourceConfig(models.Model):
    """
    爬虫数据源配置
    存储已验证通过的数据源配置
    """

    STATUS_CHOICES = [
        ('active', '启用'),
        ('inactive', '停用'),
        ('blocked', '被封禁'),
        ('requires_review', '需重新审核'),
    ]

    name = models.CharField('配置名称', max_length=200, unique=True)
    code = models.CharField('配置代码', max_length=50, unique=True, db_index=True)

    base_url = models.URLField('基础URL', max_length=1000)

    source_type = models.CharField('数据源类型', max_length=50)

    status = models.CharField('状态', max_length=20, choices=STATUS_CHOICES, default='requires_review')

    verification = models.OneToOneField(
        DataSourceVerification,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='验证记录'
    )

    config_data = models.JSONField('配置数据', default=dict, blank=True)

    notice_types = models.JSONField('支持的公告类型', default=list, blank=True)

    created_by = models.ForeignKey(
        get_user_model(),
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_sources',
        verbose_name='创建人'
    )

    is_active = models.BooleanField('是否启用', default=True)

    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        db_table = 'crawler_source_config'
        verbose_name = '爬虫数据源配置'
        verbose_name_plural = '爬虫数据源配置'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.code})"
