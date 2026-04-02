"""
统一调度任务
整合投标自动化和定时采集的所有调度任务，使用Celery Beat统一管理
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any
from celery import shared_task
from django.utils import timezone
from django.db import connection
from django.core.cache import cache

logger = logging.getLogger(__name__)


@shared_task(name='unified_scheduler.tender_scan')
def tender_scan():
    """
    招标信息扫描任务
    扫描所有启用的采集计划，执行采集
    """
    from apps.crawler.scheduler_models import CrawlSchedule, CrawlScheduleLog
    from apps.tenders.models import TenderSource, TenderProject
    from apps.crawler.models import CrawlSession, CrawlResult
    from services.qualification_matcher import tender_qualification_matcher

    logger.info("开始执行招标信息扫描任务")

    try:
        active_schedules = CrawlSchedule.objects.filter(
            is_active=True,
            status='active'
        )

        total_collected = 0
        total_matched = 0
        total_deleted = 0

        for schedule in active_schedules:
            try:
                schedule_log = CrawlScheduleLog.objects.create(
                    schedule=schedule,
                    status='running'
                )

                template = schedule.website_template
                keywords = schedule.keywords or []
                max_pages = schedule.max_pages or 10

                from apps.crawler.services import UniversalCrawlerEngine
                from crawler.base_crawler import CrawlerConfig

                config = CrawlerConfig(
                    headless=True,
                    timeout=60,
                    request_delay_min=2.0,
                    request_delay_max=5.0,
                    max_retries=3
                )

                engine = UniversalCrawlerEngine(config=config, website_template=template)
                results = engine.crawl(
                    target_url=template.base_url,
                    keywords=keywords,
                    max_pages=max_pages
                )

                saved_count = 0
                for result in results:
                    try:
                        source_url = result.get('source_url', '')
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
                                'title': result.get('title', ''),
                                'project_code': result.get('project_code', ''),
                                'source': source,
                                'publish_date': result.get('publish_date'),
                                'region': result.get('region', ''),
                                'industry': result.get('industry', ''),
                                'budget': result.get('budget'),
                                'description': result.get('description', ''),
                                'status': 'pending',
                                'raw_data': result.get('raw_data', {}),
                            }
                        )

                        if created:
                            saved_count += 1

                    except Exception as e:
                        logger.error(f"保存招标项目失败: {str(e)}")
                        continue

                total_collected += saved_count

                matched_count = 0
                deleted_count = 0

                if schedule.auto_match:
                    match_result = tender_qualification_matcher.process_new_tenders(
                        user_id=schedule.created_by_id if schedule.created_by else None,
                        auto_delete=schedule.auto_delete_unmatched,
                        threshold=schedule.match_threshold
                    )
                    matched_count = match_result.get('matched', 0)
                    deleted_count = match_result.get('deleted', 0)
                    total_matched += matched_count
                    total_deleted += deleted_count

                schedule_log.status = 'success'
                schedule_log.result_count = saved_count
                schedule_log.matched_count = matched_count
                schedule_log.deleted_count = deleted_count
                schedule_log.finished_at = timezone.now()
                schedule_log.duration = (schedule_log.finished_at - schedule_log.started_at).total_seconds()
                schedule_log.save()

                schedule.last_run_at = timezone.now()
                schedule.last_result_count = saved_count
                schedule.total_result_count += saved_count
                schedule.run_count += 1
                schedule.save(update_fields=['last_run_at', 'last_result_count', 'total_result_count', 'run_count'])

                logger.info(f"采集计划 {schedule.name} 执行完成: 采集 {saved_count} 条, 匹配 {matched_count} 条")

            except Exception as e:
                logger.error(f"采集计划 {schedule.name} 执行失败: {str(e)}")
                schedule.error_count += 1
                schedule.last_error = str(e)
                schedule.save(update_fields=['error_count', 'last_error'])
                continue

        logger.info(f"招标扫描任务完成: 采集 {total_collected} 条, 匹配 {total_matched} 条, 删除 {total_deleted} 条")
        return {
            'collected': total_collected,
            'matched': total_matched,
            'deleted': total_deleted
        }

    except Exception as e:
        logger.error(f"招标扫描任务执行失败: {str(e)}")
        return {'error': str(e)}


@shared_task(name='unified_scheduler.bid_auto_submit')
def bid_auto_submit():
    """
    自动投标执行任务
    检查待投标项目，自动启动投标流程
    """
    from apps.tenders.models import TenderProject
    from apps.enterprise.models import Enterprise, EnterpriseMatchRule
    from services.bid_automation_workflow import bid_automation_workflow

    logger.info("开始执行自动投标检查任务")

    try:
        pending_tenders = TenderProject.objects.filter(
            status='pending',
            auto_bid_enabled=True
        ).exclude(
            bid_workflows__status__in=['running', 'pending']
        )[:10]

        started_count = 0

        for tender in pending_tenders:
            try:
                matching_rules = EnterpriseMatchRule.objects.filter(
                    is_active=True,
                    enterprise__auto_bid_enabled=True
                )

                matched_enterprise = None
                best_score = 0

                for rule in matching_rules:
                    score = _calculate_match_score(tender, rule)
                    if score >= rule.min_match_score and score > best_score:
                        best_score = score
                        matched_enterprise = rule.enterprise

                if matched_enterprise:
                    result = asyncio.run(bid_automation_workflow.start_workflow(
                        tender_id=tender.id,
                        enterprise_id=matched_enterprise.id
                    ))

                    if result.get('status') == 'started':
                        started_count += 1
                        logger.info(f"已启动投标工作流: {tender.title} -> {matched_enterprise.name}")

            except Exception as e:
                logger.error(f"启动投标工作流失败 {tender.id}: {str(e)}")

        logger.info(f"自动投标检查完成: 启动 {started_count} 个工作流")
        return {'started': started_count}

    except Exception as e:
        logger.error(f"自动投标任务失败: {str(e)}")
        return {'error': str(e)}


@shared_task(name='unified_scheduler.result_check')
def result_check():
    """
    中标结果检查任务
    检查已投标项目的中标结果并通知
    """
    from apps.crawler.models import BidProjectTracking
    from apps.enterprise.models import Enterprise
    from services.dingtalk_service import bid_result_notification_service

    logger.info("开始执行中标结果检查任务")

    try:
        tracking_projects = BidProjectTracking.objects.filter(
            tracking_status='tracking'
        )

        notified_count = 0

        for tracking in tracking_projects:
            try:
                tracking.last_checked_at = timezone.now()
                tracking.check_count += 1
                tracking.save(update_fields=['last_checked_at', 'check_count'])

                result = _check_single_bid_result(tracking)

                if result:
                    tracking.tracking_status = result['status']
                    tracking.winner_name = result.get('winner_name')
                    tracking.winner_amount = result.get('winner_amount')
                    tracking.our_rank = result.get('our_rank')
                    tracking.result_announce_date = result.get('announce_date')
                    tracking.save()

                    if result['status'] == 'won':
                        bid_result_notification_service.notify_bid_win(
                            tender_title=tracking.tender_title,
                            tender_url=tracking.tender_url,
                            bid_amount=tracking.bid_amount or 0,
                            announce_date=str(result.get('announce_date', '')),
                            enterprise_name=tracking.bid_company
                        )
                        notified_count += 1

                    elif result['status'] == 'lost':
                        bid_result_notification_service.notify_bid_lost(
                            tender_title=tracking.tender_title,
                            tender_url=tracking.tender_url,
                            our_amount=tracking.bid_amount or 0,
                            winner_name=result.get('winner_name', ''),
                            winner_amount=result.get('winner_amount', 0),
                            our_rank=result.get('our_rank')
                        )
                        notified_count += 1

            except Exception as e:
                logger.error(f"检查项目 {tracking.tender_title} 结果失败: {str(e)}")
                continue

        logger.info(f"中标结果检查完成: 通知 {notified_count} 个项目")
        return {'notified': notified_count}

    except Exception as e:
        logger.error(f"中标结果检查任务失败: {str(e)}")
        return {'error': str(e)}


@shared_task(name='unified_scheduler.vector_cleanup')
def vector_cleanup():
    """
    向量库维护任务
    清理低质量文档和过期索引
    """
    logger.info("开始执行向量库维护任务")

    try:
        from apps.vectorlib.models import BidDocumentLibrary
        from services.vector import document_vector_store

        deleted_count, _ = BidDocumentLibrary.objects.filter(
            vector_status='failed',
            created_at__lt=timezone.now() - timedelta(days=30)
        ).delete()

        low_quality_docs = BidDocumentLibrary.objects.filter(
            quality_score__lt=30,
            use_count=0,
            view_count=0
        )

        for doc in low_quality_docs:
            document_vector_store.delete_document(doc.id)

        low_quality_docs.delete()

        logger.info(f"向量库维护完成: 清理 {deleted_count} 条记录")
        return {'deleted': deleted_count}

    except Exception as e:
        logger.error(f"向量库维护任务失败: {str(e)}")
        return {'error': str(e)}


@shared_task(name='unified_scheduler.system_health_check')
def system_health_check():
    """
    系统健康检查任务
    检查数据库、缓存、向量库状态
    """
    logger.info("开始执行系统健康检查任务")

    try:
        health_status = {
            'database': 'ok',
            'cache': 'ok',
            'vector_db': 'ok',
            'timestamp': timezone.now().isoformat()
        }

        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
        except Exception as e:
            health_status['database'] = f'error: {str(e)}'

        try:
            cache.set('health_check', 'ok', 10)
            if cache.get('health_check') != 'ok':
                health_status['cache'] = 'error: cache not working'
        except Exception as e:
            health_status['cache'] = f'error: {str(e)}'

        try:
            from services.vector import document_vector_store
            count = document_vector_store.get_count()
            health_status['vector_count'] = count
        except Exception as e:
            health_status['vector_db'] = f'error: {str(e)}'

        cache.set('system_health', health_status, 300)

        logger.info(f"系统健康检查完成: {health_status}")
        return health_status

    except Exception as e:
        logger.error(f"系统健康检查失败: {str(e)}")
        return {'error': str(e)}


@shared_task(name='unified_scheduler.daily_summary')
def daily_summary():
    """
    每日汇总报告任务
    发送每日工作汇总到钉钉
    """
    from apps.tenders.models import TenderProject
    from apps.crawler.models import BidProjectTracking
    from services.dingtalk_service import bid_result_notification_service

    logger.info("开始生成每日汇总报告")

    try:
        today = timezone.now().date()
        yesterday = today - timedelta(days=1)

        new_tenders = TenderProject.objects.filter(
            created_at__date=yesterday
        ).count()

        matched_tenders = TenderProject.objects.filter(
            created_at__date=yesterday,
            status__in=['processing', 'submitted']
        ).count()

        won_bids = BidProjectTracking.objects.filter(
            tracking_status='won',
            result_announce_date=yesterday
        ).count()

        lost_bids = BidProjectTracking.objects.filter(
            tracking_status='lost',
            result_announce_date=yesterday
        ).count()

        total_tenders = TenderProject.objects.count()

        bid_result_notification_service.send_daily_summary(
            total_tenders=total_tenders,
            new_tenders=new_tenders,
            matched_tenders=matched_tenders,
            won_bids=won_bids,
            lost_bids=lost_bids
        )

        logger.info("每日汇总报告已发送")
        return {
            'total_tenders': total_tenders,
            'new_tenders': new_tenders,
            'matched_tenders': matched_tenders,
            'won_bids': won_bids,
            'lost_bids': lost_bids
        }

    except Exception as e:
        logger.error(f"生成每日汇总报告失败: {str(e)}")
        return {'error': str(e)}


@shared_task(name='unified_scheduler.cleanup_old_tasks')
def cleanup_old_tasks():
    """
    清理旧任务记录
    删除30天前的已完成任务
    """
    from apps.openclaw.workflow_models import BidWorkflow

    logger.info("开始清理旧任务记录")

    try:
        cutoff_date = timezone.now() - timedelta(days=30)

        old_workflows = BidWorkflow.objects.filter(
            created_at__lt=cutoff_date,
            status__in=['completed', 'cancelled', 'failed']
        )

        count = old_workflows.count()
        old_workflows.delete()

        logger.info(f"已清理 {count} 条旧任务记录")
        return {'deleted': count}

    except Exception as e:
        logger.error(f"清理旧任务记录失败: {str(e)}")
        return {'error': str(e)}


def _calculate_match_score(tender, rule) -> float:
    """
    计算招标项目与匹配规则的匹配分数
    """
    score = 0.0

    title = (tender.title or '').lower()
    description = (tender.description or '').lower()
    content = f"{title} {description}"

    keywords = rule.keywords or []
    if keywords:
        matched_keywords = sum(1 for kw in keywords if kw.lower() in content)
        score += (matched_keywords / len(keywords)) * 40

    if rule.industries and tender.industry in rule.industries:
        score += 20

    if rule.regions and tender.region in rule.regions:
        score += 20

    if rule.project_types and tender.project_type in rule.project_types:
        score += 20

    return min(score, 100.0)


def _check_single_bid_result(tracking) -> Dict[str, Any]:
    """
    检查单个投标项目的结果
    """
    from apps.bids.models import BidRecord, BidResult

    try:
        bid_record = BidRecord.objects.filter(
            tender__title__icontains=tracking.tender_title[:20]
        ).first()

        if bid_record:
            bid_result = BidResult.objects.filter(bid_record=bid_record).first()

            if bid_result and bid_result.result_type != 'pending':
                return {
                    'status': 'won' if bid_result.result_type == 'win' else 'lost',
                    'winner_name': bid_result.winner_name,
                    'winner_amount': bid_result.winner_amount,
                    'our_rank': bid_result.our_rank,
                    'announce_date': bid_result.announce_date
                }

    except Exception as e:
        logger.warning(f"查询投标结果失败: {str(e)}")

    return None


DEFAULT_SCHEDULE_CONFIGS = [
    {
        'task_id': 'tender_scan',
        'task_name': 'unified_scheduler.tender_scan',
        'name': '招标信息扫描',
        'description': '每小时扫描指定招标网站，发现新项目',
        'cron_expression': '0 * * * *',
        'enabled': True
    },
    {
        'task_id': 'bid_auto_submit',
        'task_name': 'unified_scheduler.bid_auto_submit',
        'name': '自动投标执行',
        'description': '每30分钟检查待投标项目，自动启动投标流程',
        'cron_expression': '*/30 * * * *',
        'enabled': True
    },
    {
        'task_id': 'result_check',
        'task_name': 'unified_scheduler.result_check',
        'name': '中标结果检查',
        'description': '每日9:00检查中标公告，匹配并通知',
        'cron_expression': '0 9 * * *',
        'enabled': True
    },
    {
        'task_id': 'vector_cleanup',
        'task_name': 'unified_scheduler.vector_cleanup',
        'name': '向量库维护',
        'description': '每周日凌晨3:00清理向量库',
        'cron_expression': '0 3 * * 0',
        'enabled': True
    },
    {
        'task_id': 'system_health_check',
        'task_name': 'unified_scheduler.system_health_check',
        'name': '系统健康检查',
        'description': '每5分钟检查系统状态',
        'cron_expression': '*/5 * * * *',
        'enabled': True
    },
    {
        'task_id': 'daily_summary',
        'task_name': 'unified_scheduler.daily_summary',
        'name': '每日汇总报告',
        'description': '每日18:00发送工作汇总',
        'cron_expression': '0 18 * * *',
        'enabled': True
    },
    {
        'task_id': 'cleanup_old_tasks',
        'task_name': 'unified_scheduler.cleanup_old_tasks',
        'name': '清理旧任务',
        'description': '每日凌晨2:00清理30天前的任务记录',
        'cron_expression': '0 2 * * *',
        'enabled': True
    }
]


def setup_default_schedules():
    """
    初始化默认调度任务
    创建Celery Beat定时任务
    """
    from django_celery_beat.models import PeriodicTask, CrontabSchedule
    import json

    for config in DEFAULT_SCHEDULE_CONFIGS:
        try:
            parts = config['cron_expression'].split()
            minute, hour, day_of_month, month_of_year, day_of_week = parts

            schedule, _ = CrontabSchedule.objects.get_or_create(
                minute=minute,
                hour=hour,
                day_of_month=day_of_month,
                month_of_year=month_of_year,
                day_of_week=day_of_week,
                timezone='Asia/Shanghai'
            )

            PeriodicTask.objects.update_or_create(
                name=f'unified_{config["task_id"]}',
                defaults={
                    'crontab': schedule,
                    'task': config['task_name'],
                    'enabled': config['enabled'],
                    'kwargs': json.dumps({}),
                }
            )

            logger.info(f"已创建调度任务: {config['name']}")

        except Exception as e:
            logger.error(f"创建调度任务失败 {config['name']}: {str(e)}")
