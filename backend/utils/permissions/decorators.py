"""
权限装饰器
提供函数级别的权限验证装饰器
"""
from functools import wraps
from rest_framework.response import Response
from rest_framework import status


def require_auth(view_func):
    """
    要求用户已认证的装饰器

    使用示例:
        @require_auth
        def my_view(request):
            return Response({'data': 'success'})
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user or not request.user.is_authenticated:
            return Response(
                {'success': False, 'message': '用户未登录'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        return view_func(request, *args, **kwargs)
    return wrapper


def require_enterprise_owner(view_func):
    """
    要求用户是企业所有者的装饰器

    使用示例:
        @require_enterprise_owner
        def my_view(request, enterprise_id):
            return Response({'data': 'success'})
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        enterprise_id = kwargs.get('enterprise_id')
        if not enterprise_id:
            return Response(
                {'success': False, 'message': '请提供企业ID'},
                status=status.HTTP_400_BAD_REQUEST
            )

        from apps.enterprise.models import Enterprise

        try:
            enterprise = Enterprise.objects.get(id=enterprise_id)
        except Enterprise.DoesNotExist:
            return Response(
                {'success': False, 'message': '企业不存在'},
                status=status.HTTP_404_NOT_FOUND
            )

        from utils.permissions.enterprise import verify_enterprise_ownership

        if not verify_enterprise_ownership(request.user, enterprise):
            return Response(
                {'success': False, 'message': '无权限操作该企业'},
                status=status.HTTP_403_FORBIDDEN
            )

        return view_func(request, *args, **kwargs)
    return wrapper


def require_admin(view_func):
    """
    要求用户是管理员的装饰器

    使用示例:
        @require_admin
        def my_view(request):
            return Response({'data': 'success'})
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user or not request.user.is_authenticated:
            return Response(
                {'success': False, 'message': '用户未登录'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        if not request.user.is_admin():
            return Response(
                {'success': False, 'message': '需要管理员权限'},
                status=status.HTTP_403_FORBIDDEN
            )
        return view_func(request, *args, **kwargs)
    return wrapper