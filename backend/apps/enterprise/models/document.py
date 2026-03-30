"""
企业证书文档模型
"""
from django.db import models
from django.conf import settings
from django.utils import timezone

from core.constants import ENTERPRISE_DOC_TYPE_CHOICES, ENTERPRISE_DOC_STATUS_CHOICES, AUDIT_ACTION_TYPE_CHOICES
from .base import Enterprise


class EnterpriseDocument(models.Model):
    """
    企业证书资料模型 - 集中管理企业各类证书资料
    包括：营业执照、资质证书、荣誉证书、合同复印件等
    支持双用途：AI招标公告比对 + 标书生成素材
    """
    DOCUMENT_TYPE_CHOICES = ENTERPRISE_DOC_TYPE_CHOICES
    DOCUMENT_STATUS_CHOICES = ENTERPRISE_DOC_STATUS_CHOICES

    enterprise = models.ForeignKey(
        Enterprise,
        on_delete=models.CASCADE,
        verbose_name='企业',
        related_name='documents'
    )

    document_type = models.CharField('证书类型', max_length=50, choices=ENTERPRISE_DOC_TYPE_CHOICES)
    document_name = models.CharField('证书名称', max_length=200)
    document_no = models.CharField('证书编号', max_length=100, blank=True, null=True)

    issue_date = models.DateField('发证日期', blank=True, null=True)
    expiry_date = models.DateField('有效期至', blank=True, null=True)
    issuing_authority = models.CharField('发证机关', max_length=200, blank=True, null=True)

    file_path = models.FileField('证书文件', upload_to='enterprise_docs/%Y/%m/', blank=True, null=True)
    file_size = models.BigIntegerField('文件大小', blank=True, null=True, help_text='字节')
    file_type = models.CharField('文件类型', max_length=50, blank=True, null=True, help_text='MIME类型')

    status = models.CharField('状态', max_length=20, choices=ENTERPRISE_DOC_STATUS_CHOICES, default='valid')

    description = models.TextField('描述', blank=True, null=True)
    tags = models.JSONField('标签', default=list, blank=True)

    is_primary = models.BooleanField('是否主要证书', default=False)
    is_verified = models.BooleanField('是否已验证', default=False)

    remind_days = models.IntegerField('提前提醒天数', default=30, help_text='过期前多少天提醒')
    last_remind_date = models.DateField('上次提醒日期', blank=True, null=True)

    extracted_content = models.TextField('提取内容', blank=True, null=True, help_text='OCR/文本提取的内容')
    extracted_data = models.JSONField('提取数据', default=dict, blank=True, help_text='结构化提取数据')
    recognition_status = models.CharField('识别状态', max_length=20, default='pending',
                                         help_text='pending: 待识别, processing: 识别中, completed: 已完成, failed: 识别失败')
    recognition_error = models.TextField('识别错误信息', blank=True, null=True)
    recognition_at = models.DateField('识别时间', blank=True, null=True)

    comparison_result = models.JSONField('比对结果', default=dict, blank=True, help_text='与数据库比对的结果')
    comparison_at = models.DateTimeField('比对时间', blank=True, null=True)

    is_ai_reference = models.BooleanField('是否用于AI比对', default=True, help_text='作为AI招标公告比对的参考数据')
    is_bid_material = models.BooleanField('是否用于标书生成', default=True, help_text='作为标书生成的素材')

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='上传人',
        related_name='uploaded_enterprise_documents'
    )
    created_at = models.DateTimeField('创建时间', default=timezone.now)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        db_table = 'enterprise_documents'
        verbose_name = '企业证书'
        verbose_name_plural = verbose_name
        ordering = ['-is_primary', 'document_type', '-expiry_date']
        indexes = [
            models.Index(fields=['enterprise', 'document_type']),
            models.Index(fields=['status']),
            models.Index(fields=['expiry_date']),
            models.Index(fields=['recognition_status']),
        ]

    def __str__(self):
        return f'{self.enterprise.name} - {self.document_name}'

    def check_status(self):
        """检查文档状态"""
        from datetime import date, timedelta

        if not self.expiry_date:
            return 'valid'

        today = date.today()

        if self.expiry_date < today:
            return 'expired'
        elif self.expiry_date <= today + timedelta(days=self.remind_days):
            return 'expiring'
        else:
            return 'valid'

    def save(self, *args, **kwargs):
        """保存时自动更新状态"""
        self.status = self.check_status()
        super().save(*args, **kwargs)

    @property
    def days_to_expiry(self):
        """距离过期的天数"""
        if not self.expiry_date:
            return None
        from datetime import date
        delta = self.expiry_date - date.today()
        return delta.days

    @property
    def file_url(self):
        """获取文件URL"""
        if self.file_path:
            return self.file_path.url
        return None

    @property
    def file_size_display(self):
        """获取文件大小显示"""
        if not self.file_size:
            return '-'

        if self.file_size < 1024:
            return f'{self.file_size}B'
        elif self.file_size < 1024 * 1024:
            return f'{self.file_size / 1024:.1f}KB'
        elif self.file_size < 1024 * 1024 * 1024:
            return f'{self.file_size / 1024 / 1024:.1f}MB'
        else:
            return f'{self.file_size / 1024 / 1024 / 1024:.1f}GB'


class DocumentAuditLog(models.Model):
    """
    证书资料审计日志模型 - 记录所有操作以便追溯
    """
    document = models.ForeignKey(
        EnterpriseDocument,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='证书',
        related_name='audit_logs'
    )

    action_type = models.CharField('操作类型', max_length=20, choices=AUDIT_ACTION_TYPE_CHOICES)
    action_detail = models.TextField('操作详情', blank=True, null=True)

    old_data = models.JSONField('修改前数据', default=dict, blank=True)
    new_data = models.JSONField('修改后数据', default=dict, blank=True)

    recognition_result = models.JSONField('识别结果', default=dict, blank=True)
    comparison_result = models.JSONField('比对结果', default=dict, blank=True)
    update_result = models.JSONField('更新结果', default=dict, blank=True)

    is_success = models.BooleanField('是否成功', default=True)
    error_message = models.TextField('错误信息', blank=True, null=True)

    ip_address = models.CharField('IP地址', max_length=50, blank=True, null=True)
    user_agent = models.CharField('用户代理', max_length=500, blank=True, null=True)

    operated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='操作人',
        related_name='document_audit_logs'
    )
    operated_at = models.DateTimeField('操作时间', default=timezone.now)

    class Meta:
        db_table = 'document_audit_logs'
        verbose_name = '证书审计日志'
        verbose_name_plural = verbose_name
        ordering = ['-operated_at']
        indexes = [
            models.Index(fields=['document', 'action_type']),
            models.Index(fields=['operated_at']),
        ]

    def __str__(self):
        doc_name = self.document.document_name if self.document else '已删除'
        return f'{doc_name} - {self.get_action_type_display()} - {self.operated_at}'