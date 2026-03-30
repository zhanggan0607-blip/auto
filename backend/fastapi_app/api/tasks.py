"""
任务相关API接口
处理Celery任务触发、状态查询等
"""
import asyncio
import json
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from celery.result import AsyncResult

logger = logging.getLogger(__name__)
router = APIRouter()


class TaskStatus(str, Enum):
    """任务状态枚举"""
    PENDING = "PENDING"
    STARTED = "STARTED"
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
    REVOKED = "REVOKED"


class TaskCreate(BaseModel):
    """创建通用任务"""
    task_name: str = Field(..., description="任务名称")
    task_params: Dict[str, Any] = Field(default_factory=dict, description="任务参数")
    priority: int = Field(default=5, ge=1, le=10, description="优先级")


class TaskResponse(BaseModel):
    """任务响应"""
    task_id: str
    status: str
    message: str


class TaskResult(BaseModel):
    """任务结果"""
    task_id: str
    status: str
    result: Optional[Any] = None
    error: Optional[str] = None
    traceback: Optional[str] = None
    date_created: Optional[datetime] = None
    date_done: Optional[datetime] = None


@router.post("/", response_model=TaskResponse)
async def create_task(task_data: TaskCreate, background_tasks: BackgroundTasks):
    """
    创建通用异步任务
    """
    try:
        from backend.crawler.tasks import (
            run_crawl_task,
            sync_enterprise_to_vector,
            process_bid_document,
            send_dingtalk_notification,
        )

        task_mapping = {
            "crawl": run_crawl_task,
            "sync_enterprise": sync_enterprise_to_vector,
            "process_document": process_bid_document,
            "send_notification": send_dingtalk_notification,
        }

        task_func = task_mapping.get(task_data.task_name)

        if not task_func:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown task: {task_data.task_name}"
            )

        task = task_func.apply_async(
            kwargs=task_data.task_params,
            priority=task_data.priority,
        )

        return TaskResponse(
            task_id=task.id,
            status="pending",
            message=f"Task {task_data.task_name} submitted successfully"
        )

    except Exception as e:
        logger.error(f"创建任务失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{task_id}/", response_model=TaskResult)
async def get_task_result(task_id: str):
    """
    获取任务结果
    """
    try:
        from config.celery import app

        result = AsyncResult(task_id, app=app)

        return TaskResult(
            task_id=task_id,
            status=result.status,
            result=result.result if result.ready() else None,
            error=str(result.info) if result.failed() else None,
            traceback=result.traceback if result.failed() else None,
            date_created=result.date_created,
            date_done=result.date_done,
        )

    except Exception as e:
        logger.error(f"获取任务结果失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{task_id}/")
async def revoke_task(task_id: str, force: bool = False):
    """
    撤销任务
    """
    try:
        from config.celery import app

        result = AsyncResult(task_id, app=app)
        result.revoke(terminate=force)

        return {
            "task_id": task_id,
            "status": "revoked",
            "message": f"Task {task_id} has been revoked"
        }

    except Exception as e:
        logger.error(f"撤销任务失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/batch/")
async def create_batch_tasks(tasks: List[TaskCreate]):
    """
    批量创建任务
    """
    results = []

    for task_data in tasks:
        try:
            from backend.crawler.tasks import (
                run_crawl_task,
                sync_enterprise_to_vector,
            )

            task_mapping = {
                "crawl": run_crawl_task,
                "sync_enterprise": sync_enterprise_to_vector,
            }

            task_func = task_mapping.get(task_data.task_name)

            if task_func:
                task = task_func.apply_async(
                    kwargs=task_data.task_params,
                    priority=task_data.priority,
                )
                results.append({
                    "task_name": task_data.task_name,
                    "task_id": task.id,
                    "status": "pending",
                })
            else:
                results.append({
                    "task_name": task_data.task_name,
                    "status": "failed",
                    "error": f"Unknown task: {task_data.task_name}",
                })

        except Exception as e:
            results.append({
                "task_name": task_data.task_name,
                "status": "failed",
                "error": str(e),
            })

    return {"results": results, "total": len(tasks)}


@router.get("/stats/summary/")
async def get_task_stats_summary():
    """
    获取任务统计摘要
    """
    try:
        from django.core.cache import cache

        stats = cache.get("celery_task_stats") or {}

        return {
            "stats": stats,
            "timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        logger.error(f"获取任务统计失败: {e}")
        return {"stats": {}, "error": str(e)}
