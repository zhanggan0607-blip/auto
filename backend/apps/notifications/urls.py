"""
通知管理模块 - URL路由
"""
from django.urls import path
from .views import (
    NotificationListView, NotificationDetailView,
    NotificationMarkReadView, UnreadCountView
)

app_name = 'notifications'

urlpatterns = [
    path('', NotificationListView.as_view(), name='notification_list'),
    path('<int:pk>/', NotificationDetailView.as_view(), name='notification_detail'),
    path('mark-read/', NotificationMarkReadView.as_view(), name='mark_read'),
    path('<int:pk>/mark-read/', NotificationMarkReadView.as_view(), name='mark_single_read'),
    path('unread-count/', UnreadCountView.as_view(), name='unread_count'),
]
