"""
文档管理模块 - 服务层
"""
import os
import logging
from django.db import transaction
from django.utils import timezone
from django.conf import settings

from .models import DocumentTemplate, GeneratedDocument

logger = logging.getLogger(__name__)


class DocumentService:
    """
    文档服务类
    """
    
    @staticmethod
    @transaction.atomic
    def generate_document(user, template_id, tender_id, document_name, variables=None, generate_pdf=True):
        """
        生成文档
        
        Args:
            user: 用户对象
            template_id: 模板ID
            tender_id: 招标项目ID
            document_name: 文档名称
            variables: 变量数据
            generate_pdf: 是否生成PDF
            
        Returns:
            GeneratedDocument: 生成的文档对象
        """
        from apps.tenders.models import TenderProject
        from services.document_generator import DocumentGenerator
        
        template = DocumentTemplate.objects.get(pk=template_id)
        tender = TenderProject.objects.get(pk=tender_id)
        
        generator = DocumentGenerator()
        result = generator.generate(
            template=template,
            tender=tender,
            variables=variables or {},
            generate_pdf=generate_pdf
        )
        
        doc = GeneratedDocument.objects.create(
            name=document_name,
            template=template,
            tender=tender,
            file_path=result.get('docx_path'),
            pdf_path=result.get('pdf_path'),
            variables_data=variables or {},
            status='generated',
            created_by=user
        )
        
        logger.info(f"文档生成成功: {doc.id} - {document_name}")
        return doc
    
    @staticmethod
    @transaction.atomic
    def review_document(doc_id, reviewer):
        """
        审核文档
        
        Args:
            doc_id: 文档ID
            reviewer: 审核人
            
        Returns:
            GeneratedDocument: 文档对象
        """
        doc = GeneratedDocument.objects.get(pk=doc_id)
        doc.status = 'reviewed'
        doc.reviewed_by = reviewer
        doc.reviewed_at = timezone.now()
        doc.save()
        
        logger.info(f"文档审核通过: {doc_id}, 审核人: {reviewer.id}")
        return doc
    
    @staticmethod
    @transaction.atomic
    def batch_delete_documents(doc_ids, user):
        """
        批量删除文档
        
        Args:
            doc_ids: 文档ID列表
            user: 操作用户
            
        Returns:
            int: 删除数量
        """
        count = GeneratedDocument.objects.filter(id__in=doc_ids).delete()[0]
        logger.info(f"批量删除文档: {doc_ids}, 操作人: {user.id}")
        return count


class TemplateService:
    """
    模板服务类
    """
    
    @staticmethod
    def get_active_templates(template_type=None):
        """
        获取活跃模板
        
        Args:
            template_type: 模板类型
            
        Returns:
            QuerySet: 模板查询集
        """
        queryset = DocumentTemplate.objects.filter(is_active=True)
        if template_type:
            queryset = queryset.filter(template_type=template_type)
        return queryset
    
    @staticmethod
    def get_template_variables(template_id):
        """
        获取模板变量
        
        Args:
            template_id: 模板ID
            
        Returns:
            list: 变量列表
        """
        from services.document_generator import DocumentGenerator
        
        template = DocumentTemplate.objects.get(pk=template_id)
        generator = DocumentGenerator()
        return generator.extract_variables(template.file_path.path)
