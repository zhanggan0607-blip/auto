"""
Agent事件驱动架构

用于解耦Agent与业务服务的通信

核心概念：
- Event: 事件基类
- EventBus: 事件总线，负责事件分发
- EventHandler: 事件处理器
- AgentEvent: Agent相关事件

使用示例：
    from core.events import event_bus, AgentEvent, event_handler

    # 定义事件处理器
    @event_handler('enterprise.created')
    def handle_enterprise_created(event):
        enterprise = event.data
        # 执行业务逻辑
        pass

    # Agent发布事件
    await event_bus.publish(AgentEvent(
        event_type='enterprise.created',
        data={'enterprise_id': 1, 'name': 'xxx'}
    ))
"""
import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Type
from abc import ABC, abstractmethod
import uuid

logger = logging.getLogger(__name__)


class EventPriority(Enum):
    """事件优先级"""
    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3


@dataclass
class Event:
    """
    事件基类
    """
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    event_type: str = ''
    timestamp: datetime = field(default_factory=datetime.now)
    source: str = ''
    data: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    priority: EventPriority = EventPriority.NORMAL
    correlation_id: Optional[str] = None

    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            'event_id': self.event_id,
            'event_type': self.event_type,
            'timestamp': self.timestamp.isoformat(),
            'source': self.source,
            'data': self.data,
            'metadata': self.metadata,
            'priority': self.priority.value,
            'correlation_id': self.correlation_id
        }


class AgentEvent(Event):
    """
    Agent相关事件基类
    """

    def __init__(self, event_type: str, data: Dict = None, **kwargs):
        super().__init__(event_type=event_type, data=data or {}, **kwargs)
        self.source = self.source or 'agent'


class BusinessEvent(Event):
    """
    业务相关事件基类
    """

    def __init__(self, event_type: str, data: Dict = None, **kwargs):
        super().__init__(event_type=event_type, data=data or {}, **kwargs)
        self.source = self.source or 'business'


class EventHandler(ABC):
    """
    事件处理器基类
    """

    @abstractmethod
    async def handle(self, event: Event):
        """
        处理事件

        Args:
            event: 事件对象
        """
        pass

    @property
    def handler_name(self) -> str:
        """处理器名称"""
        return self.__class__.__name__


class EventBus:
    """
    事件总线

    负责事件的注册、分发和订阅
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._initialized = True
        self._handlers: Dict[str, List[tuple[EventHandler, int]]] = {}
        self._pattern_handlers: Dict[str, List[tuple[EventHandler, int]]] = {}
        self._middlewares: List[Callable] = []
        self._event_queue: asyncio.Queue = asyncio.Queue()
        self._running = False
        self._handler_stats: Dict[str, int] = {}

    def subscribe(
        self,
        event_type: str,
        handler: EventHandler,
        priority: int = 0
    ):
        """
        订阅事件

        Args:
            event_type: 事件类型（支持通配符，如 user.*）
            handler: 事件处理器
            priority: 优先级，数字越大越先执行
        """
        if event_type.endswith('.*'):
            pattern = event_type[:-1] + '.*'
            if pattern not in self._pattern_handlers:
                self._pattern_handlers[pattern] = []
            self._pattern_handlers[pattern].append((handler, priority))
            self._pattern_handlers[pattern].sort(key=lambda x: -x[1])
        else:
            if event_type not in self._handlers:
                self._handlers[event_type] = []
            self._handlers[event_type].append((handler, priority))
            self._handlers[event_type].sort(key=lambda x: -x[1])

        logger.info(f"Subscribed handler {handler.handler_name} to event: {event_type}")

    def unsubscribe(self, event_type: str, handler: EventHandler = None):
        """
        取消订阅

        Args:
            event_type: 事件类型
            handler: 处理器（None表示取消该类型所有处理器）
        """
        if event_type.endswith('.*'):
            pattern = event_type[:-1] + '*'
            if pattern in self._pattern_handlers:
                if handler:
                    self._pattern_handlers[pattern] = [
                        (h, p) for h, p in self._pattern_handlers[pattern]
                        if h.handler_name != handler.handler_name
                    ]
                else:
                    del self._pattern_handlers[pattern]
        else:
            if event_type in self._handlers:
                if handler:
                    self._handlers[event_type] = [
                        (h, p) for h, p in self._handlers[event_type]
                        if h.handler_name != handler.handler_name
                    ]
                else:
                    del self._handlers[event_type]

    def add_middleware(self, middleware: Callable):
        """
        添加中间件

        Args:
            middleware: 中间件函数，签名: async def middleware(event, next_handler
        """
        self._middlewares.append(middleware)

    async def publish(self, event: Event) -> List[Any]:
        """
        发布事件

        Args:
            event: 事件对象

        Returns:
            处理结果列表
        """
        event.correlation_id = event.correlation_id or str(uuid.uuid4())

        logger.debug(f"Publishing event: {event.event_type}, id: {event.event_id}")

        handlers = self._get_matching_handlers(event.event_type)
        if not handlers:
            logger.debug(f"No handlers for event: {event.event_type}")
            return []

        results = []
        for handler, _ in handlers:
            try:
                if self._middlewares:
                    async def chained_handler(h, e):
                        for mw in self._middlewares:
                            await mw(e, h)
                        return await h.handle(e)
                    result = await chained_handler(handler, event)
                else:
                    result = await handler.handle(event)

                results.append(result)
                self._handler_stats[handler.handler_name] = \
                    self._handler_stats.get(handler.handler_name, 0) + 1

            except Exception as e:
                logger.error(f"Handler {handler.handler_name} failed: {str(e)}")
                results.append({'error': str(e), 'handler': handler.handler_name})

        return results

    def _get_matching_handlers(self, event_type: str) -> List[tuple]:
        """获取匹配的事件处理器"""
        handlers = []

        if event_type in self._handlers:
            handlers.extend(self._handlers[event_type])

        for pattern, pattern_handlers in self._pattern_handlers.items():
            if event_type.startswith(pattern.rstrip('*')):
                handlers.extend(pattern_handlers)

        handlers.sort(key=lambda x: -x[1])
        return handlers

    async def publish_async(self, event: Event):
        """
        异步发布事件（不等待处理结果）

        Args:
            event: 事件对象
        """
        await self._event_queue.put(event)

    async def start_processing(self):
        """开始异步处理事件队列"""
        self._running = True
        while self._running:
            try:
                event = await asyncio.wait_for(self._event_queue.get(), timeout=1.0)
                await self.publish(event)
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Event processing error: {str(e)}")

    def stop_processing(self):
        """停止异步处理"""
        self._running = False

    def get_statistics(self) -> Dict[str, Any]:
        """
        获取事件处理统计

        Returns:
            统计信息
        """
        return {
            'total_handlers': sum(len(h) for h in self._handlers.values()),
            'pattern_handlers': len(self._pattern_handlers),
            'handler_stats': self._handler_stats,
            'queue_size': self._event_queue.qsize()
        }


event_bus = EventBus()


def event_handler(event_type: str, priority: int = 0):
    """
    事件处理器装饰器

    用于将函数注册为事件处理器

    Example:
        @event_handler('enterprise.created', priority=1)
        async def handle_enterprise_created(event):
            # 处理逻辑
            pass
    """

    class FunctionEventHandler(EventHandler):
        def __init__(self, func):
            self._func = func

        @property
        def handler_name(self) -> str:
            return self._func.__name__

        async def handle(self, event: Event):
            return await self._func(event)

    def decorator(func: Callable) -> FunctionEventHandler:
        handler = FunctionEventHandler(func)
        event_bus.subscribe(event_type, handler, priority)
        return func

    return decorator


# 预定义事件类型
class EnterpriseEvents:
    """企业相关事件"""
    CREATED = 'enterprise.created'
    UPDATED = 'enterprise.updated'
    DELETED = 'enterprise.deleted'
    QUALIFICATION_ADDED = 'enterprise.qualification.added'
    QUALIFICATION_EXPIRED = 'enterprise.qualification.expired'
    CONTACT_ADDED = 'enterprise.contact.added'


class TenderEvents:
    """招标相关事件"""
    CREATED = 'tender.created'
    UPDATED = 'tender.updated'
    DELETED = 'tender.deleted'
    DEADLINE_APPROACHING = 'tender.deadline.approaching'
    STATUS_CHANGED = 'tender.status.changed'


class BidEvents:
    """投标相关事件"""
    CREATED = 'bid.created'
    SUBMITTED = 'bid.submitted'
    WON = 'bid.won'
    LOST = 'bid.lost'
    RESULT_UPDATED = 'bid.result.updated'


class AgentEvents:
    """Agent相关事件"""
    TASK_STARTED = 'agent.task.started'
    TASK_COMPLETED = 'agent.task.completed'
    TASK_FAILED = 'agent.task.failed'
    TOOL_CALLED = 'agent.tool.called'
    TOOL_RESULT = 'agent.tool.result'
    WORKFLOW_STARTED = 'agent.workflow.started'
    WORKFLOW_STAGE_CHANGED = 'agent.workflow.stage.changed'
    WORKFLOW_COMPLETED = 'agent.workflow.completed'


class CrawlerEvents:
    """爬虫相关事件"""
    CRAWL_STARTED = 'crawler.crawl.started'
    CRAWL_COMPLETED = 'crawler.crawl.completed'
    CRAWL_FAILED = 'crawler.crawl.failed'
    PAGE_DISCOVERED = 'crawler.page.discovered'
    ITEM_EXTRACTED = 'crawler.item.extracted'
