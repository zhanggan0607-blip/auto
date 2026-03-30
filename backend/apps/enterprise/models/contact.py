"""
企业联系人模型
"""
from django.db import models
from django.utils import timezone

from core.constants import CONTACT_TYPE_CHOICES
from .base import Enterprise


class EnterpriseContact(models.Model):
    """
    企业联系人模型 - 存储企业多个联系人信息
    """
    enterprise = models.ForeignKey(
        Enterprise,
        on_delete=models.CASCADE,
        verbose_name='企业',
        related_name='contacts'
    )

    contact_type = models.CharField('联系人类型', max_length=20,
                                    choices=CONTACT_TYPE_CHOICES, default='business')
    name = models.CharField('姓名', max_length=100)
    position = models.CharField('职位', max_length=100, blank=True, null=True)
    department = models.CharField('部门', max_length=100, blank=True, null=True)

    phone = models.CharField('电话', max_length=50, blank=True, null=True)
    mobile = models.CharField('手机', max_length=50, blank=True, null=True)
    email = models.EmailField('邮箱', max_length=100, blank=True, null=True)
    wechat = models.CharField('微信', max_length=100, blank=True, null=True)

    is_primary = models.BooleanField('是否主要联系人', default=False)
    is_active = models.BooleanField('是否有效', default=True)

    remarks = models.TextField('备注', blank=True, null=True)

    created_at = models.DateTimeField('创建时间', default=timezone.now)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        db_table = 'enterprise_contacts'
        verbose_name = '企业联系人'
        verbose_name_plural = verbose_name
        ordering = ['-is_primary', 'name']

    def __str__(self):
        return f'{self.enterprise.name} - {self.name}'