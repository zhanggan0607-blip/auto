"""
自定义限流类
支持多种限流策略
安全改进：添加关键接口（登录、认证、通知）的独立限流策略
"""
import hashlib
import time
from rest_framework.throttling import UserRateThrottle, AnonRateThrottle
from django.core.cache import cache


class LoginRateThrottle(AnonRateThrottle):
    """
    登录限流器
    防止暴力破解登录
    """
    rate = '5/minute'
    scope = 'login'

    def get_cache_key(self, request, view):
        ident = self.get_ident(request)
        return f"throttle_login_{ident}"

    def allow_request(self, request, view):
        if hasattr(request, 'data') and request.data:
            username = request.data.get('username', '')
            if username:
                cache_key = f"throttle_login_user_{hashlib.md5(username.encode()).hexdigest()[:8]}"
                login_count = cache.get(cache_key, 0)
                if login_count >= 3:
                    self.rate = '1/minute'
        return super().allow_request(request, view)


class LoginSuccessThrottle(AnonRateThrottle):
    """
    登录成功计数
    跟踪登录成功次数用于安全监控
    """
    rate = '20/minute'
    scope = 'login_success'

    def get_cache_key(self, request, view):
        ident = self.get_ident(request)
        return f"throttle_login_success_{ident}"


class AuthRefreshThrottle(UserRateThrottle):
    """
    Token刷新限流器
    限制Token刷新频率
    """
    rate = '10/minute'
    scope = 'auth_refresh'


class WorkflowRateThrottle(UserRateThrottle):
    """
    工作流限流器
    限制工作流启动频率
    """
    rate = '30/minute'
    scope = 'workflow'

    def get_cache_key(self, request, view):
        if request.user and request.user.is_authenticated:
            ident = request.user.pk
        else:
            ident = self.get_ident(request)

        return self.cache_format % {
            'scope': self.scope,
            'ident': ident
        }


class UploadRateThrottle(UserRateThrottle):
    """
    上传限流器
    限制文件上传频率
    """
    rate = '10/minute'
    scope = 'upload'


class BurstRateThrottle(UserRateThrottle):
    """
    突发流量限流器
    """
    rate = '100/minute'
    scope = 'burst'


class IPRateThrottle(AnonRateThrottle):
    """
    IP限流器
    基于IP地址限流
    """
    rate = '300/hour'
    scope = 'ip'
    
    def get_cache_key(self, request, view):
        return f"throttle_ip_{self.get_ident(request)}"


class DynamicRateThrottle(UserRateThrottle):
    """
    动态限流器
    根据系统负载动态调整限流阈值
    """
    scope = 'dynamic'
    
    def get_rate(self):
        try:
            from django.core.cache import cache
            
            load = cache.get('system_load', 0)
            
            if load > 0.8:
                return '50/minute'
            elif load > 0.6:
                return '100/minute'
            else:
                return '200/minute'
        except Exception:
            return '100/minute'


class ConcurrentRequestThrottle:
    """
    并发请求限流器
    限制同时进行的请求数量
    """
    MAX_CONCURRENT = 100
    
    def __init__(self):
        self._current_requests = 0
    
    def acquire(self, request):
        key = f"concurrent_{self.get_ident(request)}"
        current = cache.get(key, 0)
        
        if current >= self.MAX_CONCURRENT:
            return False
        
        cache.incr(key)
        cache.expire(key, 60)
        return True
    
    def release(self, request):
        key = f"concurrent_{self.get_ident(request)}"
        current = cache.get(key, 0)
        if current > 0:
            cache.decr(key)
    
    def get_ident(self, request):
        xff = request.META.get('HTTP_X_FORWARDED_FOR')
        if xff:
            return xff.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', '0.0.0.0')


class SlidingWindowThrottle:
    """
    滑动窗口限流器
    更精确的限流控制
    """
    
    def __init__(self, max_requests: int, window_seconds: int):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
    
    def is_allowed(self, key: str) -> tuple:
        """
        检查是否允许请求
        
        Returns:
            tuple: (is_allowed, remaining_requests, reset_time)
        """
        now = time.time()
        window_start = now - self.window_seconds
        
        requests = cache.get(key, [])
        
        requests = [t for t in requests if t > window_start]
        
        if len(requests) >= self.max_requests:
            oldest = min(requests) if requests else now
            reset_time = int(oldest + self.window_seconds - now)
            return False, 0, reset_time
        
        requests.append(now)
        cache.set(key, requests, self.window_seconds + 10)
        
        remaining = self.max_requests - len(requests)
        return True, remaining, self.window_seconds


def sliding_window_rate_limit(key: str, max_requests: int, window_seconds: int) -> tuple:
    """
    滑动窗口限流辅助函数
    
    Args:
        key: 缓存键
        max_requests: 最大请求数
        window_seconds: 时间窗口(秒)
    
    Returns:
        tuple: (is_allowed, remaining, reset_time)
    """
    throttle = SlidingWindowThrottle(max_requests, window_seconds)
    return throttle.is_allowed(key)
