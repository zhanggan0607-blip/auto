"""
SAAS采集模块 - 视图
"""
import logging
import uuid
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, OpenApiParameter

from .models import WebsiteTemplate, CrawlSession, CrawlResult, CrawlLog
from .serializers import (
    WebsiteTemplateSerializer, WebsiteTemplateListSerializer,
    CrawlSessionSerializer, CrawlSessionListSerializer,
    CrawlResultSerializer, CrawlResultListSerializer,
    CrawlLogSerializer, QuickCrawlSerializer, SearchConfigSerializer
)
from .services import UniversalCrawlerEngine
from crawler.base_crawler import CrawlerConfig
from core.viewsets import AuthenticatedModelViewSet, APIResponseMixin
from core.progress_tracker import progress_tracker
from utils.responses import UnifiedResponse

logger = logging.getLogger(__name__)


class WebsiteTemplateViewSet(AuthenticatedModelViewSet):
    """
    网站模板视图集
    """
    queryset = WebsiteTemplate.objects.all()
    filterset_fields = ['website_type', 'is_active']
    search_fields = ['name', 'code', 'base_url']
    ordering_fields = ['priority', 'created_at']
    ordering = ['-priority', '-created_at']
    
    def get_serializer_class(self):
        """
        根据动作选择序列化器
        """
        if self.action == 'list':
            return WebsiteTemplateListSerializer
        return WebsiteTemplateSerializer
    
    def perform_create(self, serializer):
        """
        创建时设置创建人
        """
        serializer.save(created_by=self.request.user)

    @extend_schema(
        summary='检查模板代码是否重复',
        description='检查指定模板代码是否已存在'
    )
    @action(detail=False, methods=['get'])
    def check_duplicate_code(self, request):
        """
        检查模板代码是否重复
        """
        code = request.query_params.get('code', '').strip()
        exclude_id = request.query_params.get('exclude_id')

        if not code:
            return UnifiedResponse.error(message='模板代码不能为空')

        queryset = WebsiteTemplate.objects.filter(code=code)

        if exclude_id:
            try:
                queryset = queryset.exclude(pk=int(exclude_id))
            except (ValueError, TypeError):
                pass

        is_duplicate = queryset.exists()

        return UnifiedResponse.success(
            data={
                'is_duplicate': is_duplicate,
                'code': code
            }
        )

    @extend_schema(
        summary='测试网站模板',
        description='测试网站模板配置是否正确'
    )
    @action(detail=True, methods=['post'])
    def test(self, request, pk=None):
        """
        测试网站模板
        """
        template = self.get_object()

        try:
            config = CrawlerConfig(
                headless=True,
                timeout=30,
                request_delay_min=1.0,
                request_delay_max=2.0
            )

            engine = UniversalCrawlerEngine(config=config, website_template=template)
            results = engine.crawl(
                target_url=template.base_url,
                max_pages=1
            )

            return UnifiedResponse.success(
                message=f'测试成功，获取到 {len(results)} 条数据',
                data={'sample_data': results[:3] if results else []}
            )

        except Exception as e:
            logger.error(f"测试网站模板失败: {str(e)}")
            return UnifiedResponse.error(
                message=f'测试失败: {str(e)}',
                status_code=status.HTTP_400_BAD_REQUEST
            )

    @extend_schema(
        summary='批量测试网站模板',
        description='批量测试所有网站模板，实时返回进度和结果'
    )
    @action(detail=False, methods=['post'])
    def batch_test(self, request):
        """
        批量测试所有启用的网站模板
        返回任务ID，前端通过该ID轮询获取进度
        """
        from django.conf import settings

        template_ids = request.data.get('template_ids', None)
        task_id = f"batch_test_{uuid.uuid4().hex[:12]}"

        templates = WebsiteTemplate.objects.filter(is_active=True)
        if template_ids:
            templates = templates.filter(id__in=template_ids)

        templates = list(templates.order_by('-priority'))
        total = len(templates)

        if total == 0:
            return UnifiedResponse.error(
                message='没有找到要测试的模板',
                status_code=status.HTTP_400_BAD_REQUEST
            )

        steps = []
        for i, t in enumerate(templates):
            steps.append({
                'title': f'测试: {t.name}',
                'description': f'正在准备测试 {t.name}...',
                'progress': 0
            })
        steps.append({
            'title': '生成报告',
            'description': '正在生成测试报告...',
            'progress': 0
        })

        progress_tracker.create_task(
            task_id=task_id,
            task_name='批量测试网站模板',
            total_steps=total + 1,
            description=f'共 {total} 个模板',
            steps=steps
        )
        progress_tracker.start_task(task_id)

        from crawler.tasks import run_batch_template_test

        try:
            task_eager = getattr(settings, 'CELERY_TASK_ALWAYS_EAGER', False)
            if task_eager:
                run_batch_template_test(task_id, [t.id for t in templates])
            else:
                run_batch_template_test.delay(task_id, [t.id for t in templates])
        except Exception as e:
            logger.warning(f"Celery任务发送失败，改用同步执行: {str(e)}")
            import threading
            def run_sync():
                try:
                    run_batch_template_test(task_id, [t.id for t in templates])
                except Exception as ex:
                    logger.error(f"同步执行采集任务失败: {str(ex)}")
                    try:
                        progress_tracker.fail_task(task_id, str(ex))
                    except:
                        pass
            thread = threading.Thread(target=run_sync)
            thread.daemon = True
            thread.start()

        return UnifiedResponse.success(
            message='批量测试任务已启动',
            data={'task_id': task_id, 'total_templates': total}
        )

    @extend_schema(
        summary='获取批量测试进度',
        description='通过task_id获取批量测试进度'
    )
    @action(detail=False, methods=['get'], url_path='batch_test/(?P<task_id>[^/.]+)')
    def get_batch_test_progress(self, request, task_id=None):
        """
        获取批量测试进度
        """
        task = progress_tracker.get_task_status(task_id)
        if task is None:
            return UnifiedResponse.error(
                message='任务不存在或已过期',
                status_code=status.HTTP_404_NOT_FOUND
            )
        return UnifiedResponse.success(data=task)


class CrawlSessionViewSet(APIResponseMixin, viewsets.ModelViewSet):
    """
    采集会话视图集
    """
    queryset = CrawlSession.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['status', 'crawl_type', 'website_template']
    search_fields = ['name', 'target_url']
    ordering_fields = ['created_at', 'started_at']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        """
        根据动作选择序列化器
        """
        if self.action == 'list':
            return CrawlSessionListSerializer
        return CrawlSessionSerializer
    
    def perform_create(self, serializer):
        """
        创建时设置创建人
        """
        serializer.save(created_by=self.request.user)
    
    @extend_schema(
        summary='快速采集',
        description='输入网址快速采集信息',
        request=QuickCrawlSerializer,
        responses={200: CrawlResultListSerializer(many=True)}
    )
    @action(detail=False, methods=['post'])
    def quick_crawl(self, request):
        """
        快速采集 - 输入网址即可采集
        """
        from utils.url_security import is_url_safe

        serializer = QuickCrawlSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        target_url = serializer.validated_data['target_url']

        is_safe, reason = is_url_safe(target_url)
        if not is_safe:
            return UnifiedResponse.error(
                message=f'URL安全验证失败: {reason}',
                status_code=status.HTTP_400_BAD_REQUEST
            )

        keywords = serializer.validated_data.get('keywords', [])
        max_pages = serializer.validated_data.get('max_pages', 5)
        template_id = serializer.validated_data.get('website_template_id')
        save_results = serializer.validated_data.get('save_results', True)
        
        website_template = None
        if template_id:
            try:
                website_template = WebsiteTemplate.objects.get(id=template_id)
            except WebsiteTemplate.DoesNotExist:
                pass
        
        session = None
        if save_results:
            session = CrawlSession.objects.create(
                name=f'快速采集-{target_url[:50]}',
                target_url=target_url,
                website_template=website_template,
                crawl_type='search' if keywords else 'list',
                keywords=keywords,
                params={'max_pages': max_pages},
                status='running',
                created_by=request.user
            )
            session.started_at = timezone.now()
            session.save()
        
        try:
            config = CrawlerConfig(
                headless=True,
                timeout=30,
                request_delay_min=1.0,
                request_delay_max=3.0,
                max_retries=3
            )
            
            engine = UniversalCrawlerEngine(config=config, website_template=website_template)
            results = engine.crawl(
                target_url=target_url,
                keywords=keywords,
                max_pages=max_pages
            )
            
            crawl_results = []
            if save_results and session:
                for result in results:
                    crawl_result = CrawlResult.objects.create(
                        session=session,
                        title=result.get('title', ''),
                        source_url=result.get('source_url', ''),
                        detail_url=result.get('detail_url'),
                        publish_date=result.get('publish_date'),
                        region=result.get('region'),
                        category=result.get('category'),
                        industry=result.get('industry'),
                        budget=result.get('budget'),
                        project_code=result.get('project_code'),
                        purchaser_name=result.get('purchaser_name'),
                        purchaser_contact=result.get('purchaser_contact'),
                        purchaser_phone=result.get('purchaser_phone'),
                        agency_name=result.get('agency_name'),
                        description=result.get('description'),
                        raw_data=result.get('raw_data', {}),
                        status='pending'
                    )
                    crawl_results.append(crawl_result)
                
                session.status = 'completed'
                session.result_count = len(results)
                session.finished_at = timezone.now()
                session.duration = (session.finished_at - session.started_at).seconds
                session.save()
            
            result_serializer = CrawlResultListSerializer(
                crawl_results if save_results else results,
                many=True
            )

            return UnifiedResponse.success(
                message=f'采集完成，共获取 {len(results)} 条数据',
                data={
                    'session_id': session.id if session else None,
                    'results': result_serializer.data
                }
            )

        except Exception as e:
            logger.error(f"快速采集失败: {str(e)}")

            if session:
                session.status = 'failed'
                session.error_message = str(e)
                session.finished_at = timezone.now()
                session.save()

            return UnifiedResponse.error(
                message=f'采集失败: {str(e)}',
                status_code=status.HTTP_400_BAD_REQUEST
            )

    @extend_schema(
        summary='取消采集',
        description='取消正在执行的采集任务'
    )
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """
        取消采集
        """
        session = self.get_object()

        if session.status not in ['pending', 'running']:
            return UnifiedResponse.error(
                message='该任务已完成或已取消',
                status_code=status.HTTP_400_BAD_REQUEST
            )

        session.status = 'cancelled'
        session.finished_at = timezone.now()
        session.save()

        return UnifiedResponse.success(message='任务已取消')

    @extend_schema(
        summary='获取采集结果',
        description='获取指定采集会话的所有结果'
    )
    @action(detail=True, methods=['get'])
    def results(self, request, pk=None):
        """
        获取采集结果
        """
        session = self.get_object()
        results = CrawlResult.objects.filter(session=session)

        serializer = CrawlResultSerializer(results, many=True)
        return UnifiedResponse.success(data=serializer.data)


class CrawlResultViewSet(AuthenticatedModelViewSet):
    """
    采集结果视图集
    """
    queryset = CrawlResult.objects.all()
    filterset_fields = ['status', 'region', 'category', 'industry', 'session']
    search_fields = ['title', 'project_code', 'purchaser_name']
    ordering_fields = ['publish_date', 'created_at', 'budget']
    ordering = ['-publish_date', '-created_at']
    
    def get_serializer_class(self):
        """
        根据动作选择序列化器
        """
        if self.action == 'list':
            return CrawlResultListSerializer
        return CrawlResultSerializer
    
    @extend_schema(
        summary='批量更新状态',
        description='批量更新采集结果状态'
    )
    @action(detail=False, methods=['post'])
    def batch_update_status(self, request):
        """
        批量更新状态
        """
        ids = request.data.get('ids', [])
        new_status = request.data.get('status')

        if not ids or not new_status:
            return UnifiedResponse.validation_error(message='缺少必要参数')

        updated = CrawlResult.objects.filter(id__in=ids).update(status=new_status)

        return UnifiedResponse.success(message=f'成功更新 {updated} 条记录')

    @extend_schema(
        summary='获取详情',
        description='获取采集结果的完整详情信息'
    )
    @action(detail=True, methods=['get'])
    def full_detail(self, request, pk=None):
        """
        获取完整详情
        """
        result = self.get_object()

        if not result.detail_url:
            return UnifiedResponse.error(
                message='没有详情链接',
                status_code=status.HTTP_400_BAD_REQUEST
            )

        try:
            config = CrawlerConfig(
                headless=True,
                timeout=30
            )

            engine = UniversalCrawlerEngine(config=config)
            detail_data = engine.get_detail(result.detail_url)

            result.description = detail_data.get('description', '')
            result.raw_data.update(detail_data.get('raw_data', {}))
            result.save()

            serializer = self.get_serializer(result)
            return UnifiedResponse.success(data=serializer.data)

        except Exception as e:
            logger.error(f"获取详情失败: {str(e)}")
            return UnifiedResponse.error(
                message=f'获取详情失败: {str(e)}',
                status_code=status.HTTP_400_BAD_REQUEST
            )


class CrawlLogViewSet(APIResponseMixin, viewsets.ReadOnlyModelViewSet):
    """
    采集日志视图集（只读）
    """
    queryset = CrawlLog.objects.all()
    serializer_class = CrawlLogSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['session', 'level']
    ordering = ['-created_at']
