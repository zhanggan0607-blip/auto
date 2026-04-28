"""
24小时不间断投标任务调度系统
负责定时扫描、任务分配、工作流触发
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
from django.utils import timezone
from django.db.models import Q
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

logger = logging.getLogger(__name__)


class ScheduleType(Enum):
    """
    调度类型
    """
    TENDER_SCAN = 'tender_scan'
    BID_AUTO_SUBMIT = 'bid_auto_submit'
    RESULT_CHECK = 'result_check'
    VECTOR_CLEANUP = 'vector_cleanup'
    SYSTEM_HEALTH = 'system_health'


@dataclass
class ScheduleTask:
    """
    调度任务配置
    """
    task_id: str
    task_type: ScheduleType
    name: str
    description: str
    cron_expression: str
    enabled: bool = True
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    run_count: int = 0
    error_count: int = 0
    last_error: str = ''


class BidTaskScheduler:
    """
    投标任务调度器
    
    24小时不间断执行以下任务：
    1. 招标信息扫描 - 每小时扫描指定网站
    2. 自动投标执行 - 根据匹配规则自动启动投标流程
    3. 中标结果检查 - 每日检查中标公告
    4. 向量库维护 - 定期清理和优化
    5. 系统健康检查 - 监控系统状态
    """
    
    DEFAULT_SCHEDULES = [
        {
            'task_id': 'tender_scan_hourly',
            'task_type': ScheduleType.TENDER_SCAN,
            'name': '招标信息扫描',
            'description': '每小时扫描指定招标网站，发现新项目',
            'cron_expression': '0 * * * *',
            'enabled': True
        },
        {
            'task_id': 'bid_auto_submit',
            'task_type': ScheduleType.BID_AUTO_SUBMIT,
            'name': '自动投标执行',
            'description': '每30分钟检查待投标项目，自动启动投标流程',
            'cron_expression': '*/30 * * * *',
            'enabled': True
        },
        {
            'task_id': 'result_check_daily',
            'task_type': ScheduleType.RESULT_CHECK,
            'name': '中标结果检查',
            'description': '每日9:00检查中标公告，匹配并通知',
            'cron_expression': '0 9 * * *',
            'enabled': True
        },
        {
            'task_id': 'vector_cleanup_weekly',
            'task_type': ScheduleType.VECTOR_CLEANUP,
            'name': '向量库维护',
            'description': '每周日凌晨3:00清理向量库',
            'cron_expression': '0 3 * * 0',
            'enabled': True
        },
        {
            'task_id': 'system_health_check',
            'task_type': ScheduleType.SYSTEM_HEALTH,
            'name': '系统健康检查',
            'description': '每5分钟检查系统状态',
            'cron_expression': '*/5 * * * *',
            'enabled': True
        }
    ]
    
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self._tasks: Dict[str, ScheduleTask] = {}
        self._running = False
        self._init_default_schedules()
    
    def _init_default_schedules(self):
        """
        初始化默认调度任务
        """
        for config in self.DEFAULT_SCHEDULES:
            task = ScheduleTask(
                task_id=config['task_id'],
                task_type=config['task_type'],
                name=config['name'],
                description=config['description'],
                cron_expression=config['cron_expression'],
                enabled=config['enabled']
            )
            self._tasks[task.task_id] = task
    
    async def start(self):
        """
        启动调度器
        """
        if self._running:
            logger.warning("调度器已在运行")
            return
        
        for task_id, task in self._tasks.items():
            if task.enabled:
                self._add_job(task)
        
        self.scheduler.start()
        self._running = True
        logger.info("投标任务调度器已启动")
    
    async def stop(self):
        """
        停止调度器
        """
        if self.scheduler.running:
            self.scheduler.shutdown(wait=True)
        self._running = False
        logger.info("投标任务调度器已停止")
    
    def _add_job(self, task: ScheduleTask):
        """
        添加调度任务
        """
        try:
            trigger = CronTrigger.from_crontab(task.cron_expression)
            
            handler = self._get_task_handler(task.task_type)
            
            self.scheduler.add_job(
                handler,
                trigger=trigger,
                id=task.task_id,
                name=task.name,
                replace_existing=True,
                kwargs={'task_id': task.task_id}
            )
            
            logger.info(f"已添加调度任务: {task.name} ({task.cron_expression})")
            
        except Exception as e:
            logger.error(f"添加调度任务失败 {task.task_id}: {str(e)}")
    
    def _get_task_handler(self, task_type: ScheduleType):
        """
        获取任务处理器
        """
        handlers = {
            ScheduleType.TENDER_SCAN: self._task_tender_scan,
            ScheduleType.BID_AUTO_SUBMIT: self._task_bid_auto_submit,
            ScheduleType.RESULT_CHECK: self._task_result_check,
            ScheduleType.VECTOR_CLEANUP: self._task_vector_cleanup,
            ScheduleType.SYSTEM_HEALTH: self._task_system_health,
        }
        return handlers.get(task_type, self._task_default)
    
    async def _task_tender_scan(self, task_id: str):
        """
        任务: 招标信息扫描
        每小时扫描指定招标网站，发现新项目
        """
        task = self._tasks.get(task_id)
        if task:
            task.last_run = timezone.now()
        
        logger.info("开始执行招标信息扫描...")
        
        try:
            from apps.crawler.models import CrawlSchedule, CrawlScheduleLog
            from crawler.shanghai_gov_crawler_v2 import ShanghaiGovCrawler
            from crawler.shanghai_construction_crawler import ShanghaiConstructionCrawler
            
            active_schedules = CrawlSchedule.objects.filter(
                is_active=True,
                schedule_type='tender_scan'
            )
            
            total_found = 0
            new_count = 0
            
            for schedule in active_schedules:
                try:
                    if 'shanghai_gov' in schedule.website_template.name.lower():
                        crawler = ShanghaiGovCrawler()
                    else:
                        crawler = ShanghaiConstructionCrawler()
                    
                    result = await crawler.crawl(
                        keywords=schedule.keywords,
                        max_pages=schedule.max_pages or 5
                    )
                    
                    total_found += result.get('total', 0)
                    new_count += result.get('new_count', 0)
                    
                    CrawlScheduleLog.objects.create(
                        schedule=schedule,
                        status='completed',
                        result_summary=result
                    )
                    
                except Exception as e:
                    logger.error(f"爬取失败 {schedule.website_template.name}: {str(e)}")
                    CrawlScheduleLog.objects.create(
                        schedule=schedule,
                        status='failed',
                        error_message=str(e)
                    )
            
            if task:
                task.run_count += 1
            
            logger.info(f"招标扫描完成: 发现 {total_found} 条，新增 {new_count} 条")
            
        except Exception as e:
            logger.error(f"招标扫描任务失败: {str(e)}")
            if task:
                task.error_count += 1
                task.last_error = str(e)
    
    async def _task_bid_auto_submit(self, task_id: str):
        """
        任务: 自动投标执行
        每30分钟检查待投标项目，自动启动投标流程
        """
        task = self._tasks.get(task_id)
        if task:
            task.last_run = timezone.now()
        
        logger.info("开始执行自动投标检查...")
        
        try:
            from apps.tenders.models import TenderProject
            from apps.enterprise.models import Enterprise, EnterpriseMatchRule
            from services.bid_automation_workflow import bid_automation_workflow
            
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
                        score = self._calculate_match_score(tender, rule)
                        if score >= rule.min_match_score and score > best_score:
                            best_score = score
                            matched_enterprise = rule.enterprise
                    
                    if matched_enterprise:
                        result = await bid_automation_workflow.start_workflow(
                            tender_id=tender.id,
                            enterprise_id=matched_enterprise.id
                        )
                        
                        if result.get('status') == 'started':
                            started_count += 1
                            logger.info(f"已启动投标工作流: {tender.title} -> {matched_enterprise.name}")
                            
                except Exception as e:
                    logger.error(f"启动投标工作流失败 {tender.id}: {str(e)}")
            
            if task:
                task.run_count += 1
            
            logger.info(f"自动投标检查完成: 启动 {started_count} 个工作流")
            
        except Exception as e:
            logger.error(f"自动投标任务失败: {str(e)}")
            if task:
                task.error_count += 1
                task.last_error = str(e)
    
    async def _task_result_check(self, task_id: str):
        """
        任务: 中标结果检查
        每日检查中标公告，匹配并通知
        """
        task = self._tasks.get(task_id)
        if task:
            task.last_run = timezone.now()
        
        logger.info("开始执行中标结果检查...")
        
        try:
            from apps.crawler.models import BidProjectTracking
            from apps.enterprise.models import Enterprise
            from services.dingtalk_service import DingtalkService
            
            tracking_projects = BidProjectTracking.objects.filter(
                status='submitted',
                bid_date__lte=timezone.now().date()
            )
            
            notified_count = 0
            
            for tracking in tracking_projects:
                try:
                    result = await self._check_bid_result(tracking)
                    
                    if result.get('has_result'):
                        tracking.status = result.get('status', 'pending')
                        tracking.result_date = timezone.now().date()
                        tracking.result_url = result.get('result_url', '')
                        tracking.save()
                        
                        if result.get('status') == 'won':
                            enterprise = Enterprise.objects.get(pk=tracking.enterprise_id)
                            message = f"""【中标通知】
项目名称: {tracking.tender.title}
中标企业: {enterprise.name}
中标金额: {result.get('amount', '未知')}
公告日期: {timezone.now().strftime('%Y-%m-%d')}
"""
                            dingtalk = DingtalkService()
                            await dingtalk.send_message(message)
                            notified_count += 1
                            
                except Exception as e:
                    logger.error(f"检查中标结果失败 {tracking.id}: {str(e)}")
            
            if task:
                task.run_count += 1
            
            logger.info(f"中标结果检查完成: 通知 {notified_count} 个中标项目")
            
        except Exception as e:
            logger.error(f"中标结果检查任务失败: {str(e)}")
            if task:
                task.error_count += 1
                task.last_error = str(e)
    
    async def _check_bid_result(self, tracking) -> Dict[str, Any]:
        """
        检查单个项目的投标结果
        """
        from apps.tenders.models import TenderProject
        
        try:
            tender = TenderProject.objects.get(pk=tracking.tender_id)
            
            if 'shanghai' in (tender.source_url or '').lower():
                from crawler.shanghai_gov_crawler_v2 import ShanghaiGovCrawler
                crawler = ShanghaiGovCrawler()
                result = await crawler.check_bid_result(
                    tender_id=tender.id,
                    enterprise_name=tracking.enterprise.name
                )
                return result
            
            return {'has_result': False}
            
        except Exception as e:
            logger.error(f"检查投标结果异常: {str(e)}")
            return {'has_result': False, 'error': str(e)}
    
    async def _task_vector_cleanup(self, task_id: str):
        """
        任务: 向量库维护
        每周清理向量库，优化存储
        """
        task = self._tasks.get(task_id)
        if task:
            task.last_run = timezone.now()
        
        logger.info("开始执行向量库维护...")
        
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
            
            if task:
                task.run_count += 1
            
            logger.info(f"向量库维护完成: 清理 {deleted_count} 条记录")
            
        except Exception as e:
            logger.error(f"向量库维护任务失败: {str(e)}")
            if task:
                task.error_count += 1
                task.last_error = str(e)
    
    async def _task_system_health(self, task_id: str):
        """
        任务: 系统健康检查
        每5分钟检查系统状态
        """
        task = self._tasks.get(task_id)
        if task:
            task.last_run = timezone.now()
        
        try:
            from django.db import connection
            from django.core.cache import cache
            
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
            
            if task:
                task.run_count += 1
            
        except Exception as e:
            logger.error(f"系统健康检查失败: {str(e)}")
            if task:
                task.error_count += 1
                task.last_error = str(e)
    
    async def _task_default(self, task_id: str):
        """
        默认任务处理器
        """
        logger.warning(f"执行默认任务处理器: {task_id}")
    
    def _calculate_match_score(self, tender, rule) -> float:
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
    
    async def get_scheduler_status(self) -> Dict[str, Any]:
        """
        获取调度器状态
        """
        jobs = []
        for job in self.scheduler.get_jobs():
            jobs.append({
                'id': job.id,
                'name': job.name,
                'next_run_time': job.next_run_time.isoformat() if job.next_run_time else None,
                'trigger': str(job.trigger)
            })
        
        return {
            'running': self._running,
            'job_count': len(jobs),
            'jobs': jobs,
            'tasks': {
                task_id: {
                    'name': task.name,
                    'enabled': task.enabled,
                    'last_run': task.last_run.isoformat() if task.last_run else None,
                    'run_count': task.run_count,
                    'error_count': task.error_count
                }
                for task_id, task in self._tasks.items()
            }
        }
    
    async def enable_task(self, task_id: str) -> bool:
        """
        启用调度任务
        """
        task = self._tasks.get(task_id)
        if not task:
            return False
        
        task.enabled = True
        self._add_job(task)
        return True
    
    async def disable_task(self, task_id: str) -> bool:
        """
        禁用调度任务
        """
        task = self._tasks.get(task_id)
        if not task:
            return False
        
        task.enabled = False
        
        try:
            self.scheduler.remove_job(task_id)
        except Exception:
            pass
        
        return True
    
    async def run_task_now(self, task_id: str) -> Dict[str, Any]:
        """
        立即执行任务
        """
        task = self._tasks.get(task_id)
        if not task:
            return {'error': '任务不存在'}
        
        handler = self._get_task_handler(task.task_type)
        
        try:
            await handler(task_id)
            return {'success': True, 'message': f'任务 {task.name} 执行完成'}
        except Exception as e:
            return {'success': False, 'error': str(e)}


bid_task_scheduler = BidTaskScheduler()
