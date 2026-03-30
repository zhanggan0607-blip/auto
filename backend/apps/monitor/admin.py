"""
Monitor Django Admin配置
"""
from django.contrib import admin
from .models import MonitoredService, ServiceHealthRecord, ServiceAlert, ServiceActionLog


@admin.register(MonitoredService)
class MonitoredServiceAdmin(admin.ModelAdmin):
    list_display = [
        'display_name', 'category', 'status', 'is_enabled',
        'is_critical', 'consecutive_failures', 'last_health_check'
    ]
    list_filter = ['category', 'is_enabled', 'is_critical']
    search_fields = ['name', 'display_name']
    readonly_fields = [
        'last_health_check', 'last_restart_time',
        'consecutive_failures', 'restart_attempts_today'
    ]


@admin.register(ServiceHealthRecord)
class ServiceHealthRecordAdmin(admin.ModelAdmin):
    list_display = ['service', 'is_healthy', 'response_time_ms', 'cpu_usage', 'memory_usage', 'timestamp']
    list_filter = ['is_healthy', 'service']
    search_fields = ['service__name']
    readonly_fields = ['created_at']
    date_hierarchy = 'timestamp'


@admin.register(ServiceAlert)
class ServiceAlertAdmin(admin.ModelAdmin):
    list_display = ['service', 'level', 'status', 'title', 'created_at', 'notified_at']
    list_filter = ['level', 'status', 'service']
    search_fields = ['title', 'message']
    readonly_fields = ['created_at', 'updated_at', 'notified_at', 'resolved_at']


@admin.register(ServiceActionLog)
class ServiceActionLogAdmin(admin.ModelAdmin):
    list_display = ['service', 'action_type', 'status', 'started_at', 'duration_ms', 'performed_by']
    list_filter = ['action_type', 'status', 'service']
    search_fields = ['service__name', 'result_message']
    readonly_fields = ['started_at', 'completed_at', 'duration_ms']
    date_hierarchy = 'started_at'