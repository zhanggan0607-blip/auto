"""
OpenClaw Admin配置
"""
from django.contrib import admin
from .models import (
    LLMProvider, LLMModel, AgentModelConfig, LLMUsageLog
)


@admin.register(LLMProvider)
class LLMProviderAdmin(admin.ModelAdmin):
    list_display = ['name', 'provider_type', 'code', 'default_model', 'is_active', 'is_default']
    list_filter = ['provider_type', 'is_active', 'is_default']
    search_fields = ['name', 'code']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(LLMModel)
class LLMModelAdmin(admin.ModelAdmin):
    list_display = ['name', 'provider', 'model_type', 'model_id', 'is_active']
    list_filter = ['provider', 'model_type', 'is_active']
    search_fields = ['name', 'model_id']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(AgentModelConfig)
class AgentModelConfigAdmin(admin.ModelAdmin):
    list_display = ['agent_type', 'chat_model', 'reasoning_model', 'temperature', 'is_active']
    list_filter = ['agent_type', 'is_active']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(LLMUsageLog)
class LLMUsageLogAdmin(admin.ModelAdmin):
    list_display = ['provider', 'model', 'agent_type', 'total_tokens', 'cost', 'success', 'created_at']
    list_filter = ['provider', 'agent_type', 'success', 'created_at']
    search_fields = ['model', 'session_id']
    readonly_fields = ['created_at']
