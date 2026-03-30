"""
权限基类
提供基础的DRF权限类
"""
from rest_framework import permissions


class IsAdminUser(permissions.BasePermission):
    """
    仅允许管理员访问
    """

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_admin()


class IsOwnerOrAdmin(permissions.BasePermission):
    """
    仅允许所有者或管理员访问
    """

    def has_object_permission(self, request, view, obj):
        if request.user.is_admin():
            return True
        return obj.user == request.user if hasattr(obj, 'user') else obj == request.user


class IsAuthenticated(permissions.BasePermission):
    """
    仅允许已认证用户访问
    """

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated