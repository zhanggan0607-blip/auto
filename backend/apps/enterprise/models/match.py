"""
企业匹配规则与结果模型
"""
from django.db import models
from django.utils import timezone

from core.constants import MATCH_RULE_TYPE_CHOICES
from .base import Enterprise


class EnterpriseMatchRule(models.Model):
    """
    企业匹配规则模型 - 配置企业信息与招标信息的匹配规则
    """
    enterprise = models.ForeignKey(
        Enterprise,
        on_delete=models.CASCADE,
        verbose_name='企业',
        related_name='match_rules'
    )

    name = models.CharField('规则名称', max_length=200)
    rule_type = models.CharField('规则类型', max_length=20, choices=MATCH_RULE_TYPE_CHOICES)

    keywords = models.JSONField('关键词列表', default=list, blank=True)
    industries = models.JSONField('行业列表', default=list, blank=True)
    regions = models.JSONField('地区列表', default=list, blank=True)

    qualification_requirements = models.JSONField('资质要求', default=list, blank=True)
    performance_requirements = models.JSONField('业绩要求', default=dict, blank=True)

    budget_min = models.DecimalField('最小金额', max_digits=15, decimal_places=2,
                                  blank=True, null=True)
    budget_max = models.DecimalField('最大金额', max_digits=15, decimal_places=2,
                                  blank=True, null=True)

    weight = models.IntegerField('权重', default=1)
    priority = models.IntegerField('优先级', default=0)

    is_active = models.BooleanField('是否启用', default=True)

    created_at = models.DateTimeField('创建时间', default=timezone.now)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        db_table = 'enterprise_match_rules'
        verbose_name = '企业匹配规则'
        verbose_name_plural = verbose_name
        ordering = ['-priority', '-weight', 'name']

    def __str__(self):
        return f'{self.enterprise.name} - {self.name}'


class EnterpriseMatchResult(models.Model):
    """
    企业匹配结果模型 - 记录企业与招标信息的匹配结果
    """
    enterprise = models.ForeignKey(
        Enterprise,
        on_delete=models.CASCADE,
        verbose_name='企业',
        related_name='match_results'
    )

    tender_title = models.CharField('招标标题', max_length=500)
    tender_url = models.URLField('招标链接', max_length=1000)
    tender_source = models.CharField('招标来源', max_length=100, blank=True, null=True)

    publish_date = models.DateField('发布日期', blank=True, null=True)
    deadline_date = models.DateField('截止日期', blank=True, null=True)

    matched_keywords = models.JSONField('匹配关键词', default=list, blank=True)
    matched_industries = models.JSONField('匹配行业', default=list, blank=True)
    matched_regions = models.JSONField('匹配地区', default=list, blank=True)

    match_score = models.FloatField('匹配得分', default=0)
    match_level = models.CharField('匹配等级', max_length=20, default='low',
                                  help_text='high: 高度匹配, medium: 中度匹配, low: 低度匹配')

    matched_rules = models.JSONField('匹配规则', default=list, blank=True)

    tender_data = models.JSONField('招标数据', default=dict, blank=True)

    is_read = models.BooleanField('是否已读', default=False)
    is_favorite = models.BooleanField('是否收藏', default=False)
    is_applied = models.BooleanField('是否已投标', default=False)

    remarks = models.TextField('备注', blank=True, null=True)

    created_at = models.DateTimeField('创建时间', default=timezone.now)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        db_table = 'enterprise_match_results'
        verbose_name = '企业匹配结果'
        verbose_name_plural = verbose_name
        ordering = ['-match_score', '-publish_date', '-created_at']
        indexes = [
            models.Index(fields=['enterprise', 'match_level']),
            models.Index(fields=['publish_date']),
        ]

    def __str__(self):
        return f'{self.enterprise.name} - {self.tender_title[:50]}'