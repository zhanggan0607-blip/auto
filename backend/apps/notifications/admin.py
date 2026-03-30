from django.contrib import admin
from .models import NotificationChannel, Notification, NotificationTemplate, NotificationLog


@admin.register(NotificationChannel)
class NotificationChannelAdmin(admin.ModelAdmin):
    list_display = ['name', 'channel_type', 'is_active', 'user', 'created_at']
    list_filter = ['channel_type', 'is_active']
    search_fields = ['name', 'user__username']


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['title', 'notification_type', 'priority', 'recipient', 'is_read', 'is_sent', 'created_at']
    list_filter = ['notification_type', 'priority', 'is_read', 'is_sent']
    search_fields = ['title', 'recipient__username']


@admin.register(NotificationTemplate)
class NotificationTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'notification_type', 'is_active', 'created_at']
    list_filter = ['notification_type', 'is_active']
    search_fields = ['name']


@admin.register(NotificationLog)
class NotificationLogAdmin(admin.ModelAdmin):
    list_display = ['notification', 'channel', 'status', 'sent_at', 'created_at']
    list_filter = ['status']
    search_fields = ['notification__title']
