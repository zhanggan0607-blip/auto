"""
投标文档向量库 - Admin配置
"""
from django.contrib import admin
from .models import BidDocumentLibrary, DocumentSearchLog, AISearchTask


@admin.register(BidDocumentLibrary)
class BidDocumentLibraryAdmin(admin.ModelAdmin):
    list_display = ['title', 'document_type', 'source_type', 'vector_status', 'view_count', 'use_count', 'created_at']
    list_filter = ['document_type', 'source_type', 'vector_status', 'industry', 'is_verified', 'is_featured']
    search_fields = ['title', 'content_summary', 'keywords']
    readonly_fields = ['view_count', 'use_count', 'vector_id', 'created_at', 'updated_at']
    fieldsets = (
        ('基本信息', {
            'fields': ('title', 'document_type', 'source_type', 'file_path', 'file_size', 'file_format')
        }),
        ('内容信息', {
            'fields': ('content_text', 'content_summary', 'keywords')
        }),
        ('向量化信息', {
            'fields': ('vector_status', 'vector_id', 'vector_text')
        }),
        ('来源信息', {
            'fields': ('source_url', 'source_website', 'search_keyword')
        }),
        ('分类信息', {
            'fields': ('project_type', 'industry', 'region', 'tags')
        }),
        ('统计信息', {
            'fields': ('view_count', 'use_count', 'quality_score', 'is_verified', 'is_featured')
        }),
        ('元数据', {
            'fields': ('metadata', 'created_by', 'created_at', 'updated_at')
        }),
    )


@admin.register(DocumentSearchLog)
class DocumentSearchLogAdmin(admin.ModelAdmin):
    list_display = ['query_text', 'search_type', 'result_count', 'user', 'created_at']
    list_filter = ['search_type', 'created_at']
    search_fields = ['query_text']
    readonly_fields = ['created_at']


@admin.register(AISearchTask)
class AISearchTaskAdmin(admin.ModelAdmin):
    list_display = ['keyword', 'status', 'total_found', 'saved_count', 'created_by', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['keyword']
    readonly_fields = ['started_at', 'completed_at', 'created_at']
