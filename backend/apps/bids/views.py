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
from utils.responses import APIResponse


class BidRecordListView(generics.ListCreateAPIView):
    """
    投标记录列表视图
    """
    permission_classes = [IsAuthenticated]

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

    def list(self, request, *args, **kwargs):
        """
        重写list方法，使用自定义响应格式
        """
        queryset = self.filter_queryset(self.get_queryset())
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            total_count = page.paginator.count if hasattr(page, 'paginator') else len(queryset)
            return APIResponse.success(data={
                'list': serializer.data,
                'pagination': {
                    'total': total_count,
                    'page': int(request.query_params.get('page', 1)),
                    'page_size': int(request.query_params.get('page_size', 20))
                }
            })
        
        serializer = self.get_serializer(queryset, many=True)
        return APIResponse.success(data={'list': serializer.data})

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


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
        return APIResponse.success(data=serializer.data)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return APIResponse.success(data=serializer.data, message='更新成功')

    def destroy(self, request, *args, **kwargs):
        """
        删除投标记录
        只有创建者或管理员可以删除
        """
        instance = self.get_object()
        
        if not (request.user.is_staff or instance.created_by == request.user):
            return APIResponse.error(
                message='无权限删除此记录',
                status_code=status.HTTP_403_FORBIDDEN
            )
        
        instance.delete()
        return APIResponse.success(message='删除成功')


class BidResultListView(generics.ListCreateAPIView):
    """
    中标结果列表视图
    """
    permission_classes = [IsAuthenticated]

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

    def list(self, request, *args, **kwargs):
        """
        重写list方法，使用自定义响应格式
        """
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return APIResponse.success(data={'list': serializer.data})


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
        return APIResponse.success(data=serializer.data)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return APIResponse.success(data=serializer.data, message='更新成功')


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
        
        return APIResponse.success(data=BidStatisticsSerializer(stats).data)

    def update_statistics(self, user, year):
        """
        更新统计数据
        """
        from apps.tenders.models import TenderProject
        
        bid_records = BidRecord.objects.filter(
            created_by=user,
            created_at__year=year
        )
        
        total_bids = bid_records.count()
        won_bids = bid_records.filter(status='won').count()
        lost_bids = bid_records.filter(status='lost').count()
        pending_bids = bid_records.filter(status__in=['preparing', 'submitted', 'reviewing']).count()
        
        total_bid_amount = bid_records.aggregate(
            total=Sum('bid_price')
        )['total'] or 0
        
        won_records = bid_records.filter(status='won')
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


class BidDashboardView(APIView):
    """
    投标仪表盘视图
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        获取仪表盘数据
        """
        user = request.user
        
        total_bids = BidRecord.objects.filter(created_by=user).count()
        won_bids = BidRecord.objects.filter(created_by=user, status='won').count()
        pending_bids = BidRecord.objects.filter(
            created_by=user, 
            status__in=['preparing', 'submitted', 'reviewing']
        ).count()
        
        win_rate = (won_bids / total_bids * 100) if total_bids > 0 else 0
        
        recent_bids = BidRecord.objects.filter(
            created_by=user
        ).order_by('-created_at')[:5]
        
        upcoming_deadlines = BidRecord.objects.filter(
            created_by=user,
            status='preparing',
            tender__deadline_date__gte=timezone.now().date()
        ).order_by('tender__deadline_date')[:5]
        
        return APIResponse.success(data={
            'summary': {
                'total_bids': total_bids,
                'won_bids': won_bids,
                'pending_bids': pending_bids,
                'win_rate': round(win_rate, 2)
            },
            'recent_bids': BidRecordListSerializer(recent_bids, many=True).data,
            'upcoming_deadlines': BidRecordListSerializer(upcoming_deadlines, many=True).data
        })
