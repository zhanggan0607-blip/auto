"""
公共Serializer字段
提供统一的字段定义和自定义字段
"""
from rest_framework import serializers
from django.utils import timezone
from django.conf import settings


class TimestampField(serializers.Field):
    """
    Unix时间戳字段
    存储为整数，序列化/反序列化时自动转换
    """

    def to_representation(self, value):
        """DateTime转Unix时间戳"""
        if value is None:
            return None
        return int(value.timestamp())

    def to_internal_value(self, data):
        """Unix时间戳转DateTime"""
        if data is None:
            return None
        from datetime import datetime
        return datetime.fromtimestamp(data)


class FileUrlField(serializers.CharField):
    """
    文件URL字段
    自动生成文件的完整URL
    """

    def to_representation(self, value):
        """获取文件完整URL"""
        if not value:
            return None

        if hasattr(value, 'url'):
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(value.url)
            return value.url
        return value


class FileSizeField(serializers.IntegerField):
    """
    文件大小字段
    字节数转换为人类可读格式
    """

    def to_representation(self, value):
        """字节转KB/MB/GB"""
        if not value:
            return 0

        if value < 1024:
            return f"{value}B"
        elif value < 1024 * 1024:
            return f"{value / 1024:.1f}KB"
        elif value < 1024 * 1024 * 1024:
            return f"{value / 1024 / 1024:.1f}MB"
        else:
            return f"{value / 1024 / 1024 / 1024:.1f}GB"


class FlexibleDateField(serializers.Field):
    """
    灵活日期字段
    支持YYYY-MM-DD和Unix时间戳两种格式
    """

    def to_representation(self, value):
        """DateTime转字符串"""
        if value is None:
            return None
        if hasattr(value, 'strftime'):
            return value.strftime('%Y-%m-%d')
        return value

    def to_internal_value(self, data):
        """字符串或时间戳转Date"""
        if data is None:
            return None

        if isinstance(data, int):
            from datetime import datetime
            return datetime.fromtimestamp(data).date()

        from datetime import datetime
        return datetime.strptime(data, '%Y-%m-%d').date()


class JSONField(serializers.Field):
    """
    JSON字段
    确保返回的是dict/list而非字符串
    """

    def to_representation(self, value):
        if value is None:
            return {}
        if isinstance(value, (dict, list)):
            return value
        if isinstance(value, str):
            import json
            try:
                return json.loads(value)
            except Exception:
                return {}
        return {}

    def to_internal_value(self, data):
        if data is None:
            return {}
        if isinstance(data, (dict, list)):
            return data
        if isinstance(data, str):
            import json
            try:
                return json.loads(data)
            except Exception:
                return {}
        return {}


class ChoiceField(serializers.ChoiceField):
    """
    选择字段
    支持返回display名称
    """

    def __init__(self, *args, display_method='display', **kwargs):
        self.display_method = display_method
        super().__init__(*args, **kwargs)

    def to_representation(self, value):
        """返回value而非display名称"""
        if value is None:
            return None
        return value

    def to_native(self, value):
        """返回显示名称"""
        if value is None:
            return None
        return super().to_native(value)


class ReadOnlyField(serializers.Field):
    """
    只读字段
    只在响应中返回，提交时被忽略
    """

    def __init__(self, **kwargs):
        kwargs['read_only'] = True
        kwargs['required'] = False
        super().__init__(**kwargs)


class CreatedAtField(serializers.DateTimeField):
    """
    创建时间字段
    格式化为 YYYY-MM-DD HH:MM:SS
    """

    def __init__(self, **kwargs):
        kwargs['format'] = '%Y-%m-%d %H:%M:%S'
        kwargs['required'] = False
        kwargs['read_only'] = True
        super().__init__(**kwargs)


class UpdatedAtField(serializers.DateTimeField):
    """
    更新时间字段
    格式化为 YYYY-MM-DD HH:MM:SS
    """

    def __init__(self, **kwargs):
        kwargs['format'] = '%Y-%m-%d %H:%M:%S'
        kwargs['required'] = False
        kwargs['read_only'] = True
        super().__init__(**kwargs)


class ObjectIdField(serializers.IntegerField):
    """
    对象ID字段
    主键字段的简写
    """

    def __init__(self, **kwargs):
        kwargs['required'] = True
        super().__init__(**kwargs)


class UserIdField(serializers.IntegerField):
    """
    用户ID字段
    外键到User的简写
    """

    def __init__(self, **kwargs):
        kwargs['required'] = False
        kwargs['allow_null'] = True
        super().__init__(**kwargs)
