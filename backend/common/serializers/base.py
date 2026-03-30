"""
公共Serializer基类
为业务Serializer提供统一的基础功能
"""
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from django.db.models import QuerySet

from .fields import (
    TimestampField,
    FileUrlField,
    FileSizeField,
    FlexibleDateField,
    JSONField,
    CreatedAtField,
    UpdatedAtField,
)
from .validators import (
    validate_phone,
    validate_credit_code,
    validate_url,
    validate_date_range,
)


class BaseSerializer(serializers.Serializer):
    """
    基础Serializer基类
    提供通用配置和辅助方法
    """

    def to_representation(self, instance):
        """
        统一序列化逻辑
        """
        ret = super().to_representation(instance)

        if hasattr(self, 'custom_fields') and self.custom_fields:
            for field in self.custom_fields:
                if field not in ret:
                    ret[field] = None

        return ret


class BaseModelSerializer(serializers.ModelSerializer):
    """
    基础ModelSerializer基类

    已集成的功能：
    - 自动处理created_at/updated_at只读
    - 自动处理created_by/updated_by用户追踪
    - 提供统一的时间戳格式

    使用示例：
        class EnterpriseSerializer(BaseModelSerializer):
            class Meta:
                model = Enterprise
                fields = ['id', 'name', 'created_at', 'updated_at']
    """

    created_at = CreatedAtField(required=False)
    updated_at = UpdatedAtField(required=False)

    def create(self, validated_data):
        """创建时自动设置创建人"""
        request = self.context.get('request')
        if request and hasattr(request, 'user') and request.user.is_authenticated:
            validated_data['created_by'] = request.user
        return super().create(validated_data)

    def update(self, instance, validated_data):
        """更新时自动设置更新人"""
        request = self.context.get('request')
        if request and hasattr(request, 'user') and request.user.is_authenticated:
            validated_data['updated_by'] = request.user
        return super().update(instance, validated_data)


class ListSerializer(serializers.ListSerializer):
    """
    列表序列化器基类
    支持批量操作
    """

    def update(self, instance, validated_data):
        """批量更新"""
        instance_mapping = {item.id: item for item in instance}
        ret = []

        for data in validated_data:
            if 'id' in data:
                item = instance_mapping.get(data['id'])
                if item:
                    ret.append(self.child.update(item, data))
                else:
                    ret.append(self.child.create(data))
            else:
                ret.append(self.child.create(data))

        return ret

    def to_representation(self, data):
        """优化列表序列化"""
        if isinstance(data, QuerySet):
            data = list(data)
        return super().to_representation(data)


class NestedListSerializer(BaseModelSerializer):
    """
    嵌套列表序列化器
    支持在列表视图中返回简要信息，在详情视图中返回完整信息

    使用示例：
        class QualificationSerializer(NestedListSerializer):
            enterprise = EnterpriseSummarySerializer(read_only=True)

            class Meta:
                model = EnterpriseQualification
                fields = ['id', 'qualification_name', 'enterprise']

            def get_list_fields(self):
                return ['id', 'qualification_name']

            def get_detail_fields(self):
                return ['id', 'qualification_name', 'enterprise']
    """

    def to_representation(self, instance):
        """根据上下文自动选择简要或完整字段"""
        if self.context.get('list_view', False):
            fields = self.get_list_fields()
        else:
            fields = self.get_detail_fields()

        return self.get_serializer(instance, fields=fields).data

    def get_list_fields(self):
        """获取列表视图字段"""
        meta = getattr(self, 'Meta', None)
        if meta and hasattr(meta, 'fields'):
            return meta.fields
        return []

    def get_detail_fields(self):
        """获取详情视图字段"""
        return self.get_list_fields()


class SummarySerializer(BaseModelSerializer):
    """
    摘要序列化器
    用于列表展示的简要信息

    使用示例：
        class EnterpriseSummarySerializer(SummarySerializer):
            class Meta:
                model = Enterprise
                fields = ['id', 'name', 'enterprise_type']
    """
    pass


class DetailSerializer(BaseModelSerializer):
    """
    详情序列化器
    用于详情页面展示的完整信息
    """
    pass


class CreateSerializer(BaseModelSerializer):
    """
    创建专用序列化器
    只包含创建时需要的字段
    """
    pass


class UpdateSerializer(BaseModelSerializer):
    """
    更新专用序列化器
    包含更新时需要的字段
    """
    pass


class PaginatedSerializer(serializers.Serializer):
    """
    分页响应序列化器
    统一分页数据格式

    使用示例：
        class EnterpriseListSerializer(PaginatedSerializer):
            class Meta:
                resource_serializer = EnterpriseSummarySerializer
                resource_name = 'enterprises'
    """

    def __init__(self, *args, **kwargs):
        self.resource_serializer = kwargs.pop('resource_serializer', None)
        self.resource_name = kwargs.pop('resource_name', 'items')
        super().__init__(*args, **kwargs)

    @classmethod
    def from_queryset(cls, queryset, page=1, page_size=20, request=None):
        """从QuerySet生成分页数据"""
        total = queryset.count()
        start = (page - 1) * page_size
        end = start + page_size

        items = queryset[start:end]

        if cls.resource_serializer:
            serializer = cls.resource_serializer(items, many=True, context={'request': request})
            items_data = serializer.data
        else:
            items_data = list(items)

        return {
            cls.resource_name: items_data,
            'pagination': {
                'page': page,
                'page_size': page_size,
                'total': total,
                'total_pages': (total + page_size - 1) // page_size if page_size > 0 else 0
            }
        }
