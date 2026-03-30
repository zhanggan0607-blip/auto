"""
企业权限模块
提供企业相关的权限验证功能
安全改进：修复has_permission逻辑bug，添加全局租户边界校验
"""
from rest_framework import permissions


class IsEnterpriseOwner(permissions.BasePermission):
    """
    验证用户是否为企业的所有者
    仅企业创建者或管理员可以操作该企业
    安全修复：has_permission必须返回False由has_object_permission判断
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.is_admin():
            return True
        return False

    def has_object_permission(self, request, view, obj):
        if request.user.is_admin():
            return True
        if hasattr(obj, 'created_by'):
            return obj.created_by == request.user
        if hasattr(obj, 'enterprise'):
            return obj.enterprise.created_by == request.user
        return False


def verify_enterprise_ownership(user, enterprise, allow_admin=True):
    """
    验证用户是否为企业的所有者

    Args:
        user: 用户对象
        enterprise: 企业对象
        allow_admin: 是否允许管理员操作

    Returns:
        bool: 是否验证通过
    """
    if not user or not user.is_authenticated:
        return False

    if allow_admin and (user.is_admin() or user.is_staff):
        return True

    if hasattr(enterprise, 'created_by'):
        return enterprise.created_by == user

    return False


def verify_enterprise_list_ownership(user, enterprise_ids):
    """
    批量验证用户是否拥有指定企业的操作权限

    Args:
        user: 用户对象
        enterprise_ids: 企业ID列表

    Returns:
        set: 用户有权操作的企业ID集合
    """
    from apps.enterprise.models import Enterprise

    if not user or not user.is_authenticated:
        return set()

    if user.is_admin() or user.is_staff:
        return set(enterprise_ids)

    owned = set(
        Enterprise.objects.filter(
            id__in=enterprise_ids,
            created_by=user
        ).values_list('id', flat=True)
    )

    return owned


def can_modify_enterprise(user, enterprise_id):
    """
    检查用户是否可以修改指定企业

    Args:
        user: 用户对象
        enterprise_id: 企业ID

    Returns:
        tuple: (can_modify: bool, reason: str)
    """
    from apps.enterprise.models import Enterprise

    if not user or not user.is_authenticated:
        return False, "用户未登录"

    if user.is_admin() or user.is_staff:
        return True, ""

    try:
        enterprise = Enterprise.objects.get(id=enterprise_id)
    except Enterprise.DoesNotExist:
        return False, "企业不存在"

    if enterprise.created_by != user:
        return False, "无权限操作该企业"

    return True, ""


def can_access_enterprise(user, enterprise_id):
    """
    检查用户是否可以访问指定企业

    Args:
        user: 用户对象
        enterprise_id: 企业ID

    Returns:
        tuple: (can_access: bool, reason: str)
    """
    from apps.enterprise.models import Enterprise

    if not user or not user.is_authenticated:
        return False, "用户未登录"

    if user.is_admin() or user.is_staff:
        return True, ""

    try:
        enterprise = Enterprise.objects.get(id=enterprise_id)
    except Enterprise.DoesNotExist:
        return False, "企业不存在"

    if enterprise.created_by != user:
        return False, "无权限访问该企业"

    return True, ""