"""
标书质量反馈学习模型
记录标书审核反馈、投标结果，并自动提取生成策略
"""
from django.db import models
from django.conf import settings
from django.utils import timezone


class BidFeedbackRecord(models.Model):
    """
    标书反馈记录
    记录每次标书审核/投标结果的反馈数据
    """

    BID_RESULT_CHOICES = [
        ('won', '中标'),
        ('lost', '未中标'),
        ('rejected', '废标'),
        ('pending', '待定'),
    ]

    tender_id = models.IntegerField('招标项目ID')
    enterprise_id = models.IntegerField('企业ID', null=True, blank=True)
    workflow_id = models.IntegerField('工作流ID', null=True, blank=True)

    bid_result = models.CharField('投标结果', max_length=20, choices=BID_RESULT_CHOICES, default='pending')

    overall_score = models.IntegerField('总体评分', default=0, help_text='0-100')
    compliance_score = models.IntegerField('合规性评分', default=0)
    completeness_score = models.IntegerField('完整性评分', default=0)
    quality_score = models.IntegerField('质量评分', default=0)
    competitiveness_score = models.IntegerField('竞争力评分', default=0)

    weaknesses = models.JSONField('待改进点', default=list, blank=True)
    suggestions = models.JSONField('优化建议', default=list, blank=True)

    document_sections_summary = models.JSONField('文档章节摘要', default=list, blank=True)

    rejection_reason = models.TextField('废标/被拒原因', blank=True, null=True)

    is_learned = models.BooleanField('是否已学习', default=False, help_text='是否已提取策略')

    created_at = models.DateTimeField('创建时间', default=timezone.now)

    class Meta:
        db_table = 'bid_feedback_records'
        verbose_name = '标书反馈记录'
        verbose_name_plural = verbose_name
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['tender_id']),
            models.Index(fields=['bid_result', 'created_at']),
            models.Index(fields=['overall_score']),
        ]

    def __str__(self):
        return f"反馈 tender={self.tender_id} score={self.overall_score} result={self.bid_result}"


class GenerationStrategy(models.Model):
    """
    生成策略
    从反馈记录中自动提取的标书生成优化策略
    """

    CATEGORY_CHOICES = [
        ('rejection_prevention', '废标预防'),
        ('quality_critical', '质量关键提升'),
        ('compliance_improvement', '合规性改进'),
        ('completeness_improvement', '完整性补全'),
        ('content_quality', '内容质量优化'),
        ('competitiveness_boost', '竞争力增强'),
        ('general_optimization', '通用优化'),
    ]

    category = models.CharField('策略分类', max_length=50, choices=CATEGORY_CHOICES, db_index=True)
    name = models.CharField('策略名称', max_length=200)
    description = models.TextField('策略描述', blank=True)

    optimization_rules = models.JSONField('优化规则', default=list, blank=True, help_text='提取的优化规则列表')

    feedback_count = models.IntegerField('反馈样本数', default=0)
    average_score = models.FloatField('平均评分', default=0)
    success_count = models.IntegerField('成功次数', default=0)
    failure_count = models.IntegerField('失败次数', default=0)
    effectiveness_score = models.FloatField('有效性评分', default=0, help_text='0-100, 基于成功率')

    last_feedback_at = models.DateTimeField('最近反馈时间', null=True, blank=True)

    is_active = models.BooleanField('是否启用', default=True)

    created_at = models.DateTimeField('创建时间', default=timezone.now)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        db_table = 'generation_strategies'
        verbose_name = '生成策略'
        verbose_name_plural = verbose_name
        ordering = ['-effectiveness_score', '-feedback_count']
        indexes = [
            models.Index(fields=['category', 'is_active']),
            models.Index(fields=['effectiveness_score']),
        ]

    def __str__(self):
        return f"{self.name} (有效性: {self.effectiveness_score}%)"


class StrategyLearningLog(models.Model):
    """
    策略学习日志
    记录每次从反馈中提取策略的过程
    """

    LEARNING_TYPE_CHOICES = [
        ('auto_extract', '自动提取'),
        ('manual_update', '手动更新'),
        ('batch_learning', '批量学习'),
    ]

    strategy = models.ForeignKey(
        GenerationStrategy,
        on_delete=models.CASCADE,
        verbose_name='关联策略',
        related_name='learning_logs'
    )

    feedback_record = models.ForeignKey(
        BidFeedbackRecord,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='关联反馈记录',
        related_name='learning_logs'
    )

    learning_type = models.CharField('学习类型', max_length=20, choices=LEARNING_TYPE_CHOICES, default='auto_extract')

    extracted_rules = models.JSONField('提取的规则', default=list, blank=True)
    confidence = models.FloatField('置信度', default=0, help_text='0-1, 学习结果的置信度')

    created_at = models.DateTimeField('创建时间', default=timezone.now)

    class Meta:
        db_table = 'strategy_learning_logs'
        verbose_name = '策略学习日志'
        verbose_name_plural = verbose_name
        ordering = ['-created_at']

    def __str__(self):
        return f"学习日志 strategy={self.strategy_id} confidence={self.confidence}"
