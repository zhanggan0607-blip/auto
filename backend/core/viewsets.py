"""
核心视图集模块 [已废弃]

此模块已废弃，请使用 common.views.base 替代。

迁移指南：
    # 旧代码 (已废弃)
    from core.viewsets import AuthenticatedModelViewSet, APIResponseMixin

    # 新代码 (推荐)
    from common.views.base import BaseViewSet  # 替代 AuthenticatedModelViewSet
    from common.views.base import APIResponseMixin  # 保持不变

    # 或直接使用 common.views (推荐)
    from common.views import BaseViewSet, APIResponseMixin

    # ViewSet命名对照：
    # - AuthenticatedModelViewSet  -> BaseViewSet
    # - AuthenticatedReadOnlyViewSet -> ReadOnlyModelViewSet
    # - ActionLoggingViewSet -> AuditViewSet

废弃日期: 2026-03-27
计划删除日期: 2026-06-27

此文件保留仅为向后兼容，不建议在新代码中使用。
"""
import warnings

warnings.warn(
    "core.viewsets is deprecated, use common.views.base instead. "
    "See migration guide in common/views/base.py",
    DeprecationWarning,
    stacklevel=2
)

# 为了保持向后兼容，重新导出 common.views 中的类
from common.views.base import (
    BaseViewSet,
    ReadOnlyModelViewSet,
    ToggleStatusViewSet,
    ExportViewSet,
    BulkActionViewSet,
    AuditViewSet,
    FullFeaturedViewSet,
    SoftDeleteViewSet,
    # 兼容类
    AuthenticatedModelViewSet,
    AuthenticatedReadOnlyViewSet,
    ActionLoggingViewSet,
    APIResponseMixin,
    ManualPermissionViewSet,
)

# 为了保持向后兼容，保留原始类名
# 但实际指向 common.views.base 中的类

__all__ = [
    'BaseViewSet',
    'ReadOnlyModelViewSet',
    'ToggleStatusViewSet',
    'ExportViewSet',
    'BulkActionViewSet',
    'AuditViewSet',
    'FullFeaturedViewSet',
    'SoftDeleteViewSet',
    'AuthenticatedModelViewSet',
    'AuthenticatedReadOnlyViewSet',
    'ActionLoggingViewSet',
    'APIResponseMixin',
    'ManualPermissionViewSet',
]
