import os
import sys
sys.path.insert(0, 'd:/共享文件/AUTO/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

import django
django.setup()

from apps.crawler.scheduler_models import CrawlSchedule, CrawlScheduleLog
from apps.crawler.models import CrawlSession, CrawlResult, WebsiteTemplate

print('=== 采集计划统计 ===')
total = CrawlSchedule.objects.count()
active = CrawlSchedule.objects.filter(status='active').count()
print(f'总计划数: {total}')
print(f'激活计划数: {active}')

print()
print('=== 采集计划列表 ===')
for s in CrawlSchedule.objects.all()[:10]:
    print(f'  ID:{s.id} | {s.name} | 状态:{s.status} | 上次执行:{s.last_run_at} | 上次采集:{s.last_result_count}条')

print()
print('=== 网站模板统计 ===')
total_templates = WebsiteTemplate.objects.count()
active_templates = WebsiteTemplate.objects.filter(is_active=True).count()
print(f'总模板数: {total_templates}')
print(f'激活模板数: {active_templates}')

print()
print('=== 采集会话统计 ===')
total_sessions = CrawlSession.objects.count()
completed_sessions = CrawlSession.objects.filter(status='completed').count()
print(f'总会话数: {total_sessions}')
print(f'已完成会话数: {completed_sessions}')

print()
print('=== 最新采集会话 ===')
recent = CrawlSession.objects.order_by('-started_at')[:5]
for s in recent:
    print(f'  {s.name} | 状态:{s.status} | 结果数:{s.result_count} | 开始:{s.started_at}')

print()
print('=== 采集结果统计 ===')
total_results = CrawlResult.objects.count()
pending_results = CrawlResult.objects.filter(status='pending').count()
processed_results = CrawlResult.objects.filter(status='processed').count()
print(f'总结果数: {total_results}')
print(f'待处理: {pending_results}')
print(f'已处理: {processed_results}')

print()
print('=== 最新采集日志 ===')
for log in CrawlScheduleLog.objects.order_by('-started_at')[:5]:
    print(f'  计划:{log.schedule.name} | 状态:{log.status} | 采集:{log.result_count} | 匹配:{log.matched_count} | 时间:{log.started_at}')