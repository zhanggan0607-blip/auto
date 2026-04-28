import logging
import time
import asyncio
from typing import Dict, Optional, Any
from functools import wraps

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)

_DEFAULT_TIMEOUT = 30
_DEFAULT_MAX_RETRIES = 3
_DEFAULT_RETRY_BACKOFF = 1
_DEFAULT_CIRCUIT_BREAKER_THRESHOLD = 5
_DEFAULT_CIRCUIT_BREAKER_RESET_TIMEOUT = 60


class CircuitBreakerState:
    CLOSED = 'closed'
    OPEN = 'open'
    HALF_OPEN = 'half_open'


class CircuitBreaker:
    def __init__(
        self,
        failure_threshold: int = _DEFAULT_CIRCUIT_BREAKER_THRESHOLD,
        reset_timeout: int = _DEFAULT_CIRCUIT_BREAKER_RESET_TIMEOUT,
    ):
        self._failure_threshold = failure_threshold
        self._reset_timeout = reset_timeout
        self._failure_count = 0
        self._state = CircuitBreakerState.CLOSED
        self._last_failure_time = None

    @property
    def state(self) -> str:
        if self._state == CircuitBreakerState.OPEN:
            if self._last_failure_time and (
                time.time() - self._last_failure_time >= self._reset_timeout
            ):
                self._state = CircuitBreakerState.HALF_OPEN
        return self._state

    def record_success(self):
        self._failure_count = 0
        self._state = CircuitBreakerState.CLOSED

    def record_failure(self):
        self._failure_count += 1
        self._last_failure_time = time.time()
        if self._failure_count >= self._failure_threshold:
            self._state = CircuitBreakerState.OPEN

    def is_available(self) -> bool:
        return self.state != CircuitBreakerState.OPEN


class HttpResponse:
    def __init__(self, status_code: int, data: Any = None, headers: Dict = None, error: str = None):
        self.status_code = status_code
        self.data = data
        self.headers = headers or {}
        self.error = error

    @property
    def success(self) -> bool:
        return self.error is None and 200 <= self.status_code < 300

    def to_dict(self) -> Dict:
        result = {
            'success': self.success,
            'status_code': self.status_code,
        }
        if self.data is not None:
            result['data'] = self.data
        if self.headers:
            result['headers'] = dict(self.headers)
        if self.error:
            result['error'] = self.error
        return result


_circuit_breakers: Dict[str, CircuitBreaker] = {}


def _get_circuit_breaker(host: str) -> CircuitBreaker:
    if host not in _circuit_breakers:
        _circuit_breakers[host] = CircuitBreaker()
    return _circuit_breakers[host]


def _build_session(
    max_retries: int = _DEFAULT_MAX_RETRIES,
    retry_backoff: float = _DEFAULT_RETRY_BACKOFF,
) -> requests.Session:
    session = requests.Session()
    retry_strategy = Retry(
        total=max_retries,
        backoff_factor=retry_backoff,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH'],
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session


def _check_url_security(url: str) -> Optional[str]:
    try:
        from utils.url_security import is_url_safe
        is_safe, reason = is_url_safe(url)
        if not is_safe:
            return reason
    except ImportError:
        pass
    return None


def _parse_response(response: requests.Response) -> Any:
    content_type = response.headers.get('content-type', '')
    if 'application/json' in content_type:
        try:
            return response.json()
        except ValueError:
            return response.text
    return response.text


def http_request(
    method: str,
    url: str,
    headers: Dict = None,
    data: Any = None,
    params: Dict = None,
    timeout: int = _DEFAULT_TIMEOUT,
    max_retries: int = _DEFAULT_MAX_RETRIES,
    verify_ssl: bool = True,
    check_url_safety: bool = True,
) -> HttpResponse:
    if check_url_safety:
        reason = _check_url_security(url)
        if reason:
            return HttpResponse(status_code=0, error=f'URL安全验证失败: {reason}')

    from urllib.parse import urlparse
    host = urlparse(url).netloc
    cb = _get_circuit_breaker(host)
    if not cb.is_available():
        return HttpResponse(status_code=0, error=f'熔断器开启，服务暂不可用: {host}')

    session = _build_session(max_retries=max_retries)
    method_upper = method.upper()

    try:
        kwargs = {
            'headers': headers,
            'timeout': timeout,
            'verify': verify_ssl,
        }
        if method_upper in ('GET', 'DELETE'):
            kwargs['params'] = params or data
        else:
            kwargs['json'] = data
            if params:
                kwargs['params'] = params

        response = session.request(method_upper, url, **kwargs)
        parsed_data = _parse_response(response)
        cb.record_success()
        return HttpResponse(
            status_code=response.status_code,
            data=parsed_data,
            headers=dict(response.headers),
        )
    except requests.Timeout:
        cb.record_failure()
        return HttpResponse(status_code=0, error='请求超时')
    except requests.ConnectionError as e:
        cb.record_failure()
        return HttpResponse(status_code=0, error=f'连接失败: {e}')
    except requests.RequestException as e:
        cb.record_failure()
        return HttpResponse(status_code=0, error=str(e))
    except Exception as e:
        cb.record_failure()
        return HttpResponse(status_code=0, error=str(e))
    finally:
        session.close()


def http_get(url: str, **kwargs) -> HttpResponse:
    return http_request('GET', url, **kwargs)


def http_post(url: str, data: Any = None, **kwargs) -> HttpResponse:
    return http_request('POST', url, data=data, **kwargs)


def http_put(url: str, data: Any = None, **kwargs) -> HttpResponse:
    return http_request('PUT', url, data=data, **kwargs)


def http_delete(url: str, **kwargs) -> HttpResponse:
    return http_request('DELETE', url, **kwargs)


async def async_http_request(method: str, url: str, **kwargs) -> HttpResponse:
    return await asyncio.get_running_loop().run_in_executor(
        None, lambda: http_request(method, url, **kwargs)
    )


async def async_http_get(url: str, **kwargs) -> HttpResponse:
    return await async_http_request('GET', url, **kwargs)


async def async_http_post(url: str, data: Any = None, **kwargs) -> HttpResponse:
    return await async_http_request('POST', url, data=data, **kwargs)


def get_circuit_breaker_stats() -> Dict[str, Dict]:
    return {
        host: {
            'state': cb.state,
            'failure_count': cb._failure_count,
            'last_failure_time': cb._last_failure_time,
        }
        for host, cb in _circuit_breakers.items()
    }
