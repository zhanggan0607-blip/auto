"""
Monitor序列化器
"""
from rest_framework import serializers
from .models import (
    MonitoredService, ServiceHealthRecord,
    ServiceAlert, ServiceActionLog
)


class MonitoredServiceSerializer(serializers.ModelSerializer):
    """被监控服务序列化器"""
    status = serializers.CharField(read_only=True)
    status_display = serializers.SerializerMethodField()
    category_display = serializers.CharField(source='get_category_display', read_only=True)

    class Meta:
        model = MonitoredService
        fields = [
            'id', 'name', 'display_name', 'category', 'category_display',
            'description', 'health_check_url', 'health_check_port',
            'health_check_type', 'health_check_interval', 'health_check_timeout',
            'consecutive_failures_to_restart', 'consecutive_failures_to_alert',
            'restart_cooldown_minutes', 'max_restart_attempts',
            'is_enabled', 'is_critical', 'auto_restart_enabled',
            'last_health_check', 'last_restart_time', 'consecutive_failures',
            'restart_attempts_today', 'status', 'status_display',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'last_health_check', 'last_restart_time', 'consecutive_failures',
            'restart_attempts_today', 'created_at', 'updated_at'
        ]

    def get_status_display(self, obj):
        status_map = {
            'healthy': '健康',
            'degraded': '性能下降',
            'unhealthy': '异常',
            'restarting': '重启中',
            'unknown': '未知',
            'offline': '离线',
        }
        return status_map.get(obj.status, obj.status)


class MonitoredServiceCreateSerializer(serializers.ModelSerializer):
    """创建被监控服务序列化器"""

    class Meta:
        model = MonitoredService
        fields = [
            'name', 'display_name', 'category', 'description',
            'health_check_url', 'health_check_port', 'health_check_type',
            'health_check_interval', 'health_check_timeout',
            'consecutive_failures_to_restart', 'consecutive_failures_to_alert',
            'restart_cooldown_minutes', 'max_restart_attempts',
            'is_enabled', 'is_critical', 'auto_restart_enabled'
        ]

    def validate_health_check_interval(self, value):
        if value < 5:
            raise serializers.ValidationError("检查间隔不能小于5秒")
        if value > 3600:
            raise serializers.ValidationError("检查间隔不能大于3600秒")
        return value


class ServiceHealthRecordSerializer(serializers.ModelSerializer):
    """健康检查记录序列化器"""
    service_name = serializers.CharField(source='service.display_name', read_only=True)

    class Meta:
        model = ServiceHealthRecord
        fields = [
            'id', 'service', 'service_name', 'timestamp',
            'is_healthy', 'response_time_ms', 'cpu_usage', 'memory_usage',
            'error_message', 'details', 'created_at'
        ]
        read_only_fields = ['created_at']


class ServiceAlertSerializer(serializers.ModelSerializer):
    """服务告警序列化器"""
    service_name = serializers.CharField(source='service.display_name', read_only=True)
    level_display = serializers.CharField(source='get_level_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = ServiceAlert
        fields = [
            'id', 'service', 'service_name', 'level', 'level_display',
            'status', 'status_display', 'title', 'message',
            'triggered_by', 'consecutive_failures',
            'notified_at', 'resolved_at', 'actions_taken',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'notified_at', 'resolved_at', 'created_at', 'updated_at'
        ]


class ServiceAlertUpdateSerializer(serializers.ModelSerializer):
    """更新服务告警序列化器"""

    class Meta:
        model = ServiceAlert
        fields = ['status', 'actions_taken']

    def validate_status(self, value):
        if value == 'resolved' and not self.instance:
            raise serializers.ValidationError("缺少告警实例")
        return value


class ServiceActionLogSerializer(serializers.ModelSerializer):
    """服务操作日志序列化器"""
    service_name = serializers.CharField(source='service.display_name', read_only=True)
    action_type_display = serializers.CharField(source='get_action_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = ServiceActionLog
        fields = [
            'id', 'service', 'service_name', 'action_type', 'action_type_display',
            'status', 'status_display', 'started_at', 'completed_at',
            'duration_ms', 'trigger_condition', 'result_message',
            'error_details', 'performed_by', 'details'
        ]


class ServiceStatusSummarySerializer(serializers.Serializer):
    """服务状态汇总序列化器"""
    service_id = serializers.IntegerField()
    service_name = serializers.CharField()
    display_name = serializers.CharField()
    category = serializers.CharField()
    status = serializers.CharField()
    status_display = serializers.CharField()
    is_healthy = serializers.BooleanField()
    consecutive_failures = serializers.IntegerField()
    last_health_check = serializers.DateTimeField(allow_null=True)
    response_time_ms = serializers.IntegerField(allow_null=True)
    cpu_usage = serializers.FloatField(allow_null=True)
    memory_usage = serializers.FloatField(allow_null=True)
    restart_attempts_today = serializers.IntegerField()
    is_critical = serializers.BooleanField()
    auto_restart_enabled = serializers.BooleanField()