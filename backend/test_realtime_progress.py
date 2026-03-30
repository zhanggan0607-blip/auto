"""
测试实时进度反馈的采集流程
"""
import os
import sys

sys.path.insert(0, r'd:\共享文件\AUTO\backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
os.environ.setdefault('DB_PASSWORD', '123456')

import django
django.setup()

from core.progress_tracker import progress_tracker

task_id = "test_realtime_progress"

print("=" * 70)
print("测试实时进度反馈")
print("=" * 70)

progress_steps = [
    {'title': '初始化环境', 'description': '正在准备采集环境...', 'progress': 5},
    {'title': '创建采集会话', 'description': '正在创建采集会话...', 'progress': 10},
    {'title': '执行网页采集', 'description': '正在从网站采集数据...', 'progress': 35},
    {'title': '保存采集结果', 'description': '正在保存采集结果...', 'progress': 50},
    {'title': '转换为招标项目', 'description': '正在转换为招标项目...', 'progress': 65},
]

progress_tracker.create_task(
    task_id=task_id,
    task_name="测试采集任务",
    total_steps=100,
    description="测试实时进度反馈",
    steps=progress_steps
)

print("\n1. 创建任务")
progress_tracker.start_task(task_id)

print("\n2. 模拟采集进度...")
for i in range(5):
    progress_tracker.update_progress(
        task_id, 3, 20 + i * 3,
        f"采集中... (第 {i+1} 页)"
    )
    print(f"   进度: 20+{i*3}% - 采集中... (第 {i+1} 页)")

print("\n3. 完成采集")
progress_tracker.update_progress(task_id, 3, 35, "采集完成，已获取 5 条数据")

print("\n4. 查看进度状态")
state = progress_tracker.get_task_status(task_id)
print(f"   当前步骤: {state.get('current_step', 'N/A')}")
print(f"   进度: {state.get('progress', 0)}%")
print(f"   消息: {state.get('message', 'N/A')}")

print("\n5. 完成整个任务")
progress_tracker.complete_task(task_id, {'result_count': 5})

print("\n" + "=" * 70)
print("测试完成")
print("=" * 70)
