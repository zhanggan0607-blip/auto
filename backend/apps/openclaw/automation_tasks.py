"""
自动化任务调度
定时执行一键投标任务
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any
from celery import shared_task
from django.conf import settings
from django.utils import timezone

from services.one_click_automation import one_click_automation_service
from services.automation_config_service import automation_config_service


logger = logging.getLogger(__name__)


@shared_task(name='automation.scheduled_bid_automation')
def scheduled_bid_automation():
    """
    定时自动投标任务
    每天自动扫描新的招标项目并启动投标流程
    使用全自动化配置参数
    """
    from apps.enterprise.models import Enterprise
    from apps.crawler.models import WebsiteTemplate
    from apps.openclaw.models import AgentModelConfig

    logger.info("开始执行定时自动投标任务")

    try:
        all_params = automation_config_service.get_all_params()
        risk_params = all_params['risk']
        decision_params = all_params['decision']
        review_params = all_params['review']
        notification_params = all_params['notification']

        active_enterprises = Enterprise.objects.filter(
            is_active=True,
            auto_bid_enabled=True
        )

        websites = WebsiteTemplate.objects.filter(
            is_active=True,
            auto_crawl_enabled=True
        )
        website_ids = list(websites.values_list('id', flat=True))

        for enterprise in active_enterprises:
            try:
                config = {
                    'auto_bid_threshold': decision_params.AUTO_BID_THRESHOLD,
                    'auto_document_threshold': review_params.AUTO_UPLOAD_THRESHOLD,
                    'notification_enabled': notification_params.NOTIFICATION_ENABLED,
                    'auto_upload': enterprise.auto_upload_enabled or False,
                    'risk_control': {
                        'max_daily_bids': risk_params.MAX_DAILY_BIDS,
                        'amount_threshold': risk_params.AMOUNT_THRESHOLD,
                        'consecutive_failures': risk_params.CONSECUTIVE_FAILURES,
                        'auto_pause_on_risk': risk_params.AUTO_PAUSE_ON_RISK
                    }
                }

                keywords = enterprise.auto_bid_keywords or []

                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    result = loop.run_until_complete(one_click_automation_service.start_automation(
                        enterprise_id=enterprise.id,
                        website_ids=website_ids,
                        keywords=keywords,
                        config=config
                    ))
                finally:
                    loop.close()

                logger.info(f"企业 {enterprise.name} 自动投标任务已启动: {result}")

            except Exception as e:
                logger.error(f"企业 {enterprise.name} 自动投标失败: {str(e)}")
                continue

        logger.info("定时自动投标任务执行完成")

    except Exception as e:
        logger.error(f"定时自动投标任务执行失败: {str(e)}")


@shared_task(name='automation.check_bid_results')
def check_bid_results():
    """
    定时检查投标结果
    每天自动查询已投标项目的中标结果

    实现逻辑：
    1. 从BidProjectTracking获取所有正在跟踪的项目
    2. 调用crawler.tasks中的_check_single_bid_result进行真正的网站爬取
    3. 根据结果更新跟踪状态并发送钉钉通知
    """
    from apps.crawler.models import BidProjectTracking
    from services.dingtalk_service import bid_result_notification_service
    from crawler.tasks import _check_single_bid_result as crawler_check_bid_result

    logger.info("开始执行投标结果检查任务")

    try:
        tracking_projects = BidProjectTracking.objects.filter(
            tracking_status='tracking'
        )

        checked_count = 0
        notified_count = 0

        for tracking in tracking_projects:
            try:
                checked_count += 1
                result = crawler_check_bid_result(tracking)

                if result:
                    tracking.tracking_status = result.get('status', 'tracking')
                    tracking.winner_name = result.get('winner_name')
                    tracking.winner_amount = result.get('winner_amount')
                    tracking.our_rank = result.get('our_rank')
                    if result.get('announce_date'):
                        tracking.result_announce_date = result.get('announce_date')
                    tracking.last_checked_at = timezone.now()
                    tracking.check_count += 1
                    tracking.save()

                    if result.get('status') == 'won' and not tracking.notification_sent:
                        bid_result_notification_service.notify_bid_win(
                            tender_title=tracking.tender_title,
                            tender_url=tracking.tender_url,
                            bid_amount=tracking.bid_amount or 0,
                            announce_date=str(result.get('announce_date', '')),
                            enterprise_name=tracking.bid_company
                        )
                        tracking.notification_sent = True
                        tracking.notification_sent_at = timezone.now()
                        tracking.save()
                        notified_count += 1

                    elif result.get('status') == 'lost' and not tracking.notification_sent:
                        bid_result_notification_service.notify_bid_lost(
                            tender_title=tracking.tender_title,
                            tender_url=tracking.tender_url,
                            our_amount=tracking.bid_amount or 0,
                            winner_name=result.get('winner_name', ''),
                            winner_amount=result.get('winner_amount', 0),
                            our_rank=result.get('our_rank')
                        )
                        tracking.notification_sent = True
                        tracking.notification_sent_at = timezone.now()
                        tracking.save()
                        notified_count += 1

            except Exception as e:
                logger.error(f"检查项目 {tracking.tender_title} 结果失败: {str(e)}")
                continue

        logger.info(f"投标结果检查任务执行完成: 检查 {checked_count} 个项目，发送 {notified_count} 条通知")

    except Exception as e:
        logger.error(f"投标结果检查任务执行失败: {str(e)}")


@shared_task(name='automation.cleanup_old_tasks')
def cleanup_old_tasks():
    """
    清理旧任务记录
    """
    from apps.openclaw.workflow_models import BidWorkflow, WorkflowStage

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

    except Exception as e:
        logger.error(f"清理旧任务记录失败: {str(e)}")


@shared_task(name='automation.daily_summary')
def daily_summary():
    """
    每日汇总报告
    """
    from django.db.models import Count, Sum
    from apps.tenders.models import TenderProject
    from apps.bids.models import BidRecord, BidResult
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

        won_bids = BidResult.objects.filter(
            created_at__date=yesterday,
            result_type='win'
        ).count()

        lost_bids = BidResult.objects.filter(
            created_at__date=yesterday,
            result_type='lose'
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

    except Exception as e:
        logger.error(f"生成每日汇总报告失败: {str(e)}")


@shared_task(name='automation.auto_crawl_websites')
def auto_crawl_websites():
    """
    自动爬取网站
    根据网站配置的定时任务自动执行爬取
    """
    from apps.crawler.models import WebsiteTemplate, CrawlSession
    from apps.crawler.scheduler_models import CrawlSchedule

    logger.info("开始执行自动爬取任务")

    try:
        schedules = CrawlSchedule.objects.filter(
            is_active=True,
            status='active'
        )

        for schedule in schedules:
            try:
                if schedule.next_run_at and schedule.next_run_at > timezone.now():
                    continue

                from services.one_click_automation import one_click_automation_service

                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    result = loop.run_until_complete(one_click_automation_service.start_automation(
                        enterprise_id=schedule.created_by.enterprise.id if hasattr(schedule.created_by, 'enterprise') else None,
                        website_ids=[schedule.website_template.id],
                        keywords=schedule.keywords,
                        config={
                            'auto_bid_threshold': schedule.match_threshold * 100,
                            'notification_enabled': True
                        }
                    ))
                finally:
                    loop.close()

                schedule.last_run_at = timezone.now()
                schedule.run_count += 1
                schedule.last_result_count = result.get('collected_count', 0)
                schedule.total_result_count += schedule.last_result_count
                schedule.save()

                logger.info(f"爬取任务 {schedule.name} 执行完成")

            except Exception as e:
                logger.error(f"爬取任务 {schedule.name} 执行失败: {str(e)}")
                schedule.error_count += 1
                schedule.last_error = str(e)
                schedule.save()
                continue

        logger.info("自动爬取任务执行完成")

    except Exception as e:
        logger.error(f"自动爬取任务执行失败: {str(e)}")
