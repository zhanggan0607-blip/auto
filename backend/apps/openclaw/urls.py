"""
OpenClaw API URL路由
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .workflow_views import BidWorkflowViewSet as AutomationWorkflowViewSet, TaskSchedulerViewSet
from .views import (
    LLMProviderViewSet, LLMModelViewSet, AgentModelConfigViewSet,
    LLMUsageLogViewSet, AutomationConfigViewSet, AIPlaygroundViewSet,
    ErrorKnowledgeViewSet, AutoOptimizerViewSet
)
from .one_click_views import OneClickAutomationViewSet, EnterpriseQuickSetupViewSet, WebsiteQuickSelectViewSet


router = DefaultRouter()
router.register(r'llm-providers', LLMProviderViewSet, basename='llm-provider')
router.register(r'llm-models', LLMModelViewSet, basename='llm-model')
router.register(r'agent-model-configs', AgentModelConfigViewSet, basename='agent-config')
router.register(r'usage-logs', LLMUsageLogViewSet, basename='usage-log')
router.register(r'automation-config', AutomationConfigViewSet, basename='automation-config')
router.register(r'automation', AutomationWorkflowViewSet, basename='automation-workflow')
router.register(r'scheduler', TaskSchedulerViewSet, basename='task-scheduler')
router.register(r'playground', AIPlaygroundViewSet, basename='ai-playground')
router.register(r'one-click', OneClickAutomationViewSet, basename='one-click')
router.register(r'one-click/enterprise', EnterpriseQuickSetupViewSet, basename='one-click-enterprise')
router.register(r'websites', WebsiteQuickSelectViewSet, basename='website-quick-select')
router.register(r'error-knowledge', ErrorKnowledgeViewSet, basename='error-knowledge')
router.register(r'optimizer', AutoOptimizerViewSet, basename='auto-optimizer')

urlpatterns = router.urls
