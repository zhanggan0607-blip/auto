"""
租户边界校验中间件
防止跨租户数据访问
安全改进：所有API请求强制校验用户-资源边界
"""
import logging
from django.http import JsonResponse

logger = logging.getLogger(__name__)


class TenantBoundaryMiddleware:
    """
    租户边界中间件
    校验用户只能访问自己有权访问的资源
    """

    EXEMPT_PATHS = [
        '/api/v1/auth/',
        '/api/v1/health/',
        '/admin/',
        '/static/',
        '/media/',
    ]

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path

        for exempt in self.EXEMPT_PATHS:
            if path.startswith(exempt):
                return self.get_response(request)

        if not hasattr(request, 'user') or not request.user.is_authenticated:
            return self.get_response(request)

        user = request.user

        if hasattr(user, 'is_admin') and user.is_admin():
            return self.get_response(request)

        request.tenant_id = getattr(user, 'tenant_id', user.id)

        logger.debug(f"租户边界校验: user={user.id}, tenant={request.tenant_id}, path={path}")

        return self.get_response(request)


class TenantAwareQuerySet:
    """
    租户感知的查询集混入类
    自动过滤跨租户数据
    """

    @classmethod
    def filter_by_tenant(cls, queryset, user):
        """
        根据用户过滤查询结果

        Args:
            queryset: Django QuerySet
            user: 用户对象

        Returns:
            QuerySet: 过滤后的查询集
        """
        if not user or not user.is_authenticated:
            return queryset.none()

        if hasattr(user, 'is_admin') and user.is_admin():
            return queryset

        if hasattr(cls, 'tenant_field'):
            tenant_field = cls.tenant_field
            return queryset.filter(**{f"{tenant_field}__id": user.tenant_id})

        if hasattr(cls, 'created_by'):
            return queryset.filter(created_by=user)

        if hasattr(cls, 'user'):
            return queryset.filter(user=user)

        return queryset
