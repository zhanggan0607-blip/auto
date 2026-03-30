"""
大模型配置和Agent工作流序列化器
"""
from rest_framework import serializers
from apps.openclaw.models import (
    LLMProvider, LLMModel, AgentModelConfig, LLMUsageLog,
    AutomationConfig, AIDecisionConfig, AutoMatchConfig,
    DocumentReviewConfig, RiskControlConfig, CrawlConfig, NotificationConfig
)
from apps.openclaw.workflow_models import (
    BidWorkflow, WorkflowStage, AgentTask, AgentMessage,
    BidDecision, DocumentReview
)


class LLMProviderSerializer(serializers.ModelSerializer):
    """
    大模型提供商序列化器
    """
    type_text = serializers.CharField(source='get_provider_type_display', read_only=True)

    class Meta:
        model = LLMProvider
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


class LLMModelSerializer(serializers.ModelSerializer):
    """
    大模型配置序列化器
    """
    provider_name = serializers.CharField(source='provider.name', read_only=True)

    class Meta:
        model = LLMModel
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


class AgentModelConfigSerializer(serializers.ModelSerializer):
    """
    Agent模型配置序列化器
    """
    chat_model_id = serializers.CharField(source='chat_model.model_id', read_only=True, allow_null=True)
    chat_model_name = serializers.CharField(source='chat_model.name', read_only=True)
    reasoning_model_id = serializers.CharField(source='reasoning_model.model_id', read_only=True, allow_null=True)
    reasoning_model_name = serializers.CharField(source='reasoning_model.name', read_only=True)

    class Meta:
        model = AgentModelConfig
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


class LLMUsageLogSerializer(serializers.ModelSerializer):
    """
    大模型使用日志序列化器
    """
    provider_name = serializers.CharField(source='provider.name', read_only=True)

    class Meta:
        model = LLMUsageLog
        fields = '__all__'


class WorkflowStageSerializer(serializers.ModelSerializer):
    """
    工作流阶段序列化器
    """
    class Meta:
        model = WorkflowStage
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


class BidDecisionSerializer(serializers.ModelSerializer):
    """
    投标决策序列化器
    """
    class Meta:
        model = BidDecision
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


class DocumentReviewSerializer(serializers.ModelSerializer):
    """
    标书审核序列化器
    """
    class Meta:
        model = DocumentReview
        fields = '__all__'
        read_only_fields = ['created_at']


class BidWorkflowSerializer(serializers.ModelSerializer):
    """
    投标工作流序列化器
    """
    tender_title = serializers.CharField(source='tender.title', read_only=True)
    stages = WorkflowStageSerializer(many=True, read_only=True)

    class Meta:
        model = BidWorkflow
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


class AutomationConfigSerializer(serializers.ModelSerializer):
    """
    全自动化配置序列化器
    """
    decision_config = serializers.SerializerMethodField()
    match_config = serializers.SerializerMethodField()
    review_config = serializers.SerializerMethodField()
    risk_config = serializers.SerializerMethodField()
    crawl_config = serializers.SerializerMethodField()
    notification_config = serializers.SerializerMethodField()

    class Meta:
        model = AutomationConfig
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']

    def get_decision_config(self, obj):
        try:
            return AIDecisionConfigSerializer(obj.decision_configs.first()).data
        except Exception:
            return None

    def get_match_config(self, obj):
        try:
            return AutoMatchConfigSerializer(obj.match_configs.first()).data
        except Exception:
            return None

    def get_review_config(self, obj):
        try:
            return DocumentReviewConfigSerializer(obj.review_configs.first()).data
        except Exception:
            return None

    def get_risk_config(self, obj):
        try:
            return RiskControlConfigSerializer(obj.risk_configs.first()).data
        except Exception:
            return None

    def get_crawl_config(self, obj):
        try:
            return CrawlConfigSerializer(obj.crawl_configs.first()).data
        except Exception:
            return None

    def get_notification_config(self, obj):
        try:
            return NotificationConfigSerializer(obj.notification_configs.first()).data
        except Exception:
            return None


class AIDecisionConfigSerializer(serializers.ModelSerializer):
    """
    AI决策配置序列化器
    """

    class Meta:
        model = AIDecisionConfig
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


class AutoMatchConfigSerializer(serializers.ModelSerializer):
    """
    自动匹配配置序列化器
    """

    class Meta:
        model = AutoMatchConfig
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


class DocumentReviewConfigSerializer(serializers.ModelSerializer):
    """
    文档审核配置序列化器
    """

    class Meta:
        model = DocumentReviewConfig
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


class RiskControlConfigSerializer(serializers.ModelSerializer):
    """
    风险控制配置序列化器
    """

    class Meta:
        model = RiskControlConfig
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


class CrawlConfigSerializer(serializers.ModelSerializer):
    """
    采集配置序列化器
    """

    class Meta:
        model = CrawlConfig
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


class NotificationConfigSerializer(serializers.ModelSerializer):
    """
    通知配置序列化器
    """

    class Meta:
        model = NotificationConfig
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']



