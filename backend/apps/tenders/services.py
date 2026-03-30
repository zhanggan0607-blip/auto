"""
招标项目模块 - 服务层
"""
import logging
from django.db import transaction
from django.db.models import Q, Count
from django.utils import timezone
from django.core.cache import cache

from .models import TenderSource, TenderProject, TenderFile, TenderKeyword, CrawlerTask

logger = logging.getLogger(__name__)


class TenderService:
    """
    招标服务类
    """
    
    CACHE_PREFIX = 'tender'
    CACHE_TIMEOUT = 300
    
    @staticmethod
    def search_tenders(keyword=None, region=None, industry=None, status=None,
                       start_date=None, end_date=None, is_favorite=None, is_read=None):
        """
        搜索招标项目
        
        Args:
            keyword: 关键词
            region: 地区
            industry: 行业
            status: 状态
            start_date: 开始日期
            end_date: 结束日期
            is_favorite: 是否收藏
            is_read: 是否已读
            
        Returns:
            QuerySet: 招标项目查询集
        """
        queryset = TenderProject.objects.select_related('source').prefetch_related('files')
        
        if keyword:
            queryset = queryset.filter(
                Q(title__icontains=keyword) |
                Q(project_code__icontains=keyword) |
                Q(description__icontains=keyword)
            )
        
        if region:
            queryset = queryset.filter(region__icontains=region)
        
        if industry:
            queryset = queryset.filter(industry__icontains=industry)
        
        if status:
            queryset = queryset.filter(status=status)
        
        if start_date:
            queryset = queryset.filter(publish_date__gte=start_date)
        
        if end_date:
            queryset = queryset.filter(publish_date__lte=end_date)
        
        if is_favorite is not None:
            queryset = queryset.filter(is_favorite=is_favorite)
        
        if is_read is not None:
            queryset = queryset.filter(is_read=is_read)
        
        return queryset.order_by('-publish_date')
    
    @staticmethod
    @transaction.atomic
    def create_tender(created_by, **kwargs):
        """
        创建招标项目
        
        Args:
            created_by: 创建人
            **kwargs: 招标项目字段
            
        Returns:
            TenderProject: 招标项目对象
        """
        tender = TenderProject.objects.create(created_by=created_by, **kwargs)
        logger.info(f"招标项目创建成功: {tender.id} - {tender.title}")
        return tender
    
    @staticmethod
    @transaction.atomic
    def update_tender(tender_id, **kwargs):
        """
        更新招标项目
        
        Args:
            tender_id: 招标项目ID
            **kwargs: 更新字段
            
        Returns:
            TenderProject: 招标项目对象
        """
        tender = TenderProject.objects.get(pk=tender_id)
        
        for field, value in kwargs.items():
            if hasattr(tender, field):
                setattr(tender, field, value)
        
        tender.save()
        TenderService.invalidate_tender_cache(tender_id)
        logger.info(f"招标项目更新成功: {tender_id}")
        return tender
    
    @staticmethod
    @transaction.atomic
    def batch_delete(tender_ids, user):
        """
        批量删除招标项目
        
        Args:
            tender_ids: 招标项目ID列表
            user: 操作用户
            
        Returns:
            int: 删除数量
        """
        count = TenderProject.objects.filter(id__in=tender_ids).delete()[0]
        logger.info(f"批量删除招标项目: {tender_ids}, 操作人: {user.id}")
        return count
    
    @staticmethod
    @transaction.atomic
    def batch_update_status(tender_ids, status, user):
        """
        批量更新状态
        
        Args:
            tender_ids: 招标项目ID列表
            status: 新状态
            user: 操作用户
            
        Returns:
            int: 更新数量
        """
        count = TenderProject.objects.filter(id__in=tender_ids).update(status=status)
        logger.info(f"批量更新招标状态: {tender_ids} -> {status}, 操作人: {user.id}")
        return count
    
    @staticmethod
    @transaction.atomic
    def toggle_favorite(tender_id):
        """
        切换收藏状态
        
        Args:
            tender_id: 招标项目ID
            
        Returns:
            bool: 新的收藏状态
        """
        tender = TenderProject.objects.get(pk=tender_id)
        tender.is_favorite = not tender.is_favorite
        tender.save()
        return tender.is_favorite
    
    @staticmethod
    @transaction.atomic
    def mark_as_read(tender_id):
        """
        标记为已读
        
        Args:
            tender_id: 招标项目ID
        """
        TenderProject.objects.filter(pk=tender_id).update(is_read=True)
    
    @staticmethod
    def get_statistics():
        """
        获取招标统计数据
        
        Returns:
            dict: 统计数据
        """
        cache_key = f"{TenderService.CACHE_PREFIX}:statistics"
        cached_data = cache.get(cache_key)
        
        if cached_data:
            return cached_data
        
        data = {
            'total': TenderProject.objects.count(),
            'pending': TenderProject.objects.filter(status='pending').count(),
            'submitted': TenderProject.objects.filter(status='submitted').count(),
            'won': TenderProject.objects.filter(status='won').count(),
            'lost': TenderProject.objects.filter(status='lost').count(),
            'favorite': TenderProject.objects.filter(is_favorite=True).count(),
            'unread': TenderProject.objects.filter(is_read=False).count(),
            'collected': TenderProject.objects.filter(source__isnull=False).count(),
        }
        
        cache.set(cache_key, data, TenderService.CACHE_TIMEOUT)
        return data
    
    @staticmethod
    def invalidate_tender_cache(tender_id=None):
        """
        清除招标缓存
        """
        cache.delete(f"{TenderService.CACHE_PREFIX}:statistics")
        if tender_id:
            cache.delete(f"{TenderService.CACHE_PREFIX}:detail:{tender_id}")


class TenderKeywordService:
    """
    招标关键词服务类
    """
    
    @staticmethod
    def get_active_keywords(category=None):
        """
        获取活跃关键词
        
        Args:
            category: 分类
            
        Returns:
            QuerySet: 关键词查询集
        """
        queryset = TenderKeyword.objects.filter(is_active=True)
        if category:
            queryset = queryset.filter(category=category)
        return queryset
    
    @staticmethod
    def match_keywords(text):
        """
        匹配关键词
        
        Args:
            text: 待匹配文本
            
        Returns:
            list: 匹配的关键词列表
        """
        keywords = TenderKeyword.objects.filter(is_active=True)
        matched = []
        
        for kw in keywords:
            if kw.keyword.lower() in text.lower():
                matched.append(kw.keyword)
        
        return matched


class CrawlerTaskService:
    """
    爬虫任务服务类
    """
    
    @staticmethod
    @transaction.atomic
    def create_task(created_by, **kwargs):
        """
        创建爬虫任务
        
        Args:
            created_by: 创建人
            **kwargs: 任务字段
            
        Returns:
            CrawlerTask: 爬虫任务对象
        """
        task = CrawlerTask.objects.create(created_by=created_by, **kwargs)
        logger.info(f"爬虫任务创建成功: {task.id} - {task.name}")
        return task
    
    @staticmethod
    def start_task(task_id):
        """
        启动爬虫任务
        
        Args:
            task_id: 任务ID
        """
        task = CrawlerTask.objects.get(pk=task_id)
        
        if task.status == 'running':
            raise ValueError('任务正在执行中')
        
        from crawler.tasks import execute_crawler_task
        execute_crawler_task.delay(task.id)
        
        task.status = 'pending'
        task.save()
        
        logger.info(f"爬虫任务已启动: {task_id}")
    
    @staticmethod
    def complete_task(task_id, result_count=0, error_message=None):
        """
        完成爬虫任务
        
        Args:
            task_id: 任务ID
            result_count: 结果数量
            error_message: 错误信息
        """
        task = CrawlerTask.objects.get(pk=task_id)
        task.status = 'failed' if error_message else 'completed'
        task.result_count = result_count
        task.error_message = error_message
        task.finished_at = timezone.now()
        task.save()
        
        logger.info(f"爬虫任务完成: {task_id}, 状态: {task.status}")


class CrawlToTenderSyncService:
    """
    采集数据同步到招标项目服务类
    负责将 crawler 模块采集的数据同步到 tender_projects 表
    """

    SYNC_STATUS_SYNCED = 'synced'
    SYNC_STATUS_FAILED = 'failed'

    FIELD_MAPPING = {
        'title': 'title',
        'source_url': 'source_url',
        'detail_url': 'source_url',
        'publish_date': 'publish_date',
        'deadline_date': 'deadline_date',
        'region': 'region',
        'category': 'category',
        'industry': 'industry',
        'budget': 'budget',
        'project_code': 'project_code',
        'purchaser_name': 'purchaser_name',
        'purchaser_contact': 'purchaser_contact',
        'purchaser_phone': 'purchaser_phone',
        'agency_name': 'agency_name',
        'agency_contact': 'agency_contact',
        'agency_phone': 'agency_phone',
        'description': 'description',
        'requirements': 'requirements',
        'raw_data': 'raw_data',
    }

    @classmethod
    def sync_all(cls, limit=None):
        """
        同步所有未同步的采集数据

        Args:
            limit: 限制同步数量

        Returns:
            dict: 同步结果统计
        """
        from apps.crawler.models import CrawlResult

        queryset = CrawlResult.objects.filter(
            status__in=['matched', 'processed']
        ).exclude(
            source_url__isnull=True
        ).exclude(
            source_url=''
        ).order_by('-publish_date')

        if limit:
            queryset = queryset[:limit]

        stats = {
            'total': queryset.count(),
            'created': 0,
            'updated': 0,
            'skipped': 0,
            'failed': 0,
            'errors': []
        }

        for crawl_result in queryset:
            try:
                result = cls.sync_single(crawl_result)
                if result == 'created':
                    stats['created'] += 1
                elif result == 'updated':
                    stats['updated'] += 1
                else:
                    stats['skipped'] += 1
            except Exception as e:
                stats['failed'] += 1
                stats['errors'].append({
                    'crawl_id': crawl_result.id,
                    'title': crawl_result.title[:50],
                    'error': str(e)
                })
                logger.error(f"同步失败: {crawl_result.id} - {str(e)}")

        if stats['errors']:
            logger.warning(f"同步完成，存在 {stats['failed']} 条失败记录")

        return stats

    @classmethod
    def sync_single(cls, crawl_result):
        """
        同步单条采集数据

        Args:
            crawl_result: CrawlResult 对象

        Returns:
            str: 'created'/'updated'/'skipped'
        """
        if not crawl_result.source_url:
            return 'skipped'

        tender_data = cls._map_fields(crawl_result)
        tender_data['source'] = cls._get_or_create_source(crawl_result)
        tender_data['keywords_matched'] = crawl_result.matched_companies or []

        tender, created = TenderProject.objects.update_or_create(
            source_url=crawl_result.source_url,
            defaults=tender_data
        )

        crawl_result.status = cls.SYNC_STATUS_SYNCED
        crawl_result.save(update_fields=['status'])

        cls._invalidate_cache()

        action = '创建' if created else '更新'
        logger.info(f"采集数据同步{tender_data['title'][:30]}... -> 招标项目{'创建' if created else '更新成功'}")
        return 'created' if created else 'updated'

    @classmethod
    def _map_fields(cls, crawl_result):
        """
        字段映射

        Args:
            crawl_result: CrawlResult 对象

        Returns:
            dict: 映射后的字段数据
        """
        data = {}

        for src_field, dst_field in cls.FIELD_MAPPING.items():
            value = getattr(crawl_result, src_field, None)
            if value is not None:
                data[dst_field] = value

        if not data.get('publish_date'):
            data['publish_date'] = timezone.now().date()

        return data

    @classmethod
    def _get_or_create_source(cls, crawl_result):
        """
        获取或创建招标来源

        Args:
            crawl_result: CrawlResult 对象

        Returns:
            TenderSource: 招标来源对象
        """
        if not crawl_result.session or not crawl_result.session.website_template:
            return None

        template = crawl_result.session.website_template
        source_code = f"crawl_{template.code}"
        source_name = template.name

        source, _ = TenderSource.objects.get_or_create(
            code=source_code,
            defaults={
                'name': source_name,
                'source_type': 'government',
                'base_url': template.base_url,
                'is_active': True
            }
        )
        return source

    @classmethod
    def _invalidate_cache(cls):
        """
        清除缓存
        """
        TenderService.invalidate_tender_cache()

    @classmethod
    def get_sync_status(cls):
        """
        获取同步状态统计

        Returns:
            dict: 同步状态统计
        """
        from apps.crawler.models import CrawlResult

        total = CrawlResult.objects.filter(status='matched').count()
        synced = CrawlResult.objects.filter(status=cls.SYNC_STATUS_SYNCED).count()
        pending = total - synced

        tender_count = TenderProject.objects.count()
        tender_with_source = TenderProject.objects.filter(source__isnull=False).count()

        return {
            'crawl_pending': pending,
            'crawl_synced': synced,
            'crawl_total': total,
            'tender_total': tender_count,
            'tender_from_crawl': tender_with_source
        }
