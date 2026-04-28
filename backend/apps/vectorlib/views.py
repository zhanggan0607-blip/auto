"""
投标文档向量库 - 视图
"""
import asyncio
import logging
import os
from pathlib import Path

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q, Count
from django.utils import timezone
from django.conf import settings

from utils.responses import UnifiedResponse
from .models import BidDocumentLibrary, DocumentSearchLog, AISearchTask
from common.views.base import APIResponseMixin
from .serializers import (
    BidDocumentLibrarySerializer, BidDocumentLibraryListSerializer,
    BidDocumentLibraryCreateSerializer, DocumentSearchSerializer,
    DocumentSearchResultSerializer, AISearchTaskSerializer,
    AISearchTaskCreateSerializer, BatchUploadSerializer, BatchUploadResultSerializer,
    AdvancedSearchSerializer
)
from services.vector import document_vector_store

logger = logging.getLogger(__name__)


class BidDocumentLibraryViewSet(APIResponseMixin, viewsets.ModelViewSet):
    """
    投标文档向量库视图集
    """
    queryset = BidDocumentLibrary.objects.all()
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_serializer_class(self):
        if self.action == 'list':
            return BidDocumentLibraryListSerializer
        if self.action == 'create':
            return BidDocumentLibraryCreateSerializer
        return BidDocumentLibrarySerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        
        document_type = self.request.query_params.get('document_type')
        if document_type:
            queryset = queryset.filter(document_type=document_type)
        
        source_type = self.request.query_params.get('source_type')
        if source_type:
            queryset = queryset.filter(source_type=source_type)
        
        industry = self.request.query_params.get('industry')
        if industry:
            queryset = queryset.filter(industry=industry)
        
        keyword = self.request.query_params.get('keyword')
        if keyword:
            queryset = queryset.filter(
                Q(title__icontains=keyword) |
                Q(content_summary__icontains=keyword) |
                Q(keywords__contains=keyword)
            )
        
        is_featured = self.request.query_params.get('is_featured')
        if is_featured and is_featured.lower() == 'true':
            queryset = queryset.filter(is_featured=True)
        
        return queryset

    def perform_create(self, serializer):
        """
        创建文档时自动处理文件和向量化
        """
        instance = serializer.save(created_by=self.request.user)
        
        if instance.file_path:
            instance.file_size = instance.file_path.size
            instance.file_format = os.path.splitext(instance.file_path.name)[1].lower().lstrip('.')
            instance.save(update_fields=['file_size', 'file_format'])
        
        self._process_document(instance)

    def _process_document(self, instance):
        """
        处理文档：提取文本、向量化
        """
        try:
            instance.vector_status = 'processing'
            instance.save(update_fields=['vector_status'])
            
            content_text = instance.content_text or ''
            
            if instance.file_path and not content_text:
                content_text = self._extract_text_from_file(instance.file_path.path)
                instance.content_text = content_text
                instance.save(update_fields=['content_text'])
            
            if not instance.content_summary and content_text:
                instance.content_summary = content_text[:500]
                instance.save(update_fields=['content_summary'])
            
            vector_text = f"{instance.title}\n{content_text}"
            instance.vector_text = vector_text
            
            metadata = {
                'document_type': instance.document_type,
                'source_type': instance.source_type,
                'industry': instance.industry,
                'project_type': instance.project_type,
            }
            
            success = document_vector_store.add_document(
                doc_id=instance.id,
                title=instance.title,
                content=content_text,
                metadata=metadata
            )
            
            if success:
                instance.vector_status = 'indexed'
                instance.vector_id = f"doc_{instance.id}"
                logger.info(f"文档向量化成功: {instance.id}")
            else:
                instance.vector_status = 'failed'
                logger.warning(f"文档向量化失败: {instance.id}")
            
            instance.save(update_fields=['vector_status', 'vector_id', 'vector_text'])
            
        except Exception as e:
            logger.error(f"处理文档失败: {str(e)}")
            instance.vector_status = 'failed'
            instance.save(update_fields=['vector_status'])

    def _extract_text_from_file(self, file_path):
        """
        从文件中提取文本
        """
        try:
            ext = os.path.splitext(file_path)[1].lower()
            
            if ext in ['.txt', '.md']:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    return f.read()
            
            elif ext in ['.docx', '.doc']:
                try:
                    from docx import Document
                    doc = Document(file_path)
                    return '\n'.join([para.text for para in doc.paragraphs])
                except ImportError:
                    logger.warning("python-docx 未安装，无法提取Word文档内容")
                    return ""
            
            elif ext == '.pdf':
                try:
                    import PyPDF2
                    with open(file_path, 'rb') as f:
                        reader = PyPDF2.PdfReader(f)
                        text = []
                        for page in reader.pages:
                            text.append(page.extract_text())
                        return '\n'.join(text)
                except ImportError:
                    logger.warning("PyPDF2 未安装，无法提取PDF内容")
                    return ""
            
            return ""
        except Exception as e:
            logger.error(f"提取文件文本失败: {str(e)}")
            return ""

    @action(detail=False, methods=['post'])
    def search(self, request):
        """
        语义搜索文档
        """
        from utils.content_moderation import check_user_input, ContentRiskLevel

        serializer = DocumentSearchSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        query = serializer.validated_data['query']

        check_result = check_user_input(query, getattr(request.user, 'id', None))
        if check_result.risk_level == ContentRiskLevel.BLOCKED:
            return UnifiedResponse.error(
                message=f'搜索内容包含敏感信息: {check_result.risk_description}',
                status_code=status.HTTP_400_BAD_REQUEST
            )

        doc_types = serializer.validated_data.get('doc_types', [])
        industries = serializer.validated_data.get('industries', [])
        limit = serializer.validated_data.get('limit', 10)

        results = document_vector_store.search_similar(
            query_text=query,
            n_results=limit,
            doc_types=doc_types if doc_types else None,
            industries=industries if industries else None
        )

        doc_ids = [r['id'] for r in results]
        documents = {
            doc.id: doc
            for doc in BidDocumentLibrary.objects.filter(id__in=doc_ids)
        }

        formatted_results = []
        for r in results:
            doc = documents.get(r['id'])
            if doc:
                file_url = None
                if doc.file_path:
                    file_url = request.build_absolute_uri(doc.file_path.url)

                formatted_results.append({
                    'id': doc.id,
                    'title': doc.title,
                    'document_type': doc.document_type,
                    'document_type_display': doc.get_document_type_display(),
                    'content_summary': doc.content_summary or doc.content_text[:200] if doc.content_text else '',
                    'similarity': r.get('similarity', 0),
                    'industry': doc.industry,
                    'project_type': doc.project_type,
                    'source_type': doc.source_type,
                    'file_url': file_url,
                })

        DocumentSearchLog.objects.create(
            query_text=query,
            search_type='semantic',
            result_count=len(formatted_results),
            user=request.user
        )

        return UnifiedResponse.success(data={
            'query': query,
            'total': len(formatted_results),
            'results': formatted_results
        })

    @action(detail=False, methods=['post'])
    def advanced_search(self, request):
        """
        高级搜索文档
        支持多关键词、逻辑运算符(AND/OR/NOT)、多文档类型和多行业选择

        请求参数:
        - keywords: 关键词列表
        - keyword_operator: 关键词逻辑运算符 (AND/OR/NOT)
        - doc_types: 文档类型列表
        - industries: 行业列表
        - project_types: 项目类型列表
        - min_similarity: 最小相似度
        - limit: 返回数量
        - include_excluded_keywords: 是否启用排除关键词
        - excluded_keywords: 排除的关键词列表
        """
        from utils.content_moderation import check_user_input, ContentRiskLevel

        serializer = AdvancedSearchSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        keywords = serializer.validated_data['keywords']
        keyword_operator = serializer.validated_data.get('keyword_operator', 'AND')
        doc_types = serializer.validated_data.get('doc_types', [])
        industries = serializer.validated_data.get('industries', [])
        project_types = serializer.validated_data.get('project_types', [])
        min_similarity = serializer.validated_data.get('min_similarity', 0.0)
        limit = serializer.validated_data.get('limit', 20)
        include_excluded = serializer.validated_data.get('include_excluded_keywords', False)
        excluded_keywords = serializer.validated_data.get('excluded_keywords', [])

        for keyword in keywords:
            check_result = check_user_input(keyword, getattr(request.user, 'id', None))
            if check_result.risk_level == ContentRiskLevel.BLOCKED:
                return UnifiedResponse.error(
                    message=f'搜索关键词包含敏感信息: {check_result.risk_description}',
                    status_code=status.HTTP_400_BAD_REQUEST
                )

        combined_query = self._build_search_query(keywords, keyword_operator)

        filters = {}
        if project_types:
            filters['project_type'] = {'$in': project_types}

        all_results = []
        if keyword_operator == 'OR':
            for keyword in keywords:
                results = document_vector_store.search_similar(
                    query_text=keyword,
                    n_results=limit,
                    filters=filters if filters else None,
                    doc_types=doc_types if doc_types else None,
                    industries=industries if industries else None,
                    min_similarity=min_similarity
                )
                for r in results:
                    if r not in all_results:
                        all_results.append(r)
            all_results.sort(key=lambda x: x.get('similarity', 0), reverse=True)
            all_results = all_results[:limit]
        elif keyword_operator == 'NOT':
            if keywords:
                base_results = document_vector_store.search_similar(
                    query_text=keywords[0],
                    n_results=limit * 2,
                    filters=filters if filters else None,
                    doc_types=doc_types if doc_types else None,
                    industries=industries if industries else None,
                    min_similarity=min_similarity
                )

                exclude_results = set()
                for keyword in keywords[1:]:
                    exclude_results.update(
                        r['id'] for r in document_vector_store.search_similar(
                            query_text=keyword,
                            n_results=limit * 2,
                            min_similarity=min_similarity
                        )
                    )

                all_results = [r for r in base_results if r['id'] not in exclude_results][:limit]
        else:
            all_results = document_vector_store.search_similar(
                query_text=combined_query,
                n_results=limit,
                filters=filters if filters else None,
                doc_types=doc_types if doc_types else None,
                industries=industries if industries else None,
                min_similarity=min_similarity
            )

        if include_excluded and excluded_keywords:
            exclude_ids = set()
            for excl_kw in excluded_keywords:
                excl_results = document_vector_store.search_similar(
                    query_text=excl_kw,
                    n_results=limit * 2,
                    min_similarity=0.0
                )
                exclude_ids.update(r['id'] for r in excl_results)
            all_results = [r for r in all_results if r['id'] not in exclude_ids]

        doc_ids = [r['id'] for r in all_results]
        documents = {
            doc.id: doc
            for doc in BidDocumentLibrary.objects.filter(id__in=doc_ids)
        }

        formatted_results = []
        for r in all_results:
            doc = documents.get(r['id'])
            if doc:
                file_url = None
                if doc.file_path:
                    file_url = request.build_absolute_uri(doc.file_path.url)

                formatted_results.append({
                    'id': doc.id,
                    'title': doc.title,
                    'document_type': doc.document_type,
                    'document_type_display': doc.get_document_type_display(),
                    'content_summary': doc.content_summary or (doc.content_text[:200] if doc.content_text else ''),
                    'similarity': r.get('similarity', 0),
                    'industry': doc.industry,
                    'industry_display': self._get_industry_display(doc.industry),
                    'project_type': doc.project_type,
                    'source_type': doc.source_type,
                    'quality_score': doc.quality_score,
                    'file_url': file_url,
                    'created_at': doc.created_at.strftime('%Y-%m-%d') if doc.created_at else None,
                })

        query_log = f"{keyword_operator.join(keywords)}"
        if include_excluded and excluded_keywords:
            query_log += f" NOT ({', '.join(excluded_keywords)})"

        DocumentSearchLog.objects.create(
            query_text=query_log,
            search_type='advanced',
            result_count=len(formatted_results),
            user=request.user
        )

        return UnifiedResponse.success(data={
            'keywords': keywords,
            'keyword_operator': keyword_operator,
            'doc_types': doc_types,
            'industries': industries,
            'project_types': project_types,
            'total': len(formatted_results),
            'results': formatted_results
        })

    def _build_search_query(self, keywords, operator):
        """
        构建组合搜索查询字符串
        """
        if operator == 'AND':
            return ' '.join(keywords)
        elif operator == 'OR':
            return ' OR '.join(keywords)
        elif operator == 'NOT':
            if len(keywords) > 1:
                return f"{keywords[0]} NOT ({' '.join(keywords[1:])})"
            return keywords[0]
        return ' '.join(keywords)

    def _get_industry_display(self, industry_code):
        """
        获取行业的可读名称
        """
        from core.constants import INDUSTRY_CATEGORY_CHOICES
        for code, name in INDUSTRY_CATEGORY_CHOICES:
            if code == industry_code:
                return name
        return industry_code

    @action(detail=True, methods=['post'])
    def increment_view(self, request, pk=None):
        """
        增加查看次数
        """
        doc = self.get_object()
        doc.increment_view_count()
        return UnifiedResponse.success()

    @action(detail=True, methods=['post'])
    def increment_use(self, request, pk=None):
        """
        增加使用次数
        """
        doc = self.get_object()
        doc.increment_use_count()
        return UnifiedResponse.success()

    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """
        获取向量库统计信息
        """
        total_count = BidDocumentLibrary.objects.count()
        indexed_count = BidDocumentLibrary.objects.filter(vector_status='indexed').count()
        upload_count = BidDocumentLibrary.objects.filter(source_type='upload').count()
        ai_search_count = BidDocumentLibrary.objects.filter(source_type='ai_search').count()
        
        vector_count = document_vector_store.get_count()
        
        doc_type_stats = {}
        from core.constants import VECTOR_DOC_TYPE_CHOICES
        for choice in VECTOR_DOC_TYPE_CHOICES:
            count = BidDocumentLibrary.objects.filter(document_type=choice[0]).count()
            if count > 0:
                doc_type_stats[choice[1]] = count
        
        return UnifiedResponse.success(data={
            'total_count': total_count,
            'indexed_count': indexed_count,
            'vector_count': vector_count,
            'upload_count': upload_count,
            'ai_search_count': ai_search_count,
            'doc_type_stats': doc_type_stats
        })

    def destroy(self, request, *args, **kwargs):
        """
        删除文档（同时删除向量）
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
        
        if instance.vector_id:
            document_vector_store.delete_document(instance.id)
        
        return super().destroy(request, *args, **kwargs)

    @action(detail=False, methods=['post'], parser_classes=[MultiPartParser, FormParser])
    def batch_upload(self, request):
        """
        批量上传文档到向量库
        
        支持大量标书文件的批量上传，建立结构化向量数据库
        只有评分90分以上的标书才会存入向量库
        
        参数:
        - files: 文件列表
        - document_type: 文档类型
        - industry: 所属行业
        - project_type: 项目类型
        - min_quality_score: 最低质量分数阈值（默认90）
        - auto_vectorize: 是否自动向量化（默认True）
        """
        serializer = BatchUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        files = request.FILES.getlist('files')
        document_type = serializer.validated_data.get('document_type', 'bid_document')
        industry = serializer.validated_data.get('industry', '')
        project_type = serializer.validated_data.get('project_type', '')
        min_quality_score = serializer.validated_data.get('min_quality_score', 90)
        auto_vectorize = serializer.validated_data.get('auto_vectorize', True)
        
        if not files:
            return UnifiedResponse.error(message='请选择要上传的文件', status_code=status.HTTP_400_BAD_REQUEST)
        
        result = {
            'total_files': len(files),
            'success_count': 0,
            'failed_count': 0,
            'vectorized_count': 0,
            'skipped_count': 0,
            'errors': [],
            'document_ids': []
        }
        
        for file_obj in files:
            try:
                doc = BidDocumentLibrary(
                    title=os.path.splitext(file_obj.name)[0],
                    document_type=document_type,
                    source_type='upload',
                    file_path=file_obj,
                    file_size=file_obj.size,
                    file_format=os.path.splitext(file_obj.name)[1].lower().lstrip('.'),
                    industry=industry,
                    project_type=project_type,
                    created_by=request.user
                )
                
                content_text = self._extract_text_from_file(doc.file_path.path)
                doc.content_text = content_text
                doc.content_summary = content_text[:500] if content_text else ''
                
                quality_score = self._calculate_quality_score(doc)
                doc.quality_score = quality_score
                
                if quality_score < min_quality_score:
                    result['skipped_count'] += 1
                    result['errors'].append({
                        'file': file_obj.name,
                        'error': f'质量分数({quality_score})低于阈值({min_quality_score})'
                    })
                    continue
                
                doc.save()
                result['document_ids'].append(doc.id)
                result['success_count'] += 1
                
                if auto_vectorize:
                    try:
                        doc.vector_status = 'processing'
                        doc.save(update_fields=['vector_status'])
                        
                        metadata = {
                            'document_type': document_type,
                            'source_type': 'upload',
                            'industry': industry,
                            'project_type': project_type,
                            'quality_score': quality_score
                        }
                        
                        success = document_vector_store.add_document(
                            doc_id=doc.id,
                            title=doc.title,
                            content=content_text,
                            metadata=metadata
                        )
                        
                        if success:
                            doc.vector_status = 'indexed'
                            doc.vector_id = f"doc_{doc.id}"
                            result['vectorized_count'] += 1
                        else:
                            doc.vector_status = 'failed'
                        
                        doc.save(update_fields=['vector_status', 'vector_id'])
                        
                    except Exception as e:
                        logger.error(f"向量化失败 {doc.id}: {str(e)}")
                        doc.vector_status = 'failed'
                        doc.save(update_fields=['vector_status'])
                
            except Exception as e:
                result['failed_count'] += 1
                result['errors'].append({
                    'file': file_obj.name,
                    'error': str(e)
                })
                logger.error(f"上传文件失败 {file_obj.name}: {str(e)}")
        
        return UnifiedResponse.success(
            data=result,
            message=f"批量上传完成: 成功{result['success_count']}个, 跳过{result['skipped_count']}个, 失败{result['failed_count']}个"
        )

    def _calculate_quality_score(self, doc) -> int:
        """
        计算文档质量分数
        
        评分标准:
        - 文件格式: 20分
        - 内容完整性: 40分
        - 文档结构: 20分
        - 关键信息: 20分
        """
        score = 0
        
        if doc.file_format in ['pdf', 'docx', 'doc']:
            score += 20
        elif doc.file_format in ['txt', 'md']:
            score += 15
        else:
            score += 5
        
        content = doc.content_text or ''
        if len(content) >= 5000:
            score += 40
        elif len(content) >= 2000:
            score += 30
        elif len(content) >= 500:
            score += 20
        elif len(content) >= 100:
            score += 10
        
        structure_keywords = ['目录', '第一章', '第二章', '一、', '二、', '1.', '2.']
        structure_count = sum(1 for kw in structure_keywords if kw in content)
        score += min(structure_count * 5, 20)
        
        key_keywords = ['投标', '招标', '报价', '技术方案', '施工组织', '质量保证', '安全措施']
        key_count = sum(1 for kw in key_keywords if kw in content)
        score += min(key_count * 3, 20)
        
        return min(score, 100)


class AISearchTaskViewSet(APIResponseMixin, viewsets.ModelViewSet):
    """
    AI全网搜索任务视图集
    """
    queryset = AISearchTask.objects.all()
    serializer_class = AISearchTaskSerializer
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'create':
            return AISearchTaskCreateSerializer
        return AISearchTaskSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        return queryset

    def create(self, request, *args, **kwargs):
        """
        创建AI搜索任务
        由于perform_create会调用_execute_ai_search（可能耗时较长），
        我们在这里处理响应，返回已创建的任务信息
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            self.perform_create(serializer)
        except Exception as e:
            logger.error(f"创建AI搜索任务失败: {str(e)}")
            return UnifiedResponse.error(message=f'创建任务失败: {str(e)}')

        instance = serializer.instance
        response_serializer = AISearchTaskSerializer(instance)
        return UnifiedResponse.success(
            data=response_serializer.data,
            message='AI搜索任务已创建，正在执行中...',
            status_code=status.HTTP_201_CREATED
        )

    def perform_create(self, serializer):
        """
        创建AI搜索任务
        """
        validated_data = serializer.validated_data
        keywords_str = validated_data.get('keywords', '')
        keywords_list = [k.strip() for k in keywords_str.split(',') if k.strip()] if keywords_str else []

        document_types_str = validated_data.get('document_types', '')
        document_types_list = [d.strip() for d in document_types_str.split(',') if d.strip()] if document_types_str else []

        industries_str = validated_data.get('industries', '')
        industries_list = [i.strip() for i in industries_str.split(',') if i.strip()] if industries_str else []

        instance = AISearchTask.objects.create(
            created_by=self.request.user,
            keyword=keywords_list[0] if keywords_list else keywords_str,
            keywords=keywords_list,
            document_types=document_types_list,
            industries=industries_list
        )
        serializer.instance = instance
        self._execute_ai_search(instance)

    def _execute_ai_search(self, task):
        """
        执行AI全网搜索
        """
        try:
            task.status = 'running'
            task.started_at = timezone.now()
            task.save(update_fields=['status', 'started_at'])

            keywords = task.keywords or []
            keyword = task.keyword or (keywords[0] if keywords else '')
            document_types = task.document_types or []
            industries = task.industries or []

            search_results = self._search_internet(keywords, document_types, industries)

            task.total_found = len(search_results)
            task.search_results = search_results
            task.progress = 50
            task.save(update_fields=['total_found', 'search_results', 'progress'])

            saved_count = 0
            primary_doc_type = document_types[0] if document_types else None
            primary_industry = industries[0] if industries else None

            for result in search_results[:20]:
                try:
                    doc, created = BidDocumentLibrary.objects.get_or_create(
                        source_url=result.get('url'),
                        defaults={
                            'title': result.get('title', '')[:500],
                            'document_type': primary_doc_type or 'other',
                            'source_type': 'ai_search',
                            'content_summary': result.get('summary', '')[:500],
                            'source_website': result.get('source', ''),
                            'search_keyword': keyword,
                            'industry': primary_industry or '',
                            'created_by': task.created_by,
                        }
                    )
                    if created:
                        saved_count += 1
                except Exception as e:
                    logger.error(f"保存搜索结果失败: {str(e)}")
                    continue

            task.saved_count = saved_count
            task.status = 'completed'
            task.completed_at = timezone.now()
            task.progress = 100
            task.save(update_fields=['saved_count', 'status', 'completed_at', 'progress'])

            logger.info(f"AI搜索任务完成: {keyword}, 发现 {task.total_found}, 保存 {saved_count}")

        except Exception as e:
            logger.error(f"AI搜索任务执行失败: {str(e)}")
            task.status = 'failed'
            task.error_message = str(e)
            task.completed_at = timezone.now()
            task.save(update_fields=['status', 'error_message', 'completed_at'])

    async def _search_internet_async(self, keywords=None, document_types=None, industries=None):
        """
        异步搜索互联网
        """
        results = []
        keywords = keywords or []
        document_types = document_types or []
        industries = industries or []

        try:
            from services.unified_llm_service import unified_llm_service
            from apps.openclaw.models import LLMProvider

            provider = unified_llm_service.get_provider()
            if not provider:
                raise ValueError(
                    "未配置LLM模型提供商。请在后台配置Ollama本地服务或配置API密钥。\n"
                    "配置方法：\n"
                    "1. 启动Ollama服务: ollama serve\n"
                    "2. 或在系统设置中配置智谱AI/通义千问/DeepSeek的API密钥"
                )

            if provider.provider_type == 'ollama':
                import requests
                try:
                    response = requests.get(f"{provider.base_url}/api/tags", timeout=5)
                    if response.status_code != 200:
                        raise ValueError(
                            f"Ollama服务未启动或不可访问 ({provider.base_url})。\n"
                            "请执行: ollama serve 启动服务"
                        )
                except requests.exceptions.ConnectionError:
                    raise ValueError(
                        f"无法连接到Ollama服务 ({provider.base_url})。\n"
                        "请执行: ollama serve 启动服务"
                    )
            elif not provider.api_key:
                raise ValueError(
                    f"LLM提供商 '{provider.name}' 未配置API密钥。\n"
                    "请在系统设置中配置API密钥，或切换到Ollama本地服务"
                )

            keyword_str = '、'.join(keywords) if keywords else '不限'
            doc_type_str = '、'.join(document_types) if document_types else '不限'
            industry_str = '、'.join(industries) if industries else '不限'

            prompt = f"""请帮我搜索关于投标文档的资料。
搜索关键词: {keyword_str}
文档类型: {doc_type_str}
行业: {industry_str}

请返回5-10个可能包含相关投标文档的网站或资源，格式为JSON数组：
[
  {{"title": "文档标题", "url": "网址", "summary": "简介", "source": "来源网站"}}
]
"""

            response = await unified_llm_service.chat(message=prompt)
            content = response.get('content', '')

            import json
            import re
            
            json_match = re.search(r'\[.*\]', content, re.DOTALL)
            if json_match:
                results = json.loads(json_match.group())
        
        except ValueError as e:
            logger.error(f"AI搜索配置错误: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"AI搜索失败: {str(e)}")
            raise ValueError(f"AI搜索服务暂时不可用: {str(e)}")
        
        return results

    def _search_internet(self, keywords=None, document_types=None, industries=None):
        """
        搜索互联网（同步包装）
        """
        keywords = keywords or []
        document_types = document_types or []
        industries = industries or []

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(
                self._search_internet_async(keywords, document_types, industries)
            )
        finally:
            loop.close()

    @action(detail=True, methods=['post'])
    def retry(self, request, pk=None):
        """
        重试失败的搜索任务
        """
        task = self.get_object()
        if task.status != 'failed':
            return UnifiedResponse.error(message='只能重试失败的任务')
        
        task.status = 'pending'
        task.error_message = ''
        task.save(update_fields=['status', 'error_message'])
        
        self._execute_ai_search(task)
        
        return UnifiedResponse.success(data=AISearchTaskSerializer(task).data)
