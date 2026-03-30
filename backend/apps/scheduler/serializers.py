"""
统一调度序列化器
"""
from rest_framework import serializers
from .models import UnifiedSchedule, ScheduleExecutionLog


class UnifiedScheduleSerializer(serializers.ModelSerializer):
    """
    统一调度任务序列化器
    """
    task_type_display = serializers.CharField(source='get_task_type_display', read_only=True)
    is_enabled_display = serializers.CharField(source='is_enabled', read_only=True)

    class Meta:
        model = UnifiedSchedule
        fields = [
            'id', 'task_id', 'task_name', 'task_type', 'task_type_display',
            'description', 'cron_expression', 'is_enabled', 'is_enabled_display',
            'last_run_at', 'next_run_at', 'last_run_status', 'last_run_result',
            'run_count', 'error_count', 'last_error',
            'created_by', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'last_run_at', 'next_run_at', 'last_run_status', 'last_run_result',
            'run_count', 'error_count', 'last_error',
            'created_at', 'updated_at'
        ]


class ScheduleExecutionLogSerializer(serializers.ModelSerializer):
    """
    调度执行日志序列化器
    """
    schedule_name = serializers.CharField(source='schedule.task_name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = ScheduleExecutionLog
        fields = [
            'id', 'schedule', 'schedule_name', 'status', 'status_display',
            'result', 'error_message', 'duration',
            'started_at', 'finished_at'
        ]
