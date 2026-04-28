"""
通知管理模块 - URL路由
"""
from django.urls import path
from .views import (
    NotificationListView, NotificationDetailView,
    NotificationMarkReadView, UnreadCountView,
    NotificationBatchDeleteView
)

app_name = 'notifications'

urlpatterns = [
    path('', NotificationListView.as_view(), name='notification_list'),
    path('batch-delete/', NotificationBatchDeleteView.as_view(), name='batch_delete'),
    path('mark-read/', NotificationMarkReadView.as_view(), name='mark_read'),
    path('unread-count/', UnreadCountView.as_view(), name='unread_count'),
    path('<int:pk>/', NotificationDetailView.as_view(), name='notification_detail'),
    path('<int:pk>/mark-read/', NotificationMarkReadView.as_view(), name='mark_single_read'),
]
