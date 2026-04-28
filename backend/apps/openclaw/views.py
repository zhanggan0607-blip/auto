"""
大模型配置和Agent工作流API视图
"""
import json
import logging
import asyncio
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from django.utils import timezone
from django.http import StreamingHttpResponse


def _run_async(coro):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()

from apps.openclaw.models import (
    LLMProvider, LLMModel, AgentModelConfig, LLMUsageLog,
    AutomationConfig, AIDecisionConfig, AutoMatchConfig,
    DocumentReviewConfig, RiskControlConfig, CrawlConfig, NotificationConfig
)
from apps.openclaw.workflow_models import WorkflowStage
from apps.openclaw.serializers import (
    LLMProviderSerializer, LLMModelSerializer, AgentModelConfigSerializer,
    LLMUsageLogSerializer,
    WorkflowStageSerializer, AutomationConfigSerializer,
    AIDecisionConfigSerializer, AutoMatchConfigSerializer,
    DocumentReviewConfigSerializer, RiskControlConfigSerializer,
    CrawlConfigSerializer, NotificationConfigSerializer
)
from common.views.base import BaseViewSet, APIResponseMixin, AuthenticatedModelViewSet
from utils.responses import UnifiedResponse


logger = logging.getLogger(__name__)


class LLMProviderViewSet(APIResponseMixin, viewsets.ModelViewSet):
    """
    大模型提供商管理
    """
    queryset = LLMProvider.objects.all()
    serializer_class = LLMProviderSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None

    @action(detail=True, methods=['post'])
    def set_default(self, request, pk=None):
        """
        设置为默认提供商
        """
        provider = self.get_object()
        provider.is_default = True
        provider.save()
        return UnifiedResponse.success(message=f'{provider.name} 已设置为默认提供商')

    @action(detail=True, methods=['get'])
    def models(self, request, pk=None):
        """
        获取提供商下的所有模型
        """
        provider = self.get_object()
        models = LLMModel.objects.filter(provider=provider)
        serializer = LLMModelSerializer(models, many=True)
        return UnifiedResponse.success(data=serializer.data)

    @action(detail=True, methods=['get'])
    def available_models(self, request, pk=None):
        """
        获取提供商支持的模型列表
        """
        provider = self.get_object()
        models = provider.get_available_models()
        return UnifiedResponse.success(data={'models': models})

    @action(detail=False, methods=['get'])
    def default(self, request):
        """
        获取默认提供商
        """
        provider = LLMProvider.objects.filter(is_default=True, is_active=True).first()
        if provider:
            serializer = self.get_serializer(provider)
            return UnifiedResponse.success(data=serializer.data)
        return UnifiedResponse.not_found(message='未设置默认提供商')

    @action(detail=False, methods=['post'])
    def test_connection(self, request):
        """
        测试模型连接
        """
        provider_id = request.data.get('provider_id')
        model_id = request.data.get('model_id')

        if not provider_id:
            return UnifiedResponse.error(message='缺少参数: provider_id', status_code=status.HTTP_400_BAD_REQUEST)
        if not model_id:
            return UnifiedResponse.error(message='缺少参数: model_id，请指定要测试的模型', status_code=status.HTTP_400_BAD_REQUEST)

        try:
            import requests as http_requests
            provider = LLMProvider.objects.get(id=provider_id)

            if not provider.is_active:
                return UnifiedResponse.error(message=f'提供商 {provider.name} 已禁用，请先启用', status_code=status.HTTP_400_BAD_REQUEST)

            if not provider.api_key and provider.provider_type not in ('ollama',):
                return UnifiedResponse.error(
                    message=f'提供商 {provider.name} 的 API Key 未配置',
                    status_code=status.HTTP_400_BAD_REQUEST
                )

            if provider.provider_type == 'zhipu':
                url = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
                payload = {
                    'model': model_id,
                    'messages': [{'role': 'user', 'content': "你好，请回复'连接成功'"}],
                    'temperature': 0.7,
                    'max_tokens': 100
                }
                headers = {
                    'Authorization': f'Bearer {provider.api_key}'
                }
            elif provider.provider_type == 'qwen':
                url = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"
                payload = {
                    'model': model_id,
                    'messages': [{'role': 'user', 'content': "你好，请回复'连接成功'"}],
                    'temperature': 0.7,
                    'max_tokens': 100
                }
                headers = {
                    'Authorization': f'Bearer {provider.api_key}',
                    'Content-Type': 'application/json'
                }
            elif provider.provider_type == 'deepseek':
                url = "https://api.deepseek.com/v1/chat/completions"
                payload = {
                    'model': model_id,
                    'messages': [{'role': 'user', 'content': "你好，请回复'连接成功'"}],
                    'temperature': 0.7,
                    'max_tokens': 100
                }
                headers = {
                    'Authorization': f'Bearer {provider.api_key}'
                }
            elif provider.provider_type == 'ollama':
                url = f"{provider.base_url or 'http://localhost:11434'}/api/chat"
                payload = {
                    'model': model_id,
                    'messages': [{'role': 'user', 'content': "你好，请回复'连接成功'"}],
                    'temperature': 0.7,
                    'stream': False
                }
                headers = {'Content-Type': 'application/json'}
            else:
                url = f"{provider.base_url}/chat/completions"
                payload = {
                    'model': model_id,
                    'messages': [{'role': 'user', 'content': "你好，请回复'连接成功'"}],
                    'temperature': 0.7,
                    'max_tokens': 100
                }
                headers = {
                    'Authorization': f'Bearer {provider.api_key}'
                }

            timeout = 10 if provider.provider_type == 'ollama' else 30
            response = http_requests.post(url, json=payload, headers=headers, timeout=timeout)
            response.raise_for_status()
            result = response.json()

            content = ''
            if 'choices' in result:
                content = result['choices'][0].get('message', {}).get('content', '')
            elif 'output' in result:
                content = result['output'].get('choices', [{}])[0].get('text', '')
            elif 'message' in result and isinstance(result.get('message'), dict):
                content = result['message'].get('content', '')

            return UnifiedResponse.success(
                message='连接成功',
                data={'response': content[:100] if content else str(result)[:100]}
            )
        except LLMProvider.DoesNotExist:
            return UnifiedResponse.error(message=f'提供商不存在 (id={provider_id})', status_code=status.HTTP_404_NOT_FOUND)
        except http_requests.ConnectionError:
            provider_name = '未知'
            try:
                p = LLMProvider.objects.get(id=provider_id)
                provider_name = p.name
            except LLMProvider.DoesNotExist:
                pass
            return UnifiedResponse.error(
                message=f'无法连接到 {provider_name} 服务，请检查服务是否启动及网络配置',
                status_code=status.HTTP_400_BAD_REQUEST
            )
        except http_requests.Timeout:
            return UnifiedResponse.error(
                message='连接超时，请检查服务是否正常运行',
                status_code=status.HTTP_400_BAD_REQUEST
            )
        except http_requests.HTTPError as e:
            status_code_resp = e.response.status_code if e.response else 0
            detail = ''
            try:
                err_body = e.response.json()
                detail = err_body.get('error', {}).get('message', '') or err_body.get('message', '')
            except Exception:
                detail = e.response.text[:200] if e.response else ''
            return UnifiedResponse.error(
                message=f'API返回错误 ({status_code_resp}): {detail or str(e)}',
                status_code=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f'test_connection 异常: provider_id={provider_id}, model_id={model_id}, error={e}')
            return UnifiedResponse.error(
                message=f'连接测试失败: {str(e)}',
                status_code=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=False, methods=['get'])
    def ollama_status(self, request):
        """
        获取 Ollama 服务状态
        """
        try:
            import httpx
            ollama_url = request.query_params.get('url', 'http://localhost:11434')
            response = httpx.get(f"{ollama_url}/api/tags", timeout=5)
            if response.status_code == 200:
                data = response.json()
                return UnifiedResponse.success(data={
                    'connected': True,
                    'version': data.get('version', 'unknown'),
                    'models': data.get('models', [])
                })
            return UnifiedResponse.error(message='Ollama 服务未响应')
        except Exception as e:
            return UnifiedResponse.success(data={
                'connected': False,
                'error': str(e)
            })

    @action(detail=False, methods=['get'])
    def ollama_models(self, request):
        """
        获取 Ollama 可用模型列表
        """
        try:
            import httpx
            ollama_url = request.query_params.get('url', 'http://localhost:11434')
            response = httpx.get(f"{ollama_url}/api/tags", timeout=10)
            if response.status_code == 200:
                data = response.json()
                models = data.get('models', [])
                return UnifiedResponse.success(data={
                    'models': models,
                    'version': data.get('version', 'unknown'),
                    'connected': True
                })
            return UnifiedResponse.success(data={
                'models': [],
                'version': '',
                'connected': False,
                'error': 'Ollama 服务未响应'
            })
        except Exception as e:
            return UnifiedResponse.success(data={
                'models': [],
                'version': '',
                'connected': False,
                'error': str(e)
            })

    @action(detail=False, methods=['post'])
    def sync_ollama_models(self, request):
        """
        自动同步Ollama已安装模型到数据库
        同步LLMProvider.available_models和LLMModel表
        """
        try:
            import httpx
            ollama_providers = LLMProvider.objects.filter(provider_type='ollama', is_active=True)
            if not ollama_providers.exists():
                return UnifiedResponse.error(message='未找到活跃的Ollama提供商')

            ollama_provider = ollama_providers.first()
            ollama_url = ollama_provider.base_url or 'http://localhost:11434'

            response = httpx.get(f"{ollama_url}/api/tags", timeout=10)
            if response.status_code != 200:
                return UnifiedResponse.error(message='无法连接Ollama服务')

            data = response.json()
            ollama_model_list = data.get('models', [])
            if not ollama_model_list:
                return UnifiedResponse.error(message='Ollama未安装任何模型')

            model_names = [m['name'] for m in ollama_model_list]
            added_count = 0
            updated_count = 0

            for model_info in ollama_model_list:
                model_name = model_info['name']
                model_size = model_info.get('size', 0)

                obj, created = LLMModel.objects.update_or_create(
                    provider=ollama_provider,
                    model_id=model_name,
                    defaults={
                        'name': model_name.upper(),
                        'model_type': 'chat',
                        'context_window': 128000,
                        'max_output_tokens': 4096,
                        'supports_streaming': True,
                    }
                )
                if created:
                    added_count += 1
                else:
                    updated_count += 1

            ollama_provider.available_models = model_names
            if not ollama_provider.default_model or ollama_provider.default_model not in model_names:
                ollama_provider.default_model = model_names[0] if model_names else None
            ollama_provider.save()

            return UnifiedResponse.success(
                message='同步成功',
                data={
                    'total_models': len(model_names),
                    'added': added_count,
                    'updated': updated_count,
                    'models': model_names,
                    'default_model': ollama_provider.default_model
                }
            )
        except Exception as e:
            logger.error(f"同步Ollama模型失败: {str(e)}")
            return UnifiedResponse.error(message=f'同步失败: {str(e)}')

    @action(detail=False, methods=['post'])
    def test_all_providers(self, request):
        """
        测试所有已配置提供商的连接状态
        """
        test_message = request.data.get('message', '你好，请回复"测试成功"')
        results = []
        providers = LLMProvider.objects.filter(is_active=True)

        for provider in providers:
            try:
                from services.unified_llm_service import unified_llm_service
                start_time = timezone.now()
                result = _run_async(unified_llm_service.chat(
                    message=test_message,
                    provider_id=provider.id,
                    model_id=provider.default_model,
                    max_tokens=100
                ))
                latency = (timezone.now() - start_time).total_seconds()
                results.append({
                    'provider_id': provider.id,
                    'provider_name': provider.name,
                    'provider_type': provider.provider_type,
                    'model': provider.default_model,
                    'status': 'success',
                    'response': result.get('content', '')[:200],
                    'latency': latency,
                    'tokens': result.get('total_tokens', 0)
                })
            except Exception as e:
                results.append({
                    'provider_id': provider.id,
                    'provider_name': provider.name,
                    'provider_type': provider.provider_type,
                    'model': provider.default_model,
                    'status': 'error',
                    'error': str(e),
                    'latency': 0
                })

        return UnifiedResponse.success(data=results)


class LLMModelViewSet(AuthenticatedModelViewSet):
    """
    大模型配置管理
    """
    queryset = LLMModel.objects.all()
    serializer_class = LLMModelSerializer
    filterset_fields = ['provider', 'model_type', 'is_active']

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        if not queryset.exists():
            providers = LLMProvider.objects.filter(is_active=True)
            default_models = []
            for provider in providers:
                if provider.default_model:
                    default_models.append({
                        'id': None,
                        'provider': provider.id,
                        'provider_name': provider.name,
                        'model_id': provider.default_model,
                        'name': provider.default_model,
                        'model_type': provider.provider_type,
                        'context_length': provider.max_tokens or 4096,
                        'is_active': True
                    })
            return UnifiedResponse.success(data=default_models)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return UnifiedResponse.success(data=serializer.data)


class AgentModelConfigViewSet(APIResponseMixin, viewsets.ModelViewSet):
    """
    Agent模型配置管理
    """
    queryset = AgentModelConfig.objects.all()
    serializer_class = AgentModelConfigSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        if not queryset.exists():
            default_configs = []
            for agent_type, type_name in AgentModelConfig.AGENT_TYPE_CHOICES:
                default_configs.append({
                    'agent_type': agent_type,
                    'chat_model_id': None,
                    'temperature': 0.7,
                    'max_tokens': 4096
                })
            serializer = self.get_serializer(default_configs, many=True)
            return UnifiedResponse.success(data=serializer.data)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return UnifiedResponse.success(data=serializer.data)

    @action(detail=False, methods=['post'])
    def batch_update(self, request):
        """
        批量更新Agent配置
        """
        configs = request.data.get('configs', [])
        updated = []

        for config_data in configs:
            agent_type = config_data.get('agent_type')
            if agent_type:
                defaults = config_data.copy()
                chat_model_id = defaults.pop('chat_model_id', None)
                if chat_model_id:
                    try:
                        chat_model = LLMModel.objects.get(model_id=chat_model_id)
                        defaults['chat_model'] = chat_model
                    except LLMModel.DoesNotExist:
                        pass

                config, created = AgentModelConfig.objects.update_or_create(
                    agent_type=agent_type,
                    defaults=defaults
                )
                updated.append(config)

        serializer = self.get_serializer(updated, many=True)
        return UnifiedResponse.success(data=serializer.data, message=f'成功更新 {len(updated)} 条配置')

class AutomationConfigViewSet(BaseViewSet):
    """
    全自动化配置管理
    支持配置AI决策参数、自动匹配参数、模型选择等
    """
    queryset = AutomationConfig.objects.all()
    serializer_class = AutomationConfigSerializer
    filterset_fields = ['is_active', 'is_default']

    def perform_create(self, serializer):
        serializer.save()

    @action(detail=False, methods=['get'])
    def default_config(self, request):
        """
        获取当前默认配置
        """
        config = AutomationConfig.objects.filter(is_default=True, is_active=True).first()
        if not config:
            config = AutomationConfig.objects.filter(is_active=True).first()

        if config:
            serializer = self.get_serializer(config)
            return UnifiedResponse.success(data=serializer.data)
        return UnifiedResponse.not_found(message='未找到有效配置')

    @action(detail=True, methods=['post'])
    def set_default(self, request, pk=None):
        """
        设置为默认配置
        """
        config = self.get_object()
        config.is_default = True
        config.is_active = True
        config.save()
        return UnifiedResponse.success(message=f'{config.name} 已设置为默认配置')

    @action(detail=True, methods=['post'])
    def update_decision_config(self, request, pk=None):
        """
        更新AI决策配置
        """
        config = self.get_object()

        decision_data = request.data.get('decision_config', {})
        decision_data.pop('config', None)
        decision_data.pop('id', None)
        decision_data.pop('created_at', None)
        decision_data.pop('updated_at', None)

        decision_config, created = AIDecisionConfig.objects.update_or_create(
            config=config,
            defaults=decision_data
        )

        serializer = AIDecisionConfigSerializer(decision_config)
        return UnifiedResponse.success(
            data=serializer.data,
            message='AI决策配置已更新'
        )

    @action(detail=True, methods=['post'])
    def update_match_config(self, request, pk=None):
        """
        更新自动匹配配置
        """
        config = self.get_object()

        match_data = request.data.get('match_config', {})
        match_data.pop('config', None)
        match_data.pop('id', None)
        match_data.pop('created_at', None)
        match_data.pop('updated_at', None)

        match_config, created = AutoMatchConfig.objects.update_or_create(
            config=config,
            defaults=match_data
        )

        serializer = AutoMatchConfigSerializer(match_config)
        return UnifiedResponse.success(
            data=serializer.data,
            message='自动匹配配置已更新'
        )

    @action(detail=True, methods=['post'])
    def update_review_config(self, request, pk=None):
        """
        更新文档审核配置
        """
        config = self.get_object()

        review_data = request.data.get('review_config', {})
        review_data.pop('config', None)
        review_data.pop('id', None)
        review_data.pop('created_at', None)
        review_data.pop('updated_at', None)

        review_config, created = DocumentReviewConfig.objects.update_or_create(
            config=config,
            defaults=review_data
        )

        serializer = DocumentReviewConfigSerializer(review_config)
        return UnifiedResponse.success(
            data=serializer.data,
            message='文档审核配置已更新'
        )

    @action(detail=True, methods=['post'])
    def update_risk_config(self, request, pk=None):
        """
        更新风险控制配置
        """
        config = self.get_object()

        risk_data = request.data.get('risk_config', {})
        risk_data.pop('config', None)
        risk_data.pop('id', None)
        risk_data.pop('created_at', None)
        risk_data.pop('updated_at', None)

        risk_config, created = RiskControlConfig.objects.update_or_create(
            config=config,
            defaults=risk_data
        )

        serializer = RiskControlConfigSerializer(risk_config)
        return UnifiedResponse.success(
            data=serializer.data,
            message='风险控制配置已更新'
        )

    @action(detail=True, methods=['post'])
    def update_crawl_config(self, request, pk=None):
        """
        更新采集配置
        """
        config = self.get_object()

        crawl_data = request.data.get('crawl_config', {})
        crawl_data.pop('config', None)
        crawl_data.pop('id', None)
        crawl_data.pop('created_at', None)
        crawl_data.pop('updated_at', None)

        crawl_config, created = CrawlConfig.objects.update_or_create(
            config=config,
            defaults=crawl_data
        )

        serializer = CrawlConfigSerializer(crawl_config)
        return UnifiedResponse.success(
            data=serializer.data,
            message='采集配置已更新'
        )

    @action(detail=True, methods=['post'])
    def update_notification_config(self, request, pk=None):
        """
        更新通知配置
        """
        config = self.get_object()

        notification_data = request.data.get('notification_config', {})
        notification_data.pop('config', None)
        notification_data.pop('id', None)
        notification_data.pop('created_at', None)
        notification_data.pop('updated_at', None)

        notification_config, created = NotificationConfig.objects.update_or_create(
            config=config,
            defaults=notification_data
        )

        serializer = NotificationConfigSerializer(notification_config)
        return UnifiedResponse.success(
            data=serializer.data,
            message='通知配置已更新'
        )

    @action(detail=True, methods=['post'])
    def update_all_configs(self, request, pk=None):
        """
        一次性更新所有子配置
        """
        config = self.get_object()

        try:
            if 'decision_config' in request.data:
                AIDecisionConfig.objects.update_or_create(
                    config=config,
                    defaults=request.data['decision_config']
                )

            if 'match_config' in request.data:
                AutoMatchConfig.objects.update_or_create(
                    config=config,
                    defaults=request.data['match_config']
                )

            if 'review_config' in request.data:
                DocumentReviewConfig.objects.update_or_create(
                    config=config,
                    defaults=request.data['review_config']
                )

            if 'risk_config' in request.data:
                RiskControlConfig.objects.update_or_create(
                    config=config,
                    defaults=request.data['risk_config']
                )

            if 'crawl_config' in request.data:
                CrawlConfig.objects.update_or_create(
                    config=config,
                    defaults=request.data['crawl_config']
                )

            if 'notification_config' in request.data:
                NotificationConfig.objects.update_or_create(
                    config=config,
                    defaults=request.data['notification_config']
                )

            serializer = self.get_serializer(config)
            return UnifiedResponse.success(
                data=serializer.data,
                message='所有配置已更新'
            )
        except Exception as e:
            return UnifiedResponse.error(message=f'更新失败: {str(e)}')

    @action(detail=False, methods=['post'])
    def create_with_defaults(self, request):
        """
        创建带默认配置的自动化配置
        """
        name = request.data.get('name', '新配置')

        try:
            config = AutomationConfig.objects.create(
                name=name,
                description=request.data.get('description', ''),
                is_active=True,
                is_default=request.data.get('is_default', False)
            )

            AIDecisionConfig.objects.create(
                config=config,
                QUALIFICATION_WEIGHT=0.4,
                COMPETITOR_WEIGHT=0.2,
                PERFORMANCE_WEIGHT=0.2,
                RISK_WEIGHT=0.2,
                AUTO_BID_THRESHOLD=60,
                OBSERVATION_THRESHOLD=40,
                SKIP_THRESHOLD=40,
                USE_AI_DECISION=True
            )

            AutoMatchConfig.objects.create(
                config=config,
                AUTO_MATCH_ENABLED=True,
                AUTO_IMPORT_THRESHOLD=0.8,
                AUTO_BID_MATCH_THRESHOLD=0.6,
                EXCLUDE_THRESHOLD=0.6,
                ADAPTIVE_THRESHOLD=True,
                LEARNING_FROM_HISTORY=True,
                KEYWORD_BOOST_ENABLED=True,
                REGION_BOOST_ENABLED=True
            )

            DocumentReviewConfig.objects.create(
                config=config,
                AUTO_UPLOAD_THRESHOLD=90,
                OBSERVATION_THRESHOLD=60,
                MANUAL_REVIEW_THRESHOLD=60,
                MAX_OPTIMIZATION_ROUNDS=3,
                ENABLE_ANTI_REJECTION_CHECK=True,
                ENABLE_PRICE_ANALYSIS=True,
                USE_SIMULATED_SCORING=True
            )

            RiskControlConfig.objects.create(
                config=config,
                MAX_DAILY_BIDS=50,
                AMOUNT_THRESHOLD=1000000,
                CONSECUTIVE_FAILURES=3,
                ENABLE_AMOUNT_CHECK=True,
                ENABLE_COUNT_CHECK=True,
                ENABLE_FAILURE_CHECK=True,
                AUTO_PAUSE_ON_RISK=True,
                NOTIFY_ON_RISK=True
            )

            CrawlConfig.objects.create(
                config=config,
                AUTO_LEARN_KEYWORDS=True,
                ADAPTIVE_CRAWL_MODE=True,
                MULTI_SOURCE_ENABLED=True,
                DEFAULT_CRAWL_INTERVAL=60,
                MAX_PAGES_PER_CRAWL=50,
                ENABLE_DEDUP=True
            )

            NotificationConfig.objects.create(
                config=config,
                NOTIFICATION_ENABLED=True,
                DINGTALK_ENABLED=True,
                KEY_EVENTS_ONLY=False,
                DAILY_REPORT_ENABLED=True,
                WEEKLY_REPORT_ENABLED=False,
                NOTIFY_ON_START=False,
                NOTIFY_ON_SUCCESS=True,
                NOTIFY_ON_FAILURE=True,
                NOTIFY_ON_WIN=True,
                NOTIFY_ON_LOSS=True
            )

            serializer = self.get_serializer(config)
            return UnifiedResponse.success(
                data=serializer.data,
                message=f'配置"{name}"创建成功'
            )
        except Exception as e:
            return UnifiedResponse.error(message=f'创建失败: {str(e)}')


class AIPlaygroundViewSet(APIResponseMixin, viewsets.ViewSet):
    """
    AI Playground - 统一模型测试界面
    支持GLM、KIMI、DEEPSEEK、QWEN、文心一言的统一调用
    """
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'])
    def providers(self, request):
        """
        获取所有可用的模型提供商
        """
        providers = LLMProvider.objects.filter(is_active=True)
        data = []
        for p in providers:
            data.append({
                'id': p.id,
                'name': p.name,
                'type': p.provider_type,
                'type_text': p.get_provider_type_display(),
                'base_url': p.base_url,
                'default_model': p.default_model,
                'available_models': p.get_available_models(),
                'is_default': p.is_default,
                'max_tokens': p.max_tokens,
                'temperature': p.temperature
            })
        return UnifiedResponse.success(data=data)

    @action(detail=False, methods=['post'])
    def chat(self, request):
        """
        统一聊天接口
        支持所有已配置的模型提供商
        """
        provider_id = request.data.get('provider_id')
        model_id = request.data.get('model_id')
        message = request.data.get('message', '')
        system_prompt = request.data.get('system_prompt', '')
        temperature = request.data.get('temperature')
        max_tokens = request.data.get('max_tokens')
        history = request.data.get('history', [])

        if not message:
            return UnifiedResponse.error(message='消息内容不能为空')

        try:
            from services.unified_llm_service import unified_llm_service

            result = _run_async(unified_llm_service.chat(
                message=message,
                provider_id=provider_id,
                model_id=model_id,
                system_prompt=system_prompt if system_prompt else None,
                temperature=temperature,
                max_tokens=max_tokens,
                history=history if history else None
            ))

            return UnifiedResponse.success(data={
                'content': result.get('content', ''),
                'model': result.get('model', ''),
                'provider': result.get('provider', ''),
                'input_tokens': result.get('input_tokens', 0),
                'output_tokens': result.get('output_tokens', 0),
                'total_tokens': result.get('total_tokens', 0),
                'latency': result.get('latency', 0),
                'timestamp': timezone.now().isoformat()
            })
        except Exception as e:
            logger.error(f"AI Chat Error: {str(e)}")
            return UnifiedResponse.error(
                message=f'调用失败: {str(e)}',
                status_code=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=False, methods=['post'])
    def stream_chat(self, request):
        """
        流式聊天接口
        支持SSE流式输出
        """
        try:
            provider_id = request.data.get('provider_id')
            model_id = request.data.get('model_id')
            message = request.data.get('message', '')
            system_prompt = request.data.get('system_prompt', '')
            temperature = request.data.get('temperature')
            max_tokens = request.data.get('max_tokens')
            history = request.data.get('history', [])

            if not message:
                return UnifiedResponse.error(message='消息内容不能为空')

            temp = temperature if temperature else 0.7
            max_tok = max_tokens if max_tokens else 4096

            def generate():
                try:
                    from services.unified_llm_service import unified_llm_service
                    from services.llm_adapters import get_adapter

                    provider = unified_llm_service.get_provider(provider_id)
                    if not provider:
                        yield f"event: error\ndata: {{\"error\": \"Provider not found\"}}\n\n"
                        return

                    messages = []
                    if system_prompt:
                        messages.append({'role': 'system', 'content': system_prompt})
                    if history:
                        messages.extend(history)
                    messages.append({'role': 'user', 'content': message})

                    try:
                        adapter = get_adapter(provider)

                        if provider.provider_type == 'ollama' and hasattr(adapter, 'chat_stream'):
                            accumulated_content = ''
                            for item in adapter.chat_stream(
                                model_id or provider.default_model,
                                messages, temp, max_tok
                            ):
                                if isinstance(item, tuple):
                                    continue
                                accumulated_content += item
                                yield f"event: message\ndata: {json.dumps({'content': item})}\n\n"
                            yield f"event: done\ndata: {json.dumps({'content': ''})}\n\n"
                        else:
                            result = _run_async(unified_llm_service.chat(
                                message=message,
                                provider_id=provider_id,
                                model_id=model_id,
                                system_prompt=system_prompt if system_prompt else None,
                                temperature=temperature,
                                max_tokens=max_tokens,
                                history=history if history else None
                            ))
                            content = result.get('content', '')
                            yield f"event: done\ndata: {json.dumps({'content': content})}\n\n"
                    except Exception as e:
                        logger.error(f"Stream error: {str(e)}")
                        from django.conf import settings as django_settings
                        if django_settings.DEBUG:
                            import traceback
                            logger.error(f"Stream traceback: {traceback.format_exc()}")
                        yield f"event: error\ndata: {json.dumps({'error': str(e)})}\n\n"
                except Exception as e:
                    logger.error(f"Stream generate error: {str(e)}")
                    from django.conf import settings as django_settings
                    if django_settings.DEBUG:
                        import traceback
                        logger.error(f"Generate traceback: {traceback.format_exc()}")
                    yield f"event: error\ndata: {json.dumps({'error': str(e)})}\n\n"

            response = StreamingHttpResponse(
                generate(),
                content_type='text/event-stream'
            )
            response['X-Accel-Buffering'] = 'no'
            response['Cache-Control'] = 'no-cache'
            return response
        except Exception as e:
            logger.error(f"Stream chat outer error: {str(e)}")
            from django.conf import settings as django_settings
            if django_settings.DEBUG:
                import traceback
                logger.error(f"Stream chat outer traceback: {traceback.format_exc()}")
            return UnifiedResponse.error(message=f'流式聊天错误: {str(e)}')

    @action(detail=False, methods=['get'])
    def history(self, request):
        """
        获取调用历史记录
        """
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 20))
        provider_id = request.query_params.get('provider_id')
        success_only = request.query_params.get('success_only', 'false') == 'true'

        queryset = LLMUsageLog.objects.all()

        if provider_id:
            queryset = queryset.filter(provider_id=provider_id)
        if success_only:
            queryset = queryset.filter(success=True)

        total = queryset.count()
        offset = (page - 1) * page_size
        logs = queryset[offset:offset + page_size]

        data = []
        for log in logs:
            data.append({
                'id': log.id,
                'provider': log.provider.name if log.provider else None,
                'provider_type': log.provider.provider_type if log.provider else None,
                'model': log.model,
                'agent_type': log.agent_type,
                'input_tokens': log.input_tokens,
                'output_tokens': log.output_tokens,
                'total_tokens': log.total_tokens,
                'latency': log.latency,
                'success': log.success,
                'error_message': log.error_message,
                'content_preview': log.request_data.get('message', '')[:100] if log.request_data else '',
                'created_at': log.created_at.isoformat() if log.created_at else None
            })

        return UnifiedResponse.success(data={
            'items': data,
            'total': total,
            'page': page,
            'page_size': page_size,
            'total_pages': (total + page_size - 1) // page_size
        })

    @action(detail=False, methods=['get'])
    def model_info(self, request):
        """
        获取模型详细信息和特性
        """
        provider_type = request.query_params.get('type')

        model_features = {
            'ollama': {
                'name': 'Ollama',
                'description': '本地大模型部署框架',
                'features': ['本地部署', '隐私保护', '无API费用', '支持多种开源模型'],
                'max_context': 128000,
                'supports_streaming': True,
                'free': True
            },
            'zhipu': {
                'name': '智谱AI (GLM)',
                'description': '国内领先的大模型服务商',
                'features': ['中文优化', '代码能力强', '永久免费模型可用', '高并发支持'],
                'max_context': 128000,
                'supports_streaming': True,
                'free': True,
                'free_model': 'GLM-4-Flash'
            },
            'kimi': {
                'name': 'Kimi (月之暗面)',
                'description': '超长上下文大模型',
                'features': ['256K超长上下文', '不限Token总量', '3次/分钟免费调用', '中文能力强'],
                'max_context': 256000,
                'supports_streaming': True,
                'free': True
            },
            'deepseek': {
                'name': 'DeepSeek',
                'description': '深度求索大模型',
                'features': ['推理能力强', '代码生成优秀', '价格低廉', '开源模型'],
                'max_context': 64000,
                'supports_streaming': True,
                'free': True
            },
            'qwen': {
                'name': '通义千问 (QWEN)',
                'description': '阿里云大模型',
                'features': ['阿里云生态集成', '中文理解强', '多模态支持', '稳定可靠'],
                'max_context': 128000,
                'supports_streaming': True,
                'free': True
            },
            'wenxin': {
                'name': '文心一言 (ERNIE)',
                'description': '百度大模型',
                'features': ['百度搜索生态', '中文创作强', '数理逻辑准确', '企业级服务'],
                'max_context': 128000,
                'supports_streaming': True,
                'free': False
            },
            'openai': {
                'name': 'OpenAI',
                'description': 'GPT系列模型',
                'features': ['GPT-4o强大能力', '多模态支持', '生态完善', '全球领先'],
                'max_context': 128000,
                'supports_streaming': True,
                'free': False
            }
        }

        if provider_type:
            if provider_type in model_features:
                return UnifiedResponse.success(data=model_features[provider_type])
            return UnifiedResponse.error(message=f'未知的模型类型: {provider_type}')

        return UnifiedResponse.success(data=model_features)


class SystemModelsView(APIView):
    """
    统一模型列表接口
    提供所有可用模型的统一访问入口
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        获取所有可用模型列表
        返回格式：包含所有提供商的模型信息
        """
        try:
            providers = LLMProvider.objects.filter(is_active=True)
            result = []

            for provider in providers:
                provider_models = LLMModel.objects.filter(provider=provider, is_active=True)
                model_list = []

                for model in provider_models:
                    model_list.append({
                        'model_id': model.model_id,
                        'name': model.name,
                        'model_type': model.model_type,
                        'context_length': model.context_window,
                        'is_active': model.is_active
                    })

                if not model_list and provider.default_model:
                    model_list.append({
                        'model_id': provider.default_model,
                        'name': provider.default_model,
                        'model_type': provider.provider_type,
                        'context_length': None,
                        'is_active': True
                    })

                result.append({
                    'provider_id': provider.id,
                    'provider_name': provider.name,
                    'provider_type': provider.provider_type,
                    'default_model': provider.default_model,
                    'is_default': provider.is_default,
                    'is_active': provider.is_active,
                    'base_url': provider.base_url or '',
                    'models': model_list
                })

            return UnifiedResponse.success(data=result)

        except Exception as e:
            logger.error(f"获取模型列表失败: {str(e)}")
            return UnifiedResponse.error(message=f"获取模型列表失败: {str(e)}")
