"""
检查实际工作流执行状态
"""
import os
import sys
import django

sys.path.insert(0, r'd:\共享文件\AUTO\backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
os.environ.setdefault('DB_PASSWORD', '123456')

django.setup()

from apps.openclaw.workflow_models import BidWorkflow, WorkflowStage

print("=" * 70)
print("实际工作流执行状态检查")
print("=" * 70)

workflows = BidWorkflow.objects.all().order_by('-created_at')[:20]

print(f"\n总工作流数量: {BidWorkflow.objects.count()}")
print(f"运行中: {BidWorkflow.objects.filter(status='running').count()}")
print(f"已完成: {BidWorkflow.objects.filter(status='completed').count()}")
print(f"失败: {BidWorkflow.objects.filter(status='failed').count()}")
print(f"待处理: {BidWorkflow.objects.filter(status='pending').count()}")

print("\n" + "-" * 70)
print("最近20个工作流:")
print("-" * 70)

for wf in workflows:
    print(f"\nID: {wf.id}")
    print(f"  名称: {wf.name}")
    print(f"  状态: {wf.status}")
    print(f"  当前阶段: {wf.current_stage}")
    print(f"  创建时间: {wf.created_at}")
    print(f"  开始时间: {wf.started_at}")
    print(f"  完成时间: {wf.completed_at}")

    stages = WorkflowStage.objects.filter(workflow_id=wf.id).order_by('order')
    if stages.exists():
        print(f"  阶段详情:")
        for stage in stages:
            print(f"    - {stage.stage_type}: {stage.status} (耗时: {stage.duration:.1f}s)" if stage.duration else f"    - {stage.stage_type}: {stage.status}")

print("\n" + "=" * 70)
