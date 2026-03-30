from django.contrib import admin
from .models import DocumentTemplate, GeneratedDocument


@admin.register(DocumentTemplate)
class DocumentTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'template_type', 'is_active', 'created_by', 'created_at']
    list_filter = ['template_type', 'is_active']
    search_fields = ['name', 'description']


@admin.register(GeneratedDocument)
class GeneratedDocumentAdmin(admin.ModelAdmin):
    list_display = ['name', 'template', 'tender', 'status', 'version', 'created_by', 'created_at']
    list_filter = ['status', 'template']
    search_fields = ['name', 'tender__title']
