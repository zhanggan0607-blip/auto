"""
投标管理模块 - URL路由
"""
from django.urls import path
from .views import (
    BidRecordListView, BidRecordDetailView,
    BidResultListView, BidResultDetailView,
    BidStatisticsView,
)

app_name = 'bids'

urlpatterns = [
    path('records/', BidRecordListView.as_view(), name='record_list'),
    path('records/<int:pk>/', BidRecordDetailView.as_view(), name='record_detail'),

    path('results/', BidResultListView.as_view(), name='result_list'),
    path('results/<int:pk>/', BidResultDetailView.as_view(), name='result_detail'),

    path('statistics/', BidStatisticsView.as_view(), name='statistics'),
]
