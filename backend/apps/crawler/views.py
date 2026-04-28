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
from common.crawler import CrawlerConfig
from common.views.base import BaseViewSet, APIResponseMixin, AuthenticatedModelViewSet
from core.progress_tracker import progress_tracker
from utils.responses import UnifiedResponse

logger = logging.getLogger(__name__)


class WebsiteTemplateViewSet(AuthenticatedModelViewSet):
    """
    网站模板视图集 - 模板为共享资源，不按用户过滤
    """
    queryset = WebsiteTemplate.objects.all()
    filterset_fields = ['website_type', 'is_active']
    search_fields = ['name', 'code', 'base_url']
    ordering_fields = ['priority', 'created_at']
    ordering = ['-priority', '-created_at']

    def get_queryset(self):
        return WebsiteTemplate.objects.all()
    
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
        summary='测试网站模板配置（无需保存）',
        description='接受模板配置数据，直接测试而不保存到数据库'
    )
    @action(detail=False, methods=['post'])
    def test_config(self, request):
        """
        测试网站模板配置 - 不保存到数据库
        用于新建/编辑表单中的"测试配置"按钮
        """
        import requests as req_lib
        import threading

        base_url = request.data.get('base_url', '').strip()
        if not base_url:
            return UnifiedResponse.error(message='基础URL不能为空')

        selectors = request.data.get('selectors', {}) or {}
        request_config = request.data.get('request_config', {}) or {}
        requires_javascript = request.data.get('requires_javascript', False)

        test_result = {'success': False, 'data': [], 'error': None, 'strategy': None}

        def _test_http():
            try:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                }
                if request_config.get('headers'):
                    headers.update(request_config['headers'])

                resp = req_lib.get(
                    base_url,
                    headers=headers,
                    timeout=15,
                    allow_redirects=True,
                    verify=False
                )
                resp.encoding = resp.apparent_encoding

                if resp.status_code == 200 and len(resp.text) > 500:
                    from bs4 import BeautifulSoup
                    soup = BeautifulSoup(resp.text, 'html.parser')
                    if selectors:
                        items = soup.select(selectors.get('item_container', selectors.get('list', 'body')))
                    else:
                        items = soup.select('li, tr, .item, .list-item, article')

                    sample_data = []
                    for item in items[:3]:
                        title_el = item.select_one(selectors.get('title', 'a, h3, h4, .title')) if selectors else item.select_one('a, h3, h4, .title')
                        link_el = item.select_one(selectors.get('link', 'a')) if selectors else item.select_one('a')
                        sample_data.append({
                            'title': title_el.get_text(strip=True) if title_el else '',
                            'url': link_el.get('href', '') if link_el else '',
                            'source_url': base_url
                        })

                    test_result['success'] = len(sample_data) > 0
                    test_result['data'] = sample_data
                    test_result['strategy'] = 'HTTP'
                    return len(sample_data) > 0
                return False
            except Exception as e:
                logger.info(f"HTTP测试失败: {str(e)}")
                return False

        def _test_selenium():
            try:
                from .models import WebsiteTemplate as WTModel
                temp_template = WTModel(
                    name=request.data.get('name', '测试模板'),
                    code=f'__test_{uuid.uuid4().hex[:8]}',
                    base_url=base_url,
                    website_type=request.data.get('website_type', 'other'),
                    selectors=selectors,
                    request_config=request_config,
                    requires_javascript=True,
                    requires_login=request.data.get('requires_login', False),
                    login_config=request.data.get('login_config', {}) or {},
                    pagination_config=request.data.get('pagination_config', {}) or {},
                )
                config = CrawlerConfig(
                    headless=True,
                    timeout=20,
                    page_load_timeout=25,
                    implicit_wait=5,
                    request_delay_min=0.5,
                    request_delay_max=1.0
                )
                engine = UniversalCrawlerEngine(
                    config=config,
                    website_template=temp_template,
                    enable_multi_strategy=False
                )
                results = engine.crawl(
                    target_url=base_url,
                    max_pages=1
                )
                if results:
                    test_result['success'] = True
                    test_result['data'] = results[:3]
                    test_result['strategy'] = 'Selenium'
                    return True
                return False
            except Exception as e:
                logger.info(f"Selenium测试失败: {str(e)}")
                test_result['error'] = str(e)
                return False

        def run_test():
            http_ok = _test_http()
            if not http_ok:
                _test_selenium()

        thread = threading.Thread(target=run_test)
        thread.daemon = True
        thread.start()
        thread.join(timeout=60)

        if thread.is_alive():
            return UnifiedResponse.error(
                message='测试超时（60秒），目标网站可能无法访问。建议检查URL是否正确，或确认网站是否需要特殊认证。',
                status_code=status.HTTP_400_BAD_REQUEST
            )

        if test_result['success']:
            return UnifiedResponse.success(
                message=f'测试成功（{test_result["strategy"]}策略），获取到 {len(test_result["data"])} 条数据',
                data={'sample_data': test_result['data']}
            )

        error_msg = test_result['error'] or '未能获取到数据'
        if requires_javascript:
            error_msg += '。该网站需要JavaScript渲染，请确认浏览器驱动(ChromeDriver)已正确安装。'
        return UnifiedResponse.error(
            message=f'测试失败: {error_msg}',
            status_code=status.HTTP_400_BAD_REQUEST
        )

    @extend_schema(
        summary='测试网站模板',
        description='测试网站模板配置是否正确'
    )
    @action(detail=True, methods=['post'])
    def test(self, request, pk=None):
        """
        测试网站模板 - 轻量级快速测试
        不使用多策略降级，直接按模板配置测试，避免累积超时
        """
        template = self.get_object()
        import requests as req_lib
        import threading

        test_result = {'success': False, 'data': [], 'error': None, 'strategy': None}

        def _test_http():
            try:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                }
                request_config = template.request_config or {}
                if request_config.get('headers'):
                    headers.update(request_config['headers'])

                resp = req_lib.get(
                    template.base_url,
                    headers=headers,
                    timeout=15,
                    allow_redirects=True,
                    verify=False
                )
                resp.encoding = resp.apparent_encoding

                if resp.status_code == 200 and len(resp.text) > 500:
                    from bs4 import BeautifulSoup
                    soup = BeautifulSoup(resp.text, 'html.parser')
                    selectors = template.selectors or {}
                    if selectors:
                        items = soup.select(selectors.get('item_container', selectors.get('list', 'body')))
                    else:
                        items = soup.select('li, tr, .item, .list-item, article')

                    sample_data = []
                    for item in items[:3]:
                        title_el = item.select_one(selectors.get('title', 'a, h3, h4, .title')) if selectors else item.select_one('a, h3, h4, .title')
                        link_el = item.select_one(selectors.get('link', 'a')) if selectors else item.select_one('a')
                        sample_data.append({
                            'title': title_el.get_text(strip=True) if title_el else '',
                            'url': link_el.get('href', '') if link_el else '',
                            'source_url': template.base_url
                        })

                    test_result['success'] = len(sample_data) > 0
                    test_result['data'] = sample_data
                    test_result['strategy'] = 'HTTP'
                    return len(sample_data) > 0
                return False
            except Exception as e:
                logger.info(f"HTTP测试失败: {str(e)}")
                return False

        def _test_selenium():
            try:
                config = CrawlerConfig(
                    headless=True,
                    timeout=20,
                    page_load_timeout=25,
                    implicit_wait=5,
                    request_delay_min=0.5,
                    request_delay_max=1.0
                )
                engine = UniversalCrawlerEngine(
                    config=config,
                    website_template=template,
                    enable_multi_strategy=False
                )
                results = engine.crawl(
                    target_url=template.base_url,
                    max_pages=1
                )
                if results:
                    test_result['success'] = True
                    test_result['data'] = results[:3]
                    test_result['strategy'] = 'Selenium'
                    return True
                return False
            except Exception as e:
                logger.info(f"Selenium测试失败: {str(e)}")
                test_result['error'] = str(e)
                return False

        def run_test():
            http_ok = _test_http()
            if not http_ok:
                _test_selenium()

        thread = threading.Thread(target=run_test)
        thread.daemon = True
        thread.start()
        thread.join(timeout=60)

        if thread.is_alive():
            return UnifiedResponse.error(
                message='测试超时（60秒），目标网站可能无法访问。建议检查URL是否正确，或确认网站是否需要特殊认证。',
                status_code=status.HTTP_400_BAD_REQUEST
            )

        if test_result['success']:
            return UnifiedResponse.success(
                message=f'测试成功（{test_result["strategy"]}策略），获取到 {len(test_result["data"])} 条数据',
                data={'sample_data': test_result['data']}
            )

        error_msg = test_result['error'] or '未能获取到数据'
        if template.requires_javascript:
            error_msg += '。该网站需要JavaScript渲染，请确认浏览器驱动(ChromeDriver)已正确安装。'
        return UnifiedResponse.error(
            message=f'测试失败: {error_msg}',
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
