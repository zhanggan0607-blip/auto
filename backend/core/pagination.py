"""
分页器模块
"""
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class StandardPagination(PageNumberPagination):
    """
    标准分页器
    """
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100
    
    def get_paginated_response(self, data):
        """
        返回统一格式的分页响应
        """
        return Response({
            'success': True,
            'code': 0,
            'message': '查询成功',
            'data': {
                'list': data,
                'pagination': {
                    'page': self.page.number,
                    'page_size': self.get_page_size(self.request),
                    'total': self.page.paginator.count,
                    'total_pages': self.page.paginator.num_pages
                }
            }
        })


class LargePagination(PageNumberPagination):
    """
    大数据量分页器
    """
    page_size = 50
    page_size_query_param = 'page_size'
    max_page_size = 200


class SmallPagination(PageNumberPagination):
    """
    小数据量分页器
    """
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 50
