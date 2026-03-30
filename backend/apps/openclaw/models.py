"""
大模型配置模块
支持多种AI大模型的配置和切换
"""
from django.db import models
from django.conf import settings
from django.utils import timezone


class LLMProvider(models.Model):
    """
    大模型提供商配置
    """
    PROVIDER_TYPE_CHOICES = [
        ('openai', 'OpenAI'),
        ('azure_openai', 'Azure OpenAI'),
        ('anthropic', 'Anthropic Claude'),
        ('ollama', 'Ollama (本地)'),
        ('vllm', 'vLLM (本地)'),
        ('zhipu', '智谱AI'),
        ('qwen', '通义千问'),
        ('deepseek', 'DeepSeek'),
        ('kimi', 'Kimi (月之暗面)'),
        ('wenxin', '文心一言'),
        ('moonshot', 'Moonshot'),
        ('minimax', 'MiniMax'),
        ('custom', '自定义'),
    ]

    name = models.CharField('提供商名称', max_length=100)
    provider_type = models.CharField('提供商类型', max_length=20, choices=PROVIDER_TYPE_CHOICES)
    code = models.CharField('提供商编码', max_length=50, unique=True)

    base_url = models.URLField('API基础URL', max_length=500, blank=True, null=True)
    api_key = models.TextField('API密钥', blank=True, null=True, help_text='加密存储')

    default_model = models.CharField('默认模型', max_length=100)
    available_models = models.JSONField('可用模型列表', default=list, blank=True)

    max_tokens = models.IntegerField('最大Token数', default=4096)
    temperature = models.FloatField('默认温度', default=0.7)
    timeout = models.IntegerField('超时时间(秒)', default=60)

    is_active = models.BooleanField('是否启用', default=True)
    is_default = models.BooleanField('是否默认', default=False)

    config = models.JSONField('扩展配置', default=dict, blank=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='创建人'
    )
    created_at = models.DateTimeField('创建时间', default=timezone.now)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        db_table = 'llm_providers'
        verbose_name = '大模型提供商'
        verbose_name_plural = verbose_name
        ordering = ['-is_default', '-created_at']

    def __str__(self):
        return f"{self.name} ({self.get_provider_type_display()})"

    def save(self, *args, **kwargs):
        if self.is_default:
            LLMProvider.objects.filter(is_default=True).exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)

    def get_available_models(self):
        """
        获取可用模型列表
        """
        if self.available_models:
            return self.available_models

        default_models = {
            'openai': ['gpt-4o', 'gpt-4-turbo', 'gpt-4', 'gpt-3.5-turbo'],
            'azure_openai': ['gpt-4o', 'gpt-4-turbo', 'gpt-35-turbo'],
            'anthropic': ['claude-3-opus', 'claude-3-sonnet', 'claude-3-haiku'],
            'ollama': ['qwen2.5:14b', 'qwen2.5:72b', 'llama3.1:70b'],
            'vllm': ['Qwen/Qwen2.5-14B-Instruct', 'Qwen/Qwen2.5-72B-Instruct'],
            'zhipu': ['glm-4', 'glm-4-flash', 'glm-4-plus'],
            'qwen': ['qwen-turbo', 'qwen-plus', 'qwen-max'],
            'deepseek': ['deepseek-chat', 'deepseek-coder'],
            'kimi': ['moonshot-v1-8k', 'moonshot-v1-32k', 'moonshot-v1-128k'],
            'wenxin': ['ernie-4.0-8k', 'ernie-4.0-128k', 'ernie-3.5-8k'],
            'moonshot': ['moonshot-v1-8k', 'moonshot-v1-32k', 'moonshot-v1-128k'],
        }

        return default_models.get(self.provider_type, [])


class LLMModel(models.Model):
    """
    大模型配置
    """
    MODEL_TYPE_CHOICES = [
        ('chat', '对话模型'),
        ('code', '代码模型'),
        ('embedding', '向量模型'),
        ('vision', '视觉模型'),
        ('reasoning', '推理模型'),
    ]

    provider = models.ForeignKey(
        LLMProvider,
        on_delete=models.CASCADE,
        verbose_name='所属提供商',
        related_name='models'
    )

    name = models.CharField('模型名称', max_length=100)
    model_id = models.CharField('模型ID', max_length=200)
    model_type = models.CharField('模型类型', max_length=20, choices=MODEL_TYPE_CHOICES, default='chat')

    context_window = models.IntegerField('上下文窗口', default=4096, help_text='最大上下文长度')
    max_output_tokens = models.IntegerField('最大输出Token', default=2048)

    supports_streaming = models.BooleanField('支持流式输出', default=True)
    supports_function_call = models.BooleanField('支持函数调用', default=False)
    supports_vision = models.BooleanField('支持视觉', default=False)

    input_price = models.DecimalField('输入价格', max_digits=10, decimal_places=6, blank=True, null=True, help_text='每千Token价格')
    output_price = models.DecimalField('输出价格', max_digits=10, decimal_places=6, blank=True, null=True, help_text='每千Token价格')

    is_active = models.BooleanField('是否启用', default=True)

    created_at = models.DateTimeField('创建时间', default=timezone.now)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        db_table = 'llm_models'
        verbose_name = '大模型配置'
        verbose_name_plural = verbose_name
        ordering = ['provider', 'model_type', 'name']
        unique_together = ['provider', 'model_id']

    def __str__(self):
        return f"{self.provider.name} - {self.name}"


class AgentModelConfig(models.Model):
    """
    Agent模型配置
    为不同类型的Agent配置不同的模型
    """
    AGENT_TYPE_CHOICES = [
        ('collector', '信息收集Agent'),
        ('matcher', '企业比对Agent'),
        ('analyst', '投标论证Agent'),
        ('generator', '标书制作Agent'),
        ('reviewer', '标书审核Agent'),
        ('tracker', '结果查询Agent'),
        ('optimizer', '质量提升Agent'),
        ('orchestrator', '协调器Agent'),
    ]

    agent_type = models.CharField('Agent类型', max_length=20, choices=AGENT_TYPE_CHOICES, unique=True)

    chat_model = models.ForeignKey(
        LLMModel,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='对话模型',
        related_name='chat_agents'
    )
    reasoning_model = models.ForeignKey(
        LLMModel,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='推理模型',
        related_name='reasoning_agents'
    )

    temperature = models.FloatField('温度参数', default=0.7)
    max_tokens = models.IntegerField('最大Token数', default=4096)

    system_prompt = models.TextField('系统提示词', blank=True, null=True)

    is_active = models.BooleanField('是否启用', default=True)

    created_at = models.DateTimeField('创建时间', default=timezone.now)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        db_table = 'agent_model_configs'
        verbose_name = 'Agent模型配置'
        verbose_name_plural = verbose_name
        ordering = ['agent_type']

    def __str__(self):
        return self.get_agent_type_display()


class LLMUsageLog(models.Model):
    """
    大模型使用日志
    """
    provider = models.ForeignKey(
        LLMProvider,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='提供商'
    )
    model = models.CharField('模型名称', max_length=100)
    agent_type = models.CharField('Agent类型', max_length=50, blank=True, null=True)
    session_id = models.CharField('会话ID', max_length=100, blank=True, null=True)

    input_tokens = models.IntegerField('输入Token数', default=0)
    output_tokens = models.IntegerField('输出Token数', default=0)
    total_tokens = models.IntegerField('总Token数', default=0)

    cost = models.DecimalField('费用', max_digits=10, decimal_places=6, default=0)

    latency = models.FloatField('响应时间(秒)', default=0)
    success = models.BooleanField('是否成功', default=True)
    error_message = models.TextField('错误信息', blank=True, null=True)

    request_data = models.JSONField('请求数据', default=dict, blank=True)
    response_data = models.JSONField('响应数据', default=dict, blank=True)

    created_at = models.DateTimeField('创建时间', default=timezone.now)

    class Meta:
        db_table = 'llm_usage_logs'
        verbose_name = '大模型使用日志'
        verbose_name_plural = verbose_name
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['provider', 'created_at']),
            models.Index(fields=['agent_type', 'created_at']),
        ]

    def __str__(self):
        return f"{self.model} - {self.total_tokens} tokens"


class AutomationConfig(models.Model):
    """
    全自动化投标配置
    集中管理AI决策参数、自动匹配参数、模型选择等配置
    """
    name = models.CharField('配置名称', max_length=100, default='默认配置')
    description = models.TextField('配置描述', blank=True)

    is_active = models.BooleanField('是否启用', default=True)
    is_default = models.BooleanField('是否默认', default=False)

    created_at = models.DateTimeField('创建时间', default=timezone.now)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        db_table = 'automation_configs'
        verbose_name = '自动化配置'
        verbose_name_plural = verbose_name
        ordering = ['-is_default', '-created_at']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if self.is_default:
            AutomationConfig.objects.filter(is_default=True).exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)


class AIDecisionConfig(models.Model):
    """
    AI决策参数配置
    控制投标决策引擎的各维度评分权重和阈值
    """
    config = models.ForeignKey(
        AutomationConfig,
        on_delete=models.CASCADE,
        verbose_name='所属配置',
        related_name='decision_configs'
    )

    QUALIFICATION_WEIGHT = models.FloatField('资质匹配权重', default=0.4)
    COMPETITOR_WEIGHT = models.FloatField('竞争对手分析权重', default=0.2)
    PERFORMANCE_WEIGHT = models.FloatField('历史业绩匹配权重', default=0.2)
    RISK_WEIGHT = models.FloatField('风险评估权重', default=0.2)

    AUTO_BID_THRESHOLD = models.IntegerField('自动投标阈值', default=60, help_text='>=此分数自动投标')
    OBSERVATION_THRESHOLD = models.IntegerField('观察阈值', default=40, help_text='>=此分数标记观察')
    SKIP_THRESHOLD = models.IntegerField('跳过阈值', default=40, help_text='<此分数自动跳过')

    USE_AI_DECISION = models.BooleanField('启用AI决策', default=True, help_text='关闭则使用规则匹配')

    created_at = models.DateTimeField('创建时间', default=timezone.now)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        db_table = 'ai_decision_configs'
        verbose_name = 'AI决策配置'
        verbose_name_plural = verbose_name

    def __str__(self):
        return f"AI决策配置 - {self.config.name}"


class AutoMatchConfig(models.Model):
    """
    自动匹配参数配置
    控制招标信息与企业资质的自动匹配逻辑
    """
    config = models.ForeignKey(
        AutomationConfig,
        on_delete=models.CASCADE,
        verbose_name='所属配置',
        related_name='match_configs'
    )

    AUTO_MATCH_ENABLED = models.BooleanField('启用自动匹配', default=True)

    AUTO_IMPORT_THRESHOLD = models.FloatField(
        '自动入库阈值', default=0.8,
        help_text='>=此相似度自动入库（无需确认）'
    )
    AUTO_BID_MATCH_THRESHOLD = models.FloatField(
        '自动投标匹配阈值', default=0.6,
        help_text='>=此相似度进行自动投标'
    )
    EXCLUDE_THRESHOLD = models.FloatField(
        '排除阈值', default=0.6,
        help_text='<此相似度自动排除'
    )

    ADAPTIVE_THRESHOLD = models.BooleanField(
        '自适应阈值调整', default=True,
        help_text='根据匹配质量自动优化阈值'
    )
    LEARNING_FROM_HISTORY = models.BooleanField(
        '从历史结果学习', default=True,
        help_text='根据中标/失标结果自动优化匹配策略'
    )

    KEYWORD_BOOST_ENABLED = models.BooleanField(
        '关键词加权', default=True,
        help_text='匹配时对关键词命中进行加权'
    )
    REGION_BOOST_ENABLED = models.BooleanField(
        '地区加权', default=True,
        help_text='匹配时对地区进行加权'
    )

    created_at = models.DateTimeField('创建时间', default=timezone.now)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        db_table = 'auto_match_configs'
        verbose_name = '自动匹配配置'
        verbose_name_plural = verbose_name

    def __str__(self):
        return f"自动匹配配置 - {self.config.name}"


class DocumentReviewConfig(models.Model):
    """
    文档审核参数配置
    控制标书生成后的AI审核和自动上传逻辑
    """
    config = models.ForeignKey(
        AutomationConfig,
        on_delete=models.CASCADE,
        verbose_name='所属配置',
        related_name='review_configs'
    )

    AUTO_UPLOAD_THRESHOLD = models.IntegerField(
        '自动上传阈值', default=90,
        help_text='>=此分数自动上传标书'
    )
    OBSERVATION_THRESHOLD = models.IntegerField(
        '观察阈值', default=60,
        help_text='>=此分数上传后标记观察'
    )
    MANUAL_REVIEW_THRESHOLD = models.IntegerField(
        '人工审核阈值', default=60,
        help_text='<此分数触发人工审核'
    )

    MAX_OPTIMIZATION_ROUNDS = models.IntegerField(
        '最大优化轮数', default=3,
        help_text='标书审核未通过时的最大自动优化次数'
    )

    ENABLE_ANTI_REJECTION_CHECK = models.BooleanField(
        '启用废标检查', default=True,
        help_text='自动检测可能导致废标的风险项'
    )
    ENABLE_PRICE_ANALYSIS = models.BooleanField(
        '启用报价分析', default=True,
        help_text='分析报价合理性和竞争力'
    )

    USE_SIMULATED_SCORING = models.BooleanField(
        '启用模拟打分', default=True,
        help_text='模拟评委视角对标书进行打分'
    )

    created_at = models.DateTimeField('创建时间', default=timezone.now)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        db_table = 'document_review_configs'
        verbose_name = '文档审核配置'
        verbose_name_plural = verbose_name

    def __str__(self):
        return f"文档审核配置 - {self.config.name}"


class RiskControlConfig(models.Model):
    """
    风险控制参数配置
    控制自动化过程中的各类风险限制
    """
    config = models.ForeignKey(
        AutomationConfig,
        on_delete=models.CASCADE,
        verbose_name='所属配置',
        related_name='risk_configs'
    )

    MAX_DAILY_BIDS = models.IntegerField(
        '每日最大投标数', default=50,
        help_text='超过此数量暂停当日自动投标'
    )
    AMOUNT_THRESHOLD = models.DecimalField(
        '金额阈值', max_digits=15, decimal_places=2, default=1000000,
        help_text='超过此金额的项目需人工确认'
    )
    CONSECUTIVE_FAILURES = models.IntegerField(
        '连续失败上限', default=3,
        help_text='连续失败超过此次数自动暂停'
    )

    ENABLE_AMOUNT_CHECK = models.BooleanField(
        '启用金额检查', default=True
    )
    ENABLE_COUNT_CHECK = models.BooleanField(
        '启用数量检查', default=True
    )
    ENABLE_FAILURE_CHECK = models.BooleanField(
        '启用失败检查', default=True
    )

    AUTO_PAUSE_ON_RISK = models.BooleanField(
        '风险自动暂停', default=True,
        help_text='检测到风险时自动暂停相关任务'
    )

    NOTIFY_ON_RISK = models.BooleanField(
        '风险通知', default=True,
        help_text='检测到风险时发送钉钉通知'
    )

    created_at = models.DateTimeField('创建时间', default=timezone.now)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        db_table = 'risk_control_configs'
        verbose_name = '风险控制配置'
        verbose_name_plural = verbose_name

    def __str__(self):
        return f"风险控制配置 - {self.config.name}"


class CrawlConfig(models.Model):
    """
    采集参数配置
    控制定时采集任务的各项参数
    """
    config = models.ForeignKey(
        AutomationConfig,
        on_delete=models.CASCADE,
        verbose_name='所属配置',
        related_name='crawl_configs'
    )

    AUTO_LEARN_KEYWORDS = models.BooleanField(
        '自动学习关键词', default=True,
        help_text='根据历史中标项目自动优化关键词'
    )
    ADAPTIVE_CRAWL_MODE = models.BooleanField(
        '自适应采集模式', default=True,
        help_text='根据网站情况自动选择最优采集策略'
    )
    MULTI_SOURCE_ENABLED = models.BooleanField(
        '多源采集', default=True,
        help_text='是否启用多网站并行采集'
    )

    DEFAULT_CRAWL_INTERVAL = models.IntegerField(
        '默认采集间隔(分钟)', default=60,
        help_text='定时采集的间隔时间'
    )
    MAX_PAGES_PER_CRAWL = models.IntegerField(
        '每次最大采集页数', default=50
    )

    ENABLE_DEDUP = models.BooleanField(
        '启用去重', default=True
    )

    created_at = models.DateTimeField('创建时间', default=timezone.now)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        db_table = 'crawl_configs'
        verbose_name = '采集配置'
        verbose_name_plural = verbose_name

    def __str__(self):
        return f"采集配置 - {self.config.name}"


class NotificationConfig(models.Model):
    """
    通知参数配置
    控制各类事件的通知方式和范围
    """
    config = models.ForeignKey(
        AutomationConfig,
        on_delete=models.CASCADE,
        verbose_name='所属配置',
        related_name='notification_configs'
    )

    NOTIFICATION_ENABLED = models.BooleanField('启用通知', default=True)
    DINGTALK_ENABLED = models.BooleanField('钉钉通知', default=True)
    KEY_EVENTS_ONLY = models.BooleanField(
        '仅关键事件', default=False,
        help_text='开启后仅对关键事件发送通知'
    )
    DAILY_REPORT_ENABLED = models.BooleanField('日报', default=True)
    WEEKLY_REPORT_ENABLED = models.BooleanField('周报', default=False)

    NOTIFY_ON_START = models.BooleanField('启动通知', default=False)
    NOTIFY_ON_SUCCESS = models.BooleanField('成功通知', default=True)
    NOTIFY_ON_FAILURE = models.BooleanField('失败通知', default=True)
    NOTIFY_ON_WIN = models.BooleanField('中标通知', default=True)
    NOTIFY_ON_LOSS = models.BooleanField('失标通知', default=True)

    created_at = models.DateTimeField('创建时间', default=timezone.now)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        db_table = 'notification_configs'
        verbose_name = '通知配置'
        verbose_name_plural = verbose_name

    def __str__(self):
        return f"通知配置 - {self.config.name}"
