"""
公共ViewSet基类
统一所有业务ViewSet的基类，整合core/viewsets.py的功能

职责：
- 提供统一响应格式
- 提供用户数据隔离
- 提供通用Mixin功能
- 替代 core/viewsets.py 的所有功能

使用规范：
1. 标准业务ViewSet继承 BaseViewSet
2. 如需日志记录功能，继承 AuditViewSet
3. 如需只读功能，继承 ReadOnlyModelViewSet
4. 如需组合使用，可用 APIResponseMixin + viewsets.ModelViewSet

从 core.viewsets 迁移：
    # 旧代码
    from core.viewsets import AuthenticatedModelViewSet
    class MyViewSet(AuthenticatedModelViewSet):

    # 新代码
    from common.views.base import BaseViewSet
    class MyViewSet(BaseViewSet):
"""
import logging
from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend

from utils.responses import UnifiedResponse
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
)


class BaseViewSet(
    ListActionMixin,
    CreateActionMixin,
    UpdateActionMixin,
    DestroyActionMixin,
    RetrieveActionMixin,
    viewsets.ModelViewSet,
):
    """
    基础ViewSet基类

    自动集成功能：
    - 统一响应格式
    - 列表查询
    - 创建操作
    - 更新操作
    - 删除操作
    - 详情查询
    - 分页支持
    - 过滤支持

    使用示例：
        class EnterpriseViewSet(BaseViewSet):
            serializer_class = EnterpriseSerializer
            queryset = Enterprise.objects.all()
            filter_backends = [SearchFilter, OrderingFilter, DjangoFilterBackend]
            search_fields = ['name', 'credit_code']
            ordering_fields = ['created_at', 'name']
    """
    permission_classes = [IsAuthenticated]
    filter_backends = [SearchFilter, OrderingFilter, DjangoFilterBackend]
    pagination_class = None

    def get_queryset(self):
        """自动过滤当前用户数据"""
        queryset = super().get_queryset()
        if hasattr(self.request, 'user') and self.request.user.is_authenticated:
            if hasattr(queryset.model, 'user'):
                queryset = queryset.filter(user=self.request.user)
        return queryset


class ReadOnlyModelViewSet(
    ListActionMixin,
    RetrieveActionMixin,
    viewsets.ReadOnlyModelViewSet,
):
    """
    只读ViewSet基类

    适用于公开的只读资源
    """
    permission_classes = [IsAuthenticated]
    filter_backends = [SearchFilter, OrderingFilter, DjangoFilterBackend]


class ToggleStatusViewSet(BaseViewSet, ToggleStatusMixin):
    """
    支持状态切换的ViewSet基类

    新增Action：
    - toggle_status: 切换启用/停用状态
    """
    pass


class ExportViewSet(BaseViewSet, ExportMixin):
    """
    支持导出的ViewSet基类

    新增Action：
    - export: 导出数据（CSV/Excel）
    """
    pass


class BulkActionViewSet(BaseViewSet, BulkActionMixin):
    """
    支持批量操作的ViewSet基类

    新增Action：
    - bulk_delete: 批量删除
    - bulk_update: 批量更新
    """
    pass


class AuditViewSet(BaseViewSet, AuditLogMixin):
    """
    支持审计日志的ViewSet基类

    自动记录以下操作：
    - create
    - update
    - destroy
    """
    pass


class FullFeaturedViewSet(
    BaseViewSet,
    ToggleStatusMixin,
    ExportMixin,
    BulkActionMixin,
    AuditLogMixin,
):
    """
    全功能ViewSet基类

    集成所有公共Mixin，适合大多数业务场景
    """
    pass


class SoftDeleteViewSet(BaseViewSet):
    """
    软删除ViewSet基类

    支持软删除和恢复功能
    """

    def get_queryset(self):
        """默认排除已删除的数据"""
        queryset = super().get_queryset()
        if hasattr(queryset.model, 'is_deleted'):
            return queryset.filter(is_deleted=False)
        return queryset

    def perform_destroy(self, instance):
        """执行软删除而非真正删除"""
        if hasattr(instance, 'soft_delete'):
            instance.soft_delete()
        else:
            instance.delete()

    @staticmethod
    def restore(request, *args, **kwargs):
        """恢复已删除的数据"""
        return UnifiedResponse.error(message='恢复功能暂未实现')


class AuthenticatedModelViewSet(BaseViewSet):
    """
    已认证的ModelViewSet基类（兼容旧代码）

    建议使用 BaseViewSet 替代

    自动添加以下功能：
    - IsAuthenticated 权限验证
    - 统一响应格式 { success, code, message, data }
    - SearchFilter 搜索过滤
    - OrderingFilter 排序
    - DjangoFilterBackend 过滤
    """
    pass


class AuthenticatedReadOnlyViewSet(ReadOnlyModelViewSet):
    """
    已认证的只读ViewSet基类（兼容旧代码）

    建议使用 ReadOnlyModelViewSet 替代

    自动添加以下功能：
    - IsAuthenticated 权限验证
    - 统一响应格式
    - SearchFilter 搜索过滤
    - OrderingFilter 排序
    """
    pass


class ActionLoggingViewSet(AuditViewSet):
    """
    带日志记录的ViewSet基类（兼容旧代码）

    建议使用 AuditViewSet 替代

    继承此类的ViewSet会自动：
    - 继承BaseViewSet的所有功能
    - 记录操作日志
    """
    pass


class APIResponseMixin:
    """
    API响应格式混合类（兼容旧代码）

    为ViewSet提供统一的响应格式，可与其他ViewSet基类组合使用
    注意：此Mixin不包含权限验证，如需权限验证请使用 BaseViewSet

    使用方式：
        class MyViewSet(APIResponseMixin, viewsets.ModelViewSet):
            permission_classes = [IsAuthenticated]
            pass
    """

    def list(self, request, *args, **kwargs):
        """重写list方法，使用自定义响应格式"""
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return UnifiedResponse.success(data=serializer.data)

    def retrieve(self, request, *args, **kwargs):
        """重写retrieve方法，使用自定义响应格式"""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return UnifiedResponse.success(data=serializer.data)

    def create(self, request, *args, **kwargs):
        """重写create方法，使用自定义响应格式"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return UnifiedResponse.success(
            data=serializer.data,
            message='创建成功',
            status_code=status.HTTP_201_CREATED
        )

    def update(self, request, *args, **kwargs):
        """重写update方法，使用自定义响应格式"""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return UnifiedResponse.success(data=serializer.data, message='更新成功')

    def destroy(self, request, *args, **kwargs):
        """重写destroy方法，使用自定义响应格式"""
        instance = self.get_object()
        self.perform_destroy(instance)
        return UnifiedResponse.success(message='删除成功')


class ManualPermissionViewSet(APIResponseMixin, viewsets.ModelViewSet):
    """
    手动权限控制ViewSet基类

    适用于需要自定义权限逻辑的场景
    不自动添加任何权限，需要子类显式指定
    """
    permission_classes = []

    def get_queryset(self):
        queryset = super().get_queryset()
        if hasattr(self.request, 'user') and self.request.user.is_authenticated:
            if hasattr(queryset.model, 'user'):
                queryset = queryset.filter(user=self.request.user)
        return queryset
