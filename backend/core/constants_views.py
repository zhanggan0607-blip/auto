"""
状态常量API视图
提供前端获取后端状态常量的接口
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.core.cache import cache

from core.constants import (
    TENDER_STATUS_CHOICES,
    BID_STATUS_CHOICES,
    RESULT_TYPE_CHOICES,
    CRAWLER_STATUS_CHOICES,
    SCHEDULE_STATUS_CHOICES,
    DOCUMENT_STATUS_CHOICES,
    NOTIFICATION_STATUS_CHOICES,
    NOTIFICATION_TYPE_CHOICES,
    VECTOR_STATUS_CHOICES,
    ENTERPRISE_DOC_STATUS_CHOICES,
    ENTERPRISE_DOC_TYPE_CHOICES,
    ENTERPRISE_TYPE_CHOICES,
    BUILDER_LEVEL_CHOICES,
    BUILDER_MAJOR_CHOICES,
    QUALIFICATION_LEVEL_CHOICES,
    QUALIFICATION_TYPE_CHOICES,
    PERFORMANCE_TYPE_CHOICES,
    MATCH_RULE_TYPE_CHOICES,
    CONTACT_TYPE_CHOICES,
    PRIORITY_CHOICES,
    CHANNEL_TYPE_CHOICES,
    CRAWL_SESSION_STATUS_CHOICES,
    CRAWL_RESULT_STATUS_CHOICES,
    FAILURE_TYPE_CHOICES,
    RESOLUTION_STATUS_CHOICES,
    TRACKING_STATUS_CHOICES,
    LOG_LEVEL_CHOICES,
)

CONSTANTS_CACHE_KEY = 'system_constants_all'
CONSTANTS_CACHE_TIMEOUT = 3600


class ConstantsAPIView(APIView):
    """
    状态常量API
    返回系统中所有状态常量和选项
    """
    permission_classes = [AllowAny]
    
    def get(self, request):
        """
        获取所有状态常量
        """
        cached_data = cache.get(CONSTANTS_CACHE_KEY)
        if cached_data is not None:
            return Response({
                'code': 0,
                'message': 'success',
                'data': cached_data
            })
        
        constants = {
            'tender_status': self._format_choices(TENDER_STATUS_CHOICES),
            'bid_status': self._format_choices(BID_STATUS_CHOICES),
            'result_type': self._format_choices(RESULT_TYPE_CHOICES),
            'crawler_status': self._format_choices(CRAWLER_STATUS_CHOICES),
            'schedule_status': self._format_choices(SCHEDULE_STATUS_CHOICES),
            'document_status': self._format_choices(DOCUMENT_STATUS_CHOICES),
            'notification_status': self._format_choices(NOTIFICATION_STATUS_CHOICES),
            'notification_type': self._format_choices(NOTIFICATION_TYPE_CHOICES),
            'vector_status': self._format_choices(VECTOR_STATUS_CHOICES),
            'enterprise_doc_status': self._format_choices(ENTERPRISE_DOC_STATUS_CHOICES),
            'enterprise_doc_type': self._format_choices(ENTERPRISE_DOC_TYPE_CHOICES),
            'enterprise_type': self._format_choices(ENTERPRISE_TYPE_CHOICES),
            'builder_level': self._format_choices(BUILDER_LEVEL_CHOICES),
            'builder_major': self._format_choices(BUILDER_MAJOR_CHOICES),
            'qualification_level': self._format_choices(QUALIFICATION_LEVEL_CHOICES),
            'qualification_type': self._format_choices(QUALIFICATION_TYPE_CHOICES),
            'performance_type': self._format_choices(PERFORMANCE_TYPE_CHOICES),
            'match_rule_type': self._format_choices(MATCH_RULE_TYPE_CHOICES),
            'contact_type': self._format_choices(CONTACT_TYPE_CHOICES),
            'priority': self._format_choices(PRIORITY_CHOICES),
            'channel_type': self._format_choices(CHANNEL_TYPE_CHOICES),
            'crawl_session_status': self._format_choices(CRAWL_SESSION_STATUS_CHOICES),
            'crawl_result_status': self._format_choices(CRAWL_RESULT_STATUS_CHOICES),
            'failure_type': self._format_choices(FAILURE_TYPE_CHOICES),
            'resolution_status': self._format_choices(RESOLUTION_STATUS_CHOICES),
            'tracking_status': self._format_choices(TRACKING_STATUS_CHOICES),
            'log_level': self._format_choices(LOG_LEVEL_CHOICES),
        }
        
        cache.set(CONSTANTS_CACHE_KEY, constants, CONSTANTS_CACHE_TIMEOUT)
        
        return Response({
            'code': 0,
            'message': 'success',
            'data': constants
        })
    
    def _format_choices(self, choices):
        """
        格式化choices为前端友好的格式
        """
        return [
            {'value': value, 'label': label}
            for value, label in choices
        ]


class ConstantsDetailAPIView(APIView):
    """
    单个状态常量API
    返回指定类型的状态常量
    """
    permission_classes = [AllowAny]
    
    CHOICES_MAP = {
        'tender_status': TENDER_STATUS_CHOICES,
        'bid_status': BID_STATUS_CHOICES,
        'result_type': RESULT_TYPE_CHOICES,
        'crawler_status': CRAWLER_STATUS_CHOICES,
        'schedule_status': SCHEDULE_STATUS_CHOICES,
        'document_status': DOCUMENT_STATUS_CHOICES,
        'notification_status': NOTIFICATION_STATUS_CHOICES,
        'notification_type': NOTIFICATION_TYPE_CHOICES,
        'vector_status': VECTOR_STATUS_CHOICES,
        'enterprise_doc_status': ENTERPRISE_DOC_STATUS_CHOICES,
        'enterprise_doc_type': ENTERPRISE_DOC_TYPE_CHOICES,
        'enterprise_type': ENTERPRISE_TYPE_CHOICES,
        'builder_level': BUILDER_LEVEL_CHOICES,
        'builder_major': BUILDER_MAJOR_CHOICES,
        'qualification_level': QUALIFICATION_LEVEL_CHOICES,
        'qualification_type': QUALIFICATION_TYPE_CHOICES,
        'performance_type': PERFORMANCE_TYPE_CHOICES,
        'match_rule_type': MATCH_RULE_TYPE_CHOICES,
        'contact_type': CONTACT_TYPE_CHOICES,
        'priority': PRIORITY_CHOICES,
        'channel_type': CHANNEL_TYPE_CHOICES,
        'crawl_session_status': CRAWL_SESSION_STATUS_CHOICES,
        'crawl_result_status': CRAWL_RESULT_STATUS_CHOICES,
        'failure_type': FAILURE_TYPE_CHOICES,
        'resolution_status': RESOLUTION_STATUS_CHOICES,
        'tracking_status': TRACKING_STATUS_CHOICES,
        'log_level': LOG_LEVEL_CHOICES,
    }
    
    def get(self, request, constant_type):
        """
        获取指定类型的状态常量
        """
        choices = self.CHOICES_MAP.get(constant_type)
        
        if not choices:
            return Response({
                'code': 404,
                'message': f'常量类型 {constant_type} 不存在',
                'data': None
            }, status=404)
        
        formatted = [
            {'value': value, 'label': label}
            for value, label in choices
        ]
        
        return Response({
            'code': 0,
            'message': 'success',
            'data': formatted
        })
