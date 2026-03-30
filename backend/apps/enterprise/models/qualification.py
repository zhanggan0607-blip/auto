"""
企业资质模型
"""
from django.db import models
from django.utils import timezone

from core.constants import QUALIFICATION_CATEGORY_CHOICES, QUALIFICATION_NAME_CHOICES
from .base import Enterprise


class EnterpriseQualification(models.Model):
    """
    企业资质模型 - 存储企业资质证书信息
    """
    enterprise = models.ForeignKey(
        Enterprise,
        on_delete=models.CASCADE,
        verbose_name='企业',
        related_name='qualifications'
    )

    qualification_category = models.CharField('资质类别', max_length=50,
                                             choices=QUALIFICATION_CATEGORY_CHOICES,
                                             default='construction')
    qualification_name = models.CharField('资质名称', max_length=50,
                                          choices=QUALIFICATION_NAME_CHOICES)
    certificate_no = models.CharField('资质证书号', max_length=100, blank=True, null=True)

    grade = models.CharField('资质等级', max_length=50, blank=True, null=True)

    issue_date = models.DateField('发证日期', blank=True, null=True)
    expiry_date = models.DateField('有效期至', blank=True, null=True)
    issuing_authority = models.CharField('发证机关', max_length=200, blank=True, null=True)

    certificate_file = models.FileField('证书文件', upload_to='qualifications/%Y/%m/',
                                        blank=True, null=True)

    is_valid = models.BooleanField('是否有效', default=True)
    is_primary = models.BooleanField('是否主要资质', default=False)

    remarks = models.TextField('备注', blank=True, null=True)

    created_at = models.DateTimeField('创建时间', default=timezone.now)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        db_table = 'enterprise_qualifications'
        verbose_name = '企业资质'
        verbose_name_plural = verbose_name
        ordering = ['-is_primary', '-expiry_date']

    def __str__(self):
        return f'{self.enterprise.name} - {self.get_qualification_name_display()}'