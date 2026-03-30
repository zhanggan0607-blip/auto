"""
Monitor URL配置
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    MonitoredServiceViewSet, ServiceHealthRecordViewSet,
    ServiceAlertViewSet, ServiceActionLogViewSet,
    ServiceStatusDashboardView, MonitorHealthCheckView,
    MonitorAutoRecoveryView
)

router = DefaultRouter()
router.register(r'services', MonitoredServiceViewSet, basename='monitored-service')
router.register(r'health-records', ServiceHealthRecordViewSet, basename='health-record')
router.register(r'alerts', ServiceAlertViewSet, basename='service-alert')
router.register(r'action-logs', ServiceActionLogViewSet, basename='action-log')

urlpatterns = [
    path('', include(router.urls)),
    path('dashboard/', ServiceStatusDashboardView.as_view(), name='service-dashboard'),
    path('health-check/', MonitorHealthCheckView.as_view(), name='monitor-health-check'),
    path('auto-recovery/', MonitorAutoRecoveryView.as_view(), name='monitor-auto-recovery'),
]