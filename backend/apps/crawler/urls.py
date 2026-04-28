from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import WebsiteTemplateViewSet
from .scheduler_views import CrawlScheduleViewSet, QualificationMatchViewSet

router = DefaultRouter()
router.register(r'templates', WebsiteTemplateViewSet, basename='website-template')
router.register(r'schedules', CrawlScheduleViewSet, basename='crawl-schedule')
router.register(r'qualification-match', QualificationMatchViewSet, basename='qualification-match')

urlpatterns = [
    path('', include(router.urls)),
]
