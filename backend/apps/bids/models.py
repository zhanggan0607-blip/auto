"""
投标管理模块 - 数据模型
"""
from django.db import models
from django.conf import settings
from django.utils import timezone

from core.constants import (
    BID_STATUS_CHOICES,
    RESULT_TYPE_CHOICES,
)


class BidRecord(models.Model):
    """
    投标记录模型
    """
    tender = models.OneToOneField(
        'tenders.TenderProject',
        on_delete=models.CASCADE,
        verbose_name='招标项目',
        related_name='bid_record'
    )
    bid_code = models.CharField('投标编号', max_length=100, blank=True, null=True)
    bid_price = models.DecimalField('投标报价', max_digits=15, decimal_places=2, blank=True, null=True)
    bid_date = models.DateField('投标日期', blank=True, null=True)
    
    status = models.CharField('状态', max_length=20, choices=BID_STATUS_CHOICES, default='preparing')
    bid_documents = models.ManyToManyField(
        'documents.GeneratedDocument',
        verbose_name='投标文件',
        blank=True,
        related_name='bid_records'
    )
    
    bid_manager = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='投标负责人',
        related_name='managed_bids'
    )
    team_members = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        verbose_name='团队成员',
        blank=True,
        related_name='participated_bids'
    )
    
    notes = models.TextField('备注', blank=True, null=True)
    win_probability = models.IntegerField('中标概率', blank=True, null=True, help_text='0-100之间的整数')
    competitor_count = models.IntegerField('竞争对手数量', blank=True, null=True)
    
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='创建人',
        related_name='created_bid_records'
    )
    created_at = models.DateTimeField('创建时间', default=timezone.now)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        db_table = 'bid_records'
        verbose_name = '投标记录'
        verbose_name_plural = verbose_name
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.tender.title} - {self.get_status_display()}"


class BidResult(models.Model):
    """
    中标结果模型
    """
    bid_record = models.OneToOneField(
        BidRecord,
        on_delete=models.CASCADE,
        verbose_name='投标记录',
        related_name='result'
    )
    result_type = models.CharField('结果类型', max_length=20, choices=RESULT_TYPE_CHOICES, default='pending')
    
    winner_name = models.CharField('中标单位', max_length=300, blank=True, null=True)
    winner_price = models.DecimalField('中标金额', max_digits=15, decimal_places=2, blank=True, null=True)
    our_rank = models.IntegerField('我方排名', blank=True, null=True)
    total_bidders = models.IntegerField('投标单位数量', blank=True, null=True)
    
    announce_date = models.DateField('公告日期', blank=True, null=True)
    announce_url = models.URLField('公告链接', max_length=1000, blank=True, null=True)
    
    win_reason = models.TextField('中标原因', blank=True, null=True)
    lose_reason = models.TextField('未中标原因', blank=True, null=True)
    lessons_learned = models.TextField('经验教训', blank=True, null=True)
    
    raw_data = models.JSONField('原始数据', default=dict, blank=True)
    
    created_at = models.DateTimeField('创建时间', default=timezone.now)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        db_table = 'bid_results'
        verbose_name = '中标结果'
        verbose_name_plural = verbose_name
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.bid_record.tender.title} - {self.get_result_type_display()}"


class BidStatistics(models.Model):
    """
    投标统计模型
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name='用户',
        related_name='bid_statistics'
    )
    
    total_bids = models.IntegerField('总投标次数', default=0)
    won_bids = models.IntegerField('中标次数', default=0)
    lost_bids = models.IntegerField('未中标次数', default=0)
    pending_bids = models.IntegerField('待定次数', default=0)
    
    total_bid_amount = models.DecimalField('总投标金额', max_digits=18, decimal_places=2, default=0)
    total_win_amount = models.DecimalField('总中标金额', max_digits=18, decimal_places=2, default=0)
    
    win_rate = models.DecimalField('中标率', max_digits=5, decimal_places=2, default=0)
    
    year = models.IntegerField('统计年份', default=timezone.now().year)
    month = models.IntegerField('统计月份', blank=True, null=True)
    
    created_at = models.DateTimeField('创建时间', default=timezone.now)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        db_table = 'bid_statistics'
        verbose_name = '投标统计'
        verbose_name_plural = verbose_name
        ordering = ['-year', '-month']

    def __str__(self):
        return f"{self.user.username} - {self.year}年统计"

    def calculate_win_rate(self):
        """
        计算中标率
        """
        if self.total_bids > 0:
            self.win_rate = (self.won_bids / self.total_bids) * 100
        else:
            self.win_rate = 0
        return self.win_rate
