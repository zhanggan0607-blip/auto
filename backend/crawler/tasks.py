"""
爬虫模块 - Celery异步任务
支持：智能采集、中标结果跟踪、企业匹配
"""
import asyncio
import logging
from celery import shared_task
from django.utils import timezone
from datetime import datetime, timedelta

from django.conf import settings
from apps.tenders.models import TenderSource, TenderProject, CrawlerTask, TenderKeyword, TenderFile
from apps.crawler.models import BidProjectTracking, FailureKnowledge, EnterpriseVectorIndex

logger = logging.getLogger(__name__)


def get_pilot_source(code: str, fallback_name: str = None, fallback_base_url: str = None):
    """
    从PILOT_WEBSITES配置获取TenderSource，不存在则创建

    Args:
        code: 数据源代码
        fallback_name: 备用名称（当配置中不存在时使用）
        fallback_base_url: 备用URL（当配置中不存在时使用）
    """
    for website in settings.PILOT_WEBSITES:
        if website['code'] == code:
            source, created = TenderSource.objects.get_or_create(
                code=code,
                defaults={
                    'name': website['name'],
                    'source_type': 'government',
                    'base_url': website['base_url'],
                    'is_active': website.get('enabled', True),
                }
            )
            if created:
                logger.info(f"自动创建数据源: {source.name} ({source.code})")
            return source

    if fallback_name and fallback_base_url:
        source, created = TenderSource.objects.get_or_create(
            code=code,
            defaults={
                'name': fallback_name,
                'source_type': 'government',
                'base_url': fallback_base_url,
                'is_active': True,
            }
        )
        if created:
            logger.info(f"自动创建数据源: {source.name} ({source.code})")
        return source

    logger.warning(f"未找到数据源配置: {code}")
    return None


@shared_task(bind=True, max_retries=3)
def execute_crawler_task(self, task_id: int):
    """
    执行爬虫任务
    
    Args:
        task_id: 任务ID
    """
    try:
        task = CrawlerTask.objects.select_related('source').get(pk=task_id)
    except CrawlerTask.DoesNotExist:
        logger.error(f"爬虫任务不存在: {task_id}")
        return

    task.status = 'running'
    task.started_at = timezone.now()
    task.save()

    try:
        source = task.source
        source_code = source.code
        params = task.params or {}
        
        keywords = list(TenderKeyword.objects.filter(
            is_active=True, 
            category__in=['industry', 'product']
        ).values_list('keyword', flat=True))
        
        notice_types = params.get('notice_types')
        start_date = params.get('start_date')
        end_date = params.get('end_date')
        region = params.get('region')
        page = params.get('page', 1)
        page_size = params.get('page_size', 20)
        
        if source_code == 'china_gov':
            from .china_gov_crawler import ChinaGovCrawler
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
        elif source_code == 'sh_gov':
            from .shanghai_gov_crawler_v2 import ShanghaiGovCrawler
            crawler = ShanghaiGovCrawler()
            results = crawler.crawl(
                notice_types=notice_types,
                keywords=keywords,
                page=page,
                page_size=page_size,
                start_date=start_date,
                end_date=end_date
            )
        else:
            results = []
            logger.warning(f"未知的爬虫来源: {source_code}")
        
        saved_count = 0
        for item in results:
            try:
                source_url = item.get('source_url', '')
                if not source_url:
                    continue
                
                tender, created = TenderProject.objects.update_or_create(
                    source_url=source_url,
                    defaults={
                        'title': item.get('title', ''),
                        'project_code': item.get('project_code', ''),
                        'source': source,
                        'publish_date': item.get('publish_date'),
                        'deadline_date': item.get('deadline_date'),
                        'open_date': item.get('open_date'),
                        'region': item.get('region', ''),
                        'industry': item.get('industry', ''),
                        'category': item.get('category', ''),
                        'purchaser_name': item.get('purchaser_name', ''),
                        'purchaser_contact': item.get('purchaser_contact', ''),
                        'purchaser_phone': item.get('purchaser_phone', ''),
                        'agency_name': item.get('agency_name', ''),
                        'agency_contact': item.get('agency_contact', ''),
                        'agency_phone': item.get('agency_phone', ''),
                        'budget': item.get('budget'),
                        'description': item.get('description', ''),
                        'requirements': item.get('requirements', ''),
                        'raw_data': item.get('raw_data', {}),
                    }
                )
                
                attachments = item.get('attachments', [])
                if attachments:
                    for att in attachments:
                        TenderFile.objects.get_or_create(
                            tender=tender,
                            file_name=att.get('name', ''),
                            defaults={
                                'file_type': 'document',
                                'download_url': att.get('url', ''),
                                'file_size': att.get('size', 0),
                            }
                        )
                
                if created:
                    saved_count += 1
            except Exception as e:
                logger.error(f"保存招标项目失败: {str(e)}")
                continue
        
        task.status = 'completed'
        task.result_count = saved_count
        task.finished_at = timezone.now()
        task.save()
        
        logger.info(f"爬虫任务完成: {task.name}, 保存 {saved_count} 条数据")
        
    except Exception as e:
        task.status = 'failed'
        task.error_message = str(e)
        task.finished_at = timezone.now()
        task.save()
        
        logger.error(f"爬虫任务执行失败: {task.name}, 错误: {str(e)}")
        
        raise self.retry(exc=e, countdown=60)


@shared_task
def scheduled_crawl():
    """
    定时爬取任务
    """
    active_sources = TenderSource.objects.filter(is_active=True)
    
    for source in active_sources:
        task = CrawlerTask.objects.create(
            name=f"定时爬取-{source.name}",
            source=source,
            task_type='scheduled',
            params={}
        )
        execute_crawler_task.delay(task.id)
    
    logger.info(f"已创建 {active_sources.count()} 个定时爬取任务")


@shared_task
def crawl_china_gov(notice_types: list = None, keywords: list = None,
                    page: int = 1, page_size: int = 20,
                    start_date: str = None, end_date: str = None,
                    region: str = None):
    """
    直接爬取中国政府采购网
    
    Args:
        notice_types: 公告类型列表
        keywords: 关键词列表
        page: 页码
        page_size: 每页数量
        start_date: 开始日期
        end_date: 结束日期
        region: 地区过滤
    """
    from .china_gov_crawler import ChinaGovCrawler
    
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
    
    saved_count = 0
    for item in results:
        try:
            source_url = item.get('source_url', '')
            if not source_url:
                continue
            
            source = get_pilot_source('china_gov', '中国政府采购网', 'http://www.ccgp.gov.cn')
            
            tender, created = TenderProject.objects.update_or_create(
                source_url=source_url,
                defaults={
                    'title': item.get('title', ''),
                    'project_code': item.get('project_code', ''),
                    'source': source,
                    'publish_date': item.get('publish_date'),
                    'region': item.get('region', ''),
                    'purchaser_name': item.get('purchaser_name', ''),
                    'source_type': 'government',
                    'notice_type': item.get('notice_type', ''),
                    'raw_data': item.get('raw_data', {}),
                }
            )
            
            if created:
                saved_count += 1
                
        except Exception as e:
            logger.error(f"保存招标项目失败: {str(e)}")
            continue
    
    logger.info(f"中国政府采购网爬取完成，保存 {saved_count} 条数据")
    return saved_count


@shared_task
def crawl_shanghai_gov_v2(notice_types: list = None, keywords: list = None,
                           page: int = 1, page_size: int = 20):
    """
    使用新版爬虫采集上海市政府采购网
    支持多级降级策略和故障自愈
    
    Args:
        notice_types: 公告类型列表
        keywords: 关键词列表
        page: 页码
        page_size: 每页数量
    """
    from crawler.shanghai_gov_crawler_v2 import crawl_shanghai_gov
    
    async def _crawl():
        return await crawl_shanghai_gov(
            notice_types=notice_types,
            keywords=keywords
        )
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        result = loop.run_until_complete(_crawl())
        
        if not result.success:
            logger.error(f"上海市政府采购网采集失败: {result.error_message}")
            return 0
        
        saved_count = 0
        for item in result.data:
            try:
                source_url = item.get('source_url', '')
                if not source_url:
                    continue
                
                source = get_pilot_source('shanghai_gov', '上海市政府采购网', 'https://www.zfcg.sh.gov.cn')
                
                tender, created = TenderProject.objects.update_or_create(
                    source_url=source_url,
                    defaults={
                        'title': item.get('title', ''),
                        'project_code': item.get('project_code', ''),
                        'source': source,
                        'publish_date': item.get('publish_date'),
                        'region': item.get('region', ''),
                        'source_type': 'government',
                        'notice_type': item.get('notice_type', ''),
                        'raw_data': item,
                    }
                )
                
                if created:
                    saved_count += 1
                    
            except Exception as e:
                logger.error(f"保存招标项目失败: {str(e)}")
                continue
        
        logger.info(f"上海市政府采购网采集完成，保存 {saved_count} 条数据")
        return saved_count
        
    finally:
        loop.close()


@shared_task
def check_bid_results():
    """
    每日检查中标结果
    自动查询已投标项目的中标结果，匹配成功则推送钉钉通知
    """
    from services.dingtalk_service import bid_result_notification_service
    
    tracking_projects = BidProjectTracking.objects.filter(
        tracking_status='tracking'
    )
    
    checked_count = 0
    notified_count = 0
    
    for project in tracking_projects:
        try:
            project.last_checked_at = timezone.now()
            project.check_count += 1
            project.save(update_fields=['last_checked_at', 'check_count'])
            
            result = _check_single_bid_result(project)
            
            if result:
                checked_count += 1
                
                if result.get('status') == 'won':
                    project.tracking_status = 'won'
                    project.winner_name = result.get('winner_name')
                    project.winner_amount = result.get('winner_amount')
                    project.result_announce_date = result.get('announce_date')
                    project.save()
                    
                    bid_result_notification_service.notify_bid_win(
                        tender_title=project.tender_title,
                        tender_url=project.tender_url,
                        bid_amount=project.bid_amount or 0,
                        announce_date=str(project.result_announce_date),
                        enterprise_name=project.winner_name
                    )
                    
                    project.notification_sent = True
                    project.notification_sent_at = timezone.now()
                    project.save(update_fields=['notification_sent', 'notification_sent_at'])
                    notified_count += 1
                    
                elif result.get('status') == 'lost':
                    project.tracking_status = 'lost'
                    project.winner_name = result.get('winner_name')
                    project.winner_amount = result.get('winner_amount')
                    project.our_rank = result.get('our_rank')
                    project.result_announce_date = result.get('announce_date')
                    project.save()
                    
                    bid_result_notification_service.notify_bid_lost(
                        tender_title=project.tender_title,
                        tender_url=project.tender_url,
                        our_amount=project.bid_amount or 0,
                        winner_name=project.winner_name,
                        winner_amount=project.winner_amount or 0,
                        our_rank=project.our_rank
                    )
                    
                    project.notification_sent = True
                    project.notification_sent_at = timezone.now()
                    project.save(update_fields=['notification_sent', 'notification_sent_at'])
                    notified_count += 1
                    
        except Exception as e:
            logger.error(f"检查中标结果失败 {project.tender_title}: {str(e)}")
            continue
    
    logger.info(f"中标结果检查完成: 检查 {checked_count} 个项目，发送 {notified_count} 条通知")
    return {'checked': checked_count, 'notified': notified_count}


def _check_single_bid_result(project: BidProjectTracking) -> dict:
    """
    检查单个项目的中标结果
    
    Args:
        project: 已投标项目跟踪记录
        
    Returns:
        dict: 检查结果
    """
    return None


@shared_task
def build_enterprise_vector_index():
    """
    构建企业向量索引
    将企业资质、经营范围、业绩向量化存储到 Chroma
    """
    from services.enterprise_matching_engine import enterprise_matching_engine
    
    try:
        count = enterprise_matching_engine.build_enterprise_index()
        logger.info(f"企业向量索引构建完成: {count} 条")
        return count
    except Exception as e:
        logger.error(f"企业向量索引构建失败: {str(e)}")
        return 0


@shared_task
def match_tenders_with_enterprises(tender_ids: list = None):
    """
    将招标信息与企业库进行匹配
    
    Args:
        tender_ids: 指定招标项目ID列表，为空则匹配所有未处理的项目
    """
    from services.enterprise_matching_engine import enterprise_matching_engine
    
    if tender_ids:
        tenders = TenderProject.objects.filter(id__in=tender_ids)
    else:
        tenders = TenderProject.objects.filter(status='pending')
    
    matched_count = 0
    
    for tender in tenders:
        try:
            tender_data = {
                'id': tender.id,
                'title': tender.title,
                'description': tender.description,
                'budget': float(tender.budget) if tender.budget else None,
                'region': tender.region,
                'industry': tender.industry,
            }
            
            matches = enterprise_matching_engine.match_tender(
                tender_data=tender_data,
                top_k=5,
                min_score=0.6
            )
            
            if matches:
                saved = enterprise_matching_engine.save_match_results(matches)
                matched_count += saved
                
                tender.status = 'matched'
                tender.save(update_fields=['status'])
                
        except Exception as e:
            logger.error(f"匹配招标项目失败 {tender.title}: {str(e)}")
            continue
    
    logger.info(f"企业匹配完成: 匹配 {matched_count} 条")
    return matched_count


@shared_task
def send_daily_summary():
    """
    发送每日汇总报告
    """
    from services.dingtalk_service import bid_result_notification_service
    
    today = timezone.now().date()
    
    total_tenders = TenderProject.objects.filter(
        created_at__date=today
    ).count()
    
    new_tenders = TenderProject.objects.filter(
        created_at__date=today,
        status='pending'
    ).count()
    
    matched_tenders = TenderProject.objects.filter(
        created_at__date=today,
        status='matched'
    ).count()
    
    won_bids = BidProjectTracking.objects.filter(
        tracking_status='won',
        result_announce_date=today
    ).count()
    
    lost_bids = BidProjectTracking.objects.filter(
        tracking_status='lost',
        result_announce_date=today
    ).count()
    
    bid_result_notification_service.send_daily_summary(
        total_tenders=total_tenders,
        new_tenders=new_tenders,
        matched_tenders=matched_tenders,
        won_bids=won_bids,
        lost_bids=lost_bids
    )
    
    logger.info(f"每日汇总发送完成")
    return True


@shared_task
def record_failure_knowledge(url: str, failure_type: str, error_message: str,
                              strategy_used: str = None, retry_count: int = 0,
                              metadata: dict = None):
    """
    记录失败知识
    
    Args:
        url: 失败URL
        failure_type: 失败类型
        error_message: 错误信息
        strategy_used: 使用的策略
        retry_count: 重试次数
        metadata: 元数据
    """
    try:
        FailureKnowledge.objects.create(
            url=url,
            failure_type=failure_type,
            error_message=error_message,
            strategy_used=strategy_used,
            retry_count=retry_count,
            metadata=metadata or {}
        )
        logger.info(f"失败知识记录成功: {url}")
    except Exception as e:
        logger.error(f"记录失败知识失败: {str(e)}")


@shared_task(bind=True, max_retries=3)
def scheduled_crawl_with_match(self, schedule_id: int):
    """
    定时采集并智能匹配企业资质

    Args:
        schedule_id: 采集计划ID
    """
    from apps.crawler.scheduler_models import CrawlSchedule, CrawlScheduleLog
    from apps.crawler.models import CrawlSession, CrawlResult, WebsiteTemplate
    from services.qualification_matcher import tender_qualification_matcher
    from core.progress_tracker import progress_tracker

    task_id = f"crawl_schedule_{schedule_id}"
    progress_steps = [
        {'title': '初始化环境', 'description': '正在准备采集环境...', 'progress': 5},
        {'title': '创建采集会话', 'description': '正在创建采集会话...', 'progress': 10},
        {'title': '执行网页采集', 'description': '正在从网站采集数据...', 'progress': 35},
        {'title': '保存采集结果', 'description': '正在保存采集结果...', 'progress': 50},
        {'title': '转换为招标项目', 'description': '正在转换为招标项目...', 'progress': 65},
        {'title': '执行资质匹配', 'description': '正在匹配企业资质...', 'progress': 85},
        {'title': '完成任务', 'description': '正在完成最后的处理...', 'progress': 95},
    ]

    try:
        schedule = CrawlSchedule.objects.select_related('website_template').get(pk=schedule_id)
    except CrawlSchedule.DoesNotExist:
        logger.error(f"采集计划不存在: {schedule_id}")
        return {'error': f'采集计划不存在: {schedule_id}'}

    schedule_log = CrawlScheduleLog.objects.create(
        schedule=schedule,
        status='running'
    )

    session = None
    try:
        progress_tracker.create_task(
            task_id=task_id,
            task_name=f"采集任务: {schedule.name}",
            total_steps=100,
            description=f"网站: {schedule.website_template.name}",
            schedule_id=schedule_id,
            steps=progress_steps
        )
        progress_tracker.start_task(task_id)
        progress_tracker.update_progress(task_id, 1, 5, "正在初始化采集环境...")

        template = schedule.website_template
        keywords = schedule.keywords or []

        crawl_mode = getattr(schedule, 'crawl_mode', 'full')
        if crawl_mode == 'full':
            max_pages = schedule.max_pages or 50
        else:
            max_pages = schedule.max_pages or 5

        today = timezone.now().strftime('%Y-%m-%d')
        date_params = {}
        if crawl_mode == 'full':
            date_params = {
                'start_date': today,
                'end_date': today,
            }

        progress_tracker.update_progress(task_id, 2, 10, "正在创建采集会话...")
        session = CrawlSession.objects.create(
            name=f'定时采集-{schedule.name}',
            target_url=template.base_url,
            website_template=template,
            crawl_type='search' if keywords else 'list',
            keywords=keywords,
            params={
                'max_pages': max_pages,
                'schedule_id': schedule_id,
                'crawl_mode': crawl_mode,
                'date_range': date_params
            },
            status='running',
            created_by=schedule.created_by
        )
        session.started_at = timezone.now()
        session.save()

        schedule_log.session = session
        schedule_log.save(update_fields=['session'])

        progress_tracker.update_progress(task_id, 3, 15, f"开始采集...")
        logger.info(f"开始采集: {schedule.name}, 关键词: {keywords}, 最大页数: {max_pages}")

        results = []
        from openclaw.skill_registry import skill_registry

        website_code = template.code if template else ''
        source_mapping = {
            'china_gov': 'china_gov',
            'shanghai_gov': 'shanghai_gov',
            'ccgp': 'china_gov',
            'zbtb': 'china_gov',
        }

        notice_type_mapping = {
            'gkzb': ['gkzb'],
            'jzxcs': ['jzxcs'],
            'jzxtp': ['jzxtp'],
            'xjcg': ['xjcg'],
        }

        notice_types = []
        schedule_params = getattr(schedule, 'params', {}) or {}
        notice_types_config = schedule_params.get('notice_types', [])

        if notice_types_config:
            for nt in notice_types_config:
                if nt in notice_type_mapping:
                    notice_types.extend(notice_type_mapping[nt])
                else:
                    notice_types.append(nt)
        else:
            notice_types = ['gkzb', 'jzxcs', 'jzxtp', 'xjcg']

        async def async_crawl():
            try:
                skill_result = await skill_registry.execute_skill(
                    'government_tender_collector',
                    source=source_mapping.get(website_code, 'china_gov'),
                    keywords=keywords,
                    notice_types=notice_types,
                    page=1,
                    page_size=20 * max_pages
                )
                return skill_result.data if skill_result else []
            except Exception as e:
                logger.error(f"skill_registry 采集失败: {str(e)}")
                return []

        import asyncio
        from concurrent.futures import ThreadPoolExecutor

        progress_tracker.update_progress(task_id, 3, 20, "正在采集第 1 页...")
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        def run_async_crawl():
            asyncio.set_event_loop(loop)
            return loop.run_until_complete(async_crawl())

        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(run_async_crawl)
            page_count = 0
            while not future.done():
                page_count += 1
                progress_pct = min(20 + page_count, 35)
                progress_tracker.update_progress(
                    task_id, 3, progress_pct,
                    f"采集中... (第 {page_count} 页，预计 5-{10 * max_pages} 秒)"
                )
                import time
                time.sleep(3)

            results = future.result()

        loop.close()

        if results:
            progress_tracker.update_progress(task_id, 3, 35, f"采集完成，已获取 {len(results)} 条数据")
            logger.info(f"采集完成，共获取 {len(results)} 条数据")
        else:
            progress_tracker.update_progress(task_id, 3, 35, "采集完成，未获取到数据")
            logger.warning(f"采集完成，未获取到数据")
        crawl_results = []

        progress_tracker.update_progress(task_id, 5, 50, "正在保存采集结果...")
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

        schedule_log.result_count = len(results)

        progress_tracker.update_progress(task_id, 6, 65, f"正在将 {len(crawl_results)} 条数据转换为招标项目...")
        saved_to_tenders = 0
        for i, crawl_result in enumerate(crawl_results):
            try:
                source_url = crawl_result.source_url
                if not source_url:
                    continue

                source, _ = TenderSource.objects.get_or_create(
                    code=template.code,
                    defaults={
                        'name': template.name,
                        'source_type': template.website_type,
                        'base_url': template.base_url,
                        'is_active': True,
                    }
                )

                tender, created = TenderProject.objects.update_or_create(
                    source_url=source_url,
                    defaults={
                        'title': crawl_result.title,
                        'project_code': crawl_result.project_code or '',
                        'source': source,
                        'publish_date': crawl_result.publish_date,
                        'region': crawl_result.region or '',
                        'industry': crawl_result.industry or '',
                        'category': crawl_result.category or '',
                        'purchaser_name': crawl_result.purchaser_name or '',
                        'purchaser_contact': crawl_result.purchaser_contact or '',
                        'purchaser_phone': crawl_result.purchaser_phone or '',
                        'agency_name': crawl_result.agency_name or '',
                        'budget': crawl_result.budget,
                        'description': crawl_result.description or '',
                        'status': 'pending',
                        'raw_data': crawl_result.raw_data,
                    }
                )

                if created:
                    saved_to_tenders += 1

                crawl_result.status = 'processed'
                crawl_result.save(update_fields=['status'])

            except Exception as e:
                logger.error(f"保存招标项目失败: {str(e)}")
                continue

            if i % 10 == 0:
                step_progress = 65 + int((i / len(crawl_results)) * 10)
                progress_tracker.update_progress(task_id, 6, step_progress, f"已处理 {i+1}/{len(crawl_results)} 条数据...")

        logger.info(f"定时采集完成: {schedule.name}, 采集 {len(results)} 条, 保存 {saved_to_tenders} 条")

        matched_count = 0
        deleted_count = 0

        if schedule.auto_match:
            progress_tracker.update_progress(task_id, 7, 85, "正在执行企业资质匹配...")
            match_result = tender_qualification_matcher.process_new_tenders(
                user_id=schedule.created_by_id if schedule.created_by else None,
                auto_delete=schedule.auto_delete_unmatched,
                threshold=schedule.match_threshold
            )
            matched_count = match_result.get('matched', 0)
            deleted_count = match_result.get('deleted', 0)

            logger.info(f"资质匹配完成: 匹配 {matched_count} 条, 删除 {deleted_count} 条")

        progress_tracker.update_progress(task_id, 8, 95, "正在完成最后的处理...")
        schedule_log.matched_count = matched_count
        schedule_log.deleted_count = deleted_count
        schedule_log.status = 'success'
        schedule_log.finished_at = timezone.now()
        schedule_log.duration = (schedule_log.finished_at - schedule_log.started_at).seconds
        schedule_log.save()

        schedule.last_run_at = timezone.now()
        schedule.last_result_count = len(results)
        schedule.total_result_count += len(results)
        schedule.run_count += 1
        schedule.save(update_fields=['last_run_at', 'last_result_count', 'total_result_count', 'run_count'])

        progress_tracker.complete_task(task_id, {
            'result_count': len(results),
            'saved_count': saved_to_tenders,
            'matched_count': matched_count,
            'deleted_count': deleted_count
        })

        from apps.tenders.services import TenderService
        TenderService.invalidate_tender_cache()

        return {
            'schedule_id': schedule_id,
            'result_count': len(results),
            'saved_count': saved_to_tenders,
            'matched_count': matched_count,
            'deleted_count': deleted_count
        }

    except Exception as e:
        logger.error(f"定时采集任务执行失败: {str(e)}")

        progress_tracker.fail_task(task_id, str(e))

        schedule_log.status = 'failed'
        schedule_log.error_message = str(e)
        schedule_log.finished_at = timezone.now()
        schedule_log.duration = (schedule_log.finished_at - schedule_log.started_at).seconds
        schedule_log.save()

        if session:
            session.status = 'failed'
            session.error_message = str(e)
            session.finished_at = timezone.now()
            session.save()

        schedule.error_count += 1
        schedule.last_error = str(e)
        schedule.save(update_fields=['error_count', 'last_error'])

        raise self.retry(exc=e, countdown=300)


@shared_task
def auto_match_qualifications(user_id: int = None, auto_delete: bool = False, threshold: float = 0.6):
    """
    自动匹配企业资质任务
    
    Args:
        user_id: 用户ID
        auto_delete: 是否自动删除不匹配的项目
        threshold: 匹配阈值
    """
    from services.qualification_matcher import tender_qualification_matcher

    result = tender_qualification_matcher.process_new_tenders(
        user_id=user_id,
        auto_delete=auto_delete,
        threshold=threshold
    )

    logger.info(f"自动资质匹配完成: 总计 {result['total']}, 匹配 {result['matched']}, 删除 {result['deleted']}")
    return result


@shared_task
def cleanup_expired_tenders(days: int = 30):
    """
    清理过期的招标项目
    
    Args:
        days: 过期天数
    """
    from datetime import timedelta

    cutoff_date = timezone.now().date() - timedelta(days=days)

    expired_tenders = TenderProject.objects.filter(
        deadline_date__lt=cutoff_date,
        status__in=['pending', 'processing']
    )

    count = expired_tenders.update(status='expired')

    logger.info(f"已将 {count} 个过期招标项目标记为已过期")
    return count


@shared_task(bind=True, max_retries=0)
def run_batch_template_test(self, task_id: str, template_ids: list):
    """
    批量测试网站模板的异步任务

    Args:
        task_id: 进度追踪任务ID
        template_ids: 要测试的模板ID列表
    """
    from apps.crawler.models import WebsiteTemplate
    from apps.crawler.services import UniversalCrawlerEngine
    from crawler.base_crawler import CrawlerConfig
    from core.progress_tracker import progress_tracker

    logger.info(f"开始批量测试任务: {task_id}, 共 {len(template_ids)} 个模板")

    templates = WebsiteTemplate.objects.filter(id__in=template_ids).order_by('-priority')
    total = len(templates)
    results = []
    success_count = 0
    failed_count = 0
    warning_count = 0

    for idx, template in enumerate(templates):
        step_index = idx + 1
        current_progress = int((idx / total) * 100)

        progress_tracker.update_progress(
            task_id=task_id,
            current_step=step_index,
            progress=current_progress,
            message=f'正在测试: {template.name}',
            step_status='active'
        )

        template_result = {
            'template_id': template.id,
            'template_name': template.name,
            'template_code': template.code,
            'base_url': template.base_url,
            'status': 'pending',
            'success': False,
            'data_count': 0,
            'error_message': None,
            'error_type': None,
            'root_cause': None,
            'recommendations': [],
            'issues': [],
            'duration': 0,
            'strategy_used': None,
            'raw_response': None
        }

        start_time = timezone.now()

        try:
            config = CrawlerConfig(
                headless=True,
                timeout=30,
                request_delay_min=1.0,
                request_delay_max=3.0,
                max_retries=2
            )

            engine = UniversalCrawlerEngine(
                config=config,
                website_template=template,
                enable_multi_strategy=True
            )

            crawl_results = engine.crawl(
                target_url=template.base_url,
                max_pages=1
            )

            duration = (timezone.now() - start_time).total_seconds()
            template_result['duration'] = duration
            template_result['data_count'] = len(crawl_results)

            if len(crawl_results) > 0:
                template_result['status'] = 'success'
                template_result['success'] = True
                template_result['strategy_used'] = 'multi_strategy_http'
                success_count += 1

                progress_tracker.update_progress(
                    task_id=task_id,
                    current_step=step_index,
                    progress=current_progress,
                    message=f'{template.name}: 成功获取 {len(crawl_results)} 条数据',
                    step_status='completed'
                )
            else:
                template_result['status'] = 'warning'
                template_result['success'] = False
                template_result['error_message'] = '未获取到任何数据'
                template_result['error_type'] = 'NO_DATA'
                template_result['root_cause'] = '网站可能返回空内容、页面结构变化、或需要JS渲染'
                template_result['recommendations'] = [
                    '检查网站是否需要登录访问',
                    '检查选择器配置是否仍然有效',
                    '尝试启用JS渲染模式',
                    '检查网站是否进行了反爬限制'
                ]
                template_result['issues'].append({
                    'severity': 'warning',
                    'description': '未获取到任何数据',
                    'detail': '网站返回空内容，可能原因：页面结构变化、需要JS渲染、需要登录'
                })
                warning_count += 1

                progress_tracker.update_progress(
                    task_id=task_id,
                    current_step=step_index,
                    progress=current_progress,
                    message=f'{template.name}: 警告 - 未获取数据',
                    step_status='completed'
                )

        except Exception as e:
            duration = (timezone.now() - start_time).total_seconds()
            template_result['duration'] = duration
            template_result['status'] = 'failed'
            template_result['success'] = False
            template_result['error_message'] = str(e)
            template_result['error_type'] = type(e).__name__
            template_result['root_cause'] = _analyze_error_root_cause(str(e), template)
            template_result['recommendations'] = _get_error_recommendations(str(e), template)
            template_result['issues'].append({
                'severity': 'error',
                'description': f'测试过程发生异常: {str(e)}',
                'detail': template_result['root_cause']
            })
            failed_count += 1

            logger.error(f"模板测试失败 {template.name}: {str(e)}")

            progress_tracker.update_progress(
                task_id=task_id,
                current_step=step_index,
                progress=current_progress,
                message=f'{template.name}: 失败 - {str(e)[:50]}',
                step_status='error',
                step_error=str(e)
            )

        results.append(template_result)

    final_progress = 100
    progress_tracker.update_progress(
        task_id=task_id,
        current_step=total + 1,
        progress=95,
        message='正在生成测试报告...',
        step_status='active'
    )

    summary = {
        'total_templates': total,
        'success_count': success_count,
        'failed_count': failed_count,
        'warning_count': warning_count,
        'success_rate': round((success_count / total) * 100, 1) if total > 0 else 0,
        'total_duration': sum(r['duration'] for r in results),
        'failed_templates': [r for r in results if r['status'] == 'failed'],
        'warning_templates': [r for r in results if r['status'] == 'warning'],
        'success_templates': [r for r in results if r['status'] == 'success'],
        'all_results': results
    }

    progress_tracker.complete_task(task_id, summary)

    logger.info(f"批量测试完成: 成功 {success_count}, 失败 {failed_count}, 警告 {warning_count}")

    return summary


def _analyze_error_root_cause(error_message: str, template) -> str:
    """
    分析错误根本原因

    Args:
        error_message: 错误信息
        template: 网站模板对象

    Returns:
        str: 根本原因分析
    """
    error_lower = error_message.lower()

    if 'timeout' in error_lower or '超时' in error_lower:
        return '网络请求超时，可能原因：网站响应过慢、网络连接不稳定、目标网站存在防火墙限制'
    elif 'connection' in error_lower or '连接' in error_lower:
        return '无法连接到目标网站，可能原因：网站服务器不可达、网络策略限制、DNS解析失败'
    elif 'certificate' in error_lower or 'ssl' in error_lower or '证书' in error_lower:
        return 'SSL证书验证失败，可能原因：网站SSL证书配置错误或已过期'
    elif '404' in error_lower or 'not found' in error_lower or '不存在' in error_lower:
        return '页面不存在(404)，可能原因：URL路径错误、网站结构变化、页面已被删除'
    elif '403' in error_lower or 'forbidden' in error_lower or '禁止' in error_lower:
        return '访问被拒绝(403)，可能原因：网站启用了反爬机制、IP被封禁、需要特定的请求头'
    elif '401' in error_lower or 'unauthorized' in error_lower or '未授权' in error_lower:
        return '需要身份认证(401)，可能原因：网站需要登录才能访问、API密钥无效'
    elif '500' in error_lower or 'server error' in error_lower or '服务器错误' in error_lower:
        return '服务器内部错误，可能原因：目标网站服务器故障、API接口变更'
    elif 'proxy' in error_lower or '代理' in error_lower:
        return '代理服务器错误，可能原因：代理不可用或被封禁'
    elif 'captcha' in error_lower or '验证码' in error_lower or '滑动' in error_lower:
        return '遇到验证码/反爬机制，可能原因：网站启用了行为验证、需要通过人机验证'
    elif 'javascript' in error_lower or 'js' in error_lower or '渲染' in error_lower:
        return '页面需要JavaScript渲染，可能原因：网站使用动态加载内容、选择了错误的爬取模式'
    else:
        return f'未知错误类型: {error_message[:100]}'


def _get_error_recommendations(error_message: str, template) -> list:
    """
    获取错误修复建议

    Args:
        error_message: 错误信息
        template: 网站模板对象

    Returns:
        list: 建议列表
    """
    error_lower = error_message.lower()
    recommendations = []

    if 'timeout' in error_lower or '超时' in error_lower:
        recommendations.extend([
            '增加请求超时时间配置',
            '检查网络连接状况',
            '降低请求频率，避免触发限流',
            '尝试使用代理池分散请求'
        ])
    elif 'connection' in error_lower or '连接' in error_lower:
        recommendations.extend([
            '验证目标URL是否可访问',
            '检查防火墙和网络策略设置',
            '确认网站服务器状态',
            '尝试使用备用的基础URL'
        ])
    elif 'certificate' in error_lower or 'ssl' in error_lower or '证书' in error_lower:
        recommendations.extend([
            '更新或重新配置SSL证书',
            '在开发环境中可以暂时禁用SSL验证（仅限测试）'
        ])
    elif '404' in error_lower or 'not found' in error_lower or '不存在' in error_lower:
        recommendations.extend([
            '检查base_url配置是否正确',
            '更新list_url_pattern和search_url_pattern',
            '确认网站页面结构是否发生变化',
            '重新抓取网站首页获取正确的URL模式'
        ])
    elif '403' in error_lower or 'forbidden' in error_lower or '禁止' in error_lower:
        recommendations.extend([
            '配置User-Agent请求头模拟真实浏览器',
            '降低请求频率',
            '使用代理池轮换IP地址',
            '尝试添加Referer等请求头',
            '考虑使用Selenium/Pyppeteer等无头浏览器模式'
        ])
    elif '401' in error_lower or 'unauthorized' in error_lower or '未授权' in error_lower:
        recommendations.extend([
            '配置正确的登录信息',
            '更新login_config中的认证凭据',
            '检查Cookie和Session配置',
            '确认登录接口是否发生变化'
        ])
    elif '500' in error_lower or 'server error' in error_lower or '服务器错误' in error_lower:
        recommendations.extend([
            '目标网站服务器暂时不可用，稍后重试',
            '检查网站官方公告是否有维护通知',
            '增加重试机制处理临时性故障'
        ])
    elif 'proxy' in error_lower or '代理' in error_lower:
        recommendations.extend([
            '更换可靠的代理服务',
            '检查代理池的可用性',
            '考虑使用住宅代理代替数据中心代理'
        ])
    elif 'captcha' in error_lower or '验证码' in error_lower or '滑动' in error_lower:
        recommendations.extend([
            '集成第三方验证码识别服务',
            '使用打码平台自动处理验证码',
            '对于滑动验证码可使用轨迹模拟方案'
        ])
    elif 'javascript' in error_lower or 'js' in error_lower or '渲染' in error_lower:
        recommendations.extend([
            '启用requires_javascript配置',
            '使用Selenium或Pyppeteer进行JS渲染爬取',
            '检查selenium相关依赖是否正确安装'
        ])
    else:
        recommendations.extend([
            '查看详细错误日志获取更多信息',
            '检查模板配置是否完整',
            '联系系统管理员获取帮助'
        ])

    if template.requires_login:
        recommendations.append('提示：该模板配置了需要登录，请确保login_config正确配置')

    if template.requires_javascript:
        recommendations.append('提示：该模板配置了需要JS渲染，请使用Selenium模式爬取')

    return recommendations


@shared_task
def sync_crawl_results_to_tenders(limit: int = 100):
    """
    定时同步采集结果到招标项目
    将 crawler 模块中状态为 matched 的采集结果同步到 tender_projects

    Args:
        limit: 单次同步限制数量
    """
    from apps.tenders.services import CrawlToTenderSyncService

    try:
        result = CrawlToTenderSyncService.sync_all(limit=limit)
        logger.info(
            f"定时同步完成: 总计 {result['total']}, "
            f"新增 {result['created']}, 更新 {result['updated']}, "
            f"跳过 {result['skipped']}, 失败 {result['failed']}"
        )
        return result
    except Exception as e:
        logger.error(f"定时同步失败: {str(e)}")
        raise
