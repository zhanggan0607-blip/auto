"""
投标文档向量库 - 序列化器
"""
from rest_framework import serializers
from .models import BidDocumentLibrary, DocumentSearchLog, AISearchTask


class BidDocumentLibrarySerializer(serializers.ModelSerializer):
    """
    投标文档向量库序列化器
    """
    document_type_display = serializers.CharField(source='get_document_type_display', read_only=True)
    source_type_display = serializers.CharField(source='get_source_type_display', read_only=True)
    vector_status_display = serializers.CharField(source='get_vector_status_display', read_only=True)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    file_url = serializers.SerializerMethodField()

    class Meta:
        model = BidDocumentLibrary
        fields = [
            'id', 'title', 'document_type', 'document_type_display',
            'source_type', 'source_type_display', 'file_path', 'file_url',
            'file_size', 'file_format', 'content_summary', 'keywords',
            'vector_status', 'vector_status_display',
            'source_url', 'source_website', 'search_keyword',
            'project_type', 'industry', 'region',
            'tags', 'metadata', 'view_count', 'use_count',
            'quality_score', 'is_verified', 'is_featured',
            'created_by', 'created_by_name', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'file_size', 'file_format', 'content_text',
            'vector_status', 'vector_id', 'vector_text',
            'view_count', 'use_count', 'quality_score',
            'created_by', 'created_at', 'updated_at'
        ]

    def get_file_url(self, obj):
        """
        获取文件URL
        """
        if obj.file_path:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.file_path.url)
            return obj.file_path.url
        return None


class BidDocumentLibraryListSerializer(serializers.ModelSerializer):
    """
    投标文档向量库列表序列化器（简化版）
    """
    document_type_display = serializers.CharField(source='get_document_type_display', read_only=True)
    source_type_display = serializers.CharField(source='get_source_type_display', read_only=True)

    class Meta:
        model = BidDocumentLibrary
        fields = [
            'id', 'title', 'document_type', 'document_type_display',
            'source_type', 'source_type_display', 'file_format',
            'content_summary', 'industry', 'project_type',
            'view_count', 'use_count', 'quality_score', 'is_featured',
            'created_at'
        ]


class BidDocumentLibraryCreateSerializer(serializers.ModelSerializer):
    """
    投标文档向量库创建序列化器
    """
    class Meta:
        model = BidDocumentLibrary
        fields = [
            'title', 'document_type', 'source_type', 'file_path',
            'content_text', 'content_summary', 'keywords',
            'source_url', 'source_website', 'search_keyword',
            'project_type', 'industry', 'region', 'tags', 'metadata'
        ]


class DocumentSearchSerializer(serializers.Serializer):
    """
    文档搜索序列化器
    """
    query = serializers.CharField(max_length=1000, help_text='搜索内容')
    doc_types = serializers.ListField(
        child=serializers.CharField(max_length=50),
        required=False,
        default=list,
        help_text='文档类型过滤'
    )
    industries = serializers.ListField(
        child=serializers.CharField(max_length=100),
        required=False,
        default=list,
        help_text='行业过滤'
    )
    limit = serializers.IntegerField(default=10, min_value=1, max_value=50, help_text='返回数量')


class AdvancedSearchSerializer(serializers.Serializer):
    """
    高级搜索序列化器
    支持多关键词、逻辑运算符、多文档类型和多行业选择
    """
    keywords = serializers.ListField(
        child=serializers.CharField(max_length=200),
        required=True,
        min_length=1,
        help_text='搜索关键词列表'
    )
    keyword_operator = serializers.ChoiceField(
        choices=['AND', 'OR', 'NOT'],
        default='AND',
        help_text='关键词之间的逻辑运算符'
    )
    doc_types = serializers.ListField(
        child=serializers.CharField(max_length=50),
        required=False,
        default=list,
        help_text='文档类型过滤列表'
    )
    industries = serializers.ListField(
        child=serializers.CharField(max_length=100),
        required=False,
        default=list,
        help_text='行业过滤列表'
    )
    project_types = serializers.ListField(
        child=serializers.CharField(max_length=100),
        required=False,
        default=list,
        help_text='项目类型过滤列表'
    )
    min_similarity = serializers.FloatField(
        default=0.0,
        min_value=0.0,
        max_value=1.0,
        help_text='最小相似度阈值'
    )
    limit = serializers.IntegerField(default=20, min_value=1, max_value=100, help_text='返回数量')
    include_excluded_keywords = serializers.BooleanField(
        default=False,
        help_text='是否启用排除关键词功能'
    )
    excluded_keywords = serializers.ListField(
        child=serializers.CharField(max_length=200),
        required=False,
        default=list,
        help_text='排除的关键词列表'
    )


class DocumentSearchResultSerializer(serializers.Serializer):
    """
    文档搜索结果序列化器
    """
    id = serializers.IntegerField()
    title = serializers.CharField()
    document_type = serializers.CharField()
    document_type_display = serializers.CharField()
    content_summary = serializers.CharField()
    similarity = serializers.FloatField(help_text='相似度分数')
    industry = serializers.CharField()
    project_type = serializers.CharField()
    source_type = serializers.CharField()
    file_url = serializers.CharField(allow_null=True)


class AISearchTaskSerializer(serializers.ModelSerializer):
    """
    AI搜索任务序列化器
    """
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    keywords_list = serializers.SerializerMethodField()

    class Meta:
        model = AISearchTask
        fields = [
            'id', 'keyword', 'keywords', 'keywords_list',
            'document_types', 'industries',
            'status', 'status_display', 'progress',
            'total_found', 'saved_count',
            'error_message', 'started_at', 'completed_at',
            'created_by', 'created_by_name', 'created_at'
        ]
        read_only_fields = [
            'id', 'status', 'progress', 'total_found', 'saved_count',
            'error_message', 'started_at', 'completed_at',
            'created_by', 'created_at'
        ]

    def get_keywords_list(self, obj):
        return obj.keywords if obj.keywords else ([obj.keyword] if obj.keyword else [])


class AISearchTaskCreateSerializer(serializers.Serializer):
    """
    AI搜索任务创建序列化器
    """
    keywords = serializers.CharField(max_length=500, help_text='搜索关键词（多个用逗号分隔）')
    document_types = serializers.CharField(max_length=200, required=False, allow_blank=True, help_text='目标文档类型（多个用逗号分隔）')
    industries = serializers.CharField(max_length=300, required=False, allow_blank=True, help_text='目标行业（多个用逗号分隔）')
    max_results = serializers.IntegerField(default=20, min_value=5, max_value=100, help_text='最大结果数')
class BatchUploadSerializer(serializers.Serializer):
    """
    批量上传序列化器
    """
    files = serializers.ListField(
        child=serializers.FileField(),
        help_text='文件列表'
    )
    document_type = serializers.CharField(
        max_length=50,
        default='bid_document',
        help_text='文档类型'
    )
    industry = serializers.CharField(
        max_length=100,
        required=False,
        allow_null=True,
        help_text='所属行业'
    )
    project_type = serializers.CharField(
        max_length=100,
        required=False,
        allow_null=True,
        help_text='项目类型'
    )
    min_quality_score = serializers.IntegerField(
        default=90,
        min_value=0,
        max_value=100,
        help_text='最低质量分数阈值，低于此分数的标书不存入向量库'
    )
    auto_vectorize = serializers.BooleanField(
        default=True,
        help_text='是否自动向量化'
    )


class BatchUploadResultSerializer(serializers.Serializer):
    """
    批量上传结果序列化器
    """
    total_files = serializers.IntegerField()
    success_count = serializers.IntegerField()
    failed_count = serializers.IntegerField()
    vectorized_count = serializers.IntegerField()
    skipped_count = serializers.IntegerField(help_text='因质量分数不足跳过的数量')
    errors = serializers.ListField(child=serializers.DictField())
    document_ids = serializers.ListField(child=serializers.IntegerField())
