"""
通知管理模块 - 视图
"""
from rest_framework import status, generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.db.models import Count
from datetime import datetime

from .models import NotificationChannel, Notification, NotificationTemplate, NotificationLog
from .serializers import (
    NotificationChannelSerializer, NotificationSerializer,
    NotificationCreateSerializer, NotificationTemplateSerializer,
    NotificationLogSerializer, NotificationStatsSerializer
)
from utils.responses import UnifiedResponse

class NotificationListView(generics.ListAPIView):
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['is_read', 'notification_type', 'priority']

    def get_queryset(self):
        return Notification.objects.filter(recipient=self.request.user).order_by('-created_at')


class NotificationDetailView(generics.RetrieveDestroyAPIView):
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(recipient=self.request.user)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.mark_as_read()
        serializer = self.get_serializer(instance)
        return UnifiedResponse.success(data=serializer.data)

    def destroy(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            instance.delete()
            return UnifiedResponse.success(message='通知已删除')
        except Exception as e:
            return UnifiedResponse.error(message=str(e), status_code=status.HTTP_400_BAD_REQUEST)


class NotificationMarkReadView(APIView):
    """
    标记通知已读视图
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, pk=None):
        """
        标记单条或全部已读
        """
        if pk:
            try:
                notification = Notification.objects.get(pk=pk, recipient=request.user)
                notification.mark_as_read()
                return UnifiedResponse.success(message='已标记为已读')
            except Notification.DoesNotExist:
                return UnifiedResponse.error(message='通知不存在', status_code=status.HTTP_404_NOT_FOUND)
        else:
            Notification.objects.filter(recipient=request.user, is_read=False).update(
                is_read=True,
                read_at=timezone.now()
            )
            return UnifiedResponse.success(message='全部已标记为已读')

class UnreadCountView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        count = Notification.objects.filter(
            recipient=request.user,
            is_read=False
        ).count()
        return UnifiedResponse.success(data={'unread_count': count})


class NotificationBatchDeleteView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        ids = request.data.get('ids', [])
        delete_read = request.data.get('delete_read', False)
        date_from = request.data.get('date_from')
        date_to = request.data.get('date_to')
        notification_type = request.data.get('notification_type')

        queryset = Notification.objects.filter(recipient=request.user)
        deleted_count = 0

        if ids and isinstance(ids, list):
            ids = [int(i) for i in ids if str(i).isdigit()]
            result = queryset.filter(id__in=ids).delete()
            deleted_count = result[0] if result else 0
        else:
            if delete_read:
                queryset = queryset.filter(is_read=True)

            if notification_type:
                queryset = queryset.filter(notification_type=notification_type)

            if date_from:
                try:
                    dt_from = datetime.strptime(date_from, '%Y-%m-%d')
                    queryset = queryset.filter(created_at__date__gte=dt_from.date())
                except (ValueError, TypeError):
                    pass

            if date_to:
                try:
                    dt_to = datetime.strptime(date_to, '%Y-%m-%d')
                    queryset = queryset.filter(created_at__date__lte=dt_to.date())
                except (ValueError, TypeError):
                    pass

            if delete_read or notification_type or date_from or date_to:
                result = queryset.delete()
                deleted_count = result[0] if result else 0

        if deleted_count > 0:
            return UnifiedResponse.success(
                message=f'成功删除 {deleted_count} 条通知',
                data={'deleted_count': deleted_count}
            )
        return UnifiedResponse.error(message='未删除任何通知，请检查删除条件', status_code=status.HTTP_400_BAD_REQUEST)
