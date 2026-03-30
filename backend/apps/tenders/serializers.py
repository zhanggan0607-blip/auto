"""
招标项目模块 - 序列化器（优化版）
"""
import re
from rest_framework import serializers
from django.core.exceptions import ValidationError
from .models import TenderSource, TenderProject, TenderFile, TenderKeyword, CrawlerTask


class TenderSourceSerializer(serializers.ModelSerializer):
    """
    招标来源序列化器
    """
    class Meta:
        model = TenderSource
        fields = [
            'id', 'name', 'code', 'source_type', 'base_url', 
            'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class TenderFileSerializer(serializers.ModelSerializer):
    """
    招标文件序列化器
    """
    file_url = serializers.SerializerMethodField()

    class Meta:
        model = TenderFile
        fields = [
            'id', 'tender', 'file_type', 'file_name', 'file_path', 
            'file_url', 'file_size', 'file_ext', 'download_url', 
            'is_downloaded', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']

    def get_file_url(self, obj):
        """
        获取文件URL
        """
        if obj.file_path:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.file_path.url)
        return None


class TenderProjectListSerializer(serializers.ModelSerializer):
    """
    招标项目列表序列化器
    """
    source_name = serializers.CharField(source='source.name', read_only=True)
    files_count = serializers.SerializerMethodField()

    class Meta:
        model = TenderProject
        fields = [
            'id', 'title', 'project_code', 'source_name', 'source_url',
            'publish_date', 'deadline_date', 'open_date', 'region', 
            'industry', 'category', 'budget', 'status', 'is_favorite', 
            'is_read', 'keywords_matched', 'files_count', 'created_at'
        ]

    def get_files_count(self, obj):
        """
        获取文件数量
        """
        return obj.files.count()


class TenderProjectDetailSerializer(serializers.ModelSerializer):
    """
    招标项目详情序列化器
    """
    source = TenderSourceSerializer(read_only=True)
    files = TenderFileSerializer(many=True, read_only=True)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)

    class Meta:
        model = TenderProject
        fields = [
            'id', 'title', 'project_code', 'source', 'source_url',
            'publish_date', 'deadline_date', 'open_date', 'region',
            'industry', 'category', 'purchaser_name', 'purchaser_contact',
            'purchaser_phone', 'agency_name', 'agency_contact', 'agency_phone',
            'budget', 'description', 'requirements', 'status', 'is_favorite',
            'is_read', 'keywords_matched', 'files', 'created_by_name', 
            'created_at', 'updated_at'
        ]


class TenderProjectCreateSerializer(serializers.ModelSerializer):
    """
    招标项目创建序列化器
    """
    class Meta:
        model = TenderProject
        fields = [
            'title', 'project_code', 'source', 'source_url', 'publish_date',
            'deadline_date', 'open_date', 'region', 'industry', 'category',
            'purchaser_name', 'purchaser_contact', 'purchaser_phone',
            'agency_name', 'agency_contact', 'agency_phone', 'budget',
            'description', 'requirements', 'keywords_matched'
        ]
    
    def validate_title(self, value):
        """
        验证标题
        """
        if len(value) < 5:
            raise serializers.ValidationError('标题长度不能少于5个字符')
        if len(value) > 200:
            raise serializers.ValidationError('标题长度不能超过200个字符')
        return value
    
    def validate_budget(self, value):
        """
        验证预算金额
        """
        if value is not None and value < 0:
            raise serializers.ValidationError('预算金额不能为负数')
        return value
    
    def validate(self, attrs):
        """
        验证日期范围
        """
        publish_date = attrs.get('publish_date')
        deadline_date = attrs.get('deadline_date')
        
        if publish_date and deadline_date and publish_date > deadline_date:
            raise serializers.ValidationError({'deadline_date': '截止日期不能早于发布日期'})
        
        return attrs


class TenderProjectUpdateSerializer(serializers.ModelSerializer):
    """
    招标项目更新序列化器
    """
    class Meta:
        model = TenderProject
        fields = [
            'title', 'project_code', 'region', 'industry', 'category',
            'purchaser_name', 'purchaser_contact', 'purchaser_phone',
            'agency_name', 'agency_contact', 'agency_phone', 'budget',
            'description', 'requirements', 'status', 'is_favorite', 'is_read'
        ]
    
    def validate_budget(self, value):
        """
        验证预算金额
        """
        if value is not None and value < 0:
            raise serializers.ValidationError('预算金额不能为负数')
        return value


class TenderBatchDeleteSerializer(serializers.Serializer):
    """
    批量删除序列化器
    """
    ids = serializers.ListField(
        child=serializers.IntegerField(min_value=1),
        min_length=1,
        max_length=100
    )
    
    def validate_ids(self, value):
        """
        验证ID列表
        """
        existing_ids = set(TenderProject.objects.filter(id__in=value).values_list('id', flat=True))
        missing_ids = set(value) - existing_ids
        
        if missing_ids:
            raise serializers.ValidationError(f'以下招标项目不存在: {list(missing_ids)}')
        
        return value


class TenderBatchUpdateSerializer(serializers.Serializer):
    """
    批量更新序列化器
    """
    ids = serializers.ListField(
        child=serializers.IntegerField(min_value=1),
        min_length=1,
        max_length=100
    )
    status = serializers.ChoiceField(choices=TenderProject.STATUS_CHOICES)
    
    def validate_ids(self, value):
        """
        验证ID列表
        """
        existing_ids = set(TenderProject.objects.filter(id__in=value).values_list('id', flat=True))
        missing_ids = set(value) - existing_ids
        
        if missing_ids:
            raise serializers.ValidationError(f'以下招标项目不存在: {list(missing_ids)}')
        
        return value


class TenderKeywordSerializer(serializers.ModelSerializer):
    """
    招标关键词序列化器
    """
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)

    class Meta:
        model = TenderKeyword
        fields = [
            'id', 'keyword', 'category', 'weight', 'is_active', 
            'created_by_name', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']
    
    def validate_keyword(self, value):
        """
        验证关键词
        """
        if len(value) < 2:
            raise serializers.ValidationError('关键词长度不能少于2个字符')
        if len(value) > 50:
            raise serializers.ValidationError('关键词长度不能超过50个字符')
        return value
    
    def validate_weight(self, value):
        """
        验证权重
        """
        if value < 1 or value > 10:
            raise serializers.ValidationError('权重必须在1-10之间')
        return value


class CrawlerTaskSerializer(serializers.ModelSerializer):
    """
    爬虫任务序列化器
    """
    source_name = serializers.CharField(source='source.name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    duration = serializers.SerializerMethodField()

    class Meta:
        model = CrawlerTask
        fields = [
            'id', 'name', 'source', 'source_name', 'task_type', 'params',
            'status', 'result_count', 'error_message', 'started_at', 
            'finished_at', 'duration', 'created_by_name', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']

    def get_duration(self, obj):
        """
        计算任务耗时
        """
        if obj.started_at and obj.finished_at:
            delta = obj.finished_at - obj.started_at
            return int(delta.total_seconds())
        return None



