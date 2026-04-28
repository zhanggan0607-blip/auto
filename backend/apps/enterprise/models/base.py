"""
企业核心模型
"""
from django.db import models
from django.conf import settings
from django.utils import timezone

from core.constants import ENTERPRISE_TYPE_CHOICES


class Enterprise(models.Model):
    """
    企业模型 - 存储企业基本信息
    """
    name = models.CharField('企业名称', max_length=300, db_index=True)
    enterprise_type = models.CharField('企业类型', max_length=25,
                                        choices=ENTERPRISE_TYPE_CHOICES, blank=True, null=True)

    credit_code = models.CharField('统一社会信用代码', max_length=50, blank=True, null=True, unique=True)

    legal_person = models.CharField('法人代表', max_length=100, blank=True, null=True)
    registered_capital = models.DecimalField('注册资本', max_digits=15, decimal_places=2,
                                             blank=True, null=True)
    establishment_date = models.DateField('成立日期', blank=True, null=True)

    province = models.CharField('省份', max_length=50, blank=True, null=True)
    city = models.CharField('城市', max_length=50, blank=True, null=True)
    district = models.CharField('区县', max_length=50, blank=True, null=True)
    address = models.CharField('详细地址', max_length=500, blank=True, null=True)

    contact_person = models.CharField('联系人', max_length=100, blank=True, null=True)
    contact_phone = models.CharField('联系电话', max_length=50, blank=True, null=True)
    contact_email = models.EmailField('联系邮箱', max_length=100, blank=True, null=True)

    business_scope = models.TextField('经营范围', blank=True, null=True)

    enterprise_scale = models.CharField('企业规模', max_length=50, blank=True, null=True, help_text='大型/中型/小型/微型')
    staff_count = models.IntegerField('员工人数', blank=True, null=True)
    insured_count = models.IntegerField('参保人数', blank=True, null=True)

    bank_name = models.CharField('开户银行', max_length=200, blank=True, null=True)
    bank_account = models.CharField('银行账号', max_length=100, blank=True, null=True)

    is_active = models.BooleanField('是否有效', default=True)
    is_verified = models.BooleanField('是否已验证', default=False)

    auto_bid_enabled = models.BooleanField('是否启用自动投标', default=False)
    auto_bid_threshold = models.IntegerField('自动投标阈值', default=60, help_text='推荐分数达到此阈值自动投标')
    auto_upload_enabled = models.BooleanField('是否启用自动上传', default=False)
    auto_bid_keywords = models.JSONField('自动投标关键词', default=list, blank=True)
    notification_channels = models.JSONField('通知渠道', default=list, blank=True)

    tags = models.JSONField('标签', default=list, blank=True)
    extra_info = models.JSONField('扩展信息', default=dict, blank=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='创建人',
        related_name='created_enterprises'
    )
    created_at = models.DateTimeField('创建时间', default=timezone.now)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        db_table = 'enterprises'
        verbose_name = '企业'
        verbose_name_plural = verbose_name
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['province', 'city']),
        ]

    def __str__(self):
        return self.name