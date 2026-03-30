"""
请求日志中间件
"""
import time
import logging
from typing import Callable
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    请求日志中间件
    记录所有请求的响应时间
    """

    async def dispatch(self, request: Request, call_next: Callable):
        start_time = time.time()

        # 记录请求
        logger.info(f"--> {request.method} {request.url.path}")

        # 处理请求
        response = await call_next(request)

        # 计算耗时
        process_time = time.time() - start_time

        # 记录响应
        logger.info(
            f"<-- {request.method} {request.url.path} "
            f"status={response.status_code} duration={process_time:.3f}s"
        )

        # 添加响应头
        response.headers["X-Process-Time"] = str(process_time)

        return response
