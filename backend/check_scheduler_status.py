"""
检查任务调度器状态
"""
import os
import sys
import django

sys.path.insert(0, r'd:\共享文件\AUTO\backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
os.environ.setdefault('DB_PASSWORD', '123456')

django.setup()

from services.bid_task_scheduler import bid_task_scheduler, ScheduleType

print("=" * 70)
print("BidTaskScheduler 调度器状态")
print("=" * 70)

print(f"\n调度器运行状态: {bid_task_scheduler._running if hasattr(bid_task_scheduler, '_running') else '未知'}")

print("\n已配置的任务:")
for task_id, task in bid_task_scheduler._tasks.items():
    print(f"\n  任务ID: {task_id}")
    print(f"    名称: {task.name}")
    print(f"    类型: {task.task_type.value}")
    print(f"    启用: {'是' if task.enabled else '否'}")
    print(f"    Cron: {task.cron_expression}")
    print(f"    上次执行: {task.last_run}")
    print(f"    下次执行: {task.next_run}")
    print(f"    执行次数: {task.run_count}")
    print(f"    错误次数: {task.error_count}")
    if task.last_error:
        print(f"    最后错误: {task.last_error[:100]}...")

print("\n" + "-" * 70)
print("默认调度的任务类型:")
for task_config in bid_task_scheduler.DEFAULT_SCHEDULES:
    print(f"  - {task_config['name']} ({task_config['task_type'].value})")
    print(f"    Cron: {task_config['cron_expression']}")

print("\n" + "=" * 70)
