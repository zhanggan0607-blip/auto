"""
投标自动化工作流API视图
"""
import logging
import asyncio
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.db.models import Q

from utils.responses import APIResponse
from services.bid_automation_workflow import bid_automation_workflow, TaskStatus
from services.bid_task_scheduler import bid_task_scheduler
from core.viewsets import APIResponseMixin

logger = logging.getLogger(__name__)


def run_async(coro):
    """
    在同步上下文中运行异步协程
    """
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                future = pool.submit(asyncio.run, coro)
                return future.result()
        else:
            return loop.run_until_complete(coro)
    except RuntimeError:
        return asyncio.run(coro)


class BidWorkflowViewSet(APIResponseMixin, viewsets.ViewSet):
    """
    投标自动化工作流视图集
    """
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['post'])
    def start(self, request):
        """
        启动投标工作流
        """
        tender_id = request.data.get('tender_id')
        enterprise_id = request.data.get('enterprise_id')
        config = request.data.get('config', {})
        
        if not tender_id or not enterprise_id:
            return APIResponse.error(
                message='缺少必要参数: tender_id, enterprise_id',
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        result = run_async(bid_automation_workflow.start_workflow(
            tender_id=tender_id,
            enterprise_id=enterprise_id,
            config=config
        ))
        
        if result.get('status') == 'started':
            return APIResponse.success(data=result, message='工作流启动成功')
        else:
            return APIResponse.error(message=result.get('error', '启动失败'))
    
    @action(detail=False, methods=['get'])
    def status(self, request):
        """
        获取工作流状态
        """
        workflow_id = request.query_params.get('workflow_id')
        
        if not workflow_id:
            return APIResponse.error(
                message='缺少参数: workflow_id',
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        result = run_async(bid_automation_workflow.get_workflow_status(workflow_id))
        
        if result:
            return APIResponse.success(data=result)
        else:
            return APIResponse.error(message='工作流不存在', status_code=status.HTTP_404_NOT_FOUND)
    
    @action(detail=False, methods=['post'])
    def resume(self, request):
        """
        恢复暂停的工作流
        """
        workflow_id = request.data.get('workflow_id')
        action_type = request.data.get('action', 'continue')
        
        if not workflow_id:
            return APIResponse.error(
                message='缺少参数: workflow_id',
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        result = run_async(bid_automation_workflow.resume_workflow(workflow_id, action_type))
        
        if 'error' in result:
            return APIResponse.error(message=result['error'])
        
        return APIResponse.success(data=result, message='工作流已恢复')
    
    @action(detail=False, methods=['get'])
    def list_active(self, request):
        """
        获取活跃的工作流列表
        """
        from apps.openclaw.workflow_models import BidWorkflow
        
        workflows = BidWorkflow.objects.filter(
            status__in=['pending', 'running', 'waiting_review']
        ).order_by('-created_at')[:20]
        
        data = [{
            'id': wf.id,
            'name': wf.name,
            'tender_id': wf.tender_id,
            'status': wf.status,
            'current_stage': wf.current_stage,
            'created_at': wf.created_at.isoformat() if wf.created_at else None,
            'started_at': wf.started_at.isoformat() if wf.started_at else None
        } for wf in workflows]
        
        return APIResponse.success(data={'list': data})
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """
        获取工作流统计数据
        """
        from apps.openclaw.workflow_models import BidWorkflow
        
        total = BidWorkflow.objects.count()
        running = BidWorkflow.objects.filter(status='running').count()
        completed = BidWorkflow.objects.filter(status='completed').count()
        pending_review = BidWorkflow.objects.filter(status='waiting_review').count()
        failed = BidWorkflow.objects.filter(status='failed').count()
        
        return APIResponse.success(data={
            'total_workflows': total,
            'running_workflows': running,
            'completed_workflows': completed,
            'pending_review': pending_review,
            'failed_workflows': failed
        })


class TaskSchedulerViewSet(APIResponseMixin, viewsets.ViewSet):
    """
    任务调度器视图集
    """
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def status(self, request):
        """
        获取调度器状态
        """
        result = run_async(bid_task_scheduler.get_scheduler_status())
        return APIResponse.success(data=result)
    
    @action(detail=False, methods=['post'])
    def start(self, request):
        """
        启动调度器
        """
        run_async(bid_task_scheduler.start())
        return APIResponse.success(message='调度器已启动')
    
    @action(detail=False, methods=['post'])
    def stop(self, request):
        """
        停止调度器
        """
        run_async(bid_task_scheduler.stop())
        return APIResponse.success(message='调度器已停止')
    
    @action(detail=False, methods=['post'])
    def enable_task(self, request):
        """
        启用调度任务
        """
        task_id = request.data.get('task_id')
        if not task_id:
            return APIResponse.error(message='缺少参数: task_id')
        success = run_async(bid_task_scheduler.enable_task(task_id))
        if success:
            return APIResponse.success(message='任务已启用')
        return APIResponse.error(message='任务不存在')
    
    @action(detail=False, methods=['post'])
    def disable_task(self, request):
        """
        禁用调度任务
        """
        task_id = request.data.get('task_id')
        if not task_id:
            return APIResponse.error(message='缺少参数: task_id')
        success = run_async(bid_task_scheduler.disable_task(task_id))
        if success:
            return APIResponse.success(message='任务已禁用')
        return APIResponse.error(message='任务不存在')
    
    @action(detail=False, methods=['post'])
    def run_now(self, request):
        """
        立即执行任务
        """
        task_id = request.data.get('task_id')
        if not task_id:
            return APIResponse.error(message='缺少参数: task_id')
        result = run_async(bid_task_scheduler.run_task_now(task_id))
        if result.get('success'):
            return APIResponse.success(message=result.get('message', '执行完成'))
        return APIResponse.error(message=result.get('error', '执行失败'))
    
    @action(detail=False, methods=['get'])
    def health(self, request):
        """
        获取系统健康状态
        """
        from django.core.cache import cache
        
        health = cache.get('system_health', {})
        
        return APIResponse.success(data={
            'status': 'healthy' if health.get('database') == 'ok' else 'degraded',
            'details': health,
            'timestamp': timezone.now().isoformat()
        })
