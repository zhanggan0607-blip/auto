"""
Django REST Framework Serializer 到 TypeScript 类型转换工具

用法:
    python -m scripts.generate_ts_types --apps tenders,enterprise,crawler

功能:
    1. 分析 Django REST Framework Serializer
    2. 生成 TypeScript 类型定义
    3. 支持嵌套类型和关联字段
    4. 支持 Choice 字段转换为联合类型
"""

import argparse
import importlib
import os
import re
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Type

import django

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from django.db import models
from rest_framework import serializers


class TypeMapping:
    """Django/DRF 类型到 TypeScript 类型的映射"""

    BASIC_MAPPING = {
        'CharField': 'string',
        'TextField': 'string',
        'SlugField': 'string',
        'URLField': 'string',
        'EmailField': 'string',
        'UUIDField': 'string',
        'IPAddressField': 'string',

        'IntegerField': 'number',
        'BigIntegerField': 'number',
        'SmallIntegerField': 'number',
        'PositiveIntegerField': 'number',
        'PositiveSmallIntegerField': 'number',
        'FloatField': 'number',
        'DecimalField': 'number',

        'BooleanField': 'boolean',
        'NullBooleanField': 'boolean',

        'DateField': 'string',
        'DateTimeField': 'string',
        'TimeField': 'string',
        'DurationField': 'string',

        'BinaryField': 'string',
        'JSONField': 'Record<string, any>',
        'DictField': 'Record<string, any>',
        'ListField': 'any[]',

        'FileField': 'string',
        'ImageField': 'string',
    }

    @classmethod
    def get_ts_type(cls, field_class: str, field: Any = None) -> str:
        if field_class in cls.BASIC_MAPPING:
            return cls.BASIC_MAPPING[field_class]

        if hasattr(field, 'choices') and field.choices:
            choices = list(field.choices.keys())
            if all(isinstance(k, (int, float)) for k in choices):
                return 'number'
            quoted_choices = [f"'{c}'" for c in choices]
            return ' | '.join(quoted_choices)

        if 'Field' in field_class:
            return 'any'

        return 'any'


class SerializerAnalyzer:
    """Serializer 分析器"""

    def __init__(self, serializer_class: Type[serializers.Serializer]):
        self.serializer_class = serializer_class
        self.serializer = serializer_class()
        self.fields = self.serializer.fields
        self.defined_types: Dict[str, str] = {}

    def get_field_info(self, field_name: str, field: Any) -> Dict[str, Any]:
        info = {
            'name': field_name,
            'required': getattr(field, 'required', False),
            'read_only': getattr(field, 'read_only', False),
            'nullable': not getattr(field, 'required', True),
            'default': getattr(field, 'default', None),
        }

        field_class = field.__class__.__name__

        if hasattr(field, 'child'):
            info['is_list'] = True
            info['item_type'] = self._get_type_from_field(field.child)
            field = field.child
            field_class = field.__class__.__name__

        if hasattr(field, 'fields'):
            info['is_nested'] = True
            info['nested_fields'] = field.__class__.__name__
        elif hasattr(field, 'choices') and field.choices:
            info['choices'] = list(field.choices.keys())
        elif hasattr(field, 'serializer_kwargs'):
            related_model = field.serializer_kwargs.get('model') or getattr(field, 'model', None)
            if related_model:
                info['is_related'] = True
                info['related_name'] = related_model.__name__
        elif hasattr(field, 'Meta') and hasattr(field.Meta, 'model'):
            info['is_related'] = True
            info['related_name'] = field.Meta.model.__name__

        info['ts_type'] = TypeMapping.get_ts_type(field_class, field)

        return info

    def _get_type_from_field(self, field: Any) -> str:
        field_class = field.__class__.__name__

        if hasattr(field, 'child'):
            item_type = self._get_type_from_field(field.child)
            return f'{item_type}[]'

        if hasattr(field, 'choices') and field.choices:
            choices = list(field.choices.keys())
            if all(isinstance(k, (int, float)) for k in choices):
                return 'number'
            quoted_choices = [f"'{c}'" for c in choices]
            return ' | '.join(quoted_choices)

        return TypeMapping.get_ts_type(field_class, field)

    def generate_interface(self) -> str:
        lines = [f'export interface {self.serializer_class.__name__} {{']

        for field_name, field in self.fields.items():
            info = self.get_field_info(field_name, field)

            if info['read_only']:
                continue

            optional_mark = '?' if (info['nullable'] and not info['required']) else ''
            lines.append(f'  {field_name}{optional_mark}: {info["ts_type"]};')

        lines.append('}')
        return '\n'.join(lines)

    def generate_type_alias(self) -> str:
        fields_str = []
        for field_name, field in self.fields.items():
            info = self.get_field_info(field_name, field)
            if info['read_only']:
                continue
            optional_mark = '?' if (info['nullable'] and not info['required']) else ''
            fields_str.append(f'  {field_name}{optional_mark}: {info["ts_type"]};')

        return f'''export type {self.serializer_class.__name__} = {{
{''.join(fields_str)}
}};'''


class TypeScriptGenerator:
    """TypeScript 类型生成器"""

    def __init__(self, app_names: List[str]):
        self.app_names = app_names
        self.generated_types: Dict[str, str] = {}
        self.type_registry: Dict[str, Set[str]] = {}

    def discover_serializers(self, app_name: str) -> List[Type[serializers.Serializer]]:
        serializers_path = f'apps.{app_name}.serializers'
        try:
            module = importlib.import_module(serializers_path)
            serializers_list = []
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if isinstance(attr, type) and issubclass(attr, serializers.Serializer):
                    if attr != serializers.Serializer and not attr.__name__.startswith('Base'):
                        serializers_list.append(attr)
            return serializers_list
        except (ImportError, ModuleNotFoundError) as e:
            print(f'Warning: Could not import {serializers_path}: {e}')
            return []

    def generate_for_app(self, app_name: str) -> str:
        output_parts = []
        output_parts.append(f'// ========================================')
        output_parts.append(f'// {app_name.upper()} - Auto-generated from serializers')
        output_parts.append(f'// Generated at: {datetime.now().isoformat()}')
        output_parts.append(f'// ========================================\n')

        serializers_list = self.discover_serializers(app_name)

        for serializer_class in serializers_list:
            try:
                analyzer = SerializerAnalyzer(serializer_class)
                interface = analyzer.generate_interface()
                output_parts.append(interface)
                output_parts.append('')
                self.generated_types[serializer_class.__name__] = interface
            except Exception as e:
                output_parts.append(f'// Error generating {serializer_class.__name__}: {e}')
                output_parts.append('')

        return '\n'.join(output_parts)

    def generate_all(self) -> str:
        header = f'''/**
 * Auto-generated TypeScript types from Django REST Framework Serializers
 * Generated at: {datetime.now().isoformat()}
 *
 * Usage:
 *   Import specific types:
 *     import {{ TenderProjectSerializer }} from '@/types/generated/tenders'
 *     import {{ EnterpriseSerializer }} from '@/types/generated/enterprise'
 *
 *   Or import all from index:
 *     import * as GeneratedTypes from '@/types/generated'
 *
 * Auto-regeneration:
 *   python -m scripts.generate_ts_types --apps tender,enterprise,crawler
 */

'''
        output_parts = [header]

        for app_name in self.app_names:
            app_output = self.generate_for_app(app_name)
            output_parts.append(app_output)

        return '\n'.join(output_parts)

    def save_output(self, output_dir: str):
        os.makedirs(output_dir, exist_ok=True)

        for app_name in self.app_names:
            app_output = self.generate_for_app(app_name)
            file_path = os.path.join(output_dir, f'{app_name}.ts')
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(app_output)
            print(f'Generated: {file_path}')

        all_output = self.generate_all()
        index_path = os.path.join(output_dir, 'index.ts')
        with open(index_path, 'w', encoding='utf-8') as f:
            f.write(all_output)
        print(f'Generated: {index_path}')


def main():
    parser = argparse.ArgumentParser(
        description='Generate TypeScript types from Django REST Framework serializers'
    )
    parser.add_argument(
        '--apps',
        type=str,
        default='tenders,enterprise,crawler,vectorlib,openclaw',
        help='Comma-separated list of Django apps to process'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='frontend/src/types/generated',
        help='Output directory for generated TypeScript files'
    )
    parser.add_argument(
        '--print',
        action='store_true',
        help='Print generated types to stdout'
    )

    args = parser.parse_args()
    app_names = [a.strip() for a in args.apps.split(',')]

    generator = TypeScriptGenerator(app_names)

    if args.print:
        print(generator.generate_all())
    else:
        generator.save_output(args.output)
        print(f'\nTypeScript types generated successfully!')
        print(f'Output directory: {args.output}')


if __name__ == '__main__':
    main()
