"""
Django认证中间件
让FastAPI可以复用Django的认证机制
"""
import asyncio
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse


class DjangoAuthMiddleware(BaseHTTPMiddleware):
    """
    Django认证中间件
    验证请求中的Django会话/JWT Token
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # 跳过健康检查和文档路由
        if request.url.path in ["/health/", "/ready/", "/docs", "/redoc", "/openapi.json"]:
            return await call_next(request)

        # 公开接口白名单
        public_paths = [
            "/api/v1/crawler/push/",  # 爬虫回调
            "/api/v1/tasks/callback/",  # 任务回调
        ]
        if request.url.path in public_paths:
            return await call_next(request)

        # 获取认证信息
        auth_header = request.headers.get("Authorization", "")
        session_id = request.cookies.get("sessionid", "")

        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
            user = await self._verify_jwt_token(token)
            if user:
                request.state.user = user
            else:
                return JSONResponse(
                    status_code=401,
                    content={"detail": "Invalid or expired token"}
                )
        elif session_id:
            user = await self._verify_session(session_id)
            if user:
                request.state.user = user
        else:
            # 检查是否需要认证
            if request.url.path.startswith("/api/v1/"):
                return JSONResponse(
                    status_code=401,
                    content={"detail": "Authentication required"}
                )

        return await call_next(request)

    async def _verify_jwt_token(self, token: str):
        """
        验证JWT Token
        """
        try:
            from utils.authentication import decode_token
            payload = decode_token(token)
            if payload:
                user_id = payload.get("user_id")
                if user_id:
                    from apps.users.models import User
                    return User.objects.get(id=user_id)
        except Exception:
            pass
        return None

    async def _verify_session(self, session_id: str):
        """
        验证Django Session
        """
        try:
            from django.contrib.sessions.backends.db import Session
            from django.contrib.auth.models import AnonymousUser

            session = Session.objects.get(session_key=session_id)
            data = session.get_decoded()
            user_id = data.get("_auth_user_id")

            if user_id:
                from apps.users.models import User
                return User.objects.get(id=user_id)
            return AnonymousUser()
        except Exception:
            return None
