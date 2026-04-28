"""
统一权限管理模块

整合 DRF 权限类和自定义权限验证函数

使用示例：
    # DRF 权限类
    from common.utils.permissions import IsAdminUser, IsOwnerOrAdmin, IsEnterpriseOwner

    class MyViewSet(BaseViewSet):
        permission_classes = [IsAuthenticated, IsAdminUser]

    # 权限验证函数
    from common.utils.permissions import verify_enterprise_ownership

    can_access, reason = verify_enterprise_ownership(user, enterprise)

    # 函数装饰器
    from common.utils.permissions import require_auth, require_admin

    @require_auth
    def my_view(request):
        ...

迁移指南：
    # 旧代码
    from utils.permissions import IsOwnerOrAdmin
    from utils.permissions.enterprise import verify_enterprise_ownership

    # 新代码（统一入口）
    from common.utils.permissions import IsOwnerOrAdmin, verify_enterprise_ownership
"""
from rest_framework import permissions

from utils.permissions.base import (
    IsAdminUser,
    IsOwnerOrAdmin,
    IsAuthenticated,
)
from utils.permissions.enterprise import (
    IsEnterpriseOwner,
    verify_enterprise_ownership,
    verify_enterprise_list_ownership,
    can_modify_enterprise,
    can_access_enterprise,
)
from utils.permissions.decorators import (
    require_auth,
    require_admin,
    require_enterprise_owner,
)

__all__ = [
    # DRF 权限基类
    'permissions',
    # utils.permissions.base 导出
    'IsAdminUser',
    'IsOwnerOrAdmin',
    'IsAuthenticated',
    # utils.permissions.enterprise 导出
    'IsEnterpriseOwner',
    'verify_enterprise_ownership',
    'verify_enterprise_list_ownership',
    'can_modify_enterprise',
    'can_access_enterprise',
    # utils.permissions.decorators 导出
    'require_auth',
    'require_admin',
    'require_enterprise_owner',
]
