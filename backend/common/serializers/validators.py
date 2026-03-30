"""
公共Serializer验证器
提供统一的字段验证逻辑
"""
import re
from rest_framework import serializers
from django.core.validators import RegexValidator


phone_validator = RegexValidator(
    regex=r'^1[3-9]\d{9}$',
    message='请输入正确的手机号码'
)


def validate_phone(value):
    """验证手机号"""
    if not value:
        return value
    if not re.match(r'^1[3-9]\d{9}$', str(value)):
        raise serializers.ValidationError('请输入正确的手机号码')
    return value


def validate_credit_code(value):
    """验证统一社会信用代码"""
    if not value:
        return value
    if not re.match(r'^[0-9A-Z]{18}$', str(value)):
        raise serializers.ValidationError('请输入正确的统一社会信用代码（18位）')
    return value


def validate_id_card(value):
    """验证身份证号"""
    if not value:
        return value
    if not re.match(r'^[1-9]\d{5}(18|19|20)\d{2}(0[1-9]|1[0-2])(0[1-9]|[12]\d|3[01])\d{3}[\dXx]$', str(value)):
        raise serializers.ValidationError('请输入正确的身份证号码')
    return value


def validate_bank_account(value):
    """验证银行卡号（ Luhm算法）"""
    if not value:
        return value
    value = str(value).replace(' ', '')

    if not value.isdigit() or len(value) < 16 or len(value) > 19:
        raise serializers.ValidationError('请输入正确的银行卡号')

    total = 0
    for i, digit in enumerate(reversed(value)):
        n = int(digit)
        if i % 2 == 1:
            n *= 2
            if n > 9:
                n -= 9
        total += n

    if total % 10 != 0:
        raise serializers.ValidationError('请输入正确的银行卡号')

    return value


def validate_url(value):
    """验证URL格式"""
    if not value:
        return value
    url_pattern = re.compile(
        r'^https?://'
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'
        r'localhost|'
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
        r'(?::\d+)?'
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)

    if not url_pattern.match(str(value)):
        raise serializers.ValidationError('请输入正确的URL地址')
    return value


def validate_positive_integer(value):
    """验证正整数"""
    if value is None:
        return value
    if not isinstance(value, int) or value <= 0:
        raise serializers.ValidationError('请输入正整数')
    return value


def validate_percentage(value):
    """验证百分比（0-100）"""
    if value is None:
        return value
    if not isinstance(value, (int, float)) or value < 0 or value > 100:
        raise serializers.ValidationError('请输入0-100之间的百分比值')
    return value


def validate_date_range(start_field='start_date', end_field='end_date'):
    """
    生成日期范围验证器
    结束日期必须大于等于开始日期

    使用方式：
        class MySerializer(serializers.Serializer):
            start_date = serializers.DateField()
            end_date = serializers.DateField()

            def validate(self, attrs):
                validate = validate_date_range('start_date', 'end_date')
                return validate(attrs)
    """
    def validator(attrs):
        start = attrs.get(start_field)
        end = attrs.get(end_field)

        if start and end and end < start:
            raise serializers.ValidationError({
                end_field: '结束日期必须大于等于开始日期'
            })

        return attrs

    return validator


class DateRangeValidator:
    """
    日期范围验证器类
    更灵活的日期范围验证
    """

    def __init__(self, start_field='start_date', end_field='end_date', allow_equal=True):
        self.start_field = start_field
        self.end_field = end_field
        self.allow_equal = allow_equal

    def __call__(self, attrs):
        start = attrs.get(self.start_field)
        end = attrs.get(self.end_field)

        if start and end:
            if self.allow_equal and end < start:
                raise serializers.ValidationError({
                    self.end_field: '结束日期必须大于等于开始日期'
                })
            elif not self.allow_equal and end <= start:
                raise serializers.ValidationError({
                    self.end_field: '结束日期必须大于开始日期'
                })

        return attrs
