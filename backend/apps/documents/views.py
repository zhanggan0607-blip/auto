"""
文档管理模块 - 视图
"""
import os
import logging
from rest_framework import status, generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from django.utils import timezone
from django.conf import settings

from .models import DocumentTemplate, GeneratedDocument
from .serializers import (
    DocumentTemplateSerializer, DocumentTemplateCreateSerializer,
    GeneratedDocumentSerializer, GeneratedDocumentCreateSerializer,
    DocumentGenerateSerializer, AddReferenceDocsSerializer,
    AISuggestionRequestSerializer
)
from utils.permissions import IsOwnerOrAdmin
from utils.responses import UnifiedResponse
from core.pagination import StandardPagination

logger = logging.getLogger(__name__)


class DocumentTemplateListView(generics.ListCreateAPIView):
    """
    文档模板列表视图
    """
    parser_classes = [MultiPartParser, FormParser]
    permission_classes = [IsAuthenticated]
    pagination_class = StandardPagination

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return DocumentTemplateCreateSerializer
        return DocumentTemplateSerializer

    def get_queryset(self):
        queryset = DocumentTemplate.objects.filter(is_active=True)
        template_type = self.request.query_params.get('template_type')
        if template_type:
            queryset = queryset.filter(template_type=template_type)
        return queryset

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class DocumentTemplateDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    文档模板详情视图
    """
    queryset = DocumentTemplate.objects.all()
    serializer_class = DocumentTemplateSerializer
    permission_classes = [IsAuthenticated]

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return UnifiedResponse.success(data=serializer.data)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return UnifiedResponse.success(data=serializer.data, message='更新成功')

    def perform_destroy(self, instance):
        instance.is_active = False
        instance.save()

    def destroy(self, request, *args, **kwargs):
        """
        删除文档模板
        只有创建者或管理员可以删除
        """
        instance = self.get_object()
        
        if not (request.user.is_staff or 
                getattr(request.user, 'is_admin', lambda: False)() or
                getattr(instance, 'created_by', None) == request.user):
            return UnifiedResponse.error(
                message='无权限删除此模板',
                status_code=status.HTTP_403_FORBIDDEN
            )
        
        self.perform_destroy(instance)
        return UnifiedResponse.success(message='删除成功')


class GeneratedDocumentListView(generics.ListCreateAPIView):
    """
    生成文档列表视图
    """
    permission_classes = [IsAuthenticated]
    pagination_class = StandardPagination

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return GeneratedDocumentCreateSerializer
        return GeneratedDocumentSerializer

    def get_queryset(self):
        queryset = GeneratedDocument.objects.select_related('template', 'tender', 'created_by')
        tender_id = self.request.query_params.get('tender_id')
        if tender_id:
            queryset = queryset.filter(tender_id=tender_id)
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        return queryset

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class GeneratedDocumentDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    生成文档详情视图
    """
    queryset = GeneratedDocument.objects.select_related('template', 'tender')
    serializer_class = GeneratedDocumentSerializer
    permission_classes = [IsAuthenticated]

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return UnifiedResponse.success(data=serializer.data)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return UnifiedResponse.success(data=serializer.data, message='更新成功')

    def destroy(self, request, *args, **kwargs):
        """
        删除生成的文档
        只有创建者或管理员可以删除
        """
        instance = self.get_object()
        
        if not (request.user.is_staff or 
                getattr(request.user, 'is_admin', lambda: False)() or
                getattr(instance, 'created_by', None) == request.user):
            return UnifiedResponse.error(
                message='无权限删除此文档',
                status_code=status.HTTP_403_FORBIDDEN
            )
        
        instance.delete()
        return UnifiedResponse.success(message='删除成功')


class DocumentGenerateView(APIView):
    """
    文档生成视图
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """
        生成文档
        """
        serializer = DocumentGenerateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        template_id = serializer.validated_data.get('template_id')
        tender_id = serializer.validated_data.get('tender_id')
        document_name = serializer.validated_data.get('document_name')
        variables = serializer.validated_data.get('variables', {})
        generate_pdf = serializer.validated_data.get('generate_pdf', True)

        try:
            template = DocumentTemplate.objects.get(pk=template_id)
        except DocumentTemplate.DoesNotExist:
            return UnifiedResponse.error(message='模板不存在', status_code=status.HTTP_404_NOT_FOUND)

        try:
            from apps.tenders.models import TenderProject
            tender = TenderProject.objects.get(pk=tender_id)
        except TenderProject.DoesNotExist:
            return UnifiedResponse.error(message='招标项目不存在', status_code=status.HTTP_404_NOT_FOUND)

        from services.document_generator import DocumentGenerator
        
        try:
            generator = DocumentGenerator()
            result = generator.generate(
                template=template,
                tender=tender,
                variables=variables,
                generate_pdf=generate_pdf
            )

            doc = GeneratedDocument.objects.create(
                name=document_name,
                template=template,
                tender=tender,
                file_path=result.get('docx_path'),
                pdf_path=result.get('pdf_path'),
                variables_data=variables,
                status='generated',
                created_by=request.user
            )

            return UnifiedResponse.success(
                data=GeneratedDocumentSerializer(doc, context={'request': request}).data,
                message='文档生成成功'
            )
        except Exception as e:
            logger.error(f"文档生成失败: {str(e)}")
            return UnifiedResponse.error(message='文档生成失败，请稍后重试')


class DocumentReviewView(APIView):
    """
    文档审核视图
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        """
        审核文档
        """
        try:
            doc = GeneratedDocument.objects.get(pk=pk)
            doc.status = 'reviewed'
            doc.reviewed_by = request.user
            doc.reviewed_at = timezone.now()
            doc.save()
            return UnifiedResponse.success(message='审核成功')
        except GeneratedDocument.DoesNotExist:
            return UnifiedResponse.error(message='文档不存在', status_code=status.HTTP_404_NOT_FOUND)


class ReferenceDocsView(APIView):
    """
    参考文档管理视图
    管理生成文档与向量库文档的关联
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        """
        获取文档关联的参考文档列表
        """
        try:
            doc = GeneratedDocument.objects.prefetch_related('reference_docs').get(pk=pk)
            serializer = GeneratedDocumentSerializer(doc, context={'request': request})
            return UnifiedResponse.success(data={
                'reference_docs': serializer.data.get('reference_docs', [])
            })
        except GeneratedDocument.DoesNotExist:
            return UnifiedResponse.error(message='文档不存在', status_code=status.HTTP_404_NOT_FOUND)

    def post(self, request, pk):
        """
        添加参考文档
        """
        serializer = AddReferenceDocsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        reference_doc_ids = serializer.validated_data.get('reference_doc_ids', [])
        
        try:
            doc = GeneratedDocument.objects.get(pk=pk)
        except GeneratedDocument.DoesNotExist:
            return UnifiedResponse.error(message='文档不存在', status_code=status.HTTP_404_NOT_FOUND)
        
        from apps.vectorlib.models import BidDocumentLibrary
        existing_ids = set(doc.reference_docs.values_list('id', flat=True))
        new_docs = BidDocumentLibrary.objects.filter(id__in=reference_doc_ids).exclude(id__in=existing_ids)
        
        doc.reference_docs.add(*new_docs)
        
        for ref_doc in new_docs:
            ref_doc.increment_use_count()
        
        return UnifiedResponse.success(
            data={'added_count': new_docs.count()},
            message=f'成功添加 {new_docs.count()} 个参考文档'
        )

    def delete(self, request, pk):
        """
        移除参考文档
        """
        serializer = AddReferenceDocsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        reference_doc_ids = serializer.validated_data.get('reference_doc_ids', [])
        
        try:
            doc = GeneratedDocument.objects.get(pk=pk)
        except GeneratedDocument.DoesNotExist:
            return UnifiedResponse.error(message='文档不存在', status_code=status.HTTP_404_NOT_FOUND)
        
        from apps.vectorlib.models import BidDocumentLibrary
        removed_docs = BidDocumentLibrary.objects.filter(id__in=reference_doc_ids)
        
        doc.reference_docs.remove(*removed_docs)
        
        return UnifiedResponse.success(message='参考文档已移除')

class SearchReferenceDocsView(APIView):
    """
    搜索向量库中的参考文档
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        搜索参考文档
        """
        query = request.query_params.get('query', '')
        doc_type = request.query_params.get('doc_type', '')
        limit = min(int(request.query_params.get('limit', 10)), 50)
        
        from apps.vectorlib.models import BidDocumentLibrary
        
        queryset = BidDocumentLibrary.objects.select_related('uploaded_by')
        
        if query:
            queryset = queryset.filter(title__icontains=query)
        
        if doc_type:
            queryset = queryset.filter(document_type=doc_type)
        
        queryset = queryset.order_by('-quality_score', '-use_count')[:limit]
        
        results = [
            {
                'id': doc.id,
                'title': doc.title,
                'document_type': doc.document_type,
                'source_type': doc.source_type,
                'quality_score': doc.quality_score,
                'use_count': doc.use_count,
                'industry': doc.industry,
                'project_type': doc.project_type,
                'content_summary': doc.content_summary[:200] if doc.content_summary else ''
            }
            for doc in queryset
        ]
        
        return UnifiedResponse.success(data=results)
