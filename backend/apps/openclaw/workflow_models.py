"""
多Agent工作流模型
定义投标全流程的工作流
"""
from django.db import models
from django.conf import settings
from django.utils import timezone


class BidWorkflow(models.Model):
    """
    投标工作流
    """
    WORKFLOW_STATUS_CHOICES = [
        ('pending', '待开始'),
        ('collecting', '信息收集中'),
        ('matching', '企业比对中'),
        ('analyzing', '投标论证中'),
        ('generating', '标书制作中'),
        ('reviewing', '标书审核中'),
        ('optimizing', '标书优化中'),
        ('uploading', '标书上传中'),
        ('tracking', '结果跟踪中'),
        ('completed', '已完成'),
        ('cancelled', '已取消'),
        ('failed', '执行失败'),
    ]

    name = models.CharField('工作流名称', max_length=200)
    tender = models.ForeignKey(
        'tenders.TenderProject',
        on_delete=models.CASCADE,
        verbose_name='招标项目',
        related_name='workflows'
    )

    status = models.CharField('状态', max_length=20, choices=WORKFLOW_STATUS_CHOICES, default='pending')
    current_stage = models.CharField('当前阶段', max_length=50, blank=True, null=True)

    session_id = models.CharField('会话ID', max_length=100, unique=True)

    config = models.JSONField('工作流配置', default=dict, blank=True)
    context = models.JSONField('工作流上下文', default=dict, blank=True)

    result_summary = models.TextField('结果摘要', blank=True, null=True)

    started_at = models.DateTimeField('开始时间', blank=True, null=True)
    completed_at = models.DateTimeField('完成时间', blank=True, null=True)

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
        db_table = 'bid_workflows'
        verbose_name = '投标工作流'
        verbose_name_plural = verbose_name
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} - {self.get_status_display()}"


class WorkflowStage(models.Model):
    """
    工作流阶段
    """
    STAGE_TYPE_CHOICES = [
        ('collect', '信息收集'),
        ('match', '企业比对'),
        ('analyze', '投标论证'),
        ('generate', '标书制作'),
        ('review', '标书审核'),
        ('optimize', '标书优化'),
        ('upload', '标书上传'),
        ('track', '结果跟踪'),
    ]

    STAGE_STATUS_CHOICES = [
        ('pending', '待执行'),
        ('running', '执行中'),
        ('completed', '已完成'),
        ('skipped', '已跳过'),
        ('failed', '执行失败'),
    ]

    workflow = models.ForeignKey(
        BidWorkflow,
        on_delete=models.CASCADE,
        verbose_name='工作流',
        related_name='stages'
    )

    stage_type = models.CharField('阶段类型', max_length=20, choices=STAGE_TYPE_CHOICES)
    stage_name = models.CharField('阶段名称', max_length=100)
    stage_order = models.IntegerField('阶段顺序', default=0)

    status = models.CharField('状态', max_length=20, choices=STAGE_STATUS_CHOICES, default='pending')

    agent_id = models.CharField('执行Agent ID', max_length=100, blank=True, null=True)
    agent_type = models.CharField('Agent类型', max_length=50, blank=True, null=True)

    input_data = models.JSONField('输入数据', default=dict, blank=True)
    output_data = models.JSONField('输出数据', default=dict, blank=True)

    error_message = models.TextField('错误信息', blank=True, null=True)
    retry_count = models.IntegerField('重试次数', default=0)

    started_at = models.DateTimeField('开始时间', blank=True, null=True)
    completed_at = models.DateTimeField('完成时间', blank=True, null=True)
    duration = models.IntegerField('耗时(秒)', default=0)

    created_at = models.DateTimeField('创建时间', default=timezone.now)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        db_table = 'workflow_stages'
        verbose_name = '工作流阶段'
        verbose_name_plural = verbose_name
        ordering = ['workflow', 'stage_order']
        unique_together = ['workflow', 'stage_type']

    def __str__(self):
        return f"{self.workflow.name} - {self.stage_name}"

    def start(self):
        """
        开始执行
        """
        self.status = 'running'
        self.started_at = timezone.now()
        self.save()

    def complete(self, output_data: dict = None):
        """
        完成
        """
        self.status = 'completed'
        self.completed_at = timezone.now()
        if self.started_at:
            self.duration = (self.completed_at - self.started_at).total_seconds()
        if output_data:
            self.output_data = output_data
        self.save()

    def fail(self, error_message: str):
        """
        失败
        """
        self.status = 'failed'
        self.error_message = error_message
        self.completed_at = timezone.now()
        if self.started_at:
            self.duration = (self.completed_at - self.started_at).total_seconds()
        self.save()


class AgentTask(models.Model):
    """
    Agent任务
    """
    TASK_STATUS_CHOICES = [
        ('pending', '待执行'),
        ('running', '执行中'),
        ('completed', '已完成'),
        ('failed', '执行失败'),
    ]

    stage = models.ForeignKey(
        WorkflowStage,
        on_delete=models.CASCADE,
        verbose_name='工作流阶段',
        related_name='tasks',
        null=True,
        blank=True
    )

    agent_type = models.CharField('Agent类型', max_length=50, default='collector')
    agent_id = models.CharField('Agent ID', max_length=100, blank=True, null=True)

    task_name = models.CharField('任务名称', max_length=200, default='')
    task_type = models.CharField('任务类型', max_length=50, default='default')

    input_data = models.JSONField('输入数据', default=dict, blank=True)
    output_data = models.JSONField('输出数据', default=dict, blank=True)

    status = models.CharField('状态', max_length=20, choices=TASK_STATUS_CHOICES, default='pending')

    llm_calls = models.IntegerField('LLM调用次数', default=0)
    total_tokens = models.IntegerField('总Token数', default=0)

    error_message = models.TextField('错误信息', blank=True, null=True)

    started_at = models.DateTimeField('开始时间', blank=True, null=True)
    completed_at = models.DateTimeField('完成时间', blank=True, null=True)
    duration = models.IntegerField('耗时(秒)', default=0)

    created_at = models.DateTimeField('创建时间', default=timezone.now)

    class Meta:
        db_table = 'agent_tasks'
        verbose_name = 'Agent任务'
        verbose_name_plural = verbose_name
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.task_name} - {self.get_status_display()}"


class AgentMessage(models.Model):
    """
    Agent消息记录
    """
    MESSAGE_TYPE_CHOICES = [
        ('user', '用户消息'),
        ('assistant', '助手消息'),
        ('system', '系统消息'),
        ('agent', 'Agent消息'),
    ]

    workflow = models.ForeignKey(
        BidWorkflow,
        on_delete=models.CASCADE,
        verbose_name='工作流',
        related_name='messages'
    )

    agent_type = models.CharField('Agent类型', max_length=50, blank=True, null=True)
    agent_id = models.CharField('Agent ID', max_length=100, blank=True, null=True)

    message_type = models.CharField('消息类型', max_length=20, choices=MESSAGE_TYPE_CHOICES)
    content = models.TextField('消息内容')

    metadata = models.JSONField('元数据', default=dict, blank=True)

    created_at = models.DateTimeField('创建时间', default=timezone.now)

    class Meta:
        db_table = 'agent_messages'
        verbose_name = 'Agent消息'
        verbose_name_plural = verbose_name
        ordering = ['created_at']

    def __str__(self):
        return f"[{self.message_type}] {self.content[:50]}..."


class BidDecision(models.Model):
    """
    投标决策记录
    """
    DECISION_TYPE_CHOICES = [
        ('participate', '参与投标'),
        ('skip', '放弃投标'),
        ('pending', '待决策'),
    ]

    workflow = models.OneToOneField(
        BidWorkflow,
        on_delete=models.CASCADE,
        verbose_name='工作流',
        related_name='decision'
    )

    decision_type = models.CharField('决策结果', max_length=20, choices=DECISION_TYPE_CHOICES, default='pending')

    match_score = models.FloatField('匹配得分', default=0)
    match_details = models.JSONField('匹配详情', default=dict, blank=True)

    risk_analysis = models.TextField('风险分析', blank=True, null=True)
    opportunity_analysis = models.TextField('机会分析', blank=True, null=True)

    recommendation = models.TextField('AI建议', blank=True, null=True)
    recommendation_score = models.IntegerField('推荐分数', blank=True, null=True, help_text='0-100')

    reasoning_process = models.TextField('推理过程', blank=True, null=True)

    final_decision = models.CharField('最终决策', max_length=20, blank=True, null=True)
    decision_reason = models.TextField('决策理由', blank=True, null=True)

    decided_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='决策人'
    )
    decided_at = models.DateTimeField('决策时间', blank=True, null=True)

    created_at = models.DateTimeField('创建时间', default=timezone.now)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        db_table = 'bid_decisions'
        verbose_name = '投标决策'
        verbose_name_plural = verbose_name

    def __str__(self):
        return f"{self.workflow.name} - {self.get_decision_type_display()}"


class DocumentReview(models.Model):
    """
    标书审核记录
    """
    workflow = models.ForeignKey(
        BidWorkflow,
        on_delete=models.CASCADE,
        verbose_name='工作流',
        related_name='reviews'
    )

    document = models.ForeignKey(
        'documents.GeneratedDocument',
        on_delete=models.CASCADE,
        verbose_name='文档',
        related_name='reviews'
    )

    overall_score = models.IntegerField('总体评分', default=0, help_text='0-100分')
    pass_threshold = models.IntegerField('通过阈值', default=90)

    compliance_score = models.IntegerField('合规性评分', default=0)
    completeness_score = models.IntegerField('完整性评分', default=0)
    quality_score = models.IntegerField('质量评分', default=0)
    competitiveness_score = models.IntegerField('竞争力评分', default=0)

    strengths = models.JSONField('优势点', default=list, blank=True)
    weaknesses = models.JSONField('待改进点', default=list, blank=True)
    suggestions = models.JSONField('优化建议', default=list, blank=True)

    comparison_with_tender = models.TextField('与招标文件对比分析', blank=True, null=True)
    risk_points = models.JSONField('风险点', default=list, blank=True)

    is_passed = models.BooleanField('是否通过', default=False)
    needs_optimization = models.BooleanField('需要优化', default=False)

    review_details = models.JSONField('审核详情', default=dict, blank=True)

    created_at = models.DateTimeField('创建时间', default=timezone.now)

    class Meta:
        db_table = 'document_reviews'
        verbose_name = '标书审核'
        verbose_name_plural = verbose_name
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.document.name} - {self.overall_score}分"

    def calculate_overall_score(self):
        """
        计算总体评分
        """
        weights = {
            'compliance': 0.35,
            'completeness': 0.25,
            'quality': 0.25,
            'competitiveness': 0.15
        }

        self.overall_score = int(
            self.compliance_score * weights['compliance'] +
            self.completeness_score * weights['completeness'] +
            self.quality_score * weights['quality'] +
            self.competitiveness_score * weights['competitiveness']
        )

        self.is_passed = self.overall_score >= self.pass_threshold
        self.needs_optimization = self.overall_score < self.pass_threshold

        return self.overall_score
