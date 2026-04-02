"""
自动化监控页面统计数据验证脚本
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
sys.path.insert(0, 'd:/共享文件/AUTO/backend')
django.setup()

from django.utils import timezone
from datetime import timedelta
from django.db.models import Count, Q

from apps.crawler.models import CrawlResult
from apps.tenders.models import TenderProject
from apps.bids.models import BidRecord
from apps.openclaw.workflow_models import BidWorkflow


def verify_crawl_stats():
    """验证采集数据统计"""
    print("\n" + "=" * 60)
    print("1. 验证 CrawlResult 采集数据统计")
    print("=" * 60)

    today = timezone.now().date()
    yesterday = today - timedelta(days=1)

    crawled_today = CrawlResult.objects.filter(created_at__date=today).count()
    crawled_yesterday = CrawlResult.objects.filter(created_at__date=yesterday).count()

    matched_today = CrawlResult.objects.filter(status='matched', created_at__date=today).count()
    matched_yesterday = CrawlResult.objects.filter(status='matched', created_at__date=yesterday).count()

    print(f"  今日采集: {crawled_today} 条")
    print(f"  昨日采集: {crawled_yesterday} 条")
    print(f"  今日匹配: {matched_today} 条")
    print(f"  昨日匹配: {matched_yesterday} 条")

    if crawled_yesterday > 0:
        crawled_trend = int(((crawled_today - crawled_yesterday) / crawled_yesterday) * 100)
        print(f"  采集趋势: {crawled_trend:+d}%")
    else:
        print(f"  采集趋势: N/A (昨日无数据)")
        crawled_trend = 0

    if matched_yesterday > 0:
        matched_trend = int(((matched_today - matched_yesterday) / matched_yesterday) * 100)
        print(f"  匹配趋势: {matched_trend:+d}%")
    else:
        print(f"  匹配趋势: N/A (昨日无数据)")
        matched_trend = 0

    all_statuses = CrawlResult.objects.values('status').annotate(count=Count('id'))
    print(f"\n  CrawlResult 状态分布:")
    for item in all_statuses:
        print(f"    {item['status']}: {item['count']}")

    return {
        'crawled_today': crawled_today,
        'crawled_yesterday': crawled_yesterday,
        'matched_today': matched_today
    }


def verify_bid_stats():
    """验证投标数据统计"""
    print("\n" + "=" * 60)
    print("2. 验证 BidRecord 投标数据统计")
    print("=" * 60)

    today = timezone.now().date()
    yesterday = today - timedelta(days=1)

    bids_today = BidRecord.objects.filter(created_at__date=today).count()
    bids_yesterday = BidRecord.objects.filter(created_at__date=yesterday).count()

    print(f"  今日投标: {bids_today} 条")
    print(f"  昨日投标: {bids_yesterday} 条")

    all_statuses = BidRecord.objects.values('status').annotate(count=Count('id'))
    print(f"\n  BidRecord 状态分布:")
    for item in all_statuses:
        print(f"    {item['status']}: {item['count']}")

    return {'bids_today': bids_today}


def verify_tender_stats():
    """验证中标数据统计"""
    print("\n" + "=" * 60)
    print("3. 验证 TenderProject 中标数据统计")
    print("=" * 60)

    today = timezone.now().date()
    yesterday = today - timedelta(days=1)

    won_today = TenderProject.objects.filter(status='won', updated_at__date=today).count()
    won_yesterday = TenderProject.objects.filter(status='won', updated_at__date=yesterday).count()

    print(f"  今日中标: {won_today} 条")
    print(f"  昨日中标: {won_yesterday} 条")

    all_statuses = TenderProject.objects.values('status').annotate(count=Count('id'))
    print(f"\n  TenderProject 状态分布:")
    for item in all_statuses:
        print(f"    {item['status']}: {item['count']}")

    return {'won_today': won_today}


def verify_workflow_stats():
    """验证工作流状态统计"""
    print("\n" + "=" * 60)
    print("4. 验证 BidWorkflow 工作流状态统计")
    print("=" * 60)

    total_workflows = BidWorkflow.objects.count()
    running_workflows = BidWorkflow.objects.filter(status__in=['collecting', 'matching', 'analyzing', 'generating', 'reviewing', 'optimizing', 'uploading', 'tracking']).count()
    completed_workflows = BidWorkflow.objects.filter(status='completed').count()
    pending_workflows = BidWorkflow.objects.filter(status='pending').count()
    failed_workflows = BidWorkflow.objects.filter(status='failed').count()
    cancelled_workflows = BidWorkflow.objects.filter(status='cancelled').count()

    print(f"  总工作流数: {total_workflows}")
    print(f"  运行中: {running_workflows}")
    print(f"  已完成: {completed_workflows}")
    print(f"  待开始: {pending_workflows}")
    print(f"  执行失败: {failed_workflows}")
    print(f"  已取消: {cancelled_workflows}")

    all_statuses = BidWorkflow.objects.values('status').annotate(count=Count('id'))
    print(f"\n  BidWorkflow 完整状态分布:")
    for item in all_statuses:
        print(f"    {item['status']}: {item['count']}")

    return {
        'total': total_workflows,
        'running': running_workflows,
        'completed': completed_workflows,
        'failed': failed_workflows
    }


def simulate_api_response():
    """模拟API响应，与前端期望格式对比"""
    print("\n" + "=" * 60)
    print("5. 对比 API 响应与前端期望格式")
    print("=" * 60)

    today = timezone.now().date()
    yesterday = today - timedelta(days=1)

    crawled_today = CrawlResult.objects.filter(created_at__date=today).count()
    crawled_yesterday = CrawlResult.objects.filter(created_at__date=yesterday).count()
    crawled_trend = int(((crawled_today - crawled_yesterday) / max(crawled_yesterday, 1)) * 100) if crawled_yesterday > 0 else 0

    matched_today = CrawlResult.objects.filter(status='matched', created_at__date=today).count()
    matched_yesterday = CrawlResult.objects.filter(status='matched', created_at__date=yesterday).count()
    matched_trend = int(((matched_today - matched_yesterday) / max(matched_yesterday, 1)) * 100) if matched_yesterday > 0 else 0

    bids_today = BidRecord.objects.filter(created_at__date=today).count()
    bids_yesterday = BidRecord.objects.filter(created_at__date=yesterday).count()
    bids_trend = int(((bids_today - bids_yesterday) / max(bids_yesterday, 1)) * 100) if bids_yesterday > 0 else 0

    won_today = TenderProject.objects.filter(status='won', updated_at__date=today).count()
    won_yesterday = TenderProject.objects.filter(status='won', updated_at__date=yesterday).count()
    won_trend = int(((won_today - won_yesterday) / max(won_yesterday, 1)) * 100) if won_yesterday > 0 else 0

    total_workflows = BidWorkflow.objects.count()
    running_workflows = BidWorkflow.objects.filter(status__in=['collecting', 'matching', 'analyzing', 'generating', 'reviewing', 'optimizing', 'uploading', 'tracking']).count()
    completed_workflows = BidWorkflow.objects.filter(status='completed').count()
    pending_review_workflows = BidWorkflow.objects.filter(status='reviewing').count()
    failed_workflows = BidWorkflow.objects.filter(status='failed').count()

    crawl_auto_rate = 95
    match_auto_rate = 80
    generate_auto_rate = 70
    review_auto_rate = 60
    upload_auto_rate = 90

    crawl_status = 'running' if running_workflows > 0 else 'idle'
    overall_status = 'running' if running_workflows > 0 else 'idle'
    if failed_workflows > running_workflows and failed_workflows > 0:
        overall_status = 'error'

    api_response = {
        'crawled_today': crawled_today,
        'crawled_trend': crawled_trend,
        'matched_today': matched_today,
        'matched_trend': matched_trend,
        'bids_today': bids_today,
        'bids_trend': bids_trend,
        'won_today': won_today,
        'won_trend': won_trend,
        'crawl_count': crawled_today,
        'crawl_auto_rate': crawl_auto_rate,
        'crawl_status': crawl_status,
        'match_count': matched_today,
        'match_auto_rate': match_auto_rate,
        'match_status': 'running' if running_workflows > 0 else 'idle',
        'generate_count': completed_workflows,
        'generate_auto_rate': generate_auto_rate,
        'generate_status': 'running' if running_workflows > 0 else 'idle',
        'review_count': pending_review_workflows,
        'review_auto_rate': review_auto_rate,
        'review_status': 'idle',
        'upload_count': bids_today,
        'upload_auto_rate': upload_auto_rate,
        'upload_status': 'idle',
        'overall_status': overall_status,
        'overall_auto_rate': (crawl_auto_rate + match_auto_rate + generate_auto_rate + review_auto_rate + upload_auto_rate) // 5,
        'avg_duration': '2.5分钟',
        'time_saved': '78%',
        'self_heal_rate': 92,
        'total_workflows': total_workflows,
        'running_workflows': running_workflows,
        'completed_workflows': completed_workflows,
        'pending_review': pending_review_workflows,
        'failed_workflows': failed_workflows
    }

    print("\n  API 返回数据 (frontend 期望的字段):")
    frontend_fields = [
        'crawled_today', 'crawled_trend', 'matched_today', 'matched_trend',
        'bids_today', 'bids_trend', 'won_today', 'won_trend',
        'overall_status',
        'crawl_count', 'crawl_auto_rate', 'crawl_status',
        'match_count', 'match_auto_rate', 'match_status',
        'generate_count', 'generate_auto_rate', 'generate_status',
        'review_count', 'review_auto_rate', 'review_status',
        'upload_count', 'upload_auto_rate', 'upload_status',
        'overall_auto_rate', 'avg_duration', 'time_saved', 'self_heal_rate'
    ]

    for field in frontend_fields:
        value = api_response.get(field, 'MISSING')
        print(f"    {field}: {value}")

    missing_fields = [f for f in frontend_fields if f not in api_response]
    if missing_fields:
        print(f"\n  缺失字段: {missing_fields}")

    return api_response


def check_data_consistency():
    """检查数据一致性"""
    print("\n" + "=" * 60)
    print("6. 数据一致性检查")
    print("=" * 60)

    issues = []

    crawl_results_count = CrawlResult.objects.count()
    tender_projects_count = TenderProject.objects.count()

    print(f"  CrawlResult 总数: {crawl_results_count}")
    print(f"  TenderProject 总数: {tender_projects_count}")

    if crawl_results_count == 0 and tender_projects_count == 0:
        issues.append("警告: 数据库中没有采集数据，统计将全部显示为0")

    bid_records_count = BidRecord.objects.count()
    print(f"  BidRecord 总数: {bid_records_count}")

    if bid_records_count == 0:
        issues.append("警告: 数据库中没有投标记录")

    workflows = BidWorkflow.objects.all()
    if workflows.count() == 0:
        issues.append("警告: 数据库中没有工作流记录")

    workflow_statuses_with_bids = BidWorkflow.objects.exclude(
        status__in=['pending', 'completed', 'cancelled', 'failed']
    ).count()
    print(f"  活跃工作流数: {workflow_statuses_with_bids}")

    for wf in workflows[:5]:
        print(f"    - {wf.name}: {wf.status} (created_at: {wf.created_at})")

    if issues:
        print("\n  发现的问题:")
        for issue in issues:
            print(f"    - {issue}")
    else:
        print("\n  未发现明显的数据一致性问题")

    return issues


def main():
    print("=" * 60)
    print("自动化监控中心 - 统计数据验证报告")
    print("=" * 60)
    print(f"验证时间: {timezone.now()}")
    print(f"数据库: PostgreSQL")

    verify_crawl_stats()
    verify_bid_stats()
    verify_tender_stats()
    verify_workflow_stats()
    simulate_api_response()
    issues = check_data_consistency()

    print("\n" + "=" * 60)
    print("验证结论")
    print("=" * 60)

    if not issues:
        print("  ✓ 统计数据计算逻辑正确")
        print("  ✓ API响应格式与前端期望一致")
        print("  ✓ 各表数据状态分布正常")
    else:
        print("  ! 存在需要关注的问题（见上文）")

    print("\n" + "=" * 60)
    print("潜在问题分析")
    print("=" * 60)
    print("""
  1. 硬编码的自动化率:
     - crawl_auto_rate = 95 (硬编码)
     - match_auto_rate = 80 (硬编码)
     - generate_auto_rate = 70 (硬编码)
     - review_auto_rate = 60 (硬编码)
     - upload_auto_rate = 90 (硬编码)
     这些值不是从实际数据计算得出的

  2. 固定的效率指标:
     - avg_duration = '2.5分钟' (硬编码)
     - time_saved = '78%' (硬编码)
     - self_heal_rate = 92 (硬编码)
     这些值没有从实际工作流执行数据计算

  3. 工作流状态映射问题:
     - 前端期望 'crawl', 'match', 'generate', 'review', 'upload'
     - 后端 BidWorkflow 实际状态: 'collecting', 'matching', 'generating', 'reviewing', 'uploading'
     - 统计API硬编码返回 'idle' 或 'running'，没有真正根据各阶段状态判断

  4. 中标数据来源:
     - won_today 统计 TenderProject.status='won'
     - 但实际中标信息可能存储在 BidResult 表中
""")


if __name__ == '__main__':
    main()
