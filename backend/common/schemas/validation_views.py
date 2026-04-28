"""
验证规则API视图
提供验证规则给前端使用
"""
from rest_framework.views import APIView
from rest_framework.response import Response

from common.schemas.validation_loader import validation_loader


class ValidationRulesAPIView(APIView):
    """
    获取验证规则API

    GET /api/v1/validation-rules/
        返回所有验证规则定义

    GET /api/v1/validation-rules/<entity_name>/
        返回指定实体的验证规则
    """

    def get(self, request, entity_name=None):
        if entity_name:
            rules = validation_loader.get_entity_rules(entity_name)
            if not rules:
                return Response({
                    'success': False,
                    'code': '404',
                    'message': f'实体 {entity_name} 的验证规则不存在',
                    'data': None
                }, status=404)

            return Response({
                'success': True,
                'code': '0',
                'message': '获取成功',
                'data': {
                    'entity': entity_name,
                    'rules': rules
                }
            })

        definitions = validation_loader.get_all_definitions()
        entities = {}

        for entity_name in validation_loader.get_all_entities():
            entities[entity_name] = validation_loader.get_entity_rules(entity_name)

        return Response({
            'success': True,
            'code': '0',
            'message': '获取成功',
            'data': {
                'definitions': definitions,
                'entities': entities
            }
        })


class ValidationRuleDetailAPIView(APIView):
    """
    获取特定字段的验证规则

    GET /api/v1/validation-rules/<entity_name>/<field_name>/
    """

    def get(self, request, entity_name, field_name):
        rules = validation_loader.get_entity_rules(entity_name)

        if not rules:
            return Response({
                'success': False,
                'code': '404',
                'message': f'实体 {entity_name} 不存在',
                'data': None
            }, status=404)

        field_rule = rules.get(field_name)

        if not field_rule:
            return Response({
                'success': False,
                'code': '404',
                'message': f'字段 {field_name} 不存在',
                'data': None
            }, status=404)

        return Response({
            'success': True,
            'code': '0',
            'message': '获取成功',
            'data': {
                'entity': entity_name,
                'field': field_name,
                'rule': field_rule
            }
        })


class ValidationDefinitionsAPIView(APIView):
    """
    获取基础类型定义

    GET /api/v1/validation-definitions/<definition_name>/
    """

    def get(self, request, definition_name=None):
        if definition_name:
            definition = validation_loader.get_definition(definition_name)
            if not definition:
                return Response({
                    'success': False,
                    'code': '404',
                    'message': f'定义 {definition_name} 不存在',
                    'data': None
                }, status=404)

            return Response({
                'success': True,
                'code': '0',
                'message': '获取成功',
                'data': {
                    'name': definition_name,
                    'definition': definition
                }
            })

        definitions = validation_loader.get_all_definitions()

        return Response({
            'success': True,
            'code': '0',
            'message': '获取成功',
            'data': {
                'definitions': definitions
            }
        })
