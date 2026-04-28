from typing import List, Dict, Any, Optional
from datetime import timedelta

from django.db import models
from django.utils import timezone

from .base_repository import BaseRepository
from apps.tenders.models import TenderProject


class TenderRepository(BaseRepository[TenderProject]):

    def __init__(self):
        super().__init__(TenderProject)

    def get_recent(self, days: int = 7) -> List[TenderProject]:
        cutoff_date = timezone.now().date() - timedelta(days=days)
        return list(
            self.model.objects.filter(publish_date__gte=cutoff_date)
            .order_by('-publish_date')
        )

    def get_by_source(self, source_id: int, limit: int = 100) -> List[TenderProject]:
        return list(
            self.model.objects.filter(source_id=source_id)
            .order_by('-publish_date')[:limit]
        )

    def search(self, keyword: str, user_id: int = None) -> List[TenderProject]:
        queryset = self.model.objects.filter(
            models.Q(title__icontains=keyword) |
            models.Q(region__icontains=keyword) |
            models.Q(industry__icontains=keyword)
        )

        if user_id:
            queryset = queryset.filter(created_by_id=user_id)

        return list(queryset)

    def get_pending(self, user_id: int = None) -> List[TenderProject]:
        queryset = self.model.objects.filter(status='pending', is_deleted=False)

        if user_id:
            queryset = queryset.filter(created_by_id=user_id)

        return list(queryset.order_by('-created_at'))

    def get_expired(self) -> List[TenderProject]:
        today = timezone.now().date()
        return list(
            self.model.objects.filter(deadline_date__lt=today, is_deleted=False)
            .exclude(status='expired')
        )

    def mark_as_processed(self, tender_id: int) -> Optional[TenderProject]:
        return self.update(tender_id, status='processed')

    def get_by_industry(self, industry: str, limit: int = 50) -> List[TenderProject]:
        return list(
            self.model.objects.filter(industry=industry, is_deleted=False)
            .order_by('-publish_date')[:limit]
        )

    def get_by_region(self, province: str = None, city: str = None) -> List[TenderProject]:
        queryset = self.model.objects.filter(is_deleted=False)

        if province:
            queryset = queryset.filter(province__icontains=province)
        if city:
            queryset = queryset.filter(city__icontains=city)

        return list(queryset.order_by('-publish_date'))

    def get_approaching_deadline(self, days: int = 7, user_id: int = None) -> List[TenderProject]:
        now = timezone.now().date()
        deadline = now + timedelta(days=days)
        queryset = self.model.objects.filter(
            deadline_date__gte=now,
            deadline_date__lte=deadline,
            is_deleted=False,
        ).order_by('deadline_date')
        if user_id:
            queryset = queryset.filter(created_by_id=user_id)
        return list(queryset)
