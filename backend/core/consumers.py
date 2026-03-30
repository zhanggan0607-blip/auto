"""
WebSocket Consumers
用于实时推送爬虫进度、通知、中标结果等
"""
import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from asgiref.sync import sync_to_async

logger = logging.getLogger(__name__)


class CrawlerProgressConsumer(AsyncWebsocketConsumer):
    """
    爬虫进度推送 Consumer
    """
    
    async def connect(self):
        self.task_id = self.scope['url_route']['kwargs']['task_id']
        self.group_name = f'crawler_{self.task_id}'
        
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        
        await self.accept()
        logger.info(f"WebSocket 连接成功: {self.group_name}")
    
    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )
        logger.info(f"WebSocket 断开连接: {self.group_name}")
    
    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message_type = text_data_json.get('type', 'ping')
        
        if message_type == 'ping':
            await self.send(text_data=json.dumps({
                'type': 'pong',
                'timestamp': str(int(time.time()))
            }))
    
    async def progress_update(self, event):
        """
        接收进度更新并推送给客户端
        """
        await self.send(text_data=json.dumps({
            'type': 'progress',
            'data': event['data']
        }))
    
    async def status_change(self, event):
        """
        接收状态变化并推送
        """
        await self.send(text_data=json.dumps({
            'type': 'status',
            'data': event['data']
        }))


class NotificationConsumer(AsyncWebsocketConsumer):
    """
    通知推送 Consumer
    """
    
    async def connect(self):
        self.user_id = self.scope['url_route']['kwargs']['user_id']
        self.group_name = f'notifications_{self.user_id}'
        
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        
        await self.accept()
        logger.info(f"通知 WebSocket 连接成功: user_{self.user_id}")
    
    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )
    
    async def notification_message(self, event):
        """
        推送通知消息
        """
        await self.send(text_data=json.dumps({
            'type': 'notification',
            'data': event['data']
        }))
    
    async def bid_result(self, event):
        """
        推送中标结果
        """
        await self.send(text_data=json.dumps({
            'type': 'bid_result',
            'data': event['data']
        }))


class BidResultConsumer(AsyncWebsocketConsumer):
    """
    中标结果推送 Consumer
    """
    
    async def connect(self):
        self.group_name = 'bid_results'
        
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        
        await self.accept()
        logger.info("中标结果 WebSocket 连接成功")
    
    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )
    
    async def bid_win(self, event):
        """
        推送中标消息
        """
        await self.send(text_data=json.dumps({
            'type': 'bid_win',
            'data': event['data']
        }))
    
    async def bid_lost(self, event):
        """
        推送未中标消息
        """
        await self.send(text_data=json.dumps({
            'type': 'bid_lost',
            'data': event['data']
        }))
    
    async def new_tender(self, event):
        """
        推送新招标消息
        """
        await self.send(text_data=json.dumps({
            'type': 'new_tender',
            'data': event['data']
        }))


import time
