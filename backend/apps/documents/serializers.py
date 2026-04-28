"""
文档管理模块 - 序列化器
"""
from rest_framework import serializers
from .models import DocumentTemplate, GeneratedDocument
from apps.vectorlib.models import BidDocumentLibrary


class ReferenceDocSimpleSerializer(serializers.ModelSerializer):

    class Meta:
        model = BidDocumentLibrary
        fields = ['id', 'title', 'document_type', 'file_path', 'file_size', 'file_format', 'content_summary']


class DocumentTemplateSerializer(serializers.ModelSerializer):
    """
    文档模板序列化器
    """
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    file_url = serializers.SerializerMethodField()

    class Meta:
        model = DocumentTemplate
        fields = [
            'id', 'name', 'template_type', 'description', 'file_path', 'file_url',
            'variables', 'is_active', 'created_by_name', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_file_url(self, obj):
        if obj.file_path:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.file_path.url)
        return None


class DocumentTemplateCreateSerializer(serializers.ModelSerializer):
    """
    文档模板创建序列化器
    """
    class Meta:
        model = DocumentTemplate
        fields = ['name', 'template_type', 'description', 'file_path', 'variables', 'is_active']


class GeneratedDocumentSerializer(serializers.ModelSerializer):
    """
    生成文档序列化器
    """
    template_name = serializers.CharField(source='template.name', read_only=True)
    tender_title = serializers.CharField(source='tender.title', read_only=True)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    reviewed_by_name = serializers.CharField(source='reviewed_by.username', read_only=True)
    file_url = serializers.SerializerMethodField()
    pdf_url = serializers.SerializerMethodField()
    reference_docs = ReferenceDocSimpleSerializer(many=True, read_only=True)
    reference_doc_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False,
        help_text='参考文档ID列表'
    )

    class Meta:
        model = GeneratedDocument
        fields = [
            'id', 'name', 'template', 'template_name', 'tender', 'tender_title',
            'file_path', 'file_url', 'pdf_path', 'pdf_url', 'variables_data',
            'reference_docs', 'reference_doc_ids', 'ai_suggestions',
            'status', 'version', 'notes', 'created_by_name', 'reviewed_by_name',
            'reviewed_at', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'ai_suggestions']

    def get_file_url(self, obj):
        if obj.file_path:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.file_path.url)
        return None

    def get_pdf_url(self, obj):
        if obj.pdf_path:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.pdf_path.url)
        return None

    def update(self, instance, validated_data):
        reference_doc_ids = validated_data.pop('reference_doc_ids', None)
        if reference_doc_ids is not None:
            from apps.vectorlib.models import BidDocumentLibrary
            docs = BidDocumentLibrary.objects.filter(id__in=reference_doc_ids)
            instance.reference_docs.set(docs)
            for doc in docs:
                doc.increment_use_count()
        return super().update(instance, validated_data)


class GeneratedDocumentCreateSerializer(serializers.ModelSerializer):
    """
    生成文档创建序列化器
    """
    reference_doc_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        write_only=True,
        help_text='参考文档ID列表'
    )

    class Meta:
        model = GeneratedDocument
        fields = ['name', 'template', 'tender', 'variables_data', 'notes', 'reference_doc_ids']

    def create(self, validated_data):
        reference_doc_ids = validated_data.pop('reference_doc_ids', [])
        doc = super().create(validated_data)
        if reference_doc_ids:
            from apps.vectorlib.models import BidDocumentLibrary
            docs = BidDocumentLibrary.objects.filter(id__in=reference_doc_ids)
            doc.reference_docs.set(docs)
            for ref_doc in docs:
                ref_doc.increment_use_count()
        return doc


class DocumentGenerateSerializer(serializers.Serializer):
    """
    文档生成序列化器
    """
    template_id = serializers.IntegerField()
    tender_id = serializers.IntegerField()
    document_name = serializers.CharField(max_length=200)
    variables = serializers.DictField(required=False, default=dict)
    generate_pdf = serializers.BooleanField(default=True)
    reference_doc_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        default=list,
        help_text='参考文档ID列表（从向量库选择）'
    )


class AddReferenceDocsSerializer(serializers.Serializer):
    """
    添加参考文档序列化器
    """
    reference_doc_ids = serializers.ListField(
        child=serializers.IntegerField(),
        help_text='要添加的参考文档ID列表'
    )


class AISuggestionRequestSerializer(serializers.Serializer):
    """
    AI建议请求序列化器
    """
    section = serializers.CharField(
        help_text='需要生成建议的章节',
        required=False
    )
    context = serializers.CharField(
        help_text='额外上下文信息',
        required=False,
        allow_blank=True
    )
