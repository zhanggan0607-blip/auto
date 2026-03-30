"""
企业业绩模型
"""
from django.db import models
from django.utils import timezone

from core.constants import PERFORMANCE_TYPE_CHOICES
from .base import Enterprise


class EnterprisePerformance(models.Model):
    """
    企业业绩模型 - 存储企业历史业绩
    """
    enterprise = models.ForeignKey(
        Enterprise,
        on_delete=models.CASCADE,
        verbose_name='企业',
        related_name='performances'
    )

    project_name = models.CharField('项目名称', max_length=500)
    project_code = models.CharField('项目编号', max_length=100, blank=True, null=True)
    performance_type = models.CharField('业绩类型', max_length=20,
                                        choices=PERFORMANCE_TYPE_CHOICES, default='project')

    client_name = models.CharField('业主名称', max_length=300)
    client_contact = models.CharField('业主联系人', max_length=100, blank=True, null=True)
    client_phone = models.CharField('业主电话', max_length=50, blank=True, null=True)

    contract_amount = models.DecimalField('合同金额', max_digits=15, decimal_places=2,
                                          blank=True, null=True)
    settlement_amount = models.DecimalField('结算金额', max_digits=15, decimal_places=2,
                                            blank=True, null=True)

    start_date = models.DateField('开始日期', blank=True, null=True)
    end_date = models.DateField('结束日期', blank=True, null=True)
    completion_date = models.DateField('竣工日期', blank=True, null=True)

    project_location = models.CharField('项目地点', max_length=300, blank=True, null=True)
    project_scale = models.CharField('项目规模', max_length=200, blank=True, null=True)

    project_manager = models.CharField('项目经理', max_length=100, blank=True, null=True)
    technical_director = models.CharField('技术负责人', max_length=100, blank=True, null=True)

    description = models.TextField('项目描述', blank=True, null=True)

    contract_file = models.FileField('合同文件', upload_to='performances/%Y/%m/',
                                      blank=True, null=True)
    completion_file = models.FileField('竣工文件', upload_to='performances/%Y/%m/',
                                        blank=True, null=True)

    is_verified = models.BooleanField('是否已验证', default=False)

    created_at = models.DateTimeField('创建时间', default=timezone.now)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        db_table = 'enterprise_performances'
        verbose_name = '企业业绩'
        verbose_name_plural = verbose_name
        ordering = ['-end_date', '-created_at']

    def __str__(self):
        return f'{self.enterprise.name} - {self.project_name}'