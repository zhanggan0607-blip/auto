"""
Monitor API视图
"""
import logging
from datetime import timedelta

from django.utils import timezone
from django.db.models import Prefetch, F, Q
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import (
    MonitoredService, ServiceHealthRecord,
    ServiceAlert, ServiceActionLog, ServiceStatus
)
from .serializers import (
    MonitoredServiceSerializer, MonitoredServiceCreateSerializer,
    ServiceHealthRecordSerializer, ServiceAlertSerializer,
    ServiceAlertUpdateSerializer, ServiceActionLogSerializer,
    ServiceStatusSummarySerializer
)
from .health_checker import ServiceHealthMonitor
from .restart_manager import ServiceRestartManager, AlertManager

logger = logging.getLogger(__name__)


class MonitoredServiceViewSet(viewsets.ModelViewSet):
    """
    被监控服务视图集
    """
    queryset = MonitoredService.objects.all()
    serializer_class = MonitoredServiceSerializer

    def get_serializer_class(self):
        if self.action == 'create':
            return MonitoredServiceCreateSerializer
        return MonitoredServiceSerializer

    def get_queryset(self):
        queryset = MonitoredService.objects.all()

        category = self.request.query_params.get('category')
        if category:
            queryset = queryset.filter(category=category)

        is_enabled = self.request.query_params.get('is_enabled')
        if is_enabled is not None:
            queryset = queryset.filter(is_enabled=is_enabled.lower() == 'true')

        is_critical = self.request.query_params.get('is_critical')
        if is_critical is not None:
            queryset = queryset.filter(is_critical=is_critical.lower() == 'true')

        status_filter = self.request.query_params.get('status')
        if status_filter:
            if status_filter == 'healthy':
                queryset = queryset.filter(consecutive_failures=0, is_enabled=True)
            elif status_filter == 'degraded':
                queryset = queryset.filter(
                    consecutive_failures__gt=0,
                    consecutive_failures__lt=F('consecutive_failures_to_alert')
                )

        return queryset.order_by('category', 'name')

    @action(detail=True, methods=['post'])
    def check_health(self, request, pk=None):
        """手动触发健康检查"""
        service = self.get_object()
        result = ServiceHealthMonitor.check_single_service(service.id)

        if 'error' in result:
            return Response({'error': result['error']}, status=status.HTTP_404_NOT_FOUND)

        serializer = MonitoredServiceSerializer(service)
        return Response({
            'service': serializer.data,
            'check_result': result
        })

    @action(detail=True, methods=['post'])
    def restart(self, request, pk=None):
        """手动触发服务重启"""
        service = self.get_object()

        can_restart, reason = ServiceRestartManager.can_restart(service)
        if not can_restart:
            return Response({'error': reason}, status=status.HTTP_400_BAD_REQUEST)

        result = ServiceRestartManager.execute_restart(
            service,
            action_type='manual_restart',
            trigger_condition='手动触发重启'
        )

        if result['success']:
            service.refresh_from_db()
            serializer = MonitoredServiceSerializer(service)
            return Response({
                'message': result['message'],
                'service': serializer.data
            })
        else:
            error_msg = result.get('message', '重启失败')
            if '不支持' in error_msg or '未找到' in error_msg or '无法' in error_msg or '未安装' in error_msg or '重启执行返回失败' in error_msg:
                return Response({'error': error_msg}, status=status.HTTP_400_BAD_REQUEST)
            return Response({'error': error_msg}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'])
    def categories(self, request):
        """获取所有服务类别"""
        categories = [
            {'value': choice[0], 'label': choice[1]}
            for choice in MonitoredService.category.field.choices
        ]
        return Response(categories)


class ServiceHealthRecordViewSet(viewsets.ReadOnlyModelViewSet):
    """
    健康检查记录视图集（只读）
    """
    queryset = ServiceHealthRecord.objects.all()
    serializer_class = ServiceHealthRecordSerializer

    def get_queryset(self):
        queryset = ServiceHealthRecord.objects.all()

        service_id = self.request.query_params.get('service_id')
        if service_id:
            queryset = queryset.filter(service_id=service_id)

        is_healthy = self.request.query_params.get('is_healthy')
        if is_healthy is not None:
            queryset = queryset.filter(is_healthy=is_healthy.lower() == 'true')

        hours = self.request.query_params.get('hours')
        if hours:
            since = timezone.now() - timedelta(hours=int(hours))
            queryset = queryset.filter(timestamp__gte=since)

        return queryset.select_related('service').order_by('-timestamp')

    @action(detail=False, methods=['get'])
    def latest(self, request):
        """获取每个服务的最新健康记录"""
        service_id = request.query_params.get('service_id')
        if service_id:
            records = ServiceHealthRecord.objects.filter(service_id=service_id).order_by('-timestamp')[:1]
        else:
            records = []
            for service in MonitoredService.objects.all():
                latest = service.health_records.order_by('-timestamp').first()
                if latest:
                    records.append(latest)

        serializer = self.get_serializer(records, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """获取健康检查统计"""
        service_id = request.query_params.get('service_id')
        hours = int(request.query_params.get('hours', 24))

        since = timezone.now() - timedelta(hours=hours)

        queryset = ServiceHealthRecord.objects.filter(timestamp__gte=since)
        if service_id:
            queryset = queryset.filter(service_id=service_id)

        total = queryset.count()
        healthy = queryset.filter(is_healthy=True).count()
        unhealthy = total - healthy

        avg_response_time = None
        try:
            avg_record = queryset.filter(
                is_healthy=True,
                response_time_ms__isnull=False
            ).only('response_time_ms').order_by('response_time_ms')[:1]
            if avg_record:
                avg_response_time = avg_record[0].response_time_ms
        except Exception:
            pass

        return Response({
            'period_hours': hours,
            'total_checks': total,
            'healthy_checks': healthy,
            'unhealthy_checks': unhealthy,
            'health_rate': round(healthy / total * 100, 2) if total > 0 else 0,
            'avg_response_time_ms': avg_response_time
        })


class ServiceAlertViewSet(viewsets.ModelViewSet):
    """
    服务告警视图集
    """
    queryset = ServiceAlert.objects.all()
    serializer_class = ServiceAlertSerializer

    def get_serializer_class(self):
        if self.action in ['update', 'partial_update']:
            return ServiceAlertUpdateSerializer
        return ServiceAlertSerializer

    def get_queryset(self):
        queryset = ServiceAlert.objects.all()

        service_id = self.request.query_params.get('service_id')
        if service_id:
            queryset = queryset.filter(service_id=service_id)

        alert_level = self.request.query_params.get('level')
        if alert_level:
            queryset = queryset.filter(level=alert_level)

        alert_status = self.request.query_params.get('status')
        if alert_status:
            queryset = queryset.filter(status=alert_status)

        days = self.request.query_params.get('days')
        if days:
            since = timezone.now() - timedelta(days=int(days))
            queryset = queryset.filter(created_at__gte=since)

        return queryset.select_related('service').order_by('-created_at')

    @action(detail=True, methods=['post'])
    def resolve(self, request, pk=None):
        """解决告警"""
        alert = self.get_object()
        success = AlertManager.resolve_alert(alert.id, request.user.username if request.user.is_authenticated else 'manual')
        if success:
            alert.refresh_from_db()
            serializer = self.get_serializer(alert)
            return Response(serializer.data)
        return Response({'error': '解决告警失败'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'])
    def resolve_all(self, request):
        """批量解决告警"""
        alert_ids = request.data.get('alert_ids', [])
        if not alert_ids:
            return Response({'error': '未指定告警ID'}, status=status.HTTP_400_BAD_REQUEST)

        updated = ServiceAlert.objects.filter(
            id__in=alert_ids,
            status__in=['pending', 'notified']
        ).update(
            status='resolved',
            resolved_at=timezone.now()
        )

        return Response({'resolved_count': updated})

    @action(detail=False, methods=['get'])
    def pending(self, request):
        """获取待处理告警"""
        alerts = AlertManager.get_pending_alerts()
        serializer = self.get_serializer(alerts, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def send_notification(self, request, pk=None):
        """手动发送告警通知"""
        alert = self.get_object()
        success = AlertManager.send_alert_notification(alert)
        if success:
            alert.refresh_from_db()
            serializer = self.get_serializer(alert)
            return Response(serializer.data)
        return Response({'error': '发送通知失败'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ServiceActionLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    服务操作日志视图集（只读）
    """
    queryset = ServiceActionLog.objects.all()
    serializer_class = ServiceActionLogSerializer

    def get_queryset(self):
        queryset = ServiceActionLog.objects.all()

        service_id = self.request.query_params.get('service_id')
        if service_id:
            queryset = queryset.filter(service_id=service_id)

        action_type = self.request.query_params.get('action_type')
        if action_type:
            queryset = queryset.filter(action_type=action_type)

        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        hours = self.request.query_params.get('hours')
        if hours:
            since = timezone.now() - timedelta(hours=int(hours))
            queryset = queryset.filter(started_at__gte=since)

        days = self.request.query_params.get('days')
        if days:
            since = timezone.now() - timedelta(days=int(days))
            queryset = queryset.filter(started_at__gte=since)

        return queryset.select_related('service').order_by('-started_at')


class ServiceStatusDashboardView(APIView):
    """
    服务状态仪表盘视图
    提供所有服务的当前状态概览
    """

    def get(self, request):
        """获取服务状态仪表盘数据"""
        services = MonitoredService.objects.all()

        service_summaries = []
        total_healthy = 0
        total_degraded = 0
        total_unhealthy = 0
        total_offline = 0

        for service in services:
            latest_record = service.health_records.order_by('-timestamp').first()

            summary = {
                'service_id': service.id,
                'service_name': service.name,
                'display_name': service.display_name,
                'category': service.category,
                'status': service.status,
                'status_display': ServiceStatus(service.status).label if service.status in [s[0] for s in ServiceStatus.choices] else service.status,
                'is_healthy': service.consecutive_failures == 0 and service.is_enabled,
                'consecutive_failures': service.consecutive_failures,
                'last_health_check': service.last_health_check,
                'response_time_ms': latest_record.response_time_ms if latest_record else None,
                'cpu_usage': latest_record.cpu_usage if latest_record else None,
                'memory_usage': latest_record.memory_usage if latest_record else None,
                'restart_attempts_today': service.restart_attempts_today,
                'is_critical': service.is_critical,
                'auto_restart_enabled': service.auto_restart_enabled,
            }

            service_summaries.append(summary)

            if service.status == 'healthy':
                total_healthy += 1
            elif service.status == 'degraded':
                total_degraded += 1
            elif service.status == 'unhealthy':
                total_unhealthy += 1
            else:
                total_offline += 1

        overall_status = 'healthy'
        if total_unhealthy > 0:
            overall_status = 'unhealthy'
        elif total_degraded > 0:
            overall_status = 'degraded'
        elif total_offline > 0:
            overall_status = 'offline'

        pending_alerts_count = ServiceAlert.objects.filter(
            status__in=['pending', 'notified']
        ).count()

        return Response({
            'overall_status': overall_status,
            'statistics': {
                'total': len(services),
                'healthy': total_healthy,
                'degraded': total_degraded,
                'unhealthy': total_unhealthy,
                'offline': total_offline,
            },
            'pending_alerts': pending_alerts_count,
            'services': service_summaries,
            'timestamp': timezone.now().isoformat()
        })


class MonitorHealthCheckView(APIView):
    """
    触发全量健康检查的API视图
    由Celery定时任务调用
    """

    def post(self, request):
        """触发全量健康检查"""
        result = ServiceHealthMonitor.check_all_services()
        return Response(result)

    def get(self, request):
        """获取检查结果"""
        result = ServiceHealthMonitor.check_all_services()
        return Response(result)


class MonitorAutoRecoveryView(APIView):
    """
    触发自动恢复流程的API视图
    """

    def post(self, request):
        """对所有异常服务执行自动恢复"""
        from django.db import models

        services = MonitoredService.objects.filter(
            is_enabled=True,
            auto_restart_enabled=True
        ).filter(
            models.Q(consecutive_failures__gte=models.F('consecutive_failures_to_restart'))
        )

        results = []
        for service in services:
            can_restart, reason = ServiceRestartManager.can_restart(service)
            if can_restart:
                result = ServiceRestartManager.execute_restart(service)
                results.append({
                    'service_id': service.id,
                    'service_name': service.name,
                    'result': result
                })

                alert = AlertManager.check_and_create_alert(service)
                if alert:
                    AlertManager.send_alert_notification(alert)

        return Response({
            'processed_count': len(results),
            'results': results
        })