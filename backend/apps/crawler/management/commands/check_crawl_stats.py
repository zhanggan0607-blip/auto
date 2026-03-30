"""
检查采集数据统计的命令
"""
from django.core.management.base import BaseCommand
from apps.tenders.models import TenderProject, TenderSource
from apps.crawler.scheduler_models import CrawlSchedule, CrawlScheduleLog
from apps.crawler.models import CrawlSession, CrawlResult, WebsiteTemplate


class Command(BaseCommand):
    help = '检查采集数据统计'

    def handle(self, *args, **options):
        self.stdout.write('=== 采集计划统计 ===')
        total = CrawlSchedule.objects.count()
        active = CrawlSchedule.objects.filter(status='active').count()
        self.stdout.write(f'总计划数: {total}')
        self.stdout.write(f'激活计划数: {active}')

        self.stdout.write('')
        self.stdout.write('=== 采集计划列表 ===')
        for s in CrawlSchedule.objects.all()[:10]:
            self.stdout.write(f'  ID:{s.id} | {s.name} | 状态:{s.status} | 上次执行:{s.last_run_at} | 上次采集:{s.last_result_count}条')

        self.stdout.write('')
        self.stdout.write('=== 网站模板统计 ===')
        total_templates = WebsiteTemplate.objects.count()
        active_templates = WebsiteTemplate.objects.filter(is_active=True).count()
        self.stdout.write(f'总模板数: {total_templates}')
        self.stdout.write(f'激活模板数: {active_templates}')

        self.stdout.write('')
        self.stdout.write('=== 采集会话统计 ===')
        total_sessions = CrawlSession.objects.count()
        completed_sessions = CrawlSession.objects.filter(status='completed').count()
        self.stdout.write(f'总会话数: {total_sessions}')
        self.stdout.write(f'已完成会话数: {completed_sessions}')

        self.stdout.write('')
        self.stdout.write('=== 最新采集会话 ===')
        recent = CrawlSession.objects.order_by('-started_at')[:5]
        for s in recent:
            self.stdout.write(f'  {s.name} | 状态:{s.status} | 结果数:{s.result_count} | 开始:{s.started_at}')

        self.stdout.write('')
        self.stdout.write('=== 采集结果统计 ===')
        total_results = CrawlResult.objects.count()
        pending_results = CrawlResult.objects.filter(status='pending').count()
        processed_results = CrawlResult.objects.filter(status='processed').count()
        self.stdout.write(f'总结果数: {total_results}')
        self.stdout.write(f'待处理: {pending_results}')
        self.stdout.write(f'已处理: {processed_results}')

        self.stdout.write('')
        self.stdout.write('=== 最新采集日志 ===')
        for log in CrawlScheduleLog.objects.order_by('-started_at')[:5]:
            self.stdout.write(f'  计划:{log.schedule.name} | 状态:{log.status} | 采集:{log.result_count} | 匹配:{log.matched_count} | 时间:{log.started_at}')

        self.stdout.write('')
        self.stdout.write('=== 招标项目统计 ===')
        total_tenders = TenderProject.objects.count()
        pending = TenderProject.objects.filter(status='pending').count()
        matched = TenderProject.objects.filter(status='matched').count()
        processing = TenderProject.objects.filter(status='processing').count()
        won = TenderProject.objects.filter(status='won').count()
        lost = TenderProject.objects.filter(status='lost').count()

        self.stdout.write(f'总招标项目数: {total_tenders}')
        self.stdout.write(f'待处理: {pending}')
        self.stdout.write(f'已匹配: {matched}')
        self.stdout.write(f'处理中: {processing}')
        self.stdout.write(f'已中标: {won}')
        self.stdout.write(f'未中标: {lost}')

        self.stdout.write('')
        self.stdout.write('=== 数据来源统计 ===')
        for source in TenderSource.objects.all():
            count = TenderProject.objects.filter(source=source).count()
            self.stdout.write(f'  {source.name}: {count}条')

        self.stdout.write('')
        self.stdout.write('=== 最新招标项目 ===')
        recent_tenders = TenderProject.objects.order_by('-created_at')[:10]
        for t in recent_tenders:
            source_name = t.source.name if t.source else '无'
            self.stdout.write(f'  [{t.status}] {t.title[:40]} | 来源:{source_name} | 发布:{t.publish_date}')