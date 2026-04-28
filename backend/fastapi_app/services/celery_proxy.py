"""
Celery任务代理
FastAPI通过此模块触发Celery任务
"""
import logging
from typing import Optional, Dict, Any, List

from celery.result import AsyncResult

logger = logging.getLogger(__name__)


class CeleryTaskProxy:
    """
    Celery任务代理
    FastAPI层通过此模块与Celery交互
    """

    def __init__(self):
        self._app = None

    def _get_app(self):
        """获取Celery应用"""
        if self._app is None:
            from config.celery import app
            self._app = app
        return self._app

    def send_crawl_task(
        self,
        website_code: str,
        keywords: Optional[List[str]] = None,
        max_pages: int = 10,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        priority: int = 5,
        **kwargs
    ) -> AsyncResult:
        """
        发送爬虫任务
        注意：实际使用 scheduled_crawl_with_match 任务
        """
        from backend.crawler.tasks import scheduled_crawl_with_match
        from apps.crawler.scheduler_models import CrawlSchedule

        try:
            schedule = CrawlSchedule.objects.filter(
                website_template__code=website_code,
                is_active=True
            ).first()

            if not schedule:
                logger.warning(f"未找到网站代码对应的采集计划: {website_code}")
                from backend.crawler.tasks import crawl_china_gov
                result = crawl_china_gov.apply_async(
                    kwargs={
                        "keywords": keywords or [],
                        "page": 1,
                        "page_size": max_pages * 20,
                        "start_date": start_date,
                        "end_date": end_date,
                    },
                    priority=priority,
                )
            else:
                result = scheduled_crawl_with_match.apply_async(
                    kwargs={"schedule_id": schedule.id},
                    priority=priority,
                )

            logger.info(f"爬虫任务已发送: task_id={result.id}, website={website_code}")
            return result

        except Exception as e:
            logger.error(f"发送爬虫任务失败: {e}")
            raise

    def send_enterprise_sync_task(
        self,
        enterprise_id: int,
        force: bool = False,
        priority: int = 5,
    ) -> AsyncResult:
        """
        发送企业同步任务
        使用 build_enterprise_vector_index 任务代替
        """
        from backend.crawler.tasks import build_enterprise_vector_index

        result = build_enterprise_vector_index.apply_async(
            kwargs={
                "enterprise_id": enterprise_id,
            },
            priority=priority,
        )

        logger.info(f"企业同步任务已发送: task_id={result.id}, enterprise_id={enterprise_id}")

        return result

    def send_document_process_task(
        self,
        document_id: int,
        priority: int = 5,
    ) -> AsyncResult:
        """
        发送文档处理任务
        注意：process_bid_document 不存在，跳过执行
        """
        logger.warning(f"文档处理任务暂不支持: document_id={document_id}")
        from celery.result import AsyncResult
        class UnsupportedTaskResult:
            id = f"unsupported_{document_id}"
            status = "FAILURE"
            ready = lambda self: True
            result = NotImplementedError("文档处理任务暂不支持")
        return UnsupportedTaskResult()

    def send_notification_task(
        self,
        notification_type: str,
        recipient: str,
        title: str,
        content: str,
        priority: int = 1,
    ) -> AsyncResult:
        """
        发送通知任务
        使用 send_daily_summary 任务代替
        """
        from backend.crawler.tasks import send_daily_summary

        result = send_daily_summary.apply_async(
            kwargs={
                "notification_type": notification_type,
                "recipient": recipient,
                "title": title,
                "content": content,
            },
            priority=priority,
        )

        logger.info(f"通知任务已发送: task_id={result.id}, type={notification_type}")

        return result

    def get_task_result(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        获取任务结果
        """
        try:
            app = self._get_app()
            result = AsyncResult(task_id, app=app)

            if result.ready():
                return {
                    "status": result.status,
                    "result": result.result,
                    "date_done": str(result.date_done) if result.date_done else None,
                }
            else:
                return {
                    "status": result.status,
                    "date_created": str(result.date_created) if result.date_created else None,
                }

        except Exception as e:
            logger.error(f"获取任务结果失败: {e}")
            return None

    def revoke_task(self, task_id: str, terminate: bool = False):
        """
        撤销任务
        """
        try:
            app = self._get_app()
            result = AsyncResult(task_id, app=app)
            result.revoke(terminate=terminate)
            logger.info(f"任务已撤销: task_id={task_id}, terminate={terminate}")
        except Exception as e:
            logger.error(f"撤销任务失败: {e}")


# 全局单例
celery_proxy = CeleryTaskProxy()
