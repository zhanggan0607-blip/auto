"""
爬虫相关API接口
处理爬虫状态推送、实时日志等
"""
import asyncio
import json
import logging
from typing import Optional, List
from datetime import datetime

from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from pydantic import BaseModel, Field
from sse_starlette.sse import EventSourceResponse

from fastapi_app.services.redis_pubsub import pubsub_manager
from fastapi_app.services.celery_proxy import celery_proxy

logger = logging.getLogger(__name__)
router = APIRouter()


class CrawlTaskCreate(BaseModel):
    """创建爬虫任务"""
    website_code: str = Field(..., description="网站代码")
    keywords: Optional[List[str]] = Field(default=None, description="关键词列表")
    max_pages: int = Field(default=10, description="最大页数")
    start_date: Optional[str] = Field(default=None, description="开始日期 YYYY-MM-DD")
    end_date: Optional[str] = Field(default=None, description="结束日期 YYYY-MM-DD")
    priority: int = Field(default=5, description="优先级 1-10")


class CrawlTaskStatus(BaseModel):
    """爬虫任务状态"""
    task_id: str
    status: str  # pending, running, completed, failed
    progress: float = Field(default=0, description="进度 0-100")
    items_crawled: int = Field(default=0, description="已采集数量")
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class CrawlResultPush(BaseModel):
    """爬虫结果推送"""
    task_id: str
    items: List[dict]
    total_count: int
    timestamp: datetime


@router.post("/tasks/", response_model=dict)
async def create_crawl_task(
    task_data: CrawlTaskCreate,
    background_tasks: BackgroundTasks,
):
    """
    创建爬虫任务
    返回任务ID，可用于查询状态和结果
    """
    try:
        # 通过Celery触发爬虫任务
        task = celery_proxy.send_crawl_task(
            website_code=task_data.website_code,
            keywords=task_data.keywords,
            max_pages=task_data.max_pages,
            start_date=task_data.start_date,
            end_date=task_data.end_date,
            priority=task_data.priority,
        )

        return {
            "task_id": task.id,
            "status": "pending",
            "message": "爬虫任务已创建",
        }
    except Exception as e:
        logger.error(f"创建爬虫任务失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tasks/{task_id}/", response_model=CrawlTaskStatus)
async def get_crawl_task_status(task_id: str):
    """
    获取爬虫任务状态
    """
    try:
        result = celery_proxy.get_task_result(task_id)

        if result is None:
            return CrawlTaskStatus(
                task_id=task_id,
                status="pending",
            )

        return CrawlTaskStatus(
            task_id=task_id,
            status=result.get("status", "unknown"),
            progress=result.get("progress", 0),
            items_crawled=result.get("items_crawled", 0),
            error_message=result.get("error"),
            started_at=result.get("started_at"),
            completed_at=result.get("completed_at"),
        )
    except Exception as e:
        logger.error(f"获取任务状态失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tasks/{task_id}/stream/")
async def stream_crawl_progress(task_id: str):
    """
    流式推送爬虫进度
    使用SSE (Server-Sent Events)
    """
    async def event_generator():
        channel = f"crawl_progress:{task_id}"

        # 订阅Redis频道
        pubsub = await pubsub_manager.subscribe(channel)

        try:
            # 发送初始连接消息
            yield {
                "event": "connected",
                "data": json.dumps({"task_id": task_id, "status": "connected"}),
            }

            # 持续接收消息直到任务完成
            while True:
                message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=30)

                if message:
                    data = json.loads(message["data"])
                    yield {
                        "event": data.get("event", "progress"),
                        "data": json.dumps(data),
                    }

                    if data.get("status") in ["completed", "failed"]:
                        break

        finally:
            await pubsub_manager.unsubscribe(channel)

    return EventSourceResponse(event_generator())


@router.post("/push/", status_code=200)
async def receive_crawl_push(data: CrawlResultPush):
    """
    接收爬虫结果推送
    爬虫服务调用此接口推送采集结果
    """
    try:
        logger.info(f"收到爬虫推送: task_id={data.task_id}, count={data.total_count}")

        # 发布到Redis频道，通知所有订阅者
        channel = f"crawl_progress:{data.task_id}"
        await pubsub_manager.publish(
            channel,
            {
                "event": "result",
                "task_id": data.task_id,
                "items": data.items,
                "total_count": data.total_count,
                "timestamp": data.timestamp.isoformat(),
            }
        )

        return {"status": "received"}
    except Exception as e:
        logger.error(f"处理爬虫推送失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/websites/")
async def list_pilot_websites():
    """
    获取试点网站列表
    """
    from django.conf import settings

    return {
        "websites": settings.PILOT_WEBSITES,
        "count": len(settings.PILOT_WEBSITES),
    }
