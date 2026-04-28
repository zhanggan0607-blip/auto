"""
共享验证规则加载器
从JSON Schema加载验证规则，供前后端使用

使用方式：
    from common.schemas.validation_loader import ValidationLoader

    loader = ValidationLoader()
    rules = loader.get_entity_rules('enterprise')
    validator = loader.get_validator('credit_code')
"""
import json
import os
from typing import Any, Dict, List, Optional

from django.conf import settings


class ValidationLoader:
    """
    验证规则加载器
    从JSON Schema文件加载验证规则
    """

    _instance = None
    _schema_cache: Dict[str, Any] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, '_initialized'):
            self._initialized = True
            self._load_schema()

    def _load_schema(self):
        """加载验证规则Schema"""
        schema_path = os.path.join(
            os.path.dirname(__file__),
            'validation_rules.json'
        )

        if os.path.exists(schema_path):
            with open(schema_path, 'r', encoding='utf-8') as f:
                self._schema_cache = json.load(f)
        else:
            self._schema_cache = {}

    def get_definition(self, name: str) -> Optional[Dict]:
        """获取基础类型定义"""
        return self._schema_cache.get('definitions', {}).get(name)

    def get_entity_rules(self, entity_name: str) -> Dict:
        """获取实体验证规则"""
        return self._schema_cache.get('entities', {}).get(entity_name, {})

    def get_validator(self, type_name: str) -> Optional[Dict]:
        """获取类型验证器"""
        return self.get_definition(type_name)

    def get_all_definitions(self) -> Dict:
        """获取所有基础类型定义"""
        return self._schema_cache.get('definitions', {})

    def get_all_entities(self) -> List[str]:
        """获取所有实体名称"""
        return list(self._schema_cache.get('entities', {}).keys())

    def to_drf_validators(self, entity_name: str) -> Dict[str, List[Dict]]:
        """
        将验证规则转换为DRF Validator格式

        Returns:
            Dict: 字段名到验证器列表的映射
        """
        rules = self.get_entity_rules(entity_name)
        drf_validators = {}

        for field_name, rule in rules.items():
            validators = []

            if 'required' in rule and rule['required']:
                validators.append({
                    'type': 'required'
                })

            if 'type' in rule:
                validators.append({
                    'type': 'type',
                    'value': rule['type']
                })

            if 'minLength' in rule:
                validators.append({
                    'type': 'min_length',
                    'value': rule['minLength']
                })

            if 'maxLength' in rule:
                validators.append({
                    'type': 'max_length',
                    'value': rule['maxLength']
                })

            if 'pattern' in rule:
                validators.append({
                    'type': 'regex',
                    'value': rule['pattern']
                })

            if 'minimum' in rule:
                validators.append({
                    'type': 'min',
                    'value': rule['minimum']
                })

            if 'maximum' in rule:
                validators.append({
                    'type': 'max',
                    'value': rule['maximum']
                })

            if 'enum' in rule:
                validators.append({
                    'type': 'choices',
                    'value': rule['enum']
                })

            if validators:
                drf_validators[field_name] = validators

        return drf_validators

    def to_typescript_validation(self, entity_name: str) -> str:
        """
        将验证规则转换为TypeScript接口定义

        Returns:
            str: TypeScript接口代码
        """
        rules = self.get_entity_rules(entity_name)
        lines = [
            f"export interface {entity_name.title()}ValidationRules {{"
        ]

        for field_name, rule in rules.items():
            optional = '' if rule.get('required', False) else '?'
            ts_type = self._to_ts_type(rule.get('type'), rule.get('format'), rule.get('enum'))

            constraints = []
            if 'minLength' in rule:
                constraints.append(f"minLength: {rule['minLength']}")
            if 'maxLength' in rule:
                constraints.append(f"maxLength: {rule['maxLength']}")
            if 'minimum' in rule:
                constraints.append(f"minimum: {rule['minimum']}")
            if 'maximum' in rule:
                constraints.append(f"maximum: {rule['maximum']}")
            if 'pattern' in rule:
                constraints.append(f"pattern: '{rule['pattern']}'")

            if constraints:
                lines.append(f"  {field_name}{optional}: {{ type: {ts_type}, {', '.join(constraints)} }};")
            else:
                lines.append(f"  {field_name}{optional}: {ts_type};")

        lines.append('}')
        return '\n'.join(lines)

    def _to_ts_type(self, type_name: str, format_type: str = None, enum_values: List = None) -> str:
        """将规则类型转换为TypeScript类型"""
        if enum_values:
            return ' | '.join(f"'{v}'" for v in enum_values)

        type_mapping = {
            'string': 'string',
            'integer': 'number',
            'number': 'number',
            'boolean': 'boolean',
        }

        if format_type == 'date':
            return 'string (YYYY-MM-DD)'
        elif format_type == 'date-time':
            return 'string (ISO 8601)'
        elif format_type == 'email':
            return 'string (email)'
        elif format_type == 'uri':
            return 'string (url)'

        return type_mapping.get(type_name, 'any')


validation_loader = ValidationLoader()
