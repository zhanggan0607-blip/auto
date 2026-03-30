"""
投标仓储
提供投标记录相关的数据访问接口
"""
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

from .base_repository import BaseRepository
from apps.bids.models import BidRecord


class BidRepository(BaseRepository[BidRecord]):
    """
    投标仓储
    提供投标记录的数据访问接口
    """

    def __init__(self):
        super().__init__(BidRecord)

    def get_by_enterprise(self, enterprise_id: int) -> List[BidRecord]:
        """
        获取指定企业的所有投标记录

        Args:
            enterprise_id: 企业ID

        Returns:
            List[BidRecord]: 投标记录列表
        """
        return list(
            self.model.objects.filter(enterprise_id=enterprise_id)
            .order_by('-created_at')
        )

    def get_by_user(self, user_id: int) -> List[BidRecord]:
        """
        获取指定用户创建的投标记录

        Args:
            user_id: 用户ID

        Returns:
            List[BidRecord]: 投标记录列表
        """
        return list(
            self.model.objects.filter(created_by_id=user_id)
            .order_by('-created_at')
        )

    def get_won(self, enterprise_id: int = None) -> List[BidRecord]:
        """
        获取已中标的投标记录

        Args:
            enterprise_id: 企业ID（可选）

        Returns:
            List[BidRecord]: 已中标的投标记录列表
        """
        queryset = self.model.objects.filter(status='won')
        if enterprise_id:
            queryset = queryset.filter(enterprise_id=enterprise_id)
        return list(queryset.order_by('-created_at'))

    def get_pending(self, enterprise_id: int = None) -> List[BidRecord]:
        """
        获取待开标的投标记录

        Args:
            enterprise_id: 企业ID（可选）

        Returns:
            List[BidRecord]: 待开标的投标记录列表
        """
        queryset = self.model.objects.filter(status='pending')
        if enterprise_id:
            queryset = queryset.filter(enterprise_id=enterprise_id)
        return list(queryset.order_by('-deadline_date'))

    def get_recent(self, days: int = 30, user_id: int = None) -> List[BidRecord]:
        """
        获取最近N天的投标记录

        Args:
            days: 天数
            user_id: 用户ID（可选）

        Returns:
            List[BidRecord]: 投标记录列表
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        queryset = self.model.objects.filter(created_at__gte=cutoff_date)
        if user_id:
            queryset = queryset.filter(created_by_id=user_id)
        return list(queryset.order_by('-created_at'))

    def get_statistics(self, enterprise_id: int) -> Dict[str, Any]:
        """
        获取企业的投标统计信息

        Args:
            enterprise_id: 企业ID

        Returns:
            Dict[str, Any]: 统计信息
        """
        records = self.model.objects.filter(enterprise_id=enterprise_id)

        total = records.count()
        won = records.filter(status='won').count()
        lost = records.filter(status='lost').count()
        pending = records.filter(status='pending').count()

        total_amount = sum(
            float(r.bid_amount or 0)
            for r in records.filter(status='won')
        )

        return {
            'total': total,
            'won': won,
            'lost': lost,
            'pending': pending,
            'win_rate': won / total if total > 0 else 0,
            'total_amount': total_amount
        }

    def search(self, keyword: str, user_id: int = None) -> List[BidRecord]:
        """
        搜索投标记录

        Args:
            keyword: 搜索关键词
            user_id: 用户ID（可选）

        Returns:
            List[BidRecord]: 匹配的投标记录列表
        """
        queryset = self.model.objects.filter(
            models.Q(tender_title__icontains=keyword) |
            models.Q(enterprise__name__icontains=keyword)
        )

        if user_id:
            queryset = queryset.filter(created_by_id=user_id)

        return list(queryset.order_by('-created_at'))

    def get_by_status(self, status: str, user_id: int = None) -> List[BidRecord]:
        """
        获取指定状态的投标记录

        Args:
            status: 状态
            user_id: 用户ID（可选）

        Returns:
            List[BidRecord]: 投标记录列表
        """
        queryset = self.model.objects.filter(status=status)
        if user_id:
            queryset = queryset.filter(created_by_id=user_id)
        return list(queryset.order_by('-created_at'))


from django.db import models