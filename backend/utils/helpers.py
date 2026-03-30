"""
工具函数
"""
import os
import uuid
import hashlib
import json
from functools import wraps
from datetime import datetime
from django.utils import timezone
from django.core.cache import cache


def cache_result(cache_key, timeout=300):
    """
    缓存函数结果的装饰器
    
    Args:
        cache_key: 缓存键名或生成函数
        timeout: 缓存超时时间（秒），默认5分钟
        
    Returns:
        装饰后的函数
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            key = cache_key if isinstance(cache_key, str) else cache_key(*args, **kwargs)
            result = cache.get(key)
            if result is not None:
                return result
            result = func(*args, **kwargs)
            cache.set(key, result, timeout)
            return result
        return wrapper
    return decorator


def cache_api_response(key_prefix, timeout=300, vary_on_user=False):
    """
    API响应缓存装饰器
    
    Args:
        key_prefix: 缓存键前缀
        timeout: 缓存超时时间（秒）
        vary_on_user: 是否按用户区分缓存
        
    Returns:
        装饰后的函数
    """
    def decorator(func):
        @wraps(func)
        def wrapper(self, request, *args, **kwargs):
            cache_key_parts = [key_prefix]
            
            if vary_on_user and request.user.is_authenticated:
                cache_key_parts.append(str(request.user.id))
            
            query_params = dict(request.query_params)
            if query_params:
                sorted_params = sorted(query_params.items())
                params_str = json.dumps(sorted_params, ensure_ascii=False)
                params_hash = hashlib.md5(params_str.encode()).hexdigest()[:8]
                cache_key_parts.append(params_hash)
            
            cache_key = ':'.join(cache_key_parts)
            
            cached_response = cache.get(cache_key)
            if cached_response is not None:
                from rest_framework.response import Response
                return Response(cached_response)
            
            response = func(self, request, *args, **kwargs)
            
            if hasattr(response, 'data') and response.status_code == 200:
                cache.set(cache_key, response.data, timeout)
            
            return response
        return wrapper
    return decorator


def invalidate_cache(key_pattern):
    """
    使缓存失效
    
    Args:
        key_pattern: 缓存键或模式
    """
    if '*' in key_pattern:
        cache.delete_many(cache.keys(key_pattern))
    else:
        cache.delete(key_pattern)


def generate_unique_filename(filename):
    """
    生成唯一文件名
    """
    ext = os.path.splitext(filename)[1]
    unique_name = f"{uuid.uuid4().hex}{ext}"
    return unique_name


def get_file_md5(file_path):
    """
    计算文件MD5值
    """
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def format_date(date_obj, format_str='%Y-%m-%d'):
    """
    格式化日期
    """
    if date_obj is None:
        return ''
    if isinstance(date_obj, str):
        return date_obj
    return date_obj.strftime(format_str)


def format_datetime(datetime_obj, format_str='%Y-%m-%d %H:%M:%S'):
    """
    格式化日期时间
    """
    if datetime_obj is None:
        return ''
    if isinstance(datetime_obj, str):
        return datetime_obj
    return datetime_obj.strftime(format_str)


def parse_date(date_str, format_str='%Y-%m-%d'):
    """
    解析日期字符串
    """
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str, format_str).date()
    except ValueError:
        return None


def ensure_directory(path):
    """
    确保目录存在
    """
    if not os.path.exists(path):
        os.makedirs(path, exist_ok=True)
    return path


def get_client_ip(request):
    """
    获取客户端IP地址
    
    Args:
        request: Django请求对象
        
    Returns:
        str: 客户端IP地址
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', '')
