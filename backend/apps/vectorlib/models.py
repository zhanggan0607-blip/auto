"""
投标文档向量库 - 数据模型
支持用户上传和AI全网搜索的投标文档
"""
from django.db import models
from django.conf import settings
from django.utils import timezone

from core.constants import (
    VECTOR_SOURCE_TYPE_CHOICES,
    VECTOR_DOC_TYPE_CHOICES,
    VECTOR_STATUS_CHOICES,
    CRAWLER_STATUS_CHOICES,
)


class BidDocumentLibrary(models.Model):
    """
    投标文档向量库
    存储各类投标文档，支持AI语义检索
    """
    title = models.CharField('文档标题', max_length=500, db_index=True)
    document_type = models.CharField('文档类型', max_length=50, choices=VECTOR_DOC_TYPE_CHOICES, default='other')
    source_type = models.CharField('来源类型', max_length=20, choices=VECTOR_SOURCE_TYPE_CHOICES, default='upload')

    file_path = models.FileField('文档文件', upload_to='vectorlib/%Y/%m/', blank=True, null=True)
    file_size = models.BigIntegerField('文件大小(字节)', default=0)
    file_format = models.CharField('文件格式', max_length=20, blank=True, null=True)

    content_text = models.TextField('文档内容', blank=True, null=True, help_text='提取的文本内容')
    content_summary = models.TextField('内容摘要', blank=True, null=True)
    keywords = models.JSONField('关键词', default=list, blank=True)

    vector_status = models.CharField('向量化状态', max_length=20, choices=VECTOR_STATUS_CHOICES, default='pending')
    vector_id = models.CharField('向量ID', max_length=100, blank=True, null=True, help_text='向量数据库中的ID')
    vector_text = models.TextField('向量文本', blank=True, null=True, help_text='用于向量化的文本')

    source_url = models.URLField('来源URL', max_length=1000, blank=True, null=True, help_text='AI搜索来源')
    source_website = models.CharField('来源网站', max_length=200, blank=True, null=True)
    search_keyword = models.CharField('搜索关键词', max_length=200, blank=True, null=True, help_text='AI搜索使用的关键词')

    project_type = models.CharField('项目类型', max_length=100, blank=True, null=True, help_text='适用的项目类型')
    industry = models.CharField('所属行业', max_length=100, blank=True, null=True)
    region = models.CharField('适用地区', max_length=100, blank=True, null=True)

    tags = models.JSONField('标签', default=list, blank=True)
    metadata = models.JSONField('元数据', default=dict, blank=True)

    view_count = models.IntegerField('查看次数', default=0)
    use_count = models.IntegerField('使用次数', default=0, help_text='在标书制作中被引用的次数')

    quality_score = models.IntegerField('质量评分', default=0, help_text='0-100分')
    is_verified = models.BooleanField('是否已验证', default=False)
    is_featured = models.BooleanField('是否推荐', default=False)

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
        db_table = 'bid_document_library'
        verbose_name = '投标文档向量库'
        verbose_name_plural = verbose_name
        ordering = ['-quality_score', '-use_count', '-created_at']
        indexes = [
            models.Index(fields=['document_type', 'source_type']),
            models.Index(fields=['vector_status']),
            models.Index(fields=['industry', 'project_type']),
        ]

    def __str__(self):
        return self.title

    def increment_view_count(self):
        """
        增加查看次数
        """
        self.view_count += 1
        self.save(update_fields=['view_count'])

    def increment_use_count(self):
        """
        增加使用次数
        """
        self.use_count += 1
        self.save(update_fields=['use_count'])


class DocumentSearchLog(models.Model):
    """
    文档搜索日志
    记录用户搜索行为，用于优化搜索结果
    """
    query_text = models.TextField('搜索内容')
    search_type = models.CharField('搜索类型', max_length=20, default='semantic', help_text='semantic: 语义搜索, keyword: 关键词搜索')

    result_count = models.IntegerField('结果数量', default=0)
    clicked_documents = models.JSONField('点击的文档', default=list, blank=True, help_text='用户点击的文档ID列表')

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='用户'
    )
    session_id = models.CharField('会话ID', max_length=100, blank=True, null=True)

    created_at = models.DateTimeField('创建时间', default=timezone.now)

    class Meta:
        db_table = 'document_search_logs'
        verbose_name = '文档搜索日志'
        verbose_name_plural = verbose_name
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.query_text[:50]} - {self.result_count}条结果'


class AISearchTask(models.Model):
    """
    AI全网搜索任务
    """
    keyword = models.CharField('搜索关键词', max_length=200)
    keywords = models.JSONField('搜索关键词列表', default=list, blank=True)
    document_types = models.JSONField('目标文档类型列表', default=list, blank=True)
    industries = models.JSONField('目标行业列表', default=list, blank=True)

    status = models.CharField('状态', max_length=20, choices=CRAWLER_STATUS_CHOICES, default='pending')
    progress = models.IntegerField('进度', default=0)

    total_found = models.IntegerField('发现文档数', default=0)
    saved_count = models.IntegerField('保存文档数', default=0)

    search_config = models.JSONField('搜索配置', default=dict, blank=True)
    search_results = models.JSONField('搜索结果', default=list, blank=True)

    error_message = models.TextField('错误信息', blank=True, null=True)

    started_at = models.DateTimeField('开始时间', blank=True, null=True)
    completed_at = models.DateTimeField('完成时间', blank=True, null=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='创建人'
    )
    created_at = models.DateTimeField('创建时间', default=timezone.now)

    class Meta:
        db_table = 'ai_search_tasks'
        verbose_name = 'AI搜索任务'
        verbose_name_plural = verbose_name
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.keyword} - {self.get_status_display()}'
