from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    EnterpriseViewSet,
    EnterpriseQualificationViewSet,
    EnterprisePerformanceViewSet,
    EnterpriseDocumentViewSet,
    EnterpriseKeyPersonnelViewSet,
    EnterpriseContactViewSet,
    EnterpriseMatchRuleViewSet,
)

router = DefaultRouter()
router.register(r'enterprises', EnterpriseViewSet, basename='enterprise')
router.register(r'qualifications', EnterpriseQualificationViewSet, basename='enterprise-qualification')
router.register(r'performances', EnterprisePerformanceViewSet, basename='enterprise-performance')
router.register(r'documents', EnterpriseDocumentViewSet, basename='enterprise-document')
router.register(r'key-personnel', EnterpriseKeyPersonnelViewSet, basename='enterprise-key-personnel')
router.register(r'contacts', EnterpriseContactViewSet, basename='enterprise-contact')
router.register(r'match-rules', EnterpriseMatchRuleViewSet, basename='enterprise-match-rule')

urlpatterns = [
    path('', include(router.urls)),
]
