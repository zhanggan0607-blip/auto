"""
统一调度API视图
提供调度任务的统一管理接口
"""
import logging
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from django.core.cache import cache

from .models import UnifiedSchedule, ScheduleExecutionLog
from .serializers import UnifiedScheduleSerializer, ScheduleExecutionLogSerializer
from .unified_tasks import DEFAULT_SCHEDULE_CONFIGS, setup_default_schedules
from core.viewsets import APIResponseMixin

logger = logging.getLogger(__name__)


class UnifiedScheduleViewSet(APIResponseMixin, viewsets.ModelViewSet):
    """
    统一调度任务管理
    """
    queryset = UnifiedSchedule.objects.all()
    serializer_class = UnifiedScheduleSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        task_type = self.request.query_params.get('task_type')
        is_enabled = self.request.query_params.get('is_enabled')

        if task_type:
            queryset = queryset.filter(task_type=task_type)
        if is_enabled is not None:
            queryset = queryset.filter(is_enabled=is_enabled.lower() == 'true')

        return queryset

    @action(detail=False, methods=['post'])
    def init_defaults(self, request):
        """
        初始化默认调度任务
        """
        try:
            setup_default_schedules()

            for config in DEFAULT_SCHEDULE_CONFIGS:
                task_path = f'unified_scheduler.{config["task_id"]}'

                UnifiedSchedule.objects.update_or_create(
                    task_id=config['task_id'],
                    defaults={
                        'task_name': config['name'],
                        'task_type': config['task_id'],
                        'description': config['description'],
                        'cron_expression': config['cron_expression'],
                        'is_enabled': config['enabled'],
                    }
                )

            return Response({
                'success': True,
                'message': '默认调度任务初始化完成',
                'count': len(DEFAULT_SCHEDULE_CONFIGS)
            })
        except Exception as e:
            logger.error(f"初始化默认调度任务失败: {str(e)}")
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['post'])
    def enable(self, request, pk=None):
        """
        启用调度任务
        """
        schedule = self.get_object()
        schedule.is_enabled = True
        schedule.update_celery_task()
        schedule.save()

        return Response({
            'success': True,
            'message': f'任务 {schedule.task_name} 已启用'
        })

    @action(detail=True, methods=['post'])
    def disable(self, request, pk=None):
        """
        禁用调度任务
        """
        schedule = self.get_object()
        schedule.is_enabled = False
        schedule.update_celery_task()
        schedule.save()

        return Response({
            'success': True,
            'message': f'任务 {schedule.task_name} 已禁用'
        })

    @action(detail=True, methods=['post'])
    def run_now(self, request, pk=None):
        """
        立即执行任务
        """
        from celery import current_app

        schedule = self.get_object()

        try:
            task_path = f'unified_scheduler.{schedule.task_id}'
            result = current_app.send_task(task_path)

            return Response({
                'success': True,
                'message': f'任务 {schedule.task_name} 已提交执行',
                'task_id': result.id
            })
        except Exception as e:
            logger.error(f"执行任务失败: {str(e)}")
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'])
    def status(self, request):
        """
        获取调度系统状态
        """
        health_status = cache.get('system_health', {})

        schedules = UnifiedSchedule.objects.all()
        total = schedules.count()
        enabled = schedules.filter(is_enabled=True).count()
        running = schedules.filter(last_run_status='running').count()

        return Response({
            'success': True,
            'data': {
                'total_tasks': total,
                'enabled_tasks': enabled,
                'running_tasks': running,
                'health': health_status,
                'timestamp': timezone.now().isoformat()
            }
        })

    @action(detail=False, methods=['get'])
    def health(self, request):
        """
        获取系统健康状态
        """
        health_status = cache.get('system_health', {})

        return Response({
            'success': True,
            'data': health_status
        })


class ScheduleExecutionLogViewSet(APIResponseMixin, viewsets.ReadOnlyModelViewSet):
    """
    调度执行日志查询
    """
    queryset = ScheduleExecutionLog.objects.all()
    serializer_class = ScheduleExecutionLogSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        schedule_id = self.request.query_params.get('schedule_id')
        status = self.request.query_params.get('status')

        if schedule_id:
            queryset = queryset.filter(schedule_id=schedule_id)
        if status:
            queryset = queryset.filter(status=status)

        return queryset[:100]
