"""
公共视图模块
统一导出所有公共视图组件
"""

from .base import (
    BaseViewSet,
    ReadOnlyModelViewSet,
    ToggleStatusViewSet,
    ExportViewSet,
    BulkActionViewSet,
    AuditViewSet,
    FullFeaturedViewSet,
    SoftDeleteViewSet,
    # 兼容旧代码 (从 core.viewsets 迁移)
    AuthenticatedModelViewSet,
    AuthenticatedReadOnlyViewSet,
    ActionLoggingViewSet,
    APIResponseMixin,
    ManualPermissionViewSet,
)

from .mixins import (
    ListActionMixin,
    CreateActionMixin,
    UpdateActionMixin,
    DestroyActionMixin,
    RetrieveActionMixin,
    ToggleStatusMixin,
    ExportMixin,
    BulkActionMixin,
    AuditLogMixin,
    FilterMixin,
)

__all__ = [
    # ViewSet基类 (推荐使用)
    'BaseViewSet',
    'ReadOnlyModelViewSet',
    'ToggleStatusViewSet',
    'ExportViewSet',
    'BulkActionViewSet',
    'AuditViewSet',
    'FullFeaturedViewSet',
    'SoftDeleteViewSet',
    # Mixin混入类
    'ListActionMixin',
    'CreateActionMixin',
    'UpdateActionMixin',
    'DestroyActionMixin',
    'RetrieveActionMixin',
    'ToggleStatusMixin',
    'ExportMixin',
    'BulkActionMixin',
    'AuditLogMixin',
    'FilterMixin',
    # 兼容旧代码 (从 core.viewsets 迁移，2026-03-27)
    'AuthenticatedModelViewSet',
    'AuthenticatedReadOnlyViewSet',
    'ActionLoggingViewSet',
    'APIResponseMixin',
    'ManualPermissionViewSet',
]
