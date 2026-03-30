"""
投标文档向量库 - URL路由
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import BidDocumentLibraryViewSet, AISearchTaskViewSet

router = DefaultRouter()
router.register(r'documents', BidDocumentLibraryViewSet, basename='vectorlib-document')
router.register(r'ai-search', AISearchTaskViewSet, basename='vectorlib-ai-search')

urlpatterns = [
    path('', include(router.urls)),
]
