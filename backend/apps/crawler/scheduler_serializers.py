"""
定时采集任务 - 序列化器
"""
from rest_framework import serializers
from apps.crawler.scheduler_models import CrawlSchedule, CrawlScheduleLog
from apps.crawler.models import WebsiteTemplate


class CrawlScheduleSerializer(serializers.ModelSerializer):
    """
    采集计划序列化器
    """
    website_template_name = serializers.CharField(source='website_template.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    crawl_mode_display = serializers.CharField(source='get_crawl_mode_display', read_only=True)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    regions_multiple = serializers.SerializerMethodField()

    class Meta:
        model = CrawlSchedule
        fields = [
            'id', 'name', 'website_template', 'website_template_name',
            'crontab', 'is_active', 'status', 'status_display',
            'max_pages', 'crawl_mode', 'crawl_mode_display', 'keywords', 'params',
            'regions', 'enterprise_ids', 'exec_datetime',
            'last_run_at', 'next_run_at', 'last_result_count',
            'total_result_count', 'run_count', 'error_count', 'last_error',
            'auto_match', 'auto_delete_unmatched', 'match_threshold',
            'created_by', 'created_by_name', 'created_at', 'updated_at',
            'regions_multiple'
        ]
        read_only_fields = [
            'last_run_at', 'next_run_at', 'last_result_count',
            'total_result_count', 'run_count', 'error_count', 'last_error',
            'created_by', 'created_at', 'updated_at'
        ]

    def get_regions_multiple(self, obj):
        params = obj.params or {}
        return params.get('regions_multiple', False)


class CrawlScheduleListSerializer(serializers.ModelSerializer):
    """
    采集计划列表序列化器
    """
    website_template_name = serializers.CharField(source='website_template.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    crawl_mode_display = serializers.CharField(source='get_crawl_mode_display', read_only=True)
    regions_multiple = serializers.SerializerMethodField()

    class Meta:
        model = CrawlSchedule
        fields = [
            'id', 'name', 'website_template_name', 'crontab',
            'is_active', 'status', 'status_display',
            'crawl_mode', 'crawl_mode_display',
            'regions', 'enterprise_ids', 'exec_datetime',
            'last_run_at', 'last_result_count', 'run_count',
            'auto_match', 'auto_delete_unmatched', 'created_at',
            'regions_multiple'
        ]

    def get_regions_multiple(self, obj):
        params = obj.params or {}
        return params.get('regions_multiple', False)


class CrawlScheduleCreateSerializer(serializers.ModelSerializer):
    """
    创建采集计划序列化器
    """
    website_template = serializers.PrimaryKeyRelatedField(
        queryset=WebsiteTemplate.objects.all(),
        required=False,
        allow_null=True,
        help_text='网站模板ID'
    )
    crontab = serializers.CharField(required=False, allow_null=True, help_text='Cron表达式')
    regions_multiple = serializers.BooleanField(required=False, default=False)

    class Meta:
        model = CrawlSchedule
        fields = [
            'name', 'website_template', 'crontab', 'is_active',
            'max_pages', 'crawl_mode', 'keywords', 'params',
            'regions', 'enterprise_ids', 'exec_datetime',
            'auto_match', 'auto_delete_unmatched', 'match_threshold',
            'regions_multiple'
        ]

    def create(self, validated_data):
        regions_multiple = validated_data.pop('regions_multiple', False)
        params = validated_data.get('params', {})
        params['regions_multiple'] = regions_multiple
        validated_data['params'] = params
        schedule = CrawlSchedule.objects.create(**validated_data)
        schedule.create_celery_task()
        return schedule

    def validate_name(self, value):
        """
        验证计划名称唯一性
        """
        if not value or not value.strip():
            raise serializers.ValidationError('计划名称不能为空')

        name = value.strip()
        queryset = CrawlSchedule.objects.filter(name=name)

        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)

        if queryset.exists():
            raise serializers.ValidationError('该计划名称已存在，请使用其他名称')

        return name

    def validate_crontab(self, value):
        """
        验证Cron表达式
        """
        if value is None:
            return value
        parts = value.strip().split()
        if len(parts) != 5:
            raise serializers.ValidationError('Cron表达式格式错误，应为5个字段：分 时 日 月 周')
        return value

    def validate_website_template(self, value):
        """
        验证网站模板
        允许 null 但不允许无效值
        """
        if value is None:
            return value
        if isinstance(value, (int, str)) and not value:
            return None
        return value


class CrawlScheduleUpdateSerializer(serializers.ModelSerializer):
    """
    更新采集计划序列化器
    """
    website_template = serializers.PrimaryKeyRelatedField(
        queryset=WebsiteTemplate.objects.all(),
        required=False,
        allow_null=True,
        help_text='网站模板ID'
    )
    crontab = serializers.CharField(required=False, allow_null=True, help_text='Cron表达式')
    regions_multiple = serializers.BooleanField(required=False, default=False, write_only=True)

    class Meta:
        model = CrawlSchedule
        fields = [
            'name', 'website_template', 'crontab', 'is_active',
            'max_pages', 'crawl_mode', 'keywords', 'params',
            'regions', 'enterprise_ids', 'exec_datetime',
            'auto_match', 'auto_delete_unmatched', 'match_threshold',
            'regions_multiple'
        ]
        extra_kwargs = {
            'regions_multiple': {'write_only': True}
        }

    def update(self, instance, validated_data):
        regions_multiple = validated_data.pop('regions_multiple', None)
        if regions_multiple is not None:
            params = instance.params or {}
            params['regions_multiple'] = regions_multiple
            validated_data['params'] = params
        return super().update(instance, validated_data)

    def validate_name(self, value):
        """
        验证计划名称唯一性
        """
        if not value or not value.strip():
            raise serializers.ValidationError('计划名称不能为空')

        name = value.strip()
        queryset = CrawlSchedule.objects.filter(name=name)

        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)

        if queryset.exists():
            raise serializers.ValidationError('该计划名称已存在，请使用其他名称')

        return name

    def validate_crontab(self, value):
        """
        验证Cron表达式
        """
        if value is None:
            return value
        parts = value.strip().split()
        if len(parts) != 5:
            raise serializers.ValidationError('Cron表达式格式错误，应为5个字段：分 时 日 月 周')
        return value

    def validate_website_template(self, value):
        """
        验证网站模板
        允许 null 但不允许无效值
        """
        if value is None:
            return value
        if isinstance(value, (int, str)) and not value:
            return None
        return value


class CrawlScheduleLogSerializer(serializers.ModelSerializer):
    """
    采集计划日志序列化器
    """
    schedule_name = serializers.CharField(source='schedule.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = CrawlScheduleLog
        fields = [
            'id', 'schedule', 'schedule_name', 'session',
            'status', 'status_display',
            'result_count', 'matched_count', 'deleted_count',
            'error_message', 'details',
            'started_at', 'finished_at', 'duration'
        ]


class QualificationMatchResultSerializer(serializers.Serializer):
    """
    资质匹配结果序列化器
    """
    tender_id = serializers.IntegerField()
    tender_title = serializers.CharField()
    is_matched = serializers.BooleanField()
    match_score = serializers.FloatField()
    reject_reasons = serializers.ListField(child=serializers.CharField())


class QualificationMatchRequestSerializer(serializers.Serializer):
    """
    资质匹配请求序列化器
    """
    tender_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        help_text='指定招标项目ID列表，为空则匹配所有待处理项目'
    )
    auto_delete = serializers.BooleanField(
        default=False,
        help_text='是否自动删除不匹配的项目'
    )
    threshold = serializers.FloatField(
        default=0.6,
        min_value=0.0,
        max_value=1.0,
        help_text='匹配阈值，低于此值的视为不匹配'
    )
