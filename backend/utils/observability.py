"""
可观测性模块

提供统一的链路追踪、指标监控和日志关联：
1. OpenTelemetry分布式追踪
2. 自定义业务指标
3. 结构化日志增强
4. 性能剖析

使用示例:
```python
from utils.observability import (
    trace,
    observe,
    metrics,
    get_current_trace_context,
    setup_observability,
)

# 追踪函数
@trace('process_tender')
def process_tender_data(tender_id):
    ...

# 观察指标
@observe('tender.processed', labels={'source': 'crawler'})
def process_tender(tender_id):
    ...

# 记录指标
metrics.increment('api.requests', tags={'endpoint': '/api/v1/tenders/'})
metrics.gauge('active.users', value=100)
metrics.histogram('request.duration', value=0.234, tags={'method': 'GET'})

# 获取追踪上下文
context = get_current_trace_context()
logger.info('Processing', extra={'trace_context': context})
```
"""
import functools
import logging
import time
import uuid
from contextlib import contextmanager
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

from django.conf import settings

logger = logging.getLogger(__name__)


class TraceContext:
    """追踪上下文"""

    def __init__(self, trace_id: str = None, span_id: str = None, parent_span_id: str = None):
        self.trace_id = trace_id or self._generate_id(32)
        self.span_id = span_id or self._generate_id(16)
        self.parent_span_id = parent_span_id
        self.start_time = time.time()
        self.end_time = None
        self.tags: Dict[str, str] = {}
        self.events: List[Dict] = []

    @staticmethod
    def _generate_id(length: int) -> str:
        return uuid.uuid4().hex[:length]

    def add_tag(self, key: str, value: str):
        self.tags[key] = value

    def add_event(self, name: str, attributes: Dict[str, Any] = None):
        self.events.append({
            'name': name,
            'timestamp': datetime.now().isoformat(),
            'attributes': attributes or {}
        })

    def finish(self):
        self.end_time = time.time()

    @property
    def duration(self) -> float:
        if self.end_time:
            return self.end_time - self.start_time
        return time.time() - self.start_time

    def to_dict(self) -> Dict[str, Any]:
        return {
            'trace_id': self.trace_id,
            'span_id': self.span_id,
            'parent_span_id': self.parent_span_id,
            'duration_ms': self.duration * 1000,
            'tags': self.tags,
            'events': self.events,
        }


class TraceContextManager:
    """追踪上下文管理器"""

    _current_context = None
    _lock = __import__('threading').Lock()

    @classmethod
    def get_current(cls) -> Optional[TraceContext]:
        return cls._current_context

    @classmethod
    def set_current(cls, context: TraceContext):
        with cls._lock:
            cls._current_context = context

    @classmethod
    @contextmanager
    def create_span(cls, name: str, parent: TraceContext = None, tags: Dict[str, str] = None):
        parent_span_id = parent.span_id if parent else None
        span = TraceContext(parent_span_id=parent_span_id)
        if tags:
            for key, value in span.tags.items():
                span.add_tag(key, value)

        cls.set_current(span)

        try:
            span.add_event(f'span.start.{name}')
            yield span
            span.add_event(f'span.end.{name}')
        except Exception as e:
            span.add_event('span.error', {'error': str(e)})
            raise
        finally:
            span.finish()
            cls.set_current(parent)


class MetricsCollector:
    """指标收集器"""

    def __init__(self):
        self._counters: Dict[str, float] = {}
        self._gauges: Dict[str, float] = {}
        self._histograms: Dict[str, List[float]] = {}
        self._lock = __import__('threading').Lock()
        self._labels: Dict[str, Dict[str, str]] = {}

    def increment(self, name: str, value: float = 1.0, tags: Dict[str, str] = None):
        """递增计数器"""
        key = self._make_key(name, tags)
        with self._lock:
            self._counters[key] = self._counters.get(key, 0) + value

    def decrement(self, name: str, value: float = 1.0, tags: Dict[str, str] = None):
        """递减计数器"""
        key = self._make_key(name, tags)
        with self._lock:
            self._counters[key] = self._counters.get(key, 0) - value

    def gauge(self, name: str, value: float, tags: Dict[str, str] = None):
        """设置Gauge值"""
        key = self._make_key(name, tags)
        with self._lock:
            self._gauges[key] = value

    def histogram(self, name: str, value: float, tags: Dict[str, str] = None):
        """记录直方图值"""
        key = self._make_key(name, tags)
        with self._lock:
            if key not in self._histograms:
                self._histograms[key] = []
            self._histograms[key].append(value)
            if len(self._histograms[key]) > 10000:
                self._histograms[key] = self._histograms[key][-5000:]

    def _make_key(self, name: str, tags: Dict[str, str] = None) -> str:
        if not tags:
            return name
        tag_str = ','.join(f'{k}={v}' for k, v in sorted(tags.items()))
        return f'{name}{{{tag_str}}}'

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        with self._lock:
            stats = {
                'counters': dict(self._counters),
                'gauges': dict(self._gauges),
                'histograms': {}
            }

            for key, values in self._histograms.items():
                if values:
                    sorted_values = sorted(values)
                    n = len(sorted_values)
                    stats['histograms'][key] = {
                        'count': n,
                        'sum': sum(values),
                        'avg': sum(values) / n,
                        'min': sorted_values[0],
                        'max': sorted_values[-1],
                        'p50': sorted_values[n // 2],
                        'p90': sorted_values[int(n * 0.9)],
                        'p95': sorted_values[int(n * 0.95)],
                        'p99': sorted_values[int(n * 0.99)],
                    }

            return stats

    def reset(self):
        """重置所有指标"""
        with self._lock:
            self._counters.clear()
            self._gauges.clear()
            self._histograms.clear()


metrics_collector = MetricsCollector()


class ObservabilityManager:
    """可观测性管理器"""

    def __init__(self):
        self.enabled = getattr(settings, 'OBSERVABILITY_ENABLED', True)
        self.trace_enabled = getattr(settings, 'TRACE_ENABLED', True)
        self.metrics_enabled = getattr(settings, 'METRICS_ENABLED', True)
        self._traces: List[TraceContext] = []
        self._max_traces = 1000

    def record_trace(self, trace: TraceContext):
        """记录追踪"""
        if not self.enabled or not self.trace_enabled:
            return

        with __import__('threading').Lock():
            self._traces.append(trace)
            if len(self._traces) > self._max_traces:
                self._traces = self._traces[-self._max_traces // 2:]

        if hasattr(settings, 'TRACE_LOG_FILE'):
            try:
                import json
                with open(settings.TRACE_LOG_FILE, 'a', encoding='utf-8') as f:
                    f.write(json.dumps(trace.to_dict(), ensure_ascii=False) + '\n')
            except Exception as e:
                logger.error(f"Failed to write trace log: {e}")

    def get_recent_traces(self, limit: int = 100) -> List[Dict]:
        """获取最近的追踪"""
        with __import__('threading').Lock():
            traces = self._traces[-limit:]
            return [t.to_dict() for t in traces]


observability_manager = ObservabilityManager()


def trace(name: str = None, tags: Dict[str, str] = None):
    """
    函数追踪装饰器

    Example:
        @trace('process_tender')
        def process_tender(tender_id):
            ...
    """
    def decorator(func: Callable) -> Callable:
        trace_name = name or f'{func.__module__}.{func.__qualname__}'

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            with TraceContextManager.create_span(trace_name, tags=tags) as span:
                start_time = time.time()
                try:
                    result = func(*args, **kwargs)
                    span.add_tag('status', 'success')
                    return result
                except Exception as e:
                    span.add_tag('status', 'error')
                    span.add_tag('error', str(e))
                    span.add_tag('error_type', type(e).__name__)
                    raise
                finally:
                    duration = time.time() - start_time
                    span.add_tag('duration_ms', str(duration * 1000))

                    if observability_manager.enabled:
                        observability_manager.record_trace(span)

                    if metrics_collector and observability_manager.metrics_enabled:
                        metrics_collector.histogram(
                            f'{trace_name}.duration',
                            duration,
                            tags={'status': span.tags.get('status', 'unknown')}
                        )

        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            with TraceContextManager.create_span(trace_name, tags=tags) as span:
                start_time = time.time()
                try:
                    result = await func(*args, **kwargs)
                    span.add_tag('status', 'success')
                    return result
                except Exception as e:
                    span.add_tag('status', 'error')
                    span.add_tag('error', str(e))
                    span.add_tag('error_type', type(e).__name__)
                    raise
                finally:
                    duration = time.time() - start_time
                    span.add_tag('duration_ms', str(duration * 1000))

                    if observability_manager.enabled:
                        observability_manager.record_trace(span)

                    if metrics_collector and observability_manager.metrics_enabled:
                        metrics_collector.histogram(
                            f'{trace_name}.duration',
                            duration,
                            tags={'status': span.tags.get('status', 'unknown')}
                        )

        if functools.iscoroutinefunction(func):
            return async_wrapper
        return wrapper

    return decorator


def observe(name: str, labels: Dict[str, str] = None):
    """
    函数观察装饰器 - 记录函数调用为指标

    Example:
        @observe('tender.processed', labels={'source': 'crawler'})
        def process_tender(tender_id):
            ...
    """
    def decorator(func: Callable) -> Callable:
        metric_name = name

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                if observability_manager.metrics_enabled:
                    metrics_collector.increment(metric_name, tags=labels)
                return result
            except Exception as e:
                if observability_manager.metrics_enabled:
                    metrics_collector.increment(f'{metric_name}.error', tags=labels)
                raise
            finally:
                duration = time.time() - start_time
                if observability_manager.metrics_enabled:
                    metrics_collector.histogram(
                        f'{metric_name}.duration',
                        duration,
                        tags=labels
                    )

        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                if observability_manager.metrics_enabled:
                    metrics_collector.increment(metric_name, tags=labels)
                return result
            except Exception as e:
                if observability_manager.metrics_enabled:
                    metrics_collector.increment(f'{metric_name}.error', tags=labels)
                raise
            finally:
                duration = time.time() - start_time
                if observability_manager.metrics_enabled:
                    metrics_collector.histogram(
                        f'{metric_name}.duration',
                        duration,
                        tags=labels
                    )

        if functools.iscoroutinefunction(func):
            return async_wrapper
        return wrapper

    return decorator


class MetricsProxy:
    """指标代理"""

    def __getattr__(self, name: str):
        return MetricsMethods(name)


class MetricsMethods:
    """指标操作方法"""

    def __init__(self, prefix: str):
        self.prefix = prefix

    def increment(self, value: float = 1.0, tags: Dict[str, str] = None):
        if observability_manager.metrics_enabled:
            metrics_collector.increment(self.prefix, value, tags)

    def decrement(self, value: float = 1.0, tags: Dict[str, str] = None):
        if observability_manager.metrics_enabled:
            metrics_collector.decrement(self.prefix, value, tags)

    def gauge(self, value: float, tags: Dict[str, str] = None):
        if observability_manager.metrics_enabled:
            metrics_collector.gauge(self.prefix, value, tags)

    def histogram(self, value: float, tags: Dict[str, str] = None):
        if observability_manager.metrics_enabled:
            metrics_collector.histogram(self.prefix, value, tags)


metrics = MetricsProxy()


def get_current_trace_context() -> Optional[Dict[str, Any]]:
    """获取当前追踪上下文"""
    context = TraceContextManager.get_current()
    return context.to_dict() if context else None


@contextmanager
def span(name: str, tags: Dict[str, str] = None):
    """创建追踪跨度"""
    with TraceContextManager.create_span(name, tags=tags) as trace_context:
        yield trace_context


def setup_observability(
    enabled: bool = True,
    trace_enabled: bool = True,
    metrics_enabled: bool = True,
    trace_log_file: str = None,
):
    """
    配置可观测性

    Example:
        setup_observability(
            enabled=True,
            trace_enabled=True,
            metrics_enabled=True,
            trace_log_file='/var/log/traces.jsonl'
        )
    """
    observability_manager.enabled = enabled
    observability_manager.trace_enabled = trace_enabled
    observability_manager.metrics_enabled = metrics_enabled

    if trace_log_file:
        import os
        os.makedirs(os.path.dirname(trace_log_file), exist_ok=True)


class StructuredLogger:
    """
    结构化日志增强器

    提供统一的日志格式，包含追踪上下文
    """

    def __init__(self, name: str):
        self.logger = logging.getLogger(name)

    def _get_extra(self, **kwargs) -> Dict[str, Any]:
        trace_context = get_current_trace_context()
        extra = kwargs.pop('extra', {})
        extra['trace'] = trace_context or {}
        extra.update(kwargs)
        return extra

    def debug(self, msg: str, **kwargs):
        self.logger.debug(msg, extra=self._get_extra(**kwargs))

    def info(self, msg: str, **kwargs):
        self.logger.info(msg, extra=self._get_extra(**kwargs))

    def warning(self, msg: str, **kwargs):
        self.logger.warning(msg, extra=self._get_extra(**kwargs))

    def error(self, msg: str, **kwargs):
        self.logger.error(msg, extra=self._get_extra(**kwargs))

    def critical(self, msg: str, **kwargs):
        self.logger.critical(msg, extra=self._get_extra(**kwargs))


def get_logger(name: str) -> StructuredLogger:
    """获取结构化日志器"""
    return StructuredLogger(name)


__all__ = [
    'TraceContext',
    'TraceContextManager',
    'MetricsCollector',
    'ObservabilityManager',
    'observability_manager',
    'metrics_collector',
    'metrics',
    'trace',
    'observe',
    'span',
    'get_current_trace_context',
    'setup_observability',
    'StructuredLogger',
    'get_logger',
]
