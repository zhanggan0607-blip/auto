"""
检查2026-03-30采集任务问题诊断脚本
"""
import os
import sys
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')

import django
django.setup()

from apps.crawler.scheduler_models import CrawlSchedule
from django_celery_beat.models import PeriodicTask, CrontabSchedule
from datetime import datetime

print("=" * 70)
print("采集任务配置详细检查报告")
print("=" * 70)

print("\n【1. CrawlSchedule 配置】")
print("-" * 50)
for s in CrawlSchedule.objects.filter(is_active=True):
    print(f"ID: {s.id}")
    print(f"  名称: {s.name}")
    print(f"  Cron表达式: {s.crontab}")
    print(f"  is_active: {s.is_active}")
    print(f"  status: {s.status}")
    print(f"  last_run_at: {s.last_run_at}")
    print(f"  error_count: {s.error_count}")
    print(f"  celery_task_id: {s.celery_task_id}")
    print()

print("\n【2. PeriodicTask 配置】")
print("-" * 50)
for pt in PeriodicTask.objects.filter(name__startswith='crawl_schedule'):
    print(f"名称: {pt.name}")
    print(f"  任务: {pt.task}")
    print(f"  args: {pt.args}")
    print(f"  enabled: {pt.enabled}")
    if pt.crontab:
        print(f"  crontab: {pt.crontab}")
        print(f"    minute: {pt.crontab.minute}")
        print(f"    hour: {pt.crontab.hour}")
        print(f"    day_of_month: {pt.crontab.day_of_month}")
        print(f"    month_of_year: {pt.crontab.month_of_year}")
        print(f"    day_of_week: {pt.crontab.day_of_week}")
        print(f"    timezone: {pt.crontab.timezone}")
    print()

print("\n【3. 任务触发时间分析】")
print("-" * 50)
target_date = datetime(2026, 3, 30)

for pt in PeriodicTask.objects.filter(name__startswith='crawl_schedule'):
    if pt.crontab:
        c = pt.crontab
        # 简化的crontab解析 - 检查是否应该在3月30日触发
        print(f"任务: {pt.name}")
        print(f"  Cron: {c.minute} {c.hour} {c.day_of_month} {c.month_of_year} {c.day_of_week}")
        print(f"  将在 20:{c.minute} 执行 (上海时区)")
        print()

print("\n【4. Celery Beat 调度状态】")
print("-" * 50)
try:
    from config.celery import app
    from celery import current_app
    from celery.apps.beat import Beat

    beat = Beat(app=current_app)
    schedule = beat.get_schedule()

    print(f"Celery Beat 调度器运行中: {len(schedule)} 个任务")
    for entry in schedule:
        print(f"  {entry.name}: {entry.schedule}")
except Exception as e:
    print(f"Celery Beat 检查失败: {e}")
    print("可能原因: Celery Beat 服务未启动")

print("\n【5. 采集日志检查】")
print("-" * 50)
from apps.crawler.scheduler_models import CrawlScheduleLog

logs = CrawlScheduleLog.objects.all().order_by('-started_at')[:10]
print(f"最近 {logs.count()} 条采集日志:")
for log in logs:
    print(f"  {log.started_at} - {log.schedule.name}: {log.status}")

print("\n" + "=" * 70)
