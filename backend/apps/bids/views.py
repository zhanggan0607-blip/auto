"""
投标管理模块 - 视图
"""
from rest_framework import status, generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.db.models import Sum, Count, Q

from .models import BidRecord, BidResult, BidStatistics
from .serializers import (
    BidRecordListSerializer, BidRecordDetailSerializer,
    BidRecordCreateSerializer, BidRecordUpdateSerializer,
    BidResultSerializer, BidResultCreateSerializer,
    BidStatisticsSerializer
)
from utils.responses import UnifiedResponse
from core.pagination import StandardPagination


class BidRecordListView(generics.ListCreateAPIView):
    """
    投标记录列表视图
    """
    permission_classes = [IsAuthenticated]
    serializer_class = BidRecordListSerializer
    pagination_class = StandardPagination

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return BidRecordCreateSerializer
        return BidRecordListSerializer

    def get_queryset(self):
        queryset = BidRecord.objects.select_related('tender', 'bid_manager', 'created_by')

        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        tender_id = self.request.query_params.get('tender_id')
        if tender_id:
            queryset = queryset.filter(tender_id=tender_id)

        bid_manager_id = self.request.query_params.get('bid_manager_id')
        if bid_manager_id:
            queryset = queryset.filter(bid_manager_id=bid_manager_id)

        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        if start_date:
            queryset = queryset.filter(bid_date__gte=start_date)
        if end_date:
            queryset = queryset.filter(bid_date__lte=end_date)

        return queryset.order_by('-created_at')

    def perform_create(self, serializer):
        tender = serializer.validated_data.get('tender')
        if tender and BidRecord.objects.filter(tender=tender).exists():
            from rest_framework.exceptions import ValidationError
            raise ValidationError({'tender': '该招标项目已存在投标记录'})
        bid = serializer.save(created_by=self.request.user)


class BidRecordDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    投标记录详情视图
    """
    queryset = BidRecord.objects.select_related('tender', 'bid_manager').prefetch_related('team_members', 'bid_documents')
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return BidRecordUpdateSerializer
        return BidRecordDetailSerializer

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return UnifiedResponse.success(data=serializer.data)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return UnifiedResponse.success(data=serializer.data, message='更新成功')

    def destroy(self, request, *args, **kwargs):
        """
        删除投标记录
        只有创建者或管理员可以删除
        """
        instance = self.get_object()
        
        if not (request.user.is_staff or instance.created_by == request.user):
            return UnifiedResponse.error(
                message='无权限删除此记录',
                status_code=status.HTTP_403_FORBIDDEN
            )
        
        instance.delete()
        return UnifiedResponse.success(message='删除成功')


class BidResultListView(generics.ListCreateAPIView):
    """
    中标结果列表视图
    """
    permission_classes = [IsAuthenticated]
    serializer_class = BidResultSerializer
    pagination_class = StandardPagination

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return BidResultCreateSerializer
        return BidResultSerializer

    def get_queryset(self):
        queryset = BidResult.objects.select_related('bid_record__tender')

        result_type = self.request.query_params.get('result_type')
        if result_type:
            queryset = queryset.filter(result_type=result_type)

        return queryset.order_by('-created_at')


class BidResultDetailView(generics.RetrieveUpdateAPIView):
    """
    中标结果详情视图
    """
    queryset = BidResult.objects.select_related('bid_record__tender')
    serializer_class = BidResultSerializer
    permission_classes = [IsAuthenticated]

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return UnifiedResponse.success(data=serializer.data)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return UnifiedResponse.success(data=serializer.data, message='更新成功')


class BidStatisticsView(APIView):
    """
    投标统计视图
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        获取投标统计数据
        """
        user = request.user
        year = request.query_params.get('year', timezone.now().year)
        
        stats, _ = BidStatistics.objects.get_or_create(
            user=user,
            year=year,
            month=None
        )
        
        self.update_statistics(user, year)
        
        return UnifiedResponse.success(data=BidStatisticsSerializer(stats).data)

    def update_statistics(self, user, year):
        from services.data import BidRepository
        repo = BidRepository()
        stats_data = repo.get_statistics(user.id)
        
        total_bids = stats_data['total']
        won_bids = stats_data['won']
        lost_bids = stats_data['lost']
        pending_bids = stats_data['pending']
        total_bid_amount = stats_data['total_amount']
        
        won_records = BidRecord.objects.filter(created_by=user, status='won', created_at__year=year)
        total_win_amount = won_records.aggregate(
            total=Sum('bid_price')
        )['total'] or 0
        
        stats, _ = BidStatistics.objects.update_or_create(
            user=user,
            year=year,
            month=None,
            defaults={
                'total_bids': total_bids,
                'won_bids': won_bids,
                'lost_bids': lost_bids,
                'pending_bids': pending_bids,
                'total_bid_amount': total_bid_amount,
                'total_win_amount': total_win_amount,
            }
        )
        
        stats.calculate_win_rate()
        stats.save()
