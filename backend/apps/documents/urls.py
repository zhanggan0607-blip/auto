"""
文档管理模块 - URL路由
"""
from django.urls import path
from .views import (
    DocumentTemplateListView, DocumentTemplateDetailView,
    GeneratedDocumentListView, GeneratedDocumentDetailView,
    DocumentGenerateView, DocumentReviewView,
    ReferenceDocsView, AISuggestionView, SearchReferenceDocsView
)

app_name = 'documents'

urlpatterns = [
    path('templates/', DocumentTemplateListView.as_view(), name='template_list'),
    path('templates/<int:pk>/', DocumentTemplateDetailView.as_view(), name='template_detail'),
    
    path('generated/', GeneratedDocumentListView.as_view(), name='generated_list'),
    path('generated/<int:pk>/', GeneratedDocumentDetailView.as_view(), name='generated_detail'),
    path('generate/', DocumentGenerateView.as_view(), name='generate'),
    path('generated/<int:pk>/review/', DocumentReviewView.as_view(), name='review'),
    
    path('generated/<int:pk>/reference-docs/', ReferenceDocsView.as_view(), name='reference_docs'),
    path('generated/<int:pk>/ai-suggestion/', AISuggestionView.as_view(), name='ai_suggestion'),
    path('search-reference-docs/', SearchReferenceDocsView.as_view(), name='search_reference_docs'),
]
