"""
服务熔断器模块

提供Resilience4j风格的熔断器实现，用于防止级联故障：
1. 熔断器状态机（CLOSED、OPEN、HALF_OPEN）
2. 失败率计算
3. 自动恢复
4. 慢请求检测
5. 事件回调

使用示例:
```python
from utils.circuit_breaker import CircuitBreaker, CircuitBreakerConfig, CircuitState

config = CircuitBreakerConfig(
    failure_rate_threshold=50,
    slow_request_threshold=3.0,
    slow_request_rate=50,
    min_calls=10,
    reset_timeout=60,
)

breaker = CircuitBreaker('external-api', config)

@breaker
def call_external_api():
    response = requests.get('https://api.example.com/data')
    return response.json()

# 获取熔断器状态
state = breaker.state
print(f"当前状态: {state.name}")
```
"""
import functools
import logging
import threading
import time
from datetime import datetime, timedelta
from enum import Enum
from typing import Callable, Any, Optional, List, Dict, TypeVar, Union

from django.conf import settings

logger = logging.getLogger(__name__)

T = TypeVar('T')


class CircuitState(Enum):
    """熔断器状态"""
    CLOSED = 'closed'
    OPEN = 'open'
    HALF_OPEN = 'half_open'


class CircuitBreakerOpen(Exception):
    """熔断器打开异常"""

    def __init__(self, circuit_name: str, retry_after: float = None):
        self.circuit_name = circuit_name
        self.retry_after = retry_after
        super().__init__(
            f"Circuit breaker '{circuit_name}' is OPEN. "
            f"Retry after {retry_after:.1f} seconds." if retry_after else
            f"Circuit breaker '{circuit_name}' is OPEN."
        )


class CircuitBreakerConfig:
    """熔断器配置"""

    def __init__(
        self,
        failure_rate_threshold: float = 50.0,
        slow_request_threshold: float = 3.0,
        slow_request_rate: float = 50.0,
        min_calls: int = 10,
        reset_timeout: float = 60.0,
        half_open_max_calls: int = 5,
        sliding_window_size: int = 100,
        permitted_number_of_calls_in_half_open_state: int = 3,
    ):
        self.failure_rate_threshold = failure_rate_threshold
        self.slow_request_threshold = slow_request_threshold
        self.slow_request_rate = slow_request_rate
        self.min_calls = min_calls
        self.reset_timeout = reset_timeout
        self.half_open_max_calls = half_open_max_calls
        self.sliding_window_size = sliding_window_size
        self.permitted_number_of_calls_in_half_open_state = (
            permitted_number_of_calls_in_half_open_state
        )


class CallRecord:
    """调用记录"""

    def __init__(
        self,
        start_time: float,
        duration: float,
        success: bool,
        error: Optional[str] = None,
    ):
        self.start_time = start_time
        self.duration = duration
        self.success = success
        self.error = error


class CircuitBreaker:
    """
    服务熔断器

    状态机转换:
    - CLOSED -> OPEN: 失败率超过阈值
    - OPEN -> HALF_OPEN: 超过重置超时时间
    - HALF_OPEN -> CLOSED: 连续成功调用达到阈值
    - HALF_OPEN -> OPEN: 任何调用失败
    """

    def __init__(
        self,
        name: str,
        config: CircuitBreakerConfig = None,
        on_state_change: Callable[['CircuitBreaker', CircuitState, CircuitState], None] = None,
    ):
        self.name = name
        self.config = config or CircuitBreakerConfig()
        self.on_state_change = on_state_change

        self._state = CircuitState.CLOSED
        self._calls: List[CallRecord] = []
        self._last_state_change_time = time.time()
        self._half_open_calls = 0
        self._lock = threading.RLock()
        self._success_count = 0
        self._failure_count = 0

    @property
    def state(self) -> CircuitState:
        """获取当前状态"""
        with self._lock:
            if self._state == CircuitState.OPEN:
                if self._should_attempt_reset():
                    self._transition_to(CircuitState.HALF_OPEN)
            return self._state

    @property
    def failure_rate(self) -> float:
        """获取失败率"""
        with self._lock:
            if len(self._calls) < self.config.min_calls:
                return 0.0

            recent_calls = self._get_recent_calls()
            if not recent_calls:
                return 0.0

            failures = sum(1 for c in recent_calls if not c.success)
            return (failures / len(recent_calls)) * 100

    @property
    def slow_request_rate(self) -> float:
        """获取慢请求率"""
        with self._lock:
            recent_calls = self._get_recent_calls()
            if not recent_calls:
                return 0.0

            slow_calls = sum(
                1 for c in recent_calls
                if c.duration > self.config.slow_request_threshold
            )
            return (slow_calls / len(recent_calls)) * 100

    @property
    def average_duration(self) -> float:
        """获取平均响应时间"""
        with self._lock:
            recent_calls = self._get_recent_calls()
            if not recent_calls:
                return 0.0
            return sum(c.duration for c in recent_calls) / len(recent_calls)

    @property
    def statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        with self._lock:
            return {
                'name': self.name,
                'state': self.state.value,
                'failure_rate': self.failure_rate,
                'slow_request_rate': self.slow_request_rate,
                'average_duration': self.average_duration,
                'total_calls': len(self._calls),
                'success_count': self._success_count,
                'failure_count': self._failure_count,
                'last_state_change': datetime.fromtimestamp(
                    self._last_state_change_time
                ).isoformat(),
            }

    def _should_attempt_reset(self) -> bool:
        """检查是否应该尝试重置"""
        elapsed = time.time() - self._last_state_change_time
        return elapsed >= self.config.reset_timeout

    def _get_recent_calls(self) -> List[CallRecord]:
        """获取最近的调用记录"""
        cutoff_time = time.time() - self.config.reset_timeout
        return [c for c in self._calls if c.start_time >= cutoff_time]

    def _transition_to(self, new_state: CircuitState):
        """转换状态"""
        if self._state == new_state:
            return

        old_state = self._state
        self._state = new_state
        self._last_state_change_time = time.time()

        logger.info(
            f"Circuit breaker '{self.name}' state changed: "
            f"{old_state.value} -> {new_state.value}"
        )

        if self.on_state_change:
            try:
                self.on_state_change(self, old_state, new_state)
            except Exception as e:
                logger.error(f"Circuit breaker state change callback error: {e}")

    def _record_success(self, duration: float):
        """记录成功调用"""
        with self._lock:
            self._calls.append(CallRecord(time.time(), duration, True))
            self._success_count += 1
            self._trim_calls()

            if self._state == CircuitState.HALF_OPEN:
                self._half_open_calls += 1
                if self._half_open_calls >= self.config.permitted_number_of_calls_in_half_open_state:
                    self._transition_to(CircuitState.CLOSED)
                    self._half_open_calls = 0
                    self._reset_counters()

    def _record_failure(self, duration: float, error: str = None):
        """记录失败调用"""
        with self._lock:
            self._calls.append(CallRecord(time.time(), duration, False, error))
            self._failure_count += 1
            self._trim_calls()

            if self._state == CircuitState.HALF_OPEN:
                self._transition_to(CircuitState.OPEN)
                self._half_open_calls = 0

            elif self._state == CircuitState.CLOSED:
                if self._should_open():
                    self._transition_to(CircuitState.OPEN)

    def _should_open(self) -> bool:
        """判断是否应该打开熔断器"""
        if len(self._calls) < self.config.min_calls:
            return False

        if self.failure_rate >= self.config.failure_rate_threshold:
            return True

        if self.slow_request_rate >= self.config.slow_request_rate:
            return True

        return False

    def _trim_calls(self):
        """清理过期的调用记录"""
        cutoff_time = time.time() - self.config.reset_timeout * 10
        self._calls = [c for c in self._calls if c.start_time >= cutoff_time]

        if len(self._calls) > self.config.sliding_window_size:
            self._calls = self._calls[-self.config.sliding_window_size:]

    def _reset_counters(self):
        """重置计数器"""
        self._success_count = 0
        self._failure_count = 0
        self._half_open_calls = 0

    def _check_before_call(self):
        """调用前检查"""
        if self.state == CircuitState.OPEN:
            retry_after = max(
                0, self.config.reset_timeout - (time.time() - self._last_state_change_time)
            )
            raise CircuitBreakerOpen(self.name, retry_after)

    def record_success(self, duration: float):
        """手动记录成功"""
        self._record_success(duration)

    def record_failure(self, duration: float, error: str = None):
        """手动记录失败"""
        self._record_failure(duration, error)

    def __call__(self, func: Callable[..., T]) -> Callable[..., T]:
        """
        作为装饰器使用

        Example:
            @CircuitBreaker('my-service')
            def call_service():
                return requests.get('https://api.example.com')
        """

        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> T:
            self._check_before_call()

            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                self._record_success(duration)
                return result

            except CircuitBreakerOpen:
                raise

            except Exception as e:
                duration = time.time() - start_time
                self._record_failure(duration, str(e))
                raise

        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs) -> T:
            self._check_before_call()

            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time
                self._record_success(duration)
                return result

            except CircuitBreakerOpen:
                raise

            except Exception as e:
                duration = time.time() - start_time
                self._record_failure(duration, str(e))
                raise

        if functools.iscoroutinefunction(func):
            return async_wrapper
        return wrapper

    def reset(self):
        """重置熔断器"""
        with self._lock:
            self._state = CircuitState.CLOSED
            self._last_state_change_time = time.time()
            self._reset_counters()
            self._calls.clear()
            logger.info(f"Circuit breaker '{self.name}' has been reset")


class CircuitBreakerRegistry:
    """
    熔断器注册表

    管理多个熔断器的注册和访问
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._breakers = {}
                    cls._instance._breakers_lock = threading.RLock()
        return cls._instance

    def register(
        self,
        name: str,
        config: CircuitBreakerConfig = None,
        on_state_change: Callable = None,
    ) -> CircuitBreaker:
        """
        注册熔断器

        Args:
            name: 熔断器名称
            config: 配置
            on_state_change: 状态变化回调

        Returns:
            CircuitBreaker实例
        """
        with self._breakers_lock:
            if name not in self._breakers:
                self._breakers[name] = CircuitBreaker(name, config, on_state_change)
            return self._breakers[name]

    def get(self, name: str) -> Optional[CircuitBreaker]:
        """获取熔断器"""
        with self._breakers_lock:
            return self._breakers.get(name)

    def get_all(self) -> Dict[str, CircuitBreaker]:
        """获取所有熔断器"""
        with self._breakers_lock:
            return dict(self._breakers)

    def get_statistics(self) -> Dict[str, Dict[str, Any]]:
        """获取所有熔断器的统计"""
        with self._breakers_lock:
            return {name: cb.statistics for name, cb in self._breakers.items()}

    def reset_all(self):
        """重置所有熔断器"""
        with self._breakers_lock:
            for cb in self._breakers.values():
                cb.reset()


circuit_breaker_registry = CircuitBreakerRegistry()


def get_circuit_breaker(
    name: str,
    config: CircuitBreakerConfig = None,
) -> CircuitBreaker:
    """
    获取或注册熔断器

    Example:
        breaker = get_circuit_breaker('my-service')
        breaker = get_circuit_breaker('my-service', CircuitBreakerConfig(failure_rate_threshold=60))
    """
    return circuit_breaker_registry.register(name, config)


def circuit_breaker(
    name: str = None,
    config: CircuitBreakerConfig = None,
):
    """
    熔断器装饰器工厂

    Example:
        @circuit_breaker('my-service')
        def call_service():
            return requests.get('https://api.example.com')

        @circuit_breaker(name='external-api', config=CircuitBreakerConfig(failure_rate_threshold=70))
        async def call_api_async():
            return await api_call()
    """
    breaker_name = name

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        actual_name = breaker_name or f"{func.__module__}.{func.__qualname__}"
        breaker = get_circuit_breaker(actual_name, config)

        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> T:
            breaker._check_before_call()

            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                breaker.record_success(time.time() - start_time)
                return result

            except CircuitBreakerOpen:
                raise

            except Exception as e:
                breaker.record_failure(time.time() - start_time, str(e))
                raise

        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs) -> T:
            breaker._check_before_call()

            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                breaker.record_success(time.time() - start_time)
                return result

            except CircuitBreakerOpen:
                raise

            except Exception as e:
                breaker.record_failure(time.time() - start_time, str(e))
                raise

        if functools.iscoroutinefunction(func):
            return async_wrapper
        return wrapper

    return decorator


__all__ = [
    'CircuitBreaker',
    'CircuitBreakerConfig',
    'CircuitBreakerOpen',
    'CircuitState',
    'CircuitBreakerRegistry',
    'circuit_breaker',
    'get_circuit_breaker',
    'circuit_breaker_registry',
]
