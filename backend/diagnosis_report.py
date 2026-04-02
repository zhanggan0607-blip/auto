"""
2026-03-30 采集任务问题诊断报告
"""
import os
import sys
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')

import django
django.setup()

from config.celery import app
from django_celery_beat.models import PeriodicTask
from apps.crawler.scheduler_models import CrawlSchedule, CrawlScheduleLog
from datetime import datetime, timedelta

print("=" * 70)
print("2026-03-30 采集任务问题诊断报告")
print("=" * 70)

print("\n【1. Celery Worker 状态】")
print("-" * 50)
try:
    i = app.control.inspect(timeout=5)
    stats = i.stats()
    if stats:
        for worker, info in stats.items():
            print(f"Worker: {worker}")
            print(f"  PID: {info.get('pid')}")
            print(f"  运行时间: {info.get('uptime', 'N/A')}秒")
            print(f"  并发数: {info.get('pool', {}).get('max-concurrency', 'N/A')}")
    else:
        print("Celery Worker 未运行")
except Exception as e:
    print(f"检查失败: {e}")

print("\n【2. Celery Beat 调度器状态】")
print("-" * 50)
try:
    from celery.apps.beat import Beat
    beat = Beat(app=app)
    scheduler = beat.get_scheduler()
    schedule = scheduler.schedule

    print(f"Celery Beat 调度器运行中")
    print(f"待执行任务数: {len(schedule)}")

    # 检查 crawl_schedule 任务的下次执行时间
    for entry_name, entry in schedule.items():
        if 'crawl_schedule' in entry_name:
            print(f"  {entry_name}: next_run={entry.next_run_time}")
except Exception as e:
    print(f"Celery Beat 检查失败: {e}")
    print("** 严重问题: Celery Beat 可能未启动 **")

print("\n【3. CrawlSchedule vs PeriodicTask 配置对比】")
print("-" * 50)
for s in CrawlSchedule.objects.filter(is_active=True):
    pt = s.celery_task
    print(f"采集计划: {s.name} (ID={s.id})")
    print(f"  CrawlSchedule.crontab: {s.crontab} (凌晨1点)")
    print(f"  PeriodicTask.crontab: {pt.crontab if pt else 'None'} (晚上20点)")
    print(f"  ** 配置不一致! **")
    print()

print("\n【4. PeriodicTask 队列配置】")
print("-" * 50)
for pt in PeriodicTask.objects.filter(name__startswith='crawl_schedule'):
    print(f"{pt.name}:")
    print(f"  task: {pt.task}")
    print(f"  queue: {pt.queue}")
    print(f"  enabled: {pt.enabled}")
    print(f"  crontab: {pt.crontab}")

print("\n【5. 任务触发时间分析 - 3月30日】")
print("-" * 50)
target_date = datetime(2026, 3, 30)
print(f"目标日期: {target_date.strftime('%Y-%m-%d')} (周一)")
print()
print("根据 PeriodicTask.crontab 配置 (20:25 和 20:35):")
print("  - crawl_schedule_4 应该在 2026-03-30 20:25 执行")
print("  - crawl_schedule_6 应该在 2026-03-30 20:35 执行")
print()
print("但根据 CrawlSchedule.crontab 配置 (01:25 和 01:35):")
print("  - 原本应该在 2026-03-30 01:25 和 01:35 执行")
print()

print("\n【6. 最近采集日志】")
print("-" * 50)
logs = CrawlScheduleLog.objects.all().order_by('-started_at')[:10]
print(f"共 {logs.count()} 条日志:")
for log in logs:
    print(f"  {log.started_at} - {log.schedule.name}: {log.status}")

print("\n【7. Celery 队列配置检查】")
print("-" * 50)
queues = app.conf.task_queues
print(f"配置的队列: {queues}")
print()
print("start_celery.bat 监听的队列: default, crawler")
print("但 celery.py 中定义的队列包括: default, workflow, crawler, vector, notification")
print("** 问题: Worker 可能没有监听所有需要的队列 **")

print("\n【8. 任务路由配置】")
print("-" * 50)
routes = app.conf.task_routes
for task, route in routes.items():
    print(f"  {task}: queue={route.get('queue')}, routing_key={route.get('routing_key')}")

print("\n" + "=" * 70)
print("问题定位总结")
print("=" * 70)
print("""
【根本原因】

1. **CrawlSchedule 和 PeriodicTask 的 crontab 配置不一致**
   - CrawlSchedule 存储的是旧配置 (凌晨 01:25 和 01:35)
   - PeriodicTask 被创建时使用了新配置 (晚上 20:25 和 20:35)
   - 说明有人修改了 CrontabSchedule 但没有同步更新 CrawlSchedule.crontab

2. **Celery Beat 调度器可能未运行**
   - Celery Worker 正在运行 (只有 system_health_check 任务被执行)
   - 但 crawl_schedule 任务没有执行记录
   - 可能原因: Celery Beat 服务未启动，或队列配置不匹配

3. **任务队列配置问题**
   - start_celery.bat 只监听 default,crawler 队列
   - 但 unified_* 任务默认使用 default 队列
   - crawl_schedule_* 任务也使用 default 队列
   - 需要确认 Beat 是否正确将任务发送到队列

4. **CrawlSchedule.last_run_at 与实际执行时间不匹配**
   - last_run_at: 2026-03-29 12:42:21 (接近北京时间晚上20:42)
   - 说明任务在 3月29日晚上执行过
   - 但 3月30日没有执行记录
""")
