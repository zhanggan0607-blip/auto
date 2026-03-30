"""
通知管理模块 - 数据模型
"""
from django.db import models
from django.conf import settings
from django.utils import timezone

from core.constants import (
    CHANNEL_TYPE_CHOICES,
    NOTIFICATION_TYPE_CHOICES,
    PRIORITY_CHOICES,
    NOTIFICATION_STATUS_CHOICES,
)


class NotificationChannel(models.Model):
    """
    通知渠道模型
    """
    name = models.CharField('渠道名称', max_length=100)
    channel_type = models.CharField('渠道类型', max_length=20, choices=CHANNEL_TYPE_CHOICES)
    config = models.JSONField('配置信息', default=dict, blank=True)
    is_active = models.BooleanField('是否启用', default=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name='所属用户',
        related_name='notification_channels'
    )
    created_at = models.DateTimeField('创建时间', default=timezone.now)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        db_table = 'notification_channels'
        verbose_name = '通知渠道'
        verbose_name_plural = verbose_name
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.get_channel_type_display()})"


class Notification(models.Model):
    """
    通知消息模型
    """
    title = models.CharField('标题', max_length=200)
    content = models.TextField('内容')
    notification_type = models.CharField('通知类型', max_length=20, choices=NOTIFICATION_TYPE_CHOICES, default='system')
    priority = models.CharField('优先级', max_length=20, choices=PRIORITY_CHOICES, default='normal')
    
    related_object_type = models.CharField('关联对象类型', max_length=50, blank=True, null=True)
    related_object_id = models.IntegerField('关联对象ID', blank=True, null=True)
    
    is_read = models.BooleanField('是否已读', default=False)
    read_at = models.DateTimeField('阅读时间', blank=True, null=True)
    
    is_sent = models.BooleanField('是否已发送', default=False)
    sent_at = models.DateTimeField('发送时间', blank=True, null=True)
    sent_channels = models.JSONField('发送渠道', default=list, blank=True)
    
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name='接收人',
        related_name='notifications'
    )
    created_at = models.DateTimeField('创建时间', default=timezone.now)

    class Meta:
        db_table = 'notifications'
        verbose_name = '通知消息'
        verbose_name_plural = verbose_name
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recipient', 'is_read']),
            models.Index(fields=['notification_type', 'created_at']),
        ]

    def __str__(self):
        return self.title

    def mark_as_read(self):
        """
        标记为已读
        """
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save()


class NotificationTemplate(models.Model):
    """
    通知模板模型
    """
    name = models.CharField('模板名称', max_length=100)
    notification_type = models.CharField('通知类型', max_length=20, choices=NOTIFICATION_TYPE_CHOICES)
    title_template = models.CharField('标题模板', max_length=200)
    content_template = models.TextField('内容模板')
    variables = models.JSONField('模板变量', default=list, blank=True)
    is_active = models.BooleanField('是否启用', default=True)
    created_at = models.DateTimeField('创建时间', default=timezone.now)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        db_table = 'notification_templates'
        verbose_name = '通知模板'
        verbose_name_plural = verbose_name
        ordering = ['-created_at']

    def __str__(self):
        return self.name


class NotificationLog(models.Model):
    """
    通知发送日志模型
    """
    notification = models.ForeignKey(
        Notification,
        on_delete=models.CASCADE,
        verbose_name='通知消息',
        related_name='logs'
    )
    channel = models.ForeignKey(
        NotificationChannel,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='发送渠道'
    )
    status = models.CharField('状态', max_length=20, choices=NOTIFICATION_STATUS_CHOICES, default='pending')
    error_message = models.TextField('错误信息', blank=True, null=True)
    sent_at = models.DateTimeField('发送时间', blank=True, null=True)
    created_at = models.DateTimeField('创建时间', default=timezone.now)

    class Meta:
        db_table = 'notification_logs'
        verbose_name = '通知日志'
        verbose_name_plural = verbose_name
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.notification.title} - {self.get_status_display()}"
