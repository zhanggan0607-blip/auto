"""
FastAPI应用层 - 异步高性能接口
用于处理爬虫状态推送、AI推理流式输出、批量任务等高并发场景

架构说明：
- Django: 处理复杂业务逻辑、Admin后台、现有REST API
- FastAPI: 处理异步密集型接口、WebSocket代理、实时推送
- 通信机制: 共享Redis进行消息传递，共享PostgreSQL进行数据存储
"""
from .main import app

__all__ = ['app']
