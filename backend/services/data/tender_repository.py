"""
招标仓储
提供招标公告相关的数据访问接口
"""
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

from .base_repository import BaseRepository
from apps.tenders.models import Tender


class TenderRepository(BaseRepository[Tender]):
    """
    招标仓储
    提供招标公告的数据访问接口
    """

    def __init__(self):
        super().__init__(Tender)

    def get_recent(self, days: int = 7) -> List[Tender]:
        """
        获取最近N天的招标公告

        Args:
            days: 天数

        Returns:
            List[Tender]: 招标公告列表
        """
        cutoff_date = datetime.now().date() - timedelta(days=days)
        return list(
            self.model.objects.filter(publish_date__gte=cutoff_date)
            .order_by('-publish_date')
        )

    def get_by_source(self, source: str, limit: int = 100) -> List[Tender]:
        """
        获取指定来源的招标公告

        Args:
            source: 来源名称
            limit: 返回数量限制

        Returns:
            List[Tender]: 招标公告列表
        """
        return list(
            self.model.objects.filter(source=source)
            .order_by('-publish_date')[:limit]
        )

    def search(self, keyword: str, user_id: int = None) -> List[Tender]:
        """
        搜索招标公告

        Args:
            keyword: 搜索关键词
            user_id: 用户ID（可选，用于权限过滤）

        Returns:
            List[Tender]: 匹配的招标公告列表
        """
        queryset = self.model.objects.filter(
            models.Q(title__icontains=keyword) |
            models.Q(project_name__icontains=keyword) |
            models.Q(buyer_name__icontains=keyword)
        )

        if user_id:
            queryset = queryset.filter(created_by_id=user_id)

        return list(queryset)

    def get_pending(self, user_id: int = None) -> List[Tender]:
        """
        获取待处理的招标公告

        Args:
            user_id: 用户ID（可选）

        Returns:
            List[Tender]: 待处理的招标公告列表
        """
        queryset = self.model.objects.filter(status='pending')

        if user_id:
            queryset = queryset.filter(created_by_id=user_id)

        return list(queryset.order_by('-created_at'))

    def get_expired(self) -> List[Tender]:
        """
        获取已过期的招标公告

        Returns:
            List[Tender]: 已过期的招标公告列表
        """
        today = datetime.now().date()
        return list(
            self.model.objects.filter(deadline_date__lt=today)
            .exclude(status='expired')
        )

    def mark_as_processed(self, tender_id: int) -> Optional[Tender]:
        """
        标记招标公告为已处理

        Args:
            tender_id: 招标公告ID

        Returns:
            Optional[Tender]: 更新后的招标公告
        """
        return self.update(tender_id, status='processed')

    def get_by_industry(self, industry: str, limit: int = 50) -> List[Tender]:
        """
        获取指定行业的招标公告

        Args:
            industry: 行业名称
            limit: 返回数量限制

        Returns:
            List[Tender]: 招标公告列表
        """
        return list(
            self.model.objects.filter(industry=industry)
            .order_by('-publish_date')[:limit]
        )

    def get_by_region(self, province: str = None, city: str = None) -> List[Tender]:
        """
        获取指定地区的招标公告

        Args:
            province: 省份
            city: 城市

        Returns:
            List[Tender]: 招标公告列表
        """
        queryset = self.model.objects.all()

        if province:
            queryset = queryset.filter(province__icontains=province)
        if city:
            queryset = queryset.filter(city__icontains=city)

        return list(queryset.order_by('-publish_date'))


from django.db import models