import logging

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from .assurance_models import CrawlHealthCheck, CrawlOptimizationPlan, CrawlAssuranceReport
from .assurance_serializers import (
    CrawlHealthCheckSerializer,
    CrawlOptimizationPlanSerializer,
    CrawlAssuranceReportListSerializer,
    CrawlAssuranceReportDetailSerializer,
    TriggerAssuranceSerializer,
    QuickHealthCheckSerializer,
)
from common.views.base import AuthenticatedModelViewSet
from utils.responses import UnifiedResponse

logger = logging.getLogger(__name__)
