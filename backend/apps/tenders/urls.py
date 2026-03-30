"""
招标项目模块 - URL路由
"""
from django.urls import path
from .views import (
    TenderProjectListView, TenderProjectDetailView,
    TenderProjectBatchView, TenderProjectFavoriteView, TenderProjectReadView,
    TenderKeywordListView, TenderKeywordDetailView,
    TenderStatisticsView, CrawlSyncView
)

app_name = 'tenders'

urlpatterns = [
    path('', TenderProjectListView.as_view(), name='project_list'),
    path('batch/', TenderProjectBatchView.as_view(), name='project_batch'),
    path('<int:pk>/', TenderProjectDetailView.as_view(), name='project_detail'),
    path('<int:pk>/favorite/', TenderProjectFavoriteView.as_view(), name='project_favorite'),
    path('<int:pk>/read/', TenderProjectReadView.as_view(), name='project_read'),
    
    path('keywords/', TenderKeywordListView.as_view(), name='keyword_list'),
    path('keywords/<int:pk>/', TenderKeywordDetailView.as_view(), name='keyword_detail'),
    
    path('statistics/', TenderStatisticsView.as_view(), name='statistics'),
    path('sync/', CrawlSyncView.as_view(), name='sync'),
]
