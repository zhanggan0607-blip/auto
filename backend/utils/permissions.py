"""
自定义权限模块 - 向后兼容导入
已拆分为 permissions/ 子目录
推荐使用: from utils.permissions import ...
"""
from utils.permissions.base import IsAdminUser, IsOwnerOrAdmin, IsAuthenticated
from utils.permissions.enterprise import (
    IsEnterpriseOwner,
    verify_enterprise_ownership,
    verify_enterprise_list_ownership,
    can_modify_enterprise,
    can_access_enterprise,
)

__all__ = [
    'IsAdminUser',
    'IsOwnerOrAdmin',
    'IsAuthenticated',
    'IsEnterpriseOwner',
    'verify_enterprise_ownership',
    'verify_enterprise_list_ownership',
    'can_modify_enterprise',
    'can_access_enterprise',
]