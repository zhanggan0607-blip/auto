"""
Agent记忆持久化模型
将Agent的会话记忆持久化到数据库，支持跨会话检索
积累企业投标历史经验
"""
from django.db import models
from django.utils import timezone


class AgentMemoryStore(models.Model):
    """
    Agent记忆持久化存储
    支持按agent_type + key维度存储，跨会话可检索
    """

    SCOPE_CHOICES = [
        ('session', '会话级'),
        ('agent_type', 'Agent类型级'),
        ('enterprise', '企业级'),
        ('global', '全局'),
    ]

    agent_id = models.CharField('Agent ID', max_length=100, db_index=True)
    agent_type = models.CharField('Agent类型', max_length=50, db_index=True)
    session_id = models.CharField('会话ID', max_length=100, db_index=True, null=True, blank=True)

    scope = models.CharField('记忆范围', max_length=20, choices=SCOPE_CHOICES, default='session')
    memory_key = models.CharField('记忆键', max_length=200, db_index=True)
    memory_value = models.JSONField('记忆值', default=dict)

    enterprise_id = models.IntegerField('企业ID', null=True, blank=True, db_index=True)

    access_count = models.IntegerField('访问次数', default=0)
    last_accessed_at = models.DateTimeField('最后访问时间', null=True, blank=True)

    expires_at = models.DateTimeField('过期时间', null=True, blank=True, help_text='为空则永不过期')

    created_at = models.DateTimeField('创建时间', default=timezone.now)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        db_table = 'agent_memory_store'
        verbose_name = 'Agent记忆存储'
        verbose_name_plural = verbose_name
        ordering = ['-updated_at']
        constraints = [
            models.UniqueConstraint(
                fields=['agent_type', 'scope', 'memory_key', 'enterprise_id'],
                name='unique_agent_memory',
                condition=models.Q(enterprise_id__isnull=False),
            ),
            models.UniqueConstraint(
                fields=['agent_type', 'scope', 'memory_key'],
                name='unique_agent_memory_global',
                condition=models.Q(enterprise_id__isnull=True),
            ),
        ]
        indexes = [
            models.Index(fields=['agent_type', 'scope']),
            models.Index(fields=['enterprise_id', 'agent_type']),
            models.Index(fields=['expires_at']),
        ]

    def __str__(self):
        return f"[{self.scope}] {self.agent_type}:{self.memory_key}"

    def is_expired(self):
        if self.expires_at and self.expires_at < timezone.now():
            return True
        return False


class EnterpriseBidExperience(models.Model):
    """
    企业投标历史经验
    积累每个企业的投标经验，供Agent跨会话复用
    """

    EXPERIENCE_TYPE_CHOICES = [
        ('win_pattern', '中标模式'),
        ('loss_pattern', '失标模式'),
        ('strength', '企业优势'),
        ('weakness', '企业劣势'),
        ('pricing_strategy', '报价策略'),
        ('technical_preference', '技术偏好'),
        ('competitor_intel', '竞争对手情报'),
        ('region_preference', '区域偏好'),
    ]

    enterprise_id = models.IntegerField('企业ID', db_index=True)
    experience_type = models.CharField('经验类型', max_length=30, choices=EXPERIENCE_TYPE_CHOICES, db_index=True)

    title = models.CharField('经验标题', max_length=200)
    content = models.JSONField('经验内容', default=dict)

    source_tender_id = models.IntegerField('来源招标ID', null=True, blank=True)
    source_workflow_id = models.IntegerField('来源工作流ID', null=True, blank=True)

    confidence = models.FloatField('置信度', default=0.5, help_text='0-1')
    relevance_score = models.FloatField('相关性评分', default=0, help_text='0-100')

    usage_count = models.IntegerField('使用次数', default=0)
    last_used_at = models.DateTimeField('最后使用时间', null=True, blank=True)

    is_verified = models.BooleanField('已验证', default=False)

    created_at = models.DateTimeField('创建时间', default=timezone.now)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        db_table = 'enterprise_bid_experiences'
        verbose_name = '企业投标经验'
        verbose_name_plural = verbose_name
        ordering = ['-confidence', '-usage_count']
        indexes = [
            models.Index(fields=['enterprise_id', 'experience_type']),
            models.Index(fields=['confidence']),
        ]

    def __str__(self):
        return f"[{self.enterprise_id}] {self.get_experience_type_display()}: {self.title}"
