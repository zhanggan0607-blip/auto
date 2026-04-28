"""
敏感字段脱敏混入类
在模型序列化时自动对敏感字段进行脱敏处理
安全改进：统一管理敏感字段的脱敏规则
"""
import re
from typing import Any, Dict, List, Optional


SENSITIVE_FIELDS_CONFIG = {
    'credit_code': {'type': 'code', 'pattern': r'^([A-Z0-9]{2})\*\*\*\*([A-Z0-9]+)$', 'show_start': 2, 'show_end': 4},
    'bank_account': {'type': 'bank', 'show_start': 4, 'show_end': 4},
    'id_card': {'type': 'id', 'show_start': 3, 'show_end': 4},
    'phone': {'type': 'phone', 'show_start': 3, 'show_end': 4},
    'email': {'type': 'email', 'show_start': 2, 'show_end': 2},
    'address': {'type': 'address', 'show_start': 6, 'show_end': 4},
    'password': {'type': 'fixed', 'mask': '***'},
    'token': {'type': 'fixed', 'mask': '***'},
    'secret': {'type': 'fixed', 'mask': '***'},
    'api_key': {'type': 'fixed', 'mask': '***'},
    'access_key': {'type': 'fixed', 'mask': '***'},
}


class SensitiveFieldMasker:
    """
    敏感字段脱敏器
    """

    @staticmethod
    def mask_credit_code(value: str) -> str:
        """
        统一社会信用代码脱敏

        Args:
            value: 原始代码

        Returns:
            str: 脱敏后的代码
        """
        if not value or len(value) < 10:
            return '***'
        return f"{value[:2]}****{value[-4:]}"

    @staticmethod
    def mask_bank_account(value: str) -> str:
        """
        银行账号脱敏

        Args:
            value: 原始账号

        Returns:
            str: 脱敏后的账号
        """
        if not value or len(value) < 9:
            return '***'
        return f"{value[:4]}{'*' * (len(value) - 8)}{value[-4:]}"

    @staticmethod
    def mask_id_card(value: str) -> str:
        """
        身份证号脱敏

        Args:
            value: 原始身份证号

        Returns:
            str: 脱敏后的身份证号
        """
        if not value or len(value) < 8:
            return '***'
        return f"{value[:3]}{'*' * (len(value) - 7)}{value[-4:]}"

    @staticmethod
    def mask_phone(value: str) -> str:
        """
        手机号脱敏

        Args:
            value: 原始手机号

        Returns:
            str: 脱敏后的手机号
        """
        if not value or len(value) < 8:
            return '***'
        return f"{value[:3]}{'*' * (len(value) - 7)}{value[-4:]}"

    @staticmethod
    def mask_email(value: str) -> str:
        """
        邮箱脱敏

        Args:
            value: 原始邮箱

        Returns:
            str: 脱敏后的邮箱
        """
        if not value or '@' not in value:
            return '***'
        parts = value.split('@')
        if len(parts[0]) <= 2:
            masked_local = '***'
        else:
            masked_local = f"{parts[0][0]}{'*' * (len(parts[0]) - 2)}{parts[0][-1]}"
        return f"{masked_local}@{parts[1]}"

    @staticmethod
    def mask_address(value: str) -> str:
        """
        地址脱敏

        Args:
            value: 原始地址

        Returns:
            str: 脱敏后的地址
        """
        if not value or len(value) < 10:
            return '***'
        return f"{value[:6]}***{value[-4:]}"

    @staticmethod
    def mask_fixed(value: str) -> str:
        """
        固定值脱敏

        Args:
            value: 原始值

        Returns:
            str: 脱敏后的值
        """
        return '***'

    @classmethod
    def mask(cls, field_name: str, value: Any) -> str:
        """
        根据字段名脱敏

        Args:
            field_name: 字段名
            value: 原始值

        Returns:
            str: 脱敏后的值
        """
        if value is None:
            return None

        value_str = str(value)

        field_lower = field_name.lower()
        for key, config in SENSITIVE_FIELDS_CONFIG.items():
            if key in field_lower:
                mask_type = config.get('type')
                if mask_type == 'code':
                    return cls.mask_credit_code(value_str)
                elif mask_type == 'bank':
                    return cls.mask_bank_account(value_str)
                elif mask_type == 'id':
                    return cls.mask_id_card(value_str)
                elif mask_type == 'phone':
                    return cls.mask_phone(value_str)
                elif mask_type == 'email':
                    return cls.mask_email(value_str)
                elif mask_type == 'address':
                    return cls.mask_address(value_str)
                elif mask_type == 'fixed':
                    return '***'

        return value_str


class ModelSerializerMaskMixin:
    """
    模型序列化器脱敏混入类
    在序列化时自动对配置的敏感字段进行脱敏

    使用方式:
    ```python
    class EnterpriseSerializer(ModelSerializerMaskMixin, serializers.ModelSerializer):
        class Meta:
            model = Enterprise
            fields = ['name', 'credit_code', 'bank_account', 'legal_person_phone']

        sensitive_fields = ['credit_code', 'bank_account', 'legal_person_phone']
    ```
    """

    sensitive_fields: List[str] = []

    def to_representation(self, instance):
        """
        序列化时脱敏敏感字段
        """
        data = super().to_representation(instance)

        if not self.sensitive_fields:
            return data

        masked_data = {}
        for field_name, value in data.items():
            if field_name in self.sensitive_fields:
                masked_data[field_name] = SensitiveFieldMasker.mask(field_name, value)
            else:
                masked_data[field_name] = value

        return masked_data


def mask_dict_sensitive_fields(data: Dict, sensitive_fields: List[str]) -> Dict:
    """
    对字典中的敏感字段进行脱敏

    Args:
        data: 原始数据字典
        sensitive_fields: 敏感字段列表

    Returns:
        Dict: 脱敏后的数据
    """
    if not data or not sensitive_fields:
        return data

    result = {}
    for key, value in data.items():
        if key in sensitive_fields:
            result[key] = SensitiveFieldMasker.mask(key, value)
        elif isinstance(value, dict):
            result[key] = mask_dict_sensitive_fields(value, sensitive_fields)
        else:
            result[key] = value

    return result


def get_default_sensitive_fields() -> List[str]:
    """
    获取默认的敏感字段列表

    Returns:
        List[str]: 敏感字段列表
    """
    return [
        'credit_code',
        'bank_account',
        'id_card',
        'phone',
        'mobile',
        'email',
        'password',
        'token',
        'secret',
        'api_key',
        'access_key',
        'access_key_id',
        'access_key_secret',
    ]
