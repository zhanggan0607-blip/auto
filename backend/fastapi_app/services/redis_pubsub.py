"""
Redis PubSub管理器
用于FastAPI和Django之间的实时消息传递
"""
import json
import logging
from typing import Optional, Callable, Any
from contextlib import asynccontextmanager

import redis.asyncio as redis

logger = logging.getLogger(__name__)


class RedisPubSubManager:
    """
    Redis PubSub管理器
    提供异步发布/订阅功能
    """

    _instance = None
    _connection: Optional[redis.Redis] = None
    _pubsub_connections = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        self._connection = None
        self._pubsub_connections = {}

    async def connect(self):
        """建立Redis连接"""
        if self._connection is None:
            try:
                import os
                self._connection = redis.Redis(
                    host=os.getenv('REDIS_HOST', 'localhost'),
                    port=int(os.getenv('REDIS_PORT', '6379')),
                    db=int(os.getenv('REDIS_DB', '0')),
                    password=os.getenv('REDIS_PASSWORD') or None,
                    decode_responses=True,
                )
                await self._connection.ping()
                logger.info("Redis连接已建立")
            except Exception as e:
                logger.error(f"Redis连接失败: {e}")
                self._connection = None

    async def disconnect(self):
        """关闭Redis连接"""
        if self._connection:
            await self._connection.close()
            self._connection = None
            logger.info("Redis连接已关闭")

    async def ping(self) -> bool:
        """检查Redis连接"""
        try:
            if self._connection:
                await self._connection.ping()
                return True
        except Exception:
            pass
        return False

    async def subscribe(self, channel: str):
        """
        订阅频道
        返回pubsub对象，使用后需要unsubscribe
        """
        if self._connection is None:
            await self.connect()

        if self._connection is None:
            raise ConnectionError("Redis not connected")

        pubsub = self._connection.pubsub()
        await pubsub.subscribe(channel)
        self._pubsub_connections[channel] = pubsub
        logger.debug(f"订阅频道: {channel}")
        return pubsub

    async def unsubscribe(self, channel: str):
        """取消订阅"""
        if channel in self._pubsub_connections:
            pubsub = self._pubsub_connections[channel]
            await pubsub.unsubscribe(channel)
            await pubsub.close()
            del self._pubsub_connections[channel]
            logger.debug(f"取消订阅: {channel}")

    async def publish(self, channel: str, message: dict):
        """
        发布消息到频道
        """
        if self._connection is None:
            await self.connect()

        if self._connection is None:
            raise ConnectionError("Redis not connected")

        try:
            message_str = json.dumps(message, default=str)
            await self._connection.publish(channel, message_str)
            logger.debug(f"发布消息到 {channel}: {message_str[:100]}")
        except Exception as e:
            logger.error(f"发布消息失败: {e}")

    @asynccontextmanager
    async def listener(self, channel: str, handler: Callable):
        """
        异步上下文管理器，用于监听频道消息

        使用示例:
            async with pubsub_manager.listener("my_channel", handle_message):
                # 监听中...
                await asyncio.sleep(60)
        """
        pubsub = await self.subscribe(channel)

        async def _listen():
            try:
                async for message in pubsub.listen():
                    if message["type"] == "message":
                        data = json.loads(message["data"])
                        await handler(data)
            except Exception as e:
                logger.error(f"Listener error: {e}")

        try:
            yield _listen
        finally:
            await self.unsubscribe(channel)

    async def get_message(self, channel: str, timeout: float = 0):
        """
        获取频道的最新消息（非阻塞或超时阻塞）
        """
        if channel not in self._pubsub_connections:
            pubsub = await self.subscribe(channel)
        else:
            pubsub = self._pubsub_connections[channel]

        return await pubsub.get_message(ignore_subscribe_messages=True, timeout=timeout)


# 全局单例
pubsub_manager = RedisPubSubManager()
