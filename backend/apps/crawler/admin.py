"""
SAAS采集模块 - Admin配置
"""
from django.contrib import admin
from .models import (
    WebsiteTemplate, CrawlSession, CrawlResult, CrawlLog,
    FailureKnowledge, EnterpriseVectorIndex, BidProjectTracking
)
from .assurance_models import CrawlHealthCheck, CrawlOptimizationPlan, CrawlAssuranceReport


@admin.register(WebsiteTemplate)
class WebsiteTemplateAdmin(admin.ModelAdmin):
    """
    网站模板管理
    """
    list_display = ['name', 'code', 'website_type', 'base_url', 'is_active', 'priority', 'created_at']
    list_filter = ['website_type', 'is_active']
    search_fields = ['name', 'code', 'base_url']
    ordering = ['-priority', '-created_at']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('基本信息', {
            'fields': ('name', 'code', 'website_type', 'base_url', 'is_active', 'priority')
        }),
        ('URL配置', {
            'fields': ('list_url_pattern', 'search_url_pattern')
        }),
        ('选择器配置', {
            'fields': ('selectors', 'pagination_config')
        }),
        ('请求配置', {
            'fields': ('request_config',)
        }),
        ('登录配置', {
            'fields': ('requires_javascript', 'requires_login', 'login_config')
        }),
        ('其他信息', {
            'fields': ('created_by', 'created_at', 'updated_at')
        }),
    )


@admin.register(CrawlSession)
class CrawlSessionAdmin(admin.ModelAdmin):
    """
    采集会话管理
    """
    list_display = ['name', 'target_url', 'crawl_type', 'status', 'progress', 
                    'result_count', 'error_count', 'created_at']
    list_filter = ['status', 'crawl_type']
    search_fields = ['name', 'target_url']
    ordering = ['-created_at']
    readonly_fields = ['started_at', 'finished_at', 'duration', 'created_at', 'updated_at']
    
    fieldsets = (
        ('基本信息', {
            'fields': ('name', 'target_url', 'website_template', 'crawl_type')
        }),
        ('参数配置', {
            'fields': ('keywords', 'params')
        }),
        ('执行状态', {
            'fields': ('status', 'progress', 'total_pages', 'current_page')
        }),
        ('执行结果', {
            'fields': ('result_count', 'error_count', 'error_message')
        }),
        ('时间信息', {
            'fields': ('started_at', 'finished_at', 'duration')
        }),
        ('其他信息', {
            'fields': ('created_by', 'created_at', 'updated_at')
        }),
    )


@admin.register(CrawlResult)
class CrawlResultAdmin(admin.ModelAdmin):
    """
    采集结果管理
    """
    list_display = ['title', 'source_url', 'publish_date', 'region', 
                    'category', 'budget', 'status', 'created_at']
    list_filter = ['status', 'region', 'category', 'industry']
    search_fields = ['title', 'project_code', 'purchaser_name']
    ordering = ['-publish_date', '-created_at']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('基本信息', {
            'fields': ('session', 'title', 'source_url', 'detail_url')
        }),
        ('日期信息', {
            'fields': ('publish_date', 'deadline_date')
        }),
        ('分类信息', {
            'fields': ('region', 'category', 'industry')
        }),
        ('金额信息', {
            'fields': ('budget', 'project_code')
        }),
        ('采购人信息', {
            'fields': ('purchaser_name', 'purchaser_contact', 'purchaser_phone')
        }),
        ('代理机构信息', {
            'fields': ('agency_name', 'agency_contact', 'agency_phone')
        }),
        ('内容信息', {
            'fields': ('description', 'requirements')
        }),
        ('原始数据', {
            'fields': ('raw_data', 'extracted_fields')
        }),
        ('状态信息', {
            'fields': ('status', 'matched_companies')
        }),
        ('其他信息', {
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(CrawlLog)
class CrawlLogAdmin(admin.ModelAdmin):
    """
    采集日志管理
    """
    list_display = ['session', 'level', 'message', 'url', 'created_at']
    list_filter = ['level']
    search_fields = ['message', 'url']
    ordering = ['-created_at']
    readonly_fields = ['created_at']


@admin.register(FailureKnowledge)
class FailureKnowledgeAdmin(admin.ModelAdmin):
    """
    失败知识库管理
    """
    list_display = ['url', 'website', 'failure_type', 'resolution_status', 'retry_count', 'created_at']
    list_filter = ['failure_type', 'resolution_status', 'website']
    search_fields = ['url', 'error_message']
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'updated_at', 'resolved_at']
    
    fieldsets = (
        ('失败信息', {
            'fields': ('url', 'website', 'failure_type', 'error_message', 'error_stack')
        }),
        ('策略信息', {
            'fields': ('strategy_used', 'retry_count', 'proxy_used', 'fingerprint_used')
        }),
        ('解决信息', {
            'fields': ('resolution_status', 'resolution_method', 'resolution_notes', 'resolved_at', 'resolved_by')
        }),
        ('其他信息', {
            'fields': ('metadata', 'created_at', 'updated_at')
        }),
    )


@admin.register(EnterpriseVectorIndex)
class EnterpriseVectorIndexAdmin(admin.ModelAdmin):
    """
    企业向量索引管理
    """
    list_display = ['enterprise_id', 'enterprise_name', 'vector_status', 'last_indexed_at', 'index_version']
    list_filter = ['vector_status']
    search_fields = ['enterprise_name', 'enterprise_id']
    ordering = ['-updated_at']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(BidProjectTracking)
class BidProjectTrackingAdmin(admin.ModelAdmin):
    """
    已投标项目跟踪管理
    """
    list_display = ['tender_title', 'bid_date', 'tracking_status', 'winner_name', 'notification_sent', 'last_checked_at']
    list_filter = ['tracking_status', 'notification_sent', 'tender_source']
    search_fields = ['tender_title', 'tender_url', 'winner_name']
    ordering = ['-bid_date', '-created_at']
    readonly_fields = ['created_at', 'updated_at', 'last_checked_at', 'check_count']
    
    fieldsets = (
        ('项目信息', {
            'fields': ('tender_title', 'tender_url', 'tender_source')
        }),
        ('投标信息', {
            'fields': ('bid_date', 'bid_amount', 'bid_company')
        }),
        ('跟踪状态', {
            'fields': ('tracking_status', 'last_checked_at', 'check_count')
        }),
        ('结果信息', {
            'fields': ('result_announce_date', 'winner_name', 'winner_amount', 'our_rank')
        }),
        ('通知信息', {
            'fields': ('notification_sent', 'notification_sent_at')
        }),
        ('其他信息', {
            'fields': ('remarks', 'extra_data', 'created_by', 'created_at', 'updated_at')
        }),
    )


@admin.register(CrawlHealthCheck)
class CrawlHealthCheckAdmin(admin.ModelAdmin):
    list_display = ['target_url', 'network_connectivity', 'http_status', 'page_structure', 'anti_crawl', 'extraction_rules', 'overall_status', 'checked_at']
    list_filter = ['overall_status', 'network_connectivity', 'anti_crawl']
    search_fields = ['target_url']
    ordering = ['-checked_at']
    readonly_fields = ['checked_at']


@admin.register(CrawlOptimizationPlan)
class CrawlOptimizationPlanAdmin(admin.ModelAdmin):
    list_display = ['health_check', 'optimization_type', 'is_applied', 'apply_result', 'created_at']
    list_filter = ['optimization_type', 'is_applied', 'apply_result']
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'applied_at']


@admin.register(CrawlAssuranceReport)
class CrawlAssuranceReportAdmin(admin.ModelAdmin):
    list_display = ['target_url', 'status', 'attempt_count', 'max_attempts', 'data_collected', 'notification_sent', 'started_at']
    list_filter = ['status', 'notification_sent']
    search_fields = ['target_url', 'trigger_reason', 'final_result']
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'updated_at', 'started_at', 'finished_at']
