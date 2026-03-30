"""
公共View Mixins
提供通用的视图混入功能
"""
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend

from utils.responses import UnifiedResponse


class ListActionMixin:
    """
    列表查询混入
    提供统一的列表查询功能
    """

    list_serializer_class = None

    def list(self, request, *args, **kwargs):
        """统一列表查询"""
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return UnifiedResponse.success(data=serializer.data)


class CreateActionMixin:
    """
    创建操作混入
    提供统一的创建功能
    """

    def create(self, request, *args, **kwargs):
        """统一创建"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        return UnifiedResponse.success(
            data=serializer.data,
            message='创建成功',
            status_code=status.HTTP_201_CREATED
        )

    def perform_create(self, serializer):
        serializer.save()


class UpdateActionMixin:
    """
    更新操作混入
    提供统一的更新功能
    """

    def update(self, request, *args, **kwargs):
        """统一更新"""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        return UnifiedResponse.success(
            data=serializer.data,
            message='更新成功'
        )

    def partial_update(self, request, *args, **kwargs):
        """部分更新"""
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)

    def perform_update(self, serializer):
        serializer.save()


class DestroyActionMixin:
    """
    删除操作混入
    提供统一的删除功能
    """

    def destroy(self, request, *args, **kwargs):
        """统一删除"""
        instance = self.get_object()
        self.perform_destroy(instance)

        return UnifiedResponse.success(message='删除成功')

    def perform_destroy(self, instance):
        instance.delete()


class RetrieveActionMixin:
    """
    详情查询混入
    提供统一的详情查询功能
    """

    def retrieve(self, request, *args, **kwargs):
        """统一详情查询"""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return UnifiedResponse.success(data=serializer.data)


class ToggleStatusMixin:
    """
    切换状态混入
    提供启用/停用功能
    """

    def toggle_status(self, request, *args, **kwargs):
        """切换状态"""
        instance = self.get_object()

        if hasattr(instance, 'is_active'):
            instance.is_active = not instance.is_active
            instance.save(update_fields=['is_active'])

            status_text = '已启用' if instance.is_active else '已停用'
            return UnifiedResponse.success(
                data={'is_active': instance.is_active},
                message=status_text
            )

        return UnifiedResponse.error(message='该对象不支持状态切换')


class ExportMixin:
    """
    导出功能混入
    提供数据导出能力
    """

    export_types = ['csv', 'excel']

    def export(self, request, *args, **kwargs):
        """导出数据"""
        export_type = request.query_params.get('type', 'csv').lower()

        if export_type not in self.export_types:
            return UnifiedResponse.error(
                message=f'不支持的导出格式，请选择: {", ".join(self.export_types)}'
            )

        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)

        if export_type == 'csv':
            return self.export_csv(serializer.data)
        elif export_type == 'excel':
            return self.export_excel(serializer.data)

        return UnifiedResponse.error(message='导出失败')

    def export_csv(self, data):
        """导出CSV格式"""
        import csv
        from io import StringIO
        from django.http import HttpResponse

        output = StringIO()
        if data:
            writer = csv.DictWriter(output, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)

        response = HttpResponse(output.getvalue(), content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="export.csv"'
        return response

    def export_excel(self, data):
        """导出Excel格式"""
        return UnifiedResponse.error(message='Excel导出暂未实现')


class BulkActionMixin:
    """
    批量操作混入
    提供批量删除、批量更新等功能
    """

    def bulk_delete(self, request, *args, **kwargs):
        """批量删除"""
        ids = request.data.get('ids', [])

        if not ids:
            return UnifiedResponse.error(message='请选择要删除的数据')

        queryset = self.get_queryset().filter(id__in=ids)
        count, _ = queryset.delete()

        return UnifiedResponse.success(
            data={'deleted_count': count},
            message=f'成功删除 {count} 条数据'
        )

    def bulk_update(self, request, *args, **kwargs):
        """批量更新"""
        ids = request.data.get('ids', [])
        update_data = request.data.get('data', {})

        if not ids:
            return UnifiedResponse.error(message='请选择要更新的数据')

        if not update_data:
            return UnifiedResponse.error(message='请提供要更新的数据')

        queryset = self.get_queryset().filter(id__in=ids)
        updated_count = queryset.update(**update_data)

        return UnifiedResponse.success(
            data={'updated_count': updated_count},
            message=f'成功更新 {updated_count} 条数据'
        )


class FilterMixin:
    """
    过滤查询混入
    统一过滤、搜索、排序功能
    """

    search_fields = []
    ordering_fields = []
    filterset_fields = []

    def get_queryset(self):
        """获取过滤后的QuerySet"""
        queryset = super().get_queryset()

        for backend in self.filter_backends:
            queryset = backend().filter_queryset(self.request, queryset, self)

        return queryset


class AuditLogMixin:
    """
    审计日志混入
    记录操作日志
    """

    def get_logger(self):
        """获取日志记录器"""
        import logging
        return logging.getLogger(self.__class__.__module__)

    def log_action(self, action, instance=None, result='success', **kwargs):
        """记录操作日志"""
        logger = self.get_logger()

        user = self.request.user if hasattr(self.request, 'user') else None
        user_info = user.username if user else 'Anonymous'

        instance_info = f'{instance.__class__.__name__}(id={instance.id})' if instance else 'N/A'

        log_data = {
            'action': action,
            'user': user_info,
            'instance': instance_info,
            'result': result,
            **kwargs
        }

        if result == 'success':
            logger.info(f"[{self.__class__.__name__}] {action} {instance_info} by {user_info}")
        else:
            logger.error(f"[{self.__class__.__name__}] {action} {instance_info} by {user_info} failed: {kwargs.get('error')}")

    def create(self, request, *args, **kwargs):
        """创建并记录日志"""
        response = super().create(request, *args, **kwargs)
        if response.status_code == 201:
            self.log_action('create', result='success')
        return response

    def update(self, request, *args, **kwargs):
        """更新并记录日志"""
        response = super().update(request, *args, **kwargs)
        if response.status_code == 200:
            self.log_action('update', result='success')
        return response

    def destroy(self, request, *args, **kwargs):
        """删除并记录日志"""
        instance = self.get_object()
        response = super().destroy(request, *args, **kwargs)
        if response.status_code == 200:
            self.log_action('destroy', instance=instance, result='success')
        return response
