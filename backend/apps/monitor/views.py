"""
Monitor API视图
"""
import logging
from datetime import timedelta

from django.utils import timezone
from django.db.models import Prefetch, F, Q
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from utils.responses import UnifiedResponse

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
    queryset = MonitoredService.objects.all()
    serializer_class = MonitoredServiceSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy', 'restart', 'check_health']:
            return [IsAuthenticated(), IsAdminUser()]
        return [IsAuthenticated()]

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
        service = self.get_object()
        result = ServiceHealthMonitor.check_single_service(service.id)

        if 'error' in result:
            return UnifiedResponse.not_found(result['error'])

        serializer = MonitoredServiceSerializer(service)
        return UnifiedResponse.success(data={
            'service': serializer.data,
            'check_result': result
        })

    @action(detail=True, methods=['post'])
    def restart(self, request, pk=None):
        service = self.get_object()

        can_restart, reason = ServiceRestartManager.can_restart(service, restart_type='manual')
        if not can_restart:
            return UnifiedResponse.error(message=reason)

        result = ServiceRestartManager.execute_restart(
            service,
            action_type='manual_restart',
            trigger_condition='手动触发重启'
        )

        if result['success']:
            service.refresh_from_db()
            serializer = MonitoredServiceSerializer(service)
            return UnifiedResponse.success(data={
                'message': result['message'],
                'service': serializer.data
            })
        else:
            error_msg = result.get('message') or '不支持此服务的重启'
            unsupported_keywords = ['不支持', '未找到', '无法', '未安装', '重启执行返回失败', '重启失败', '启动进程失败', '需要管理员权限', '冷却中', '已达上限', '超时', 'Docker', '容器', 'No such container', '未部署', '嵌入式', '手动重启', '未运行且本地未找到']
            if any(keyword in error_msg for keyword in unsupported_keywords):
                return UnifiedResponse.error(message=error_msg)
            return UnifiedResponse.server_error(message=error_msg)

    @action(detail=False, methods=['get'])
    def categories(self, request):
        categories = [
            {'value': choice[0], 'label': choice[1]}
            for choice in MonitoredService.category.field.choices
        ]
        return UnifiedResponse.success(data=categories)


class ServiceHealthRecordViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ServiceHealthRecord.objects.all()
    serializer_class = ServiceHealthRecordSerializer
    permission_classes = [IsAuthenticated]

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
        return UnifiedResponse.success(data=serializer.data)

    @action(detail=False, methods=['get'])
    def statistics(self, request):
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
            from django.db.models import Avg
            avg_result = queryset.filter(
                is_healthy=True,
                response_time_ms__isnull=False
            ).aggregate(avg_time=Avg('response_time_ms'))
            avg_response_time = round(avg_result['avg_time'], 2) if avg_result['avg_time'] else None
        except Exception:
            pass

        return UnifiedResponse.success(data={
            'period_hours': hours,
            'total_checks': total,
            'healthy_checks': healthy,
            'unhealthy_checks': unhealthy,
            'health_rate': round(healthy / total * 100, 2) if total > 0 else 0,
            'avg_response_time_ms': avg_response_time
        })


class ServiceAlertViewSet(viewsets.ModelViewSet):
    queryset = ServiceAlert.objects.all()
    serializer_class = ServiceAlertSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy', 'resolve', 'resolve_all', 'send_notification']:
            return [IsAuthenticated(), IsAdminUser()]
        return [IsAuthenticated()]

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
        alert = self.get_object()
        success = AlertManager.resolve_alert(alert.id, request.user.username if request.user.is_authenticated else 'manual')
        if success:
            alert.refresh_from_db()
            serializer = self.get_serializer(alert)
            return UnifiedResponse.success(data=serializer.data)
        return UnifiedResponse.server_error(message='解决告警失败')

    @action(detail=False, methods=['post'])
    def resolve_all(self, request):
        alert_ids = request.data.get('alert_ids', [])
        if not alert_ids:
            return UnifiedResponse.error(message='未指定告警ID')

        updated = ServiceAlert.objects.filter(
            id__in=alert_ids,
            status__in=['pending', 'notified']
        ).update(
            status='resolved',
            resolved_at=timezone.now()
        )

        return UnifiedResponse.success(data={'resolved_count': updated})

    @action(detail=False, methods=['get'])
    def pending(self, request):
        alerts = AlertManager.get_pending_alerts()
        serializer = self.get_serializer(alerts, many=True)
        return UnifiedResponse.success(data=serializer.data)

    @action(detail=True, methods=['post'])
    def send_notification(self, request, pk=None):
        alert = self.get_object()
        success = AlertManager.send_alert_notification(alert)
        if success:
            alert.refresh_from_db()
            serializer = self.get_serializer(alert)
            return UnifiedResponse.success(data=serializer.data)
        return UnifiedResponse.server_error(message='发送通知失败')


class ServiceActionLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ServiceActionLog.objects.all()
    serializer_class = ServiceActionLogSerializer
    permission_classes = [IsAuthenticated]

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
    permission_classes = [IsAuthenticated]

    def get(self, request):
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

        return UnifiedResponse.success(data={
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
    permission_classes = [IsAuthenticated, IsAdminUser]

    def post(self, request):
        result = ServiceHealthMonitor.check_all_services()
        return UnifiedResponse.success(data=result)

    def get(self, request):
        result = ServiceHealthMonitor.check_all_services()
        return UnifiedResponse.success(data=result)


class MonitorAutoRecoveryView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def post(self, request):
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

        return UnifiedResponse.success(data={
            'processed_count': len(results),
            'results': results
        })
