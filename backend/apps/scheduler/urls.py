"""
统一调度URL配置
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UnifiedScheduleViewSet, ScheduleExecutionLogViewSet

router = DefaultRouter()
router.register(r'schedules', UnifiedScheduleViewSet, basename='unified-schedule')
router.register(r'logs', ScheduleExecutionLogViewSet, basename='schedule-log')

urlpatterns = [
    path('', include(router.urls)),
]
