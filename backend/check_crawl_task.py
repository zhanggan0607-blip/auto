"""
检查采集任务状态
"""
import os
import sys
import django

sys.path.insert(0, r'd:\共享文件\AUTO\backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
os.environ.setdefault('DB_PASSWORD', '123456')

django.setup()

from apps.crawler.models import CrawlSchedule, CrawlScheduleLog

print("=" * 70)
print("采集调度任务状态")
print("=" * 70)

schedules = CrawlSchedule.objects.all().order_by('-created_at')[:10]

print(f"\n总调度任务数: {CrawlSchedule.objects.count()}")

for schedule in schedules:
    print(f"\n调度ID: {schedule.id}")
    print(f"  名称: {schedule.name}")
    print(f"  状态: {schedule.status}")
    print(f"  网站: {schedule.website_template.name if schedule.website_template else 'N/A'}")
    print(f"  创建时间: {schedule.created_at}")
    print(f"  开始时间: {schedule.started_at}")
    print(f"  完成时间: {schedule.completed_at}")
    print(f"  执行结果: {schedule.last_result_message or 'N/A'}")

    logs = CrawlScheduleLog.objects.filter(schedule=schedule).order_by('-created_at')[:5]
    if logs.exists():
        print(f"  最近日志:")
        for log in logs:
            print(f"    - {log.created_at}: {log.status} - {log.message[:50] if log.message else 'N/A'}...")

print("\n" + "=" * 70)
