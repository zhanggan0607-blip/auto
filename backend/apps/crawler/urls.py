"""
SAAS采集模块 - URL配置
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    WebsiteTemplateViewSet,
    CrawlSessionViewSet,
    CrawlResultViewSet,
    CrawlLogViewSet,
    ContentRecognitionRuleViewSet,
    RecognizedContentViewSet
)
from .scheduler_views import (
    CrawlScheduleViewSet,
    CrawlScheduleLogViewSet,
    QualificationMatchViewSet
)
from .views_verification import (
    DataSourceValidationView,
    DataSourceValidationListView,
    DualStageCollectionView,
    CollectionWorkflowStatusView
)

router = DefaultRouter()
router.register(r'templates', WebsiteTemplateViewSet, basename='website-template')
router.register(r'sessions', CrawlSessionViewSet, basename='crawl-session')
router.register(r'results', CrawlResultViewSet, basename='crawl-result')
router.register(r'logs', CrawlLogViewSet, basename='crawl-log')
router.register(r'schedules', CrawlScheduleViewSet, basename='crawl-schedule')
router.register(r'schedule-logs', CrawlScheduleLogViewSet, basename='crawl-schedule-log')
router.register(r'qualification-match', QualificationMatchViewSet, basename='qualification-match')
router.register(r'recognition-rules', ContentRecognitionRuleViewSet, basename='recognition-rule')
router.register(r'recognized', RecognizedContentViewSet, basename='recognized-content')

urlpatterns = [
    path('', include(router.urls)),
    path('validate/', DataSourceValidationView.as_view(), name='datasource-validation'),
    path('validations/', DataSourceValidationListView.as_view(), name='datasource-validation-list'),
    path('collection/', DualStageCollectionView.as_view(), name='dual-stage-collection'),
    path('workflow/<str:workflow_id>/', CollectionWorkflowStatusView.as_view(), name='workflow-status'),
]
