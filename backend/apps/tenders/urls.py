"""
招标项目模块 - URL路由
"""
from django.urls import path
from .views import (
    TenderSourceListView,
    TenderProjectListView, TenderProjectDetailView,
    TenderProjectBatchView, TenderProjectFavoriteView,
    TenderSourceContentView,
    TenderKeywordListView, TenderKeywordDetailView,
    TenderStatisticsView, TenderTrendView,
    CrawlSyncView, CrawlDataStatisticsView, CrawlDataExportView,
)

app_name = 'tenders'

urlpatterns = [
    path('', TenderProjectListView.as_view(), name='project_list'),
    path('sources/', TenderSourceListView.as_view(), name='source_list'),
    path('batch/', TenderProjectBatchView.as_view(), name='project_batch'),
    path('<int:pk>/', TenderProjectDetailView.as_view(), name='project_detail'),
    path('<int:pk>/favorite/', TenderProjectFavoriteView.as_view(), name='project_favorite'),
    path('<int:pk>/source-content/', TenderSourceContentView.as_view(), name='source_content'),

    path('keywords/', TenderKeywordListView.as_view(), name='keyword_list'),
    path('keywords/<int:pk>/', TenderKeywordDetailView.as_view(), name='keyword_detail'),

    path('statistics/', TenderStatisticsView.as_view(), name='statistics'),
    path('trend/', TenderTrendView.as_view(), name='trend'),
    path('crawl-sync/', CrawlSyncView.as_view(), name='crawl_sync'),
    path('crawl-statistics/', CrawlDataStatisticsView.as_view(), name='crawl_statistics'),
    path('crawl-export/', CrawlDataExportView.as_view(), name='crawl_export'),
]
