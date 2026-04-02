"""
SAAS采集模块 - 序列化器
"""
from rest_framework import serializers
from .models import WebsiteTemplate, CrawlSession, CrawlResult, CrawlLog


class WebsiteTemplateSerializer(serializers.ModelSerializer):
    """
    网站模板序列化器
    """
    class Meta:
        model = WebsiteTemplate
        fields = '__all__'
        read_only_fields = ['created_by', 'created_at', 'updated_at']


class WebsiteTemplateListSerializer(serializers.ModelSerializer):
    """
    网站模板列表序列化器
    """
    class Meta:
        model = WebsiteTemplate
        fields = ['id', 'name', 'code', 'website_type', 'base_url', 'is_active', 'priority']


class CrawlSessionSerializer(serializers.ModelSerializer):
    """
    采集会话序列化器
    """
    website_template_name = serializers.CharField(source='website_template.name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    duration_display = serializers.SerializerMethodField()
    
    class Meta:
        model = CrawlSession
        fields = '__all__'
        read_only_fields = ['created_by', 'created_at', 'updated_at']
    
    def get_duration_display(self, obj):
        """
        获取格式化的耗时显示
        """
        if not obj.duration:
            return '-'
        
        hours = obj.duration // 3600
        minutes = (obj.duration % 3600) // 60
        seconds = obj.duration % 60
        
        if hours > 0:
            return f'{hours}小时{minutes}分钟{seconds}秒'
        elif minutes > 0:
            return f'{minutes}分钟{seconds}秒'
        else:
            return f'{seconds}秒'


class CrawlSessionListSerializer(serializers.ModelSerializer):
    """
    采集会话列表序列化器
    """
    website_template_name = serializers.CharField(source='website_template.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = CrawlSession
        fields = ['id', 'name', 'target_url', 'website_template_name', 'crawl_type', 
                  'status', 'status_display', 'progress', 'result_count', 'error_count',
                  'created_at', 'started_at', 'finished_at']


class CrawlResultSerializer(serializers.ModelSerializer):
    """
    采集结果序列化器
    """
    session_name = serializers.CharField(source='session.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = CrawlResult
        fields = '__all__'
        read_only_fields = ['session', 'created_at', 'updated_at']


class CrawlResultListSerializer(serializers.ModelSerializer):
    """
    采集结果列表序列化器
    """
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = CrawlResult
        fields = ['id', 'title', 'source_url', 'publish_date', 'region', 
                  'category', 'budget', 'status', 'status_display', 'created_at']


class CrawlLogSerializer(serializers.ModelSerializer):
    """
    采集日志序列化器
    """
    level_display = serializers.CharField(source='get_level_display', read_only=True)
    
    class Meta:
        model = CrawlLog
        fields = '__all__'


class QuickCrawlSerializer(serializers.Serializer):
    """
    快速采集序列化器
    """
    target_url = serializers.URLField(max_length=1000, help_text='目标网址')
    keywords = serializers.ListField(
        child=serializers.CharField(max_length=100),
        required=False,
        default=list,
        help_text='搜索关键词列表'
    )
    max_pages = serializers.IntegerField(
        default=5, 
        min_value=1, 
        max_value=100,
        help_text='最大爬取页数'
    )
    website_template_id = serializers.IntegerField(
        required=False,
        allow_null=True,
        help_text='网站模板ID（可选）'
    )
    save_results = serializers.BooleanField(
        default=True,
        help_text='是否保存结果到数据库'
    )


class SearchConfigSerializer(serializers.Serializer):
    """
    搜索配置序列化器
    """
    url_pattern = serializers.CharField(max_length=500, help_text='URL模式')
    keyword_param = serializers.CharField(max_length=50, default='keyword', help_text='关键词参数名')
    page_param = serializers.CharField(max_length=50, default='page', help_text='页码参数名')
    encoding = serializers.CharField(max_length=20, default='utf-8', help_text='编码')
    method = serializers.ChoiceField(choices=['GET', 'POST'], default='GET', help_text='请求方法')


class ContentRecognitionRuleSerializer(serializers.ModelSerializer):
    """
    内容识别规则序列化器
    """
    content_type_display = serializers.CharField(source='get_content_type_display', read_only=True)

    class Meta:
        model = None
        from .models import ContentRecognitionRule
        model = ContentRecognitionRule
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


class RecognizedContentSerializer(serializers.ModelSerializer):
    """
    已识别内容序列化器
    """
    source_type_display = serializers.CharField(source='get_source_type_display', read_only=True)
    content_type_display = serializers.CharField(source='get_content_type_display', read_only=True)
    quality_grade_display = serializers.CharField(source='get_quality_grade_display', read_only=True)
    rule_name = serializers.CharField(source='rule.name', read_only=True)

    class Meta:
        model = None
        from .models import RecognizedContent
        model = RecognizedContent
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


class RecognizedContentListSerializer(serializers.ModelSerializer):
    """
    已识别内容列表序列化器
    """
    source_type_display = serializers.CharField(source='get_source_type_display', read_only=True)
    content_type_display = serializers.CharField(source='get_content_type_display', read_only=True)
    quality_grade_display = serializers.CharField(source='get_quality_grade_display', read_only=True)

    class Meta:
        model = None
        from .models import RecognizedContent
        model = RecognizedContent
        fields = ['id', 'title', 'source_url', 'source_type', 'source_type_display',
                  'content_type', 'content_type_display', 'region', 'industry',
                  'purchaser_name', 'agency_name', 'budget', 'publish_date',
                  'deadline_date', 'quality_score', 'quality_grade', 'quality_grade_display',
                  'is_processed', 'created_at']


class BatchRecognizeSerializer(serializers.Serializer):
    """
    批量识别序列化器
    """
    items = serializers.ListField(
        child=serializers.DictField(),
        min_length=1,
        max_length=100,
        help_text='要识别的内容列表'
    )
    content_type = serializers.ChoiceField(
        choices=['tender', 'enterprise', 'document', 'general'],
        default='tender',
        help_text='内容类型'
    )
    save_to_db = serializers.BooleanField(default=True, help_text='是否保存到数据库')
    validate_quality = serializers.BooleanField(default=True, help_text='是否验证质量')
