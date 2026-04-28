from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

from django.db import models

from .base_repository import BaseRepository
from apps.bids.models import BidRecord


class BidRepository(BaseRepository[BidRecord]):

    def __init__(self):
        super().__init__(BidRecord)

    def get_by_enterprise(self, enterprise_id: int) -> List[BidRecord]:
        return list(
            self.model.objects.filter(created_by__enterprise__id=enterprise_id)
            .order_by('-created_at')
        )

    def get_by_user(self, user_id: int) -> List[BidRecord]:
        return list(
            self.model.objects.filter(created_by_id=user_id)
            .order_by('-created_at')
        )

    def get_won(self, enterprise_id: int = None) -> List[BidRecord]:
        queryset = self.model.objects.filter(status='won')
        if enterprise_id:
            queryset = queryset.filter(created_by__enterprise__id=enterprise_id)
        return list(queryset.order_by('-created_at'))

    def get_pending(self, enterprise_id: int = None) -> List[BidRecord]:
        queryset = self.model.objects.filter(status='pending')
        if enterprise_id:
            queryset = queryset.filter(created_by__enterprise__id=enterprise_id)
        return list(queryset.order_by('-created_at'))

    def get_recent(self, days: int = 30, user_id: int = None) -> List[BidRecord]:
        from django.utils import timezone
        cutoff_date = timezone.now() - timedelta(days=days)
        queryset = self.model.objects.filter(created_at__gte=cutoff_date)
        if user_id:
            queryset = queryset.filter(created_by_id=user_id)
        return list(queryset.order_by('-created_at'))

    def get_statistics(self, user_id: int) -> Dict[str, Any]:
        from django.db.models import Sum, Count
        records = self.model.objects.filter(created_by_id=user_id)

        total = records.count()
        won = records.filter(status='won').count()
        lost = records.filter(status='lost').count()
        pending = records.filter(status='pending').count()

        total_amount = records.filter(status='won').aggregate(
            total=Sum('bid_price')
        )['total'] or 0

        return {
            'total': total,
            'won': won,
            'lost': lost,
            'pending': pending,
            'win_rate': won / total if total > 0 else 0,
            'total_amount': float(total_amount),
        }

    def search(self, keyword: str, user_id: int = None) -> List[BidRecord]:
        queryset = self.model.objects.filter(
            models.Q(tender__title__icontains=keyword)
        )

        if user_id:
            queryset = queryset.filter(created_by_id=user_id)

        return list(queryset.order_by('-created_at'))

    def get_by_status(self, status: str, user_id: int = None) -> List[BidRecord]:
        queryset = self.model.objects.filter(status=status)
        if user_id:
            queryset = queryset.filter(created_by_id=user_id)
        return list(queryset.order_by('-created_at'))
