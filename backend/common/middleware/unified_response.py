"""
统一API响应中间件
确保所有API返回统一格式

响应格式：
{
    "success": true/false,
    "code": 0,
    "message": "消息",
    "data": {...},
    "meta": {...},
    "timestamp": "2026-04-05T12:00:00+08:00"
}

分页格式：
{
    "success": true,
    "code": 0,
    "message": "查询成功",
    "data": [...],
    "meta": {
        "pagination": {
            "page": 1,
            "page_size": 20,
            "total": 100,
            "total_pages": 5,
            "has_next": true,
            "has_prev": false
        }
    },
    "timestamp": "..."
}
"""
import json
import logging

from django.http import HttpRequest, HttpResponse
from django.utils.deprecation import MiddlewareMixin
from django.utils.timezone import now

logger = logging.getLogger(__name__)


class UnifiedResponseMiddleware(MiddlewareMixin):
    """
    统一API响应格式中间件

    自动将所有JSON响应转换为统一格式：
    {
        "success": true/false,
        "code": 0,
        "message": "消息",
        "data": {...},
        "meta": {...},
        "timestamp": "..."
    }
    """

    EXEMPT_PATHS = [
        '/api/v1/auth/token/refresh/',
        '/admin/',
        '/static/',
        '/media/',
    ]

    def process_response(self, request: HttpRequest, response: HttpResponse) -> HttpResponse:
        if request.path.startswith('/api/'):
            if self._is_exempt(request.path):
                return response

            content_type = response.get('Content-Type', '')
            if content_type and 'application/json' in content_type:
                try:
                    content = response.content.decode('utf-8')
                    if content:
                        data = json.loads(content)
                        unified = self._transform_response(response, data)
                        response.content = json.dumps(unified, ensure_ascii=False)
                except (json.JSONDecodeError, UnicodeDecodeError) as e:
                    logger.warning(f"响应转换失败: {e}")
                except Exception as e:
                    logger.error(f"中间件处理异常: {e}")

        return response

    def _is_exempt(self, path: str) -> bool:
        for exempt in self.EXEMPT_PATHS:
            if path.startswith(exempt):
                return True
        return False

    def _transform_response(self, response: HttpResponse, data) -> dict:
        status_code = response.status_code

        if 200 <= status_code < 300:
            return self._success_response(data, status_code)
        else:
            return self._error_response(data, status_code)

    def _success_response(self, data, status_code: int) -> dict:
        timestamp = now().isoformat()

        if data is None:
            return {
                'success': True,
                'code': 0,
                'message': '操作成功',
                'data': None,
                'timestamp': timestamp
            }

        if isinstance(data, dict):
            if 'code' in data and 'message' in data and 'data' in data:
                result = {
                    'success': data.get('success', data.get('code', 0) == 0),
                    'code': data.get('code', 0),
                    'message': data.get('message', '操作成功'),
                    'timestamp': timestamp
                }

                inner_data = data.get('data')

                if isinstance(inner_data, dict) and 'list' in inner_data and 'pagination' in inner_data:
                    result['data'] = inner_data['list']
                    pagination = inner_data['pagination']
                    total_pages = pagination.get('total_pages', 1)
                    page = pagination.get('page', 1)
                    result['meta'] = {
                        'pagination': {
                            'total': pagination.get('total', 0),
                            'page': page,
                            'page_size': pagination.get('page_size', 20),
                            'total_pages': total_pages,
                            'has_next': page < total_pages,
                            'has_prev': page > 1
                        }
                    }
                else:
                    result['data'] = inner_data
                    if data.get('meta'):
                        result['meta'] = data['meta']

                return result

            if 'results' in data and 'count' in data:
                total = data.get('count', 0)
                page = data.get('page', 1)
                page_size = data.get('page_size', 20)
                total_pages = data.get('total_pages', (total + page_size - 1) // page_size if page_size > 0 else 1)
                return {
                    'success': True,
                    'code': 0,
                    'message': '查询成功',
                    'data': data.get('results'),
                    'meta': {
                        'pagination': {
                            'total': total,
                            'page': page,
                            'page_size': page_size,
                            'total_pages': total_pages,
                            'has_next': page < total_pages,
                            'has_prev': page > 1
                        }
                    },
                    'timestamp': timestamp
                }

            return {
                'success': True,
                'code': 0,
                'message': '操作成功',
                'data': data,
                'timestamp': timestamp
            }

        return {
            'success': True,
            'code': 0,
            'message': '操作成功',
            'data': data,
            'timestamp': timestamp
        }

    def _error_response(self, data, status_code: int) -> dict:
        timestamp = now().isoformat()
        message = '请求失败'

        if isinstance(data, dict):
            if 'success' in data and data['success'] is False:
                return {
                    'success': False,
                    'code': data.get('code', status_code),
                    'message': data.get('message', message),
                    'data': data.get('data'),
                    'timestamp': timestamp
                }

            message = (
                data.get('message') or
                data.get('detail') or
                data.get('error') or
                '请求失败'
            )

        return {
            'success': False,
            'code': status_code,
            'message': message,
            'data': None,
            'timestamp': timestamp
        }
