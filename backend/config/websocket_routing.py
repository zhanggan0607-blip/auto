"""
WebSocket 路由配置
"""
from django.urls import re_path

from core.consumers import (
    CrawlerProgressConsumer,
    NotificationConsumer,
    BidResultConsumer
)

websocket_urlpatterns = [
    re_path(
        r'ws/crawler/progress/(?P<task_id>[\w-]+)/$',
        CrawlerProgressConsumer.as_asgi()
    ),
    re_path(
        r'ws/notifications/(?P<user_id>\d+)/$',
        NotificationConsumer.as_asgi()
    ),
    re_path(
        r'ws/bid-results/$',
        BidResultConsumer.as_asgi()
    ),
]
