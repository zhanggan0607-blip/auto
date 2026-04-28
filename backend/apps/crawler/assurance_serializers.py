from rest_framework import serializers
from .assurance_models import CrawlHealthCheck, CrawlOptimizationPlan, CrawlAssuranceReport


class CrawlHealthCheckSerializer(serializers.ModelSerializer):
    class Meta:
        model = CrawlHealthCheck
        fields = '__all__'


class CrawlOptimizationPlanSerializer(serializers.ModelSerializer):
    optimization_type_display = serializers.CharField(source='get_optimization_type_display', read_only=True)

    class Meta:
        model = CrawlOptimizationPlan
        fields = '__all__'


class CrawlAssuranceReportListSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    website_template_name = serializers.CharField(source='website_template.name', read_only=True, default='')

    class Meta:
        model = CrawlAssuranceReport
        fields = [
            'id', 'website_template', 'website_template_name', 'target_url',
            'consecutive_failures', 'trigger_reason', 'status', 'status_display',
            'attempt_count', 'max_attempts', 'data_collected', 'final_result',
            'notification_sent', 'started_at', 'finished_at', 'duration', 'created_at',
        ]


class CrawlAssuranceReportDetailSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    website_template_name = serializers.CharField(source='website_template.name', read_only=True, default='')
    current_health_check = CrawlHealthCheckSerializer(read_only=True)
    optimization_plans = CrawlOptimizationPlanSerializer(many=True, read_only=True)

    class Meta:
        model = CrawlAssuranceReport
        fields = '__all__'


class TriggerAssuranceSerializer(serializers.Serializer):
    template_id = serializers.IntegerField(help_text='网站模板ID')
    target_url = serializers.URLField(required=False, allow_blank=True, help_text='目标URL（可选）')


class QuickHealthCheckSerializer(serializers.Serializer):
    url = serializers.URLField(help_text='目标URL')
    template_id = serializers.IntegerField(required=False, help_text='网站模板ID（可选）')
