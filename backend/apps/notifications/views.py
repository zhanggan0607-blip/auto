"""
通知管理模块 - 视图
"""
from rest_framework import status, generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.db.models import Count

from .models import NotificationChannel, Notification, NotificationTemplate, NotificationLog
from .serializers import (
    NotificationChannelSerializer, NotificationSerializer,
    NotificationCreateSerializer, NotificationTemplateSerializer,
    NotificationLogSerializer, NotificationStatsSerializer
)
from utils.responses import APIResponse


class NotificationChannelListView(generics.ListCreateAPIView):
    """
    通知渠道列表视图
    """
    serializer_class = NotificationChannelSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return NotificationChannel.objects.filter(user=self.request.user)

    def list(self, request, *args, **kwargs):
        """
        重写list方法，使用自定义响应格式
        """
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return APIResponse.success(data=serializer.data)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class NotificationChannelDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    通知渠道详情视图
    """
    serializer_class = NotificationChannelSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return NotificationChannel.objects.filter(user=self.request.user)


class NotificationListView(generics.ListAPIView):
    """
    通知消息列表视图
    """
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = Notification.objects.filter(recipient=self.request.user)
        
        is_read = self.request.query_params.get('is_read')
        if is_read is not None:
            queryset = queryset.filter(is_read=is_read.lower() == 'true')
        
        notification_type = self.request.query_params.get('notification_type')
        if notification_type:
            queryset = queryset.filter(notification_type=notification_type)
        
        priority = self.request.query_params.get('priority')
        if priority:
            queryset = queryset.filter(priority=priority)
        
        return queryset.order_by('-created_at')

    def list(self, request, *args, **kwargs):
        """
        重写list方法，使用自定义响应格式
        """
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return APIResponse.success(data={'list': serializer.data})


class NotificationDetailView(generics.RetrieveAPIView):
    """
    通知消息详情视图
    """
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(recipient=self.request.user)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.mark_as_read()
        serializer = self.get_serializer(instance)
        return APIResponse.success(data=serializer.data)


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
                return APIResponse.success(message='已标记为已读')
            except Notification.DoesNotExist:
                return APIResponse.error(message='通知不存在', status_code=status.HTTP_404_NOT_FOUND)
        else:
            Notification.objects.filter(recipient=request.user, is_read=False).update(
                is_read=True,
                read_at=timezone.now()
            )
            return APIResponse.success(message='全部已标记为已读')


class NotificationSendView(APIView):
    """
    发送通知视图
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """
        发送通知
        """
        serializer = NotificationCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        recipient_ids = serializer.validated_data.get('recipient_ids')
        title = serializer.validated_data.get('title')
        content = serializer.validated_data.get('content')
        notification_type = serializer.validated_data.get('notification_type', 'system')
        priority = serializer.validated_data.get('priority', 'normal')
        related_object_type = serializer.validated_data.get('related_object_type')
        related_object_id = serializer.validated_data.get('related_object_id')
        send_immediately = serializer.validated_data.get('send_immediately', True)
        channels = serializer.validated_data.get('channels', [])

        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        recipients = User.objects.filter(id__in=recipient_ids)
        if not recipients.exists():
            return APIResponse.error(message='未找到有效的接收人')

        notifications = []
        for recipient in recipients:
            notification = Notification.objects.create(
                title=title,
                content=content,
                notification_type=notification_type,
                priority=priority,
                related_object_type=related_object_type,
                related_object_id=related_object_id,
                recipient=recipient
            )
            notifications.append(notification)

        if send_immediately:
            from services.notification_service import NotificationService
            service = NotificationService()
            for notification in notifications:
                service.send_notification(notification, channels)

        return APIResponse.success(
            data={'sent_count': len(notifications)},
            message=f'已创建 {len(notifications)} 条通知'
        )


class NotificationTemplateListView(generics.ListCreateAPIView):
    """
    通知模板列表视图
    """
    queryset = NotificationTemplate.objects.filter(is_active=True)
    serializer_class = NotificationTemplateSerializer
    permission_classes = [IsAuthenticated]


class NotificationTemplateDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    通知模板详情视图
    """
    queryset = NotificationTemplate.objects.all()
    serializer_class = NotificationTemplateSerializer
    permission_classes = [IsAuthenticated]


class NotificationLogListView(generics.ListAPIView):
    """
    通知日志列表视图
    """
    serializer_class = NotificationLogSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = NotificationLog.objects.select_related('notification', 'channel')
        
        notification_id = self.request.query_params.get('notification_id')
        if notification_id:
            queryset = queryset.filter(notification_id=notification_id)
        
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        return queryset.order_by('-created_at')


class NotificationStatsView(APIView):
    """
    通知统计视图
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        获取通知统计数据
        """
        user = request.user
        notifications = Notification.objects.filter(recipient=user)
        
        total = notifications.count()
        unread = notifications.filter(is_read=False).count()
        
        by_type = notifications.values('notification_type').annotate(count=Count('id'))
        by_type_dict = {item['notification_type']: item['count'] for item in by_type}
        
        by_priority = notifications.values('priority').annotate(count=Count('id'))
        by_priority_dict = {item['priority']: item['count'] for item in by_priority}
        
        return APIResponse.success(data={
            'total': total,
            'unread': unread,
            'by_type': by_type_dict,
            'by_priority': by_priority_dict
        })


class UnreadCountView(APIView):
    """
    未读消息数量视图
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        获取未读消息数量
        """
        count = Notification.objects.filter(
            recipient=request.user,
            is_read=False
        ).count()
        return APIResponse.success(data={'unread_count': count})
