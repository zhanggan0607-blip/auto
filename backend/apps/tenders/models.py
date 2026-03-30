"""
招标项目模块 - 数据模型
"""
from django.db import models
from django.conf import settings
from django.utils import timezone

from core.constants import (
    SOURCE_TYPE_CHOICES,
    TENDER_STATUS_CHOICES,
    FILE_TYPE_CHOICES,
    KEYWORD_CATEGORY_CHOICES,
    CRAWLER_STATUS_CHOICES,
)


class TenderSource(models.Model):
    """
    招标信息来源模型
    """
    name = models.CharField('来源名称', max_length=200)
    code = models.CharField('来源编码', max_length=50, unique=True)
    source_type = models.CharField('来源类型', max_length=20, choices=SOURCE_TYPE_CHOICES, default='government')
    base_url = models.URLField('基础URL', max_length=500)
    is_active = models.BooleanField('是否启用', default=True)
    crawler_config = models.JSONField('爬虫配置', default=dict, blank=True)
    created_at = models.DateTimeField('创建时间', default=timezone.now)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        db_table = 'tender_sources'
        verbose_name = '招标来源'
        verbose_name_plural = verbose_name
        ordering = ['-created_at']

    def __str__(self):
        return self.name


class TenderProject(models.Model):
    """
    招标项目模型
    """
    STATUS_CHOICES = TENDER_STATUS_CHOICES
    
    title = models.CharField('项目标题', max_length=500, db_index=True)
    project_code = models.CharField('项目编号', max_length=100, blank=True, null=True)
    source = models.ForeignKey(
        TenderSource,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='信息来源',
        related_name='tenders'
    )
    source_url = models.URLField('来源链接', max_length=1000, blank=True, null=True)
    
    publish_date = models.DateField('发布日期', db_index=True)
    deadline_date = models.DateField('截止日期', blank=True, null=True)
    open_date = models.DateField('开标日期', blank=True, null=True)
    
    region = models.CharField('地区', max_length=100, blank=True, null=True)
    industry = models.CharField('行业', max_length=100, blank=True, null=True)
    category = models.CharField('类别', max_length=100, blank=True, null=True)
    
    purchaser_name = models.CharField('采购人名称', max_length=300, blank=True, null=True)
    purchaser_contact = models.CharField('采购人联系人', max_length=100, blank=True, null=True)
    purchaser_phone = models.CharField('采购人电话', max_length=50, blank=True, null=True)
    
    agency_name = models.CharField('代理机构名称', max_length=300, blank=True, null=True)
    agency_contact = models.CharField('代理机构联系人', max_length=100, blank=True, null=True)
    agency_phone = models.CharField('代理机构电话', max_length=50, blank=True, null=True)
    
    budget = models.DecimalField('预算金额', max_digits=15, decimal_places=2, blank=True, null=True)
    description = models.TextField('项目描述', blank=True, null=True)
    requirements = models.TextField('技术要求', blank=True, null=True)
    
    status = models.CharField('状态', max_length=20, choices=TENDER_STATUS_CHOICES, default='pending', db_index=True)
    is_favorite = models.BooleanField('是否收藏', default=False)
    is_read = models.BooleanField('是否已读', default=False)
    
    keywords_matched = models.JSONField('匹配关键词', default=list, blank=True)
    raw_data = models.JSONField('原始数据', default=dict, blank=True)
    
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='创建人',
        related_name='created_tenders'
    )
    created_at = models.DateTimeField('创建时间', default=timezone.now)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        db_table = 'tender_projects'
        verbose_name = '招标项目'
        verbose_name_plural = verbose_name
        ordering = ['-publish_date', '-created_at']
        indexes = [
            models.Index(fields=['status', 'publish_date']),
            models.Index(fields=['region', 'industry']),
        ]

    def __str__(self):
        return self.title


class TenderFile(models.Model):
    """
    招标文件模型
    """
    tender = models.ForeignKey(
        TenderProject,
        on_delete=models.CASCADE,
        verbose_name='招标项目',
        related_name='files'
    )
    file_type = models.CharField('文件类型', max_length=20, choices=FILE_TYPE_CHOICES, default='document')
    file_name = models.CharField('文件名称', max_length=500)
    file_path = models.FileField('文件路径', upload_to='tender_files/%Y/%m/')
    file_size = models.BigIntegerField('文件大小', blank=True, null=True)
    file_ext = models.CharField('文件扩展名', max_length=20, blank=True, null=True)
    download_url = models.URLField('下载链接', max_length=1000, blank=True, null=True)
    is_downloaded = models.BooleanField('是否已下载', default=False)
    created_at = models.DateTimeField('创建时间', default=timezone.now)

    class Meta:
        db_table = 'tender_files'
        verbose_name = '招标文件'
        verbose_name_plural = verbose_name
        ordering = ['-created_at']

    def __str__(self):
        return self.file_name


class TenderKeyword(models.Model):
    """
    招标关键词模型
    """
    keyword = models.CharField('关键词', max_length=100, unique=True)
    category = models.CharField('关键词类别', max_length=20, choices=KEYWORD_CATEGORY_CHOICES, default='industry')
    weight = models.IntegerField('权重', default=1)
    is_active = models.BooleanField('是否启用', default=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='创建人'
    )
    created_at = models.DateTimeField('创建时间', default=timezone.now)

    class Meta:
        db_table = 'tender_keywords'
        verbose_name = '招标关键词'
        verbose_name_plural = verbose_name
        ordering = ['-weight', 'keyword']

    def __str__(self):
        return self.keyword


class CrawlerTask(models.Model):
    """
    爬虫任务模型
    """
    name = models.CharField('任务名称', max_length=200)
    source = models.ForeignKey(
        TenderSource,
        on_delete=models.CASCADE,
        verbose_name='数据来源',
        related_name='crawler_tasks'
    )
    task_type = models.CharField('任务类型', max_length=50, default='crawl_tenders')
    params = models.JSONField('任务参数', default=dict, blank=True)
    status = models.CharField('任务状态', max_length=20, choices=CRAWLER_STATUS_CHOICES, default='pending')
    result_count = models.IntegerField('结果数量', default=0)
    error_message = models.TextField('错误信息', blank=True, null=True)
    started_at = models.DateTimeField('开始时间', blank=True, null=True)
    finished_at = models.DateTimeField('结束时间', blank=True, null=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='创建人'
    )
    created_at = models.DateTimeField('创建时间', default=timezone.now)

    class Meta:
        db_table = 'crawler_tasks'
        verbose_name = '爬虫任务'
        verbose_name_plural = verbose_name
        ordering = ['-created_at']

    def __str__(self):
        return self.name
