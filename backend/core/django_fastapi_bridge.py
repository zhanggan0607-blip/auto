"""
Django与FastAPI通信模块
通过Redis PubSub实现双向消息传递
"""
import json
import logging
from typing import Optional, Callable, Dict, Any
from functools import wraps

import redis
from django.conf import settings

logger = logging.getLogger(__name__)


class DjangoFastAPIBridge:
    """
    Django与FastAPI之间的消息桥
    Django通过此模块向FastAPI推送消息，或订阅来自FastAPI的消息
    """

    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self._redis_client = None
            DjangoFastAPIBridge._initialized = True

    def _get_redis(self):
        """获取Redis连接"""
        if self._redis_client is None:
            try:
                redis_host = getattr(settings, 'REDIS_HOST', 'localhost')
                redis_port = getattr(settings, 'REDIS_PORT', 6379)
                redis_db = getattr(settings, 'REDIS_CACHE_DB', 1)

                self._redis_client = redis.Redis(
                    host=redis_host,
                    port=redis_port,
                    db=redis_db,
                    decode_responses=True,
                )
                self._redis_client.ping()
            except Exception as e:
                logger.error(f"Redis连接失败: {e}")
                self._redis_client = None

        return self._redis_client

    def publish_to_fastapi(self, channel: str, message: Dict[str, Any]):
        """
        Django向FastAPI推送消息
        """
        redis_client = self._get_redis()
        if redis_client is None:
            logger.warning("Redis未连接，消息未发送")
            return False

        try:
            message_str = json.dumps(message, default=str)
            redis_client.publish(channel, message_str)
            logger.debug(f"已推送消息到 {channel}: {message_str[:100]}")
            return True
        except Exception as e:
            logger.error(f"推送消息失败: {e}")
            return False

    def subscribe_to_fastapi(self, channel: str, handler: Callable):
        """
        Django订阅来自FastAPI的消息
        """
        redis_client = self._get_redis()
        if redis_client is None:
            logger.warning("Redis未连接，无法订阅")
            return

        try:
            pubsub = redis_client.pubsub()
            pubsub.subscribe(**{channel: handler})

            def _listen():
                for message in pubsub.listen():
                    if message['type'] == 'message':
                        try:
                            data = json.loads(message['data'])
                            handler(data)
                        except json.JSONDecodeError:
                            handler(message['data'])

            import threading
            thread = threading.Thread(target=_listen, daemon=True)
            thread.start()
            logger.info(f"已订阅频道: {channel}")

        except Exception as e:
            logger.error(f"订阅失败: {e}")


# 全局单例
django_fastapi_bridge = DjangoFastAPIBridge()


def publish_crawl_result(task_id: str, items: list, total_count: int):
    """
    发布爬虫结果到FastAPI
    Django的爬虫任务完成后调用此函数
    """
    return django_fastapi_bridge.publish_to_fastapi(
        f"crawl_progress:{task_id}",
        {
            "event": "result",
            "task_id": task_id,
            "items": items,
            "total_count": total_count,
        }
    )


def publish_task_status(task_id: str, status: str, progress: float = 0, **kwargs):
    """
    发布任务状态到FastAPI
    """
    return django_fastapi_bridge.publish_to_fastapi(
        f"task_status:{task_id}",
        {
            "event": "status_update",
            "task_id": task_id,
            "status": status,
            "progress": progress,
            **kwargs
        }
    )


def publish_agent_message(session_id: str, message_type: str, content: Any):
    """
    发布Agent消息到FastAPI
    """
    return django_fastapi_bridge.publish_to_fastapi(
        f"agent_session:{session_id}",
        {
            "type": message_type,
            "content": content,
        }
    )


def send_task_to_fastapi(task_name: str, task_params: Dict[str, Any], priority: int = 5):
    """
    将任务发送到FastAPI进行处理
    FastAPI的CeleryProxy会接收并执行
    """
    return django_fastapi_bridge.publish_to_fastapi(
        "fastapi_tasks",
        {
            "task_name": task_name,
            "task_params": task_params,
            "priority": priority,
        }
    )
