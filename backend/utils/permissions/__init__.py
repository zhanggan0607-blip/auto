"""
自定义权限模块
统一管理所有权限类、装饰器和验证函数
"""
from .base import (
    IsAdminUser,
    IsOwnerOrAdmin,
    IsAuthenticated,
)
from .enterprise import (
    IsEnterpriseOwner,
    verify_enterprise_ownership,
    verify_enterprise_list_ownership,
    can_modify_enterprise,
    can_access_enterprise,
)
from .decorators import require_enterprise_owner, require_auth, require_admin

__all__ = [
    'IsAdminUser',
    'IsOwnerOrAdmin',
    'IsAuthenticated',
    'IsEnterpriseOwner',
    'verify_enterprise_ownership',
    'verify_enterprise_list_ownership',
    'can_modify_enterprise',
    'can_access_enterprise',
    'require_enterprise_owner',
    'require_auth',
    'require_admin',
]