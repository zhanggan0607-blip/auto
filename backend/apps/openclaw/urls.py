from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .workflow_views import BidWorkflowViewSet as AutomationWorkflowViewSet, TaskSchedulerViewSet
from .views import (
    LLMProviderViewSet, LLMModelViewSet, AgentModelConfigViewSet,
    AutomationConfigViewSet, AIPlaygroundViewSet,
)
from .one_click_views import OneClickAutomationViewSet

router = DefaultRouter()
router.register(r'llm-providers', LLMProviderViewSet, basename='llm-provider')
router.register(r'llm-models', LLMModelViewSet, basename='llm-model')
router.register(r'agent-model-configs', AgentModelConfigViewSet, basename='agent-config')
router.register(r'automation-config', AutomationConfigViewSet, basename='automation-config')
router.register(r'automation', AutomationWorkflowViewSet, basename='automation-workflow')
router.register(r'playground', AIPlaygroundViewSet, basename='ai-playground')
router.register(r'one-click', OneClickAutomationViewSet, basename='one-click')
router.register(r'scheduler', TaskSchedulerViewSet, basename='scheduler')

urlpatterns = router.urls
