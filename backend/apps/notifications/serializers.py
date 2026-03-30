"""
通知管理模块 - 序列化器
"""
from rest_framework import serializers
from .models import NotificationChannel, Notification, NotificationTemplate, NotificationLog


class NotificationChannelSerializer(serializers.ModelSerializer):
    """
    通知渠道序列化器
    """
    channel_type_display = serializers.CharField(source='get_channel_type_display', read_only=True)

    class Meta:
        model = NotificationChannel
        fields = [
            'id', 'name', 'channel_type', 'channel_type_display', 
            'config', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class NotificationSerializer(serializers.ModelSerializer):
    """
    通知消息序列化器
    """
    notification_type_display = serializers.CharField(source='get_notification_type_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    recipient_name = serializers.CharField(source='recipient.username', read_only=True)

    class Meta:
        model = Notification
        fields = [
            'id', 'title', 'content', 'notification_type', 'notification_type_display',
            'priority', 'priority_display', 'related_object_type', 'related_object_id',
            'is_read', 'read_at', 'is_sent', 'sent_at', 'sent_channels',
            'recipient', 'recipient_name', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class NotificationCreateSerializer(serializers.Serializer):
    """
    通知创建序列化器
    """
    recipient_ids = serializers.ListField(
        child=serializers.IntegerField(),
        help_text='接收人ID列表'
    )
    title = serializers.CharField(max_length=200)
    content = serializers.CharField()
    notification_type = serializers.CharField(max_length=20, default='system')
    priority = serializers.CharField(max_length=20, default='normal')
    related_object_type = serializers.CharField(max_length=50, required=False)
    related_object_id = serializers.IntegerField(required=False)
    send_immediately = serializers.BooleanField(default=True)
    channels = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        help_text='发送渠道列表'
    )


class NotificationTemplateSerializer(serializers.ModelSerializer):
    """
    通知模板序列化器
    """
    notification_type_display = serializers.CharField(source='get_notification_type_display', read_only=True)

    class Meta:
        model = NotificationTemplate
        fields = [
            'id', 'name', 'notification_type', 'notification_type_display',
            'title_template', 'content_template', 'variables', 'is_active',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class NotificationLogSerializer(serializers.ModelSerializer):
    """
    通知日志序列化器
    """
    notification_title = serializers.CharField(source='notification.title', read_only=True)
    channel_name = serializers.CharField(source='channel.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = NotificationLog
        fields = [
            'id', 'notification', 'notification_title', 'channel', 'channel_name',
            'status', 'status_display', 'error_message', 'sent_at', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class NotificationStatsSerializer(serializers.Serializer):
    """
    通知统计序列化器
    """
    total = serializers.IntegerField()
    unread = serializers.IntegerField()
    by_type = serializers.DictField()
    by_priority = serializers.DictField()
