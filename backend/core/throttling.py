"""
自定义限流类
"""
import hashlib
import logging
import time
from rest_framework.throttling import AnonRateThrottle
from django.core.cache import cache

logger = logging.getLogger(__name__)


class LoginRateThrottle(AnonRateThrottle):
    rate = '30/minute'
    scope = 'login'

    def get_cache_key(self, request, view):
        ident = self.get_ident(request)
        return f"throttle_login_{ident}"

    def allow_request(self, request, view):
        self._request = request
        if hasattr(request, 'data') and request.data:
            username = request.data.get('username', '')
            if username:
                cache_key = f"throttle_login_user_{hashlib.sha256(username.encode()).hexdigest()[:16]}"
                login_count = cache.get(cache_key, 0)
                if login_count >= 10:
                    self.rate = '5/minute'
        return super().allow_request(request, view)

    def throttle_failure(self):
        _record_throttle_event(self.scope, self._request)
        return super().throttle_failure()


class WorkflowRateThrottle(AnonRateThrottle):
    scope = 'workflow'

    def get_cache_key(self, request, view):
        ident = self.get_ident(request)
        return f"throttle_workflow_{ident}"

    def throttle_failure(self):
        _record_throttle_event(self.scope, self._request if hasattr(self, '_request') else None)
        return super().throttle_failure()


class TokenRefreshRateThrottle(AnonRateThrottle):
    rate = '30/minute'
    scope = 'token_refresh'

    def get_cache_key(self, request, view):
        ident = self.get_ident(request)
        return f"throttle_token_refresh_{ident}"

    def throttle_failure(self):
        _record_throttle_event(self.scope, self._request if hasattr(self, '_request') else None)
        return super().throttle_failure()


def _record_throttle_event(scope, request):
    try:
        event_key = f"throttle_events:{scope}"
        events = cache.get(event_key, [])
        event = {
            'scope': scope,
            'path': request.path,
            'method': request.method,
            'ip': request.META.get('REMOTE_ADDR', ''),
            'user_id': request.user.pk if hasattr(request, 'user') and request.user.is_authenticated else None,
            'timestamp': time.time(),
        }
        events.append(event)
        if len(events) > 100:
            events = events[-100:]
        cache.set(event_key, events, 3600)

        count_key = f"throttle_count:{scope}"
        try:
            cache.incr(count_key)
        except ValueError:
            cache.set(count_key, 1, 3600)

        logger.warning(f"Rate limit triggered: scope={scope}, path={request.path}, ip={event['ip']}")
    except Exception as e:
        logger.error(f"Failed to record throttle event: {e}")
