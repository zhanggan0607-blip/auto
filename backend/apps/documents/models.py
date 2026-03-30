"""
文档管理模块 - 数据模型
"""
from django.db import models
from django.conf import settings
from django.utils import timezone

from core.constants import (
    TEMPLATE_TYPE_CHOICES,
    DOCUMENT_STATUS_CHOICES,
    BUILDER_LEVEL_CHOICES,
)


class DocumentTemplate(models.Model):
    """
    文档模板模型
    """
    name = models.CharField('模板名称', max_length=200)
    template_type = models.CharField('模板类型', max_length=50, choices=TEMPLATE_TYPE_CHOICES, default='bid_document')
    description = models.TextField('模板描述', blank=True, null=True)
    file_path = models.FileField('模板文件', upload_to='templates/%Y/%m/')
    variables = models.JSONField('模板变量', default=list, blank=True, help_text='模板中可替换的变量列表')
    is_active = models.BooleanField('是否启用', default=True)
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
        db_table = 'document_templates'
        verbose_name = '文档模板'
        verbose_name_plural = verbose_name
        ordering = ['-created_at']

    def __str__(self):
        return self.name


class GeneratedDocument(models.Model):
    """
    生成的文档模型
    支持关联向量库中的参考文档，实现知识库与生产线的协作
    """
    name = models.CharField('文档名称', max_length=200)
    template = models.ForeignKey(
        DocumentTemplate,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='使用模板',
        related_name='generated_docs'
    )
    tender = models.ForeignKey(
        'tenders.TenderProject',
        on_delete=models.CASCADE,
        verbose_name='关联招标项目',
        related_name='documents'
    )
    reference_docs = models.ManyToManyField(
        'vectorlib.BidDocumentLibrary',
        blank=True,
        verbose_name='参考文档',
        related_name='referenced_by',
        help_text='从向量库引用的参考文档'
    )
    file_path = models.FileField('文档文件', upload_to='generated_docs/%Y/%m/', blank=True, null=True)
    pdf_path = models.FileField('PDF文件', upload_to='generated_pdfs/%Y/%m/', blank=True, null=True)
    variables_data = models.JSONField('变量数据', default=dict, blank=True)
    ai_suggestions = models.JSONField('AI建议', default=dict, blank=True, help_text='基于参考文档生成的AI建议内容')
    status = models.CharField('状态', max_length=20, choices=DOCUMENT_STATUS_CHOICES, default='draft')
    version = models.IntegerField('版本号', default=1)
    notes = models.TextField('备注', blank=True, null=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='创建人',
        related_name='created_documents'
    )
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='审核人',
        related_name='reviewed_documents'
    )
    reviewed_at = models.DateTimeField('审核时间', blank=True, null=True)
    created_at = models.DateTimeField('创建时间', default=timezone.now)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        db_table = 'generated_documents'
        verbose_name = '生成文档'
        verbose_name_plural = verbose_name
        ordering = ['-created_at']

    def __str__(self):
        return self.name

