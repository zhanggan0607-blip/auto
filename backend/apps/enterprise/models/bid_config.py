"""
企业投标配置模型
"""
from django.db import models
from django.utils import timezone

from core.constants import BUILDER_LEVEL_CHOICES
from .base import Enterprise


class EnterpriseBidConfig(models.Model):
    """
    企业投标配置模型 - 存储企业投标相关的配置信息
    """
    enterprise = models.OneToOneField(
        Enterprise,
        on_delete=models.CASCADE,
        verbose_name='企业',
        related_name='bid_config'
    )

    accept_consortium = models.BooleanField('是否接受联合体投标', default=True)

    builder_level = models.CharField('建造师等级', max_length=20, choices=BUILDER_LEVEL_CHOICES, blank=True, null=True)
    builder_majors = models.JSONField('建造师专业', default=list, blank=True)
    no_ongoing_project = models.BooleanField('是否要求无在建项目', default=False)
    need_similar_performance = models.BooleanField('是否需要类似业绩', default=False)
    similar_performance_desc = models.TextField('类似业绩描述', blank=True, null=True)
    need_safety_certificate_b = models.BooleanField('是否需要安全生产考核合格证B证', default=True)
    other_personnel_requirements = models.TextField('其他人员要求', blank=True, null=True)

    need_safety_license = models.BooleanField('是否需要有效的安全生产许可证', default=True)

    performance_years = models.IntegerField('业绩年限', blank=True, null=True, help_text='近X年内')
    min_contract_amount = models.DecimalField('最低合同金额', max_digits=15, decimal_places=2, blank=True, null=True, help_text='万元')
    min_building_area = models.DecimalField('最低建筑面积', max_digits=12, decimal_places=2, blank=True, null=True, help_text='平方米')
    structure_types = models.JSONField('结构类型', default=list, blank=True)
    other_performance_features = models.TextField('其他业绩特征描述', blank=True, null=True)

    need_audit_report = models.BooleanField('是否需要近三年审计报告', default=True)
    min_net_assets = models.DecimalField('最低净资产要求', max_digits=15, decimal_places=2, blank=True, null=True, help_text='万元')
    max_debt_ratio = models.DecimalField('资产负债率上限', max_digits=5, decimal_places=2, blank=True, null=True, help_text='百分比')
    min_credit_line = models.DecimalField('最低银行授信额度', max_digits=15, decimal_places=2, blank=True, null=True, help_text='万元')
    min_working_capital = models.DecimalField('最低流动资金要求', max_digits=15, decimal_places=2, blank=True, null=True, help_text='万元')

    no_bad_credit = models.BooleanField('是否要求无不良信用记录', default=True)
    no_bribery_record = models.BooleanField('是否要求无行贿犯罪记录', default=True)
    not_in_blacklist = models.BooleanField('是否要求不在建筑市场黑名单', default=True)
    other_reputation_requirements = models.TextField('其他信誉要求', blank=True, null=True)

    min_registered_capital = models.DecimalField('企业注册资金下限', max_digits=15, decimal_places=2, blank=True, null=True, help_text='万元')
    need_general_taxpayer = models.BooleanField('是否要求一般纳税人资格', default=False)
    company_certifications = models.JSONField('体系认证', default=list, blank=True, help_text='质量/环境/职业健康体系认证')
    equipment_requirements = models.TextField('特定机械/设备要求', blank=True, null=True)

    notes = models.TextField('备注', blank=True, null=True)

    created_at = models.DateTimeField('创建时间', default=timezone.now)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        db_table = 'enterprise_bid_configs'
        verbose_name = '企业投标配置'
        verbose_name_plural = verbose_name

    def __str__(self):
        return f'{self.enterprise.name} - 投标配置'
