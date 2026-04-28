"""
招标项目模块 - 服务层
"""
import logging
from django.db import transaction
from django.db.models import Q, Count, Case, When, IntegerField
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
                       start_date=None, end_date=None, is_favorite=None, is_read=None,
                       source_name=None):
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
        queryset = TenderProject.objects.filter(is_deleted=False).select_related('source').annotate(
            files_count=Count('files')
        )
        
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
        
        if source_name:
            queryset = queryset.filter(source__name=source_name)
        
        return queryset.order_by('source__name', '-publish_date')
    
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
        from django.shortcuts import get_object_or_404
        tender = get_object_or_404(TenderProject, pk=tender_id)
        
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
        批量软删除招标项目
        
        Args:
            tender_ids: 招标项目ID列表
            user: 操作用户
            
        Returns:
            int: 删除数量
        """
        count = TenderProject.objects.filter(id__in=tender_ids).update(is_deleted=True)
        logger.info(f"批量软删除招标项目: {tender_ids}, 操作人: {user.id}")
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
        from django.shortcuts import get_object_or_404
        tender = get_object_or_404(TenderProject, pk=tender_id)
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
        
        stats = TenderProject.objects.aggregate(
            total=Count('id'),
            pending=Count(Case(When(status='pending', then=1), output_field=IntegerField())),
            submitted=Count(Case(When(status='submitted', then=1), output_field=IntegerField())),
            won=Count(Case(When(status='won', then=1), output_field=IntegerField())),
            lost=Count(Case(When(status='lost', then=1), output_field=IntegerField())),
            favorite=Count(Case(When(is_favorite=True, then=1), output_field=IntegerField())),
            unread=Count(Case(When(is_read=False, then=1), output_field=IntegerField())),
            collected=Count(Case(When(source__isnull=False, then=1), output_field=IntegerField())),
        )
        data = {k: v or 0 for k, v in stats.items()}
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
        匹配关键词（使用缓存优化）

        Args:
            text: 待匹配文本

        Returns:
            list: 匹配的关键词列表
        """
        cache_key = f"{TenderService.CACHE_PREFIX}:active_keywords"
        keywords_data = cache.get(cache_key)

        if keywords_data is None:
            keywords = TenderKeyword.objects.filter(is_active=True)
            keywords_data = [(kw.keyword, kw.keyword.lower()) for kw in keywords]
            cache.set(cache_key, keywords_data, 300)

        text_lower = text.lower()
        matched = [kw for kw, kw_lower in keywords_data if kw_lower in text_lower]

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
        from django.shortcuts import get_object_or_404
        task = get_object_or_404(CrawlerTask, pk=task_id)
        
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
        from django.shortcuts import get_object_or_404
        task = get_object_or_404(CrawlerTask, pk=task_id)
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
        同步所有未同步的采集数据（批量优化版）

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

        batch_size = 100
        crawl_results = list(queryset)

        existing_tenders = {}
        for t in TenderProject.objects.filter(
            source_url__in=[r.source_url for r in crawl_results if r.source_url]
        ):
            if t.source_url not in existing_tenders:
                existing_tenders[t.source_url] = t

        to_create = []
        to_update = []
        crawl_to_update = []

        for crawl_result in crawl_results:
            try:
                if not crawl_result.source_url:
                    stats['skipped'] += 1
                    continue

                tender_data = cls._map_fields(crawl_result)
                tender_data['source'] = cls._get_or_create_source(crawl_result)
                tender_data['keywords_matched'] = crawl_result.matched_companies or []

                existing = existing_tenders.get(crawl_result.source_url)
                if existing:
                    for field, value in tender_data.items():
                        if field != 'source_url':
                            setattr(existing, field, value)
                    to_update.append(existing)
                    crawl_to_update.append((crawl_result, 'updated'))
                else:
                    to_create.append(TenderProject(**tender_data))
                    crawl_to_update.append((crawl_result, 'created'))
            except Exception as e:
                stats['failed'] += 1
                stats['errors'].append({
                    'crawl_id': crawl_result.id,
                    'title': crawl_result.title[:50] if crawl_result.title else '',
                    'error': str(e)
                })
                logger.error(f"同步准备失败: {crawl_result.id} - {str(e)}")

        if to_create:
            try:
                TenderProject.objects.bulk_create(to_create, ignore_conflicts=True)
                stats['created'] = len(to_create)
            except Exception as e:
                stats['failed'] += len(to_create)
                logger.error(f"批量创建失败: {str(e)}")

        if to_update:
            update_fields = list(cls.FIELD_MAPPING.values())
            update_fields = [f for f in update_fields if f != 'source_url']
            update_fields.extend(['keywords_matched', 'source'])
            try:
                TenderProject.objects.bulk_update(to_update, update_fields, batch_size=batch_size)
                stats['updated'] = len(to_update)
            except Exception as e:
                stats['failed'] += len(to_update)
                logger.error(f"批量更新失败: {str(e)}")

        synced_ids = []
        for crawl_result, action in crawl_to_update:
            if action in ('created', 'updated'):
                crawl_result.status = cls.SYNC_STATUS_SYNCED
                synced_ids.append(crawl_result)

        if synced_ids:
            CrawlResult.objects.filter(
                id__in=[r.id for r in synced_ids]
            ).update(status=cls.SYNC_STATUS_SYNCED)

        cls._invalidate_cache()

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
        source_code = template.code
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

        synced = CrawlResult.objects.filter(status=cls.SYNC_STATUS_SYNCED).count()
        pending = CrawlResult.objects.filter(status__in=['pending', 'processed', 'matched']).count()
        total = synced + pending

        tender_count = TenderProject.objects.count()
        tender_with_source = TenderProject.objects.filter(source__isnull=False).count()

        return {
            'crawl_pending': pending,
            'crawl_synced': synced,
            'crawl_total': total,
            'tender_total': tender_count,
            'tender_from_crawl': tender_with_source
        }
