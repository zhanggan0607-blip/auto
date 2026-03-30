"""
招标项目模块 - 视图（优化版）
"""
import logging
from rest_framework import status, generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
from django.db.models import Q

from .models import TenderSource, TenderProject, TenderFile, TenderKeyword, CrawlerTask

logger = logging.getLogger(__name__)
from .serializers import (
    TenderSourceSerializer, TenderProjectListSerializer, TenderProjectDetailSerializer,
    TenderProjectCreateSerializer, TenderProjectUpdateSerializer, TenderFileSerializer,
    TenderKeywordSerializer, CrawlerTaskSerializer,
    TenderBatchDeleteSerializer, TenderBatchUpdateSerializer
)
from .services import TenderService, TenderKeywordService, CrawlerTaskService
from utils.permissions import IsAdminUser
from utils.responses import APIResponse
from core.cache import cache_result


class TenderSourceListView(generics.ListCreateAPIView):
    """
    招标来源列表视图
    """
    queryset = TenderSource.objects.all()
    serializer_class = TenderSourceSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAuthenticated(), IsAdminUser()]
        return [IsAuthenticated()]


class TenderSourceDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    招标来源详情视图
    """
    queryset = TenderSource.objects.all()
    serializer_class = TenderSourceSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]


class TenderProjectListView(generics.ListCreateAPIView):
    """
    招标项目列表视图
    """
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return TenderProjectCreateSerializer
        return TenderProjectListSerializer

    def get_queryset(self):
        """
        支持多条件搜索
        """
        return TenderService.search_tenders(
            keyword=self.request.query_params.get('keyword'),
            region=self.request.query_params.get('region'),
            industry=self.request.query_params.get('industry'),
            status=self.request.query_params.get('status'),
            start_date=self.request.query_params.get('start_date'),
            end_date=self.request.query_params.get('end_date'),
            is_favorite=self.request.query_params.get('is_favorite'),
            is_read=self.request.query_params.get('is_read')
        )

    def list(self, request, *args, **kwargs):
        """
        重写list方法，使用自定义响应格式
        """
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return APIResponse.success(data={'list': serializer.data})

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class TenderProjectDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    招标项目详情视图
    """
    queryset = TenderProject.objects.select_related('source').prefetch_related('files')
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return TenderProjectUpdateSerializer
        return TenderProjectDetailSerializer

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return APIResponse.success(data=serializer.data)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return APIResponse.success(data=serializer.data, message='更新成功')


class TenderProjectBatchView(APIView):
    """
    招标项目批量操作视图
    """
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def delete(self, request):
        """
        批量删除
        """
        serializer = TenderBatchDeleteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        tender_ids = serializer.validated_data.get('ids')
        count = TenderService.batch_delete(tender_ids, request.user)
        
        return APIResponse.success(
            data={'deleted_count': count},
            message=f'成功删除 {count} 条记录'
        )

    @transaction.atomic
    def patch(self, request):
        """
        批量更新状态
        """
        serializer = TenderBatchUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        tender_ids = serializer.validated_data.get('ids')
        new_status = serializer.validated_data.get('status')
        
        count = TenderService.batch_update_status(tender_ids, new_status, request.user)
        
        return APIResponse.success(
            data={'updated_count': count},
            message=f'成功更新 {count} 条记录'
        )


class TenderProjectFavoriteView(APIView):
    """
    招标项目收藏视图
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        """
        收藏/取消收藏
        """
        try:
            is_favorite = TenderService.toggle_favorite(pk)
            return APIResponse.success(
                data={'is_favorite': is_favorite},
                message='收藏成功' if is_favorite else '取消收藏成功'
            )
        except TenderProject.DoesNotExist:
            return APIResponse.error(message='招标项目不存在', status_code=status.HTTP_404_NOT_FOUND)


class TenderProjectReadView(APIView):
    """
    招标项目已读视图
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        """
        标记为已读
        """
        try:
            TenderService.mark_as_read(pk)
            return APIResponse.success(message='已标记为已读')
        except TenderProject.DoesNotExist:
            return APIResponse.error(message='招标项目不存在', status_code=status.HTTP_404_NOT_FOUND)


class TenderFileListView(generics.ListCreateAPIView):
    """
    招标文件列表视图
    """
    serializer_class = TenderFileSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        tender_id = self.request.query_params.get('tender_id')
        if tender_id:
            return TenderFile.objects.filter(tender_id=tender_id)
        return TenderFile.objects.all()

    def list(self, request, *args, **kwargs):
        """
        重写list方法，使用自定义响应格式
        """
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return APIResponse.success(data={'list': serializer.data})


class TenderFileDetailView(generics.RetrieveDestroyAPIView):
    """
    招标文件详情视图
    """
    queryset = TenderFile.objects.all()
    serializer_class = TenderFileSerializer
    permission_classes = [IsAuthenticated]


class TenderKeywordListView(generics.ListCreateAPIView):
    """
    招标关键词列表视图
    """
    serializer_class = TenderKeywordSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        category = self.request.query_params.get('category')
        return TenderKeywordService.get_active_keywords(category)

    def list(self, request, *args, **kwargs):
        """
        重写list方法，使用自定义响应格式
        """
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return APIResponse.success(data={'list': serializer.data})

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class TenderKeywordDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    招标关键词详情视图
    """
    queryset = TenderKeyword.objects.all()
    serializer_class = TenderKeywordSerializer
    permission_classes = [IsAuthenticated]


class CrawlerTaskListView(generics.ListCreateAPIView):
    """
    爬虫任务列表视图
    """
    queryset = CrawlerTask.objects.select_related('source')
    serializer_class = CrawlerTaskSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        return queryset

    def list(self, request, *args, **kwargs):
        """
        重写list方法，使用自定义响应格式
        """
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return APIResponse.success(data={'list': serializer.data})

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class CrawlerTaskDetailView(generics.RetrieveAPIView):
    """
    爬虫任务详情视图
    """
    queryset = CrawlerTask.objects.select_related('source')
    serializer_class = CrawlerTaskSerializer
    permission_classes = [IsAuthenticated]


class CrawlerTaskExecuteView(APIView):
    """
    执行爬虫任务视图
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        """
        执行爬虫任务
        """
        try:
            CrawlerTaskService.start_task(pk)
            return APIResponse.success(message='任务已提交执行')
        except CrawlerTask.DoesNotExist:
            return APIResponse.error(message='任务不存在', status_code=status.HTTP_404_NOT_FOUND)
        except ValueError as e:
            logger.warning(f"爬虫任务参数错误: {str(e)}")
            return APIResponse.error(message='任务参数有误，请检查配置')


class TenderStatisticsView(APIView):
    """
    招标统计视图
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        获取招标统计数据
        """
        data = TenderService.get_statistics()
        return APIResponse.success(data=data)


class CrawlerNoticeTypesView(APIView):
    """
    爬虫公告类型视图
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        获取支持的公告类型
        """
        from crawler.shanghai_gov_crawler_v2 import ShanghaiGovCrawler
        
        crawler = ShanghaiGovCrawler()
        notice_types = crawler.get_notice_types()
        
        result = [
            {
                'code': code,
                'name': info['name'],
            }
            for code, info in notice_types.items()
        ]
        
        return APIResponse.success(data={'list': result})


class CrawlerExecuteView(APIView):
    """
    执行爬虫视图
    仅限管理员使用
    """
    permission_classes = [IsAuthenticated, IsAdminUser]

    def post(self, request):
        """
        执行爬虫任务
        
        请求参数:
        - source_code: 来源代码 (默认 sh_gov)
        - notice_types: 公告类型列表 (可选)
        - keywords: 关键词列表 (可选)
        - start_date: 开始日期 (可选)
        - end_date: 结束日期 (可选)
        - page: 页码 (默认 1)
        - page_size: 每页数量 (默认 20)
        """
        source_code = request.data.get('source_code', 'sh_gov')
        notice_types = request.data.get('notice_types')
        keywords = request.data.get('keywords')
        start_date = request.data.get('start_date')
        end_date = request.data.get('end_date')
        page = request.data.get('page', 1)
        page_size = request.data.get('page_size', 20)
        
        try:
            source = TenderSource.objects.get(code=source_code, is_active=True)
        except TenderSource.DoesNotExist:
            return APIResponse.error(message='数据来源不存在或未启用')
        
        task = CrawlerTask.objects.create(
            name=f"手动采集-{source.name}",
            source=source,
            task_type='manual',
            params={
                'notice_types': notice_types,
                'keywords': keywords,
                'start_date': start_date,
                'end_date': end_date,
                'page': page,
                'page_size': page_size,
            },
            created_by=request.user
        )
        
        from crawler.tasks import execute_crawler_task
        execute_crawler_task.delay(task.id)
        
        return APIResponse.success(
            data={'task_id': task.id},
            message='爬虫任务已提交执行'
        )


class CrawlerSyncExecuteView(APIView):
    """
    同步执行爬虫视图（用于测试）
    仅限管理员使用
    """
    permission_classes = [IsAuthenticated, IsAdminUser]

    def post(self, request):
        """
        同步执行爬虫任务（直接返回结果）
        
        请求参数:
        - source_code: 来源代码 (默认 china_gov)
        - notice_types: 公告类型列表 (可选)
        - keywords: 关键词列表 (可选)
        - start_date: 开始日期 (可选)
        - end_date: 结束日期 (可选)
        - region: 地区过滤 (可选)
        - page: 页码 (默认 1)
        - page_size: 每页数量 (默认 10)
        """
        source_code = request.data.get('source_code', 'china_gov')
        notice_types = request.data.get('notice_types')
        keywords = request.data.get('keywords')
        start_date = request.data.get('start_date')
        end_date = request.data.get('end_date')
        region = request.data.get('region')
        page = request.data.get('page', 1)
        page_size = request.data.get('page_size', 10)
        
        if page_size > 20:
            page_size = 20
        
        try:
            if source_code == 'china_gov':
                from crawler.china_gov_crawler import ChinaGovCrawler
                crawler = ChinaGovCrawler()
                results = crawler.crawl(
                    notice_types=notice_types,
                    keywords=keywords,
                    page=page,
                    page_size=page_size,
                    start_date=start_date,
                    end_date=end_date,
                    region=region
                )
            else:
                from crawler.shanghai_gov_crawler_v2 import ShanghaiGovCrawler
                crawler = ShanghaiGovCrawler()
                results = crawler.crawl(
                    notice_types=notice_types,
                    keywords=keywords,
                    page=page,
                    page_size=page_size,
                    start_date=start_date,
                    end_date=end_date
                )
            
            return APIResponse.success(
                data={
                    'list': results,
                    'total': len(results)
                },
                message=f'成功获取 {len(results)} 条数据'
            )
            
        except Exception as e:
            logger.error(f"同步执行爬虫失败: {str(e)}")
            return APIResponse.error(message='执行失败，请稍后重试')


class TenderProxyView(APIView):
    """
    招标公告代理视图 - 用于代理访问外部网站
    解决浏览器直接访问被拦截的问题
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        代理获取外部页面内容
        
        参数:
        - url: 要访问的URL
        """
        import requests
        from urllib.parse import urlparse
        
        target_url = request.query_params.get('url')
        
        if not target_url:
            return APIResponse.error(message='缺少URL参数')
        
        # 验证URL是否为允许的域名
        allowed_domains = [
            'www.ccgp.gov.cn',
            'ccgp.gov.cn',
            'www.shzfcg.cn',
            'shzfcg.cn'
        ]
        
        parsed_url = urlparse(target_url)
        if parsed_url.netloc not in allowed_domains:
            return APIResponse.error(message='不允许访问该域名')
        
        try:
            # 中国政府采购网有严格的反爬虫机制，详情页面无法正常访问
            # 直接返回提示页面，引导用户手动访问
            html_content = f'''
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <title>查看原文</title>
                <style>
                    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
                    body {{ 
                        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        min-height: 100vh;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        padding: 20px;
                    }}
                    .card {{ 
                        background: white;
                        border-radius: 16px;
                        box-shadow: 0 20px 60px rgba(0,0,0,0.3);
                        max-width: 600px;
                        width: 100%;
                        padding: 40px;
                        text-align: center;
                    }}
                    .icon {{ 
                        width: 80px;
                        height: 80px;
                        background: #fff3e0;
                        border-radius: 50%;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        margin: 0 auto 24px;
                        font-size: 40px;
                    }}
                    .title {{ 
                        color: #303133;
                        font-size: 24px;
                        font-weight: 600;
                        margin-bottom: 16px;
                    }}
                    .message {{ 
                        color: #606266;
                        line-height: 1.8;
                        margin-bottom: 24px;
                    }}
                    .steps {{ 
                        text-align: left;
                        background: #f5f7fa;
                        border-radius: 8px;
                        padding: 20px;
                        margin-bottom: 24px;
                    }}
                    .steps ol {{ 
                        margin: 0;
                        padding-left: 20px;
                    }}
                    .steps li {{ 
                        color: #606266;
                        line-height: 2;
                    }}
                    .link-box {{ 
                        background: #ecf5ff;
                        border: 1px solid #b3d8ff;
                        border-radius: 8px;
                        padding: 16px;
                        margin-bottom: 24px;
                    }}
                    .link-label {{ 
                        color: #409eff;
                        font-size: 14px;
                        margin-bottom: 8px;
                    }}
                    .link-url {{ 
                        color: #303133;
                        word-break: break-all;
                        font-size: 13px;
                    }}
                    .btn {{ 
                        display: inline-block;
                        background: linear-gradient(135deg, #409eff 0%, #66b1ff 100%);
                        color: white;
                        padding: 14px 32px;
                        border-radius: 8px;
                        text-decoration: none;
                        font-size: 16px;
                        font-weight: 500;
                        transition: all 0.3s;
                        box-shadow: 0 4px 12px rgba(64, 158, 255, 0.4);
                    }}
                    .btn:hover {{ 
                        transform: translateY(-2px);
                        box-shadow: 0 6px 16px rgba(64, 158, 255, 0.5);
                    }}
                    .tip {{ 
                        margin-top: 20px;
                        color: #909399;
                        font-size: 12px;
                    }}
                </style>
            </head>
            <body>
                <div class="card">
                    <div class="icon">📄</div>
                    <div class="title">查看原文公告</div>
                    <div class="message">
                        该公告来源于中国政府采购网，由于网站访问限制，请通过以下方式查看原文：
                    </div>
                    <div class="steps">
                        <ol>
                            <li>点击下方按钮直接跳转到原文页面</li>
                            <li>如无法访问，请在中国政府采购网搜索项目名称</li>
                        </ol>
                    </div>
                    <div class="link-box">
                        <div class="link-label">原文链接</div>
                        <div class="link-url">{target_url}</div>
                    </div>
                    <a href="{target_url}" target="_blank" class="btn">打开原文页面</a>
                    <div class="tip">提示：如遇到"页面不存在"，请尝试刷新或手动搜索</div>
                </div>
            </body>
            </html>
            '''
            return Response(html_content, content_type='text/html; charset=utf-8')
            
        except Exception as e:
            logger.error(f"代理请求失败: {str(e)}")
            return APIResponse.error(message='获取页面失败，请稍后重试')


class CrawlSyncView(APIView):
    """
    采集数据同步视图
    将 crawler 采集的数据同步到 tender_projects
    """
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        """
        获取同步状态
        """
        from .services import CrawlToTenderSyncService
        status = CrawlToTenderSyncService.get_sync_status()
        return APIResponse.success(data=status)

    def post(self, request):
        """
        执行同步
        """
        from .services import CrawlToTenderSyncService

        limit = request.data.get('limit')
        if limit:
            limit = int(limit)

        try:
            result = CrawlToTenderSyncService.sync_all(limit=limit)
            return APIResponse.success(
                data=result,
                message=f"同步完成: 新增 {result['created']} 条, 更新 {result['updated']} 条, 跳过 {result['skipped']} 条"
            )
        except Exception as e:
            logger.error(f"同步失败: {str(e)}")
            return APIResponse.error(message=f'同步失败: {str(e)}')
