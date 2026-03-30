"""
SAAS采集模块 - 数据模型
"""
from django.db import models
from django.conf import settings
from django.utils import timezone

from core.constants import (
    WEBSITE_TYPE_CHOICES,
    CRAWL_SESSION_STATUS_CHOICES,
    CRAWL_RESULT_STATUS_CHOICES,
    FAILURE_TYPE_CHOICES,
    RESOLUTION_STATUS_CHOICES,
    TRACKING_STATUS_CHOICES,
    VECTOR_STATUS_CHOICES,
    LOG_LEVEL_CHOICES,
)


class WebsiteTemplate(models.Model):
    """
    网站模板模型 - 存储各类网站的爬取配置
    """
    name = models.CharField('网站名称', max_length=200)
    code = models.CharField('网站编码', max_length=50, unique=True)
    website_type = models.CharField('网站类型', max_length=20, choices=WEBSITE_TYPE_CHOICES, default='other')
    base_url = models.URLField('基础URL', max_length=500)
    
    list_url_pattern = models.CharField('列表URL模式', max_length=500, blank=True, null=True, 
                                        help_text='支持变量: {page}, {keyword}, {category}, {start_date}, {end_date}')
    search_url_pattern = models.CharField('搜索URL模式', max_length=500, blank=True, null=True,
                                          help_text='支持变量: {keyword}, {page}, {start_date}, {end_date}')
    
    selectors = models.JSONField('选择器配置', default=dict, blank=True,
                                  help_text='CSS选择器配置，用于提取数据')
    pagination_config = models.JSONField('分页配置', default=dict, blank=True,
                                          help_text='分页相关配置')
    request_config = models.JSONField('请求配置', default=dict, blank=True,
                                       help_text='请求头、代理等配置')
    
    requires_javascript = models.BooleanField('需要JS渲染', default=False)
    requires_login = models.BooleanField('需要登录', default=False)
    login_config = models.JSONField('登录配置', default=dict, blank=True)
    
    is_active = models.BooleanField('是否启用', default=True)
    priority = models.IntegerField('优先级', default=0)
    
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
        db_table = 'website_templates'
        verbose_name = '网站模板'
        verbose_name_plural = verbose_name
        ordering = ['-priority', '-created_at']

    def __str__(self):
        return self.name


class CrawlSession(models.Model):
    """
    采集会话模型 - 记录每次采集任务
    """
    name = models.CharField('会话名称', max_length=200)
    target_url = models.URLField('目标URL', max_length=1000)
    website_template = models.ForeignKey(
        WebsiteTemplate,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='网站模板',
        related_name='crawl_sessions'
    )
    
    crawl_type = models.CharField('采集类型', max_length=50, default='list',
                                   help_text='list: 列表采集, search: 搜索采集, detail: 详情采集')
    keywords = models.JSONField('搜索关键词', default=list, blank=True)
    params = models.JSONField('采集参数', default=dict, blank=True)
    
    status = models.CharField('状态', max_length=20, choices=CRAWL_SESSION_STATUS_CHOICES, default='pending')
    progress = models.IntegerField('进度百分比', default=0)
    total_pages = models.IntegerField('总页数', default=0)
    current_page = models.IntegerField('当前页', default=0)
    
    result_count = models.IntegerField('结果数量', default=0)
    error_count = models.IntegerField('错误数量', default=0)
    error_message = models.TextField('错误信息', blank=True, null=True)
    
    started_at = models.DateTimeField('开始时间', blank=True, null=True)
    finished_at = models.DateTimeField('结束时间', blank=True, null=True)
    duration = models.IntegerField('耗时(秒)', default=0)
    
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
        db_table = 'crawl_sessions'
        verbose_name = '采集会话'
        verbose_name_plural = verbose_name
        ordering = ['-created_at']

    def __str__(self):
        return self.name


class CrawlResult(models.Model):
    """
    采集结果模型 - 存储采集到的原始数据
    """
    session = models.ForeignKey(
        CrawlSession,
        on_delete=models.CASCADE,
        verbose_name='采集会话',
        related_name='results'
    )
    
    title = models.CharField('标题', max_length=500, db_index=True)
    source_url = models.URLField('来源URL', max_length=1000)
    detail_url = models.URLField('详情URL', max_length=1000, blank=True, null=True)
    
    publish_date = models.DateField('发布日期', db_index=True, blank=True, null=True)
    deadline_date = models.DateField('截止日期', blank=True, null=True)
    
    region = models.CharField('地区', max_length=100, blank=True, null=True)
    category = models.CharField('类别', max_length=100, blank=True, null=True)
    industry = models.CharField('行业', max_length=100, blank=True, null=True)
    
    budget = models.DecimalField('预算金额', max_digits=15, decimal_places=2, blank=True, null=True)
    project_code = models.CharField('项目编号', max_length=100, blank=True, null=True)
    
    purchaser_name = models.CharField('采购人名称', max_length=300, blank=True, null=True)
    purchaser_contact = models.CharField('采购人联系人', max_length=100, blank=True, null=True)
    purchaser_phone = models.CharField('采购人电话', max_length=50, blank=True, null=True)
    
    agency_name = models.CharField('代理机构名称', max_length=300, blank=True, null=True)
    agency_contact = models.CharField('代理机构联系人', max_length=100, blank=True, null=True)
    agency_phone = models.CharField('代理机构电话', max_length=50, blank=True, null=True)
    
    description = models.TextField('项目描述', blank=True, null=True)
    requirements = models.TextField('技术要求', blank=True, null=True)
    
    raw_data = models.JSONField('原始数据', default=dict, blank=True)
    extracted_fields = models.JSONField('提取字段', default=dict, blank=True,
                                         help_text='从页面提取的结构化字段')
    
    status = models.CharField('状态', max_length=20, choices=CRAWL_RESULT_STATUS_CHOICES, default='pending')
    matched_companies = models.JSONField('匹配企业', default=list, blank=True)
    
    created_at = models.DateTimeField('创建时间', default=timezone.now)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        db_table = 'crawl_results'
        verbose_name = '采集结果'
        verbose_name_plural = verbose_name
        ordering = ['-publish_date', '-created_at']
        indexes = [
            models.Index(fields=['status', 'publish_date']),
            models.Index(fields=['region', 'industry']),
        ]

    def __str__(self):
        return self.title


class CrawlLog(models.Model):
    """
    采集日志模型 - 记录采集过程中的详细日志
    """
    session = models.ForeignKey(
        CrawlSession,
        on_delete=models.CASCADE,
        verbose_name='采集会话',
        related_name='logs'
    )
    
    level = models.CharField('日志级别', max_length=10, choices=LOG_LEVEL_CHOICES, default='info')
    message = models.TextField('日志消息')
    url = models.URLField('相关URL', max_length=1000, blank=True, null=True)
    extra_data = models.JSONField('额外数据', default=dict, blank=True)
    
    created_at = models.DateTimeField('创建时间', default=timezone.now)

    class Meta:
        db_table = 'crawl_logs'
        verbose_name = '采集日志'
        verbose_name_plural = verbose_name
        ordering = ['-created_at']

    def __str__(self):
        return f'[{self.level}] {self.message[:50]}'


class FailureKnowledge(models.Model):
    """
    失败知识库模型 - 记录采集失败原因和解决方案
    """
    url = models.URLField('失败URL', max_length=1000)
    website = models.CharField('网站', max_length=200, blank=True, null=True)
    
    failure_type = models.CharField('失败类型', max_length=20, choices=FAILURE_TYPE_CHOICES, default='unknown')
    error_message = models.TextField('错误信息')
    error_stack = models.TextField('错误堆栈', blank=True, null=True)
    
    strategy_used = models.CharField('使用的策略', max_length=50, blank=True, null=True)
    retry_count = models.IntegerField('重试次数', default=0)
    
    resolution_status = models.CharField('解决状态', max_length=20, choices=RESOLUTION_STATUS_CHOICES, default='pending')
    resolution_method = models.CharField('解决方法', max_length=500, blank=True, null=True)
    resolution_notes = models.TextField('解决备注', blank=True, null=True)
    
    proxy_used = models.CharField('使用的代理', max_length=200, blank=True, null=True)
    fingerprint_used = models.JSONField('使用的指纹', default=dict, blank=True)
    
    metadata = models.JSONField('元数据', default=dict, blank=True)
    
    resolved_at = models.DateTimeField('解决时间', blank=True, null=True)
    resolved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='解决人',
        related_name='resolved_failures'
    )
    
    created_at = models.DateTimeField('创建时间', default=timezone.now)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        db_table = 'failure_knowledge'
        verbose_name = '失败知识库'
        verbose_name_plural = verbose_name
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['failure_type', 'resolution_status']),
            models.Index(fields=['website']),
        ]

    def __str__(self):
        return f'[{self.failure_type}] {self.url[:50]}'

    def mark_resolved(self, method: str, notes: str = None, user=None):
        """
        标记为已解决
        """
        self.resolution_status = 'resolved'
        self.resolution_method = method
        self.resolution_notes = notes
        self.resolved_at = timezone.now()
        if user:
            self.resolved_by = user
        self.save()


class EnterpriseVectorIndex(models.Model):
    """
    企业向量索引模型 - 记录企业向量化状态
    """
    enterprise_id = models.IntegerField('企业ID', unique=True)
    enterprise_name = models.CharField('企业名称', max_length=300)
    
    vector_text = models.TextField('向量文本', help_text='用于向量化的文本内容')
    vector_status = models.CharField('向量化状态', max_length=20, default='pending',
                                      choices=VECTOR_STATUS_CHOICES)
    
    last_indexed_at = models.DateTimeField('最后索引时间', blank=True, null=True)
    index_version = models.IntegerField('索引版本', default=1)
    
    metadata = models.JSONField('元数据', default=dict, blank=True)
    
    created_at = models.DateTimeField('创建时间', default=timezone.now)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        db_table = 'enterprise_vector_index'
        verbose_name = '企业向量索引'
        verbose_name_plural = verbose_name
        ordering = ['-updated_at']

    def __str__(self):
        return f'{self.enterprise_name} - {self.vector_status}'


class BidProjectTracking(models.Model):
    """
    已投标项目跟踪模型 - 每日自动查询中标结果
    """
    tender_title = models.CharField('项目标题', max_length=500)
    tender_url = models.URLField('项目链接', max_length=1000)
    tender_source = models.CharField('项目来源', max_length=100, blank=True, null=True)
    
    bid_date = models.DateField('投标日期')
    bid_amount = models.DecimalField('投标金额', max_digits=15, decimal_places=2, blank=True, null=True)
    bid_company = models.CharField('投标单位', max_length=300, blank=True, null=True)
    
    tracking_status = models.CharField('跟踪状态', max_length=20, choices=TRACKING_STATUS_CHOICES, default='tracking')
    
    result_announce_date = models.DateField('结果公告日期', blank=True, null=True)
    winner_name = models.CharField('中标单位', max_length=300, blank=True, null=True)
    winner_amount = models.DecimalField('中标金额', max_digits=15, decimal_places=2, blank=True, null=True)
    our_rank = models.IntegerField('我方排名', blank=True, null=True)
    
    last_checked_at = models.DateTimeField('最后检查时间', blank=True, null=True)
    check_count = models.IntegerField('检查次数', default=0)
    
    notification_sent = models.BooleanField('已发送通知', default=False)
    notification_sent_at = models.DateTimeField('通知发送时间', blank=True, null=True)
    
    remarks = models.TextField('备注', blank=True, null=True)
    extra_data = models.JSONField('额外数据', default=dict, blank=True)
    
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
        db_table = 'bid_project_tracking'
        verbose_name = '已投标项目跟踪'
        verbose_name_plural = verbose_name
        ordering = ['-bid_date', '-created_at']
        indexes = [
            models.Index(fields=['tracking_status', 'last_checked_at']),
        ]

    def __str__(self):
        return f'{self.tender_title[:30]} - {self.tracking_status}'


from .scheduler_models import CrawlSchedule, CrawlScheduleLog
