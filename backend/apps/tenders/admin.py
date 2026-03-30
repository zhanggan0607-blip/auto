from django.contrib import admin
from .models import TenderSource, TenderProject, TenderFile, TenderKeyword, CrawlerTask


@admin.register(TenderSource)
class TenderSourceAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'source_type', 'base_url', 'is_active', 'created_at']
    list_filter = ['source_type', 'is_active']
    search_fields = ['name', 'code']


@admin.register(TenderProject)
class TenderProjectAdmin(admin.ModelAdmin):
    list_display = ['title', 'project_code', 'source', 'publish_date', 'region', 'status', 'is_favorite']
    list_filter = ['status', 'source', 'region', 'industry']
    search_fields = ['title', 'project_code', 'purchaser_name']
    date_hierarchy = 'publish_date'


@admin.register(TenderFile)
class TenderFileAdmin(admin.ModelAdmin):
    list_display = ['tender', 'file_type', 'file_name', 'file_size', 'is_downloaded', 'created_at']
    list_filter = ['file_type', 'is_downloaded']
    search_fields = ['file_name', 'tender__title']


@admin.register(TenderKeyword)
class TenderKeywordAdmin(admin.ModelAdmin):
    list_display = ['keyword', 'category', 'weight', 'is_active', 'created_at']
    list_filter = ['category', 'is_active']
    search_fields = ['keyword']


@admin.register(CrawlerTask)
class CrawlerTaskAdmin(admin.ModelAdmin):
    list_display = ['name', 'source', 'task_type', 'status', 'result_count', 'created_at']
    list_filter = ['status', 'source']
    search_fields = ['name']
