"""
Monitor数据模型
包含被监控服务配置、健康检查记录、告警记录和操作日志
"""
from django.db import models
from django.utils import timezone


class ServiceCategory(models.TextChoices):
    DATABASE = 'database', '数据库'
    CACHE = 'cache', '缓存'
    QUEUE = 'queue', '消息队列'
    AI = 'ai', 'AI服务'
    STORAGE = 'storage', '存储'
    CRAWLER = 'crawler', '采集服务'
    WEB = 'web', 'Web服务'
    OTHER = 'other', '其他'


class ServiceStatus(models.TextChoices):
    HEALTHY = 'healthy', '健康'
    DEGRADED = 'degraded', '性能下降'
    UNHEALTHY = 'unhealthy', '异常'
    RESTARTING = 'restarting', '重启中'
    UNKNOWN = 'unknown', '未知'
    OFFLINE = 'offline', '离线'


class AlertLevel(models.TextChoices):
    INFO = 'info', '通知'
    WARNING = 'warning', '警告'
    ERROR = 'error', '错误'
    CRITICAL = 'critical', '严重'


class AlertStatus(models.TextChoices):
    PENDING = 'pending', '待处理'
    NOTIFIED = 'notified', '已通知'
    RESOLVED = 'resolved', '已解决'
    IGNORED = 'ignored', '已忽略'


class MonitoredService(models.Model):
    """
    被监控服务配置表
    """
    name = models.CharField('服务名称', max_length=100, unique=True)
    display_name = models.CharField('显示名称', max_length=200)
    category = models.CharField(
        '服务类别',
        max_length=20,
        choices=ServiceCategory.choices,
        default=ServiceCategory.OTHER
    )
    description = models.TextField('服务描述', blank=True, default='')

    health_check_url = models.URLField('健康检查URL', blank=True, null=True)
    health_check_port = models.IntegerField('健康检查端口', blank=True, null=True)
    health_check_type = models.CharField(
        '检查类型',
        max_length=20,
        choices=[
            ('http', 'HTTP请求'),
            ('tcp', 'TCP端口'),
            ('process', '进程检测'),
            ('celery', 'Celery服务'),
            ('custom', '自定义'),
        ],
        default='http'
    )
    health_check_interval = models.IntegerField('检查间隔(秒)', default=30)
    health_check_timeout = models.IntegerField('检查超时(秒)', default=10)

    consecutive_failures_to_restart = models.IntegerField(
        '连续失败次数触发重启',
        default=3
    )
    consecutive_failures_to_alert = models.IntegerField(
        '连续失败次数触发告警',
        default=3
    )
    restart_cooldown_minutes = models.IntegerField('重启冷却时间(分钟)', default=5)
    max_restart_attempts = models.IntegerField('最大重启尝试次数', default=3)

    is_enabled = models.BooleanField('是否启用监控', default=True)
    is_critical = models.BooleanField('是否关键服务', default=False)
    auto_restart_enabled = models.BooleanField('是否启用自动重启', default=True)

    last_health_check = models.DateTimeField('上次健康检查', blank=True, null=True)
    last_restart_time = models.DateTimeField('上次重启时间', blank=True, null=True)
    consecutive_failures = models.IntegerField('连续失败次数', default=0)
    restart_attempts_today = models.IntegerField('今日重启次数', default=0)

    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        db_table = 'monitored_services'
        ordering = ['category', 'name']
        verbose_name = '被监控服务'
        verbose_name_plural = '被监控服务'

    def __str__(self):
        return f"{self.display_name} ({self.status})"

    @property
    def status(self) -> str:
        """获取服务当前状态"""
        if not self.is_enabled:
            return ServiceStatus.OFFLINE
        if self.consecutive_failures >= self.consecutive_failures_to_restart:
            if self.last_restart_time and \
               (timezone.now() - self.last_restart_time).total_seconds() < 300:
                return ServiceStatus.RESTARTING
        if self.consecutive_failures >= self.consecutive_failures_to_alert:
            return ServiceStatus.UNHEALTHY
        if self.consecutive_failures > 0:
            return ServiceStatus.DEGRADED
        return ServiceStatus.HEALTHY


class ServiceHealthRecord(models.Model):
    """
    服务健康检查历史记录
    """
    service = models.ForeignKey(
        MonitoredService,
        on_delete=models.CASCADE,
        related_name='health_records'
    )
    timestamp = models.DateTimeField('检查时间', default=timezone.now)

    is_healthy = models.BooleanField('是否健康')
    response_time_ms = models.IntegerField('响应时间(毫秒)', blank=True, null=True)
    cpu_usage = models.FloatField('CPU使用率(%)', blank=True, null=True)
    memory_usage = models.FloatField('内存使用率(%)', blank=True, null=True)

    error_message = models.TextField('错误信息', blank=True, default='')
    details = models.JSONField('详细信息', default=dict, blank=True)

    created_at = models.DateTimeField('创建时间', auto_now_add=True)

    class Meta:
        db_table = 'service_health_records'
        ordering = ['-timestamp']
        verbose_name = '健康检查记录'
        verbose_name_plural = '健康检查记录'
        indexes = [
            models.Index(fields=['service', '-timestamp']),
            models.Index(fields=['-timestamp']),
        ]

    def __str__(self):
        status = '健康' if self.is_healthy else '异常'
        return f"{self.service.display_name} - {status} @ {self.timestamp}"


class ServiceAlert(models.Model):
    """
    服务告警记录
    """
    service = models.ForeignKey(
        MonitoredService,
        on_delete=models.CASCADE,
        related_name='alerts'
    )

    level = models.CharField(
        '告警级别',
        max_length=20,
        choices=AlertLevel.choices,
        default=AlertLevel.ERROR
    )
    status = models.CharField(
        '告警状态',
        max_length=20,
        choices=AlertStatus.choices,
        default=AlertStatus.PENDING
    )

    title = models.CharField('告警标题', max_length=200)
    message = models.TextField('告警消息')

    triggered_by = models.CharField('触发原因', max_length=100, blank=True, default='')
    consecutive_failures = models.IntegerField('连续失败次数', default=0)

    notified_at = models.DateTimeField('通知时间', blank=True, null=True)
    resolved_at = models.DateTimeField('解决时间', blank=True, null=True)

    actions_taken = models.JSONField('已执行操作', default=list, blank=True)

    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        db_table = 'service_alerts'
        ordering = ['-created_at']
        verbose_name = '服务告警'
        verbose_name_plural = '服务告警'
        indexes = [
            models.Index(fields=['service', '-created_at']),
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['level', '-created_at']),
        ]

    def __str__(self):
        return f"{self.service.display_name} - {self.get_level_display()}: {self.title}"


class ServiceActionLog(models.Model):
    """
    服务操作日志
    记录所有自动和手动操作
    """
    service = models.ForeignKey(
        MonitoredService,
        on_delete=models.CASCADE,
        related_name='action_logs'
    )

    action_type = models.CharField(
        '操作类型',
        max_length=50,
        choices=[
            ('health_check', '健康检查'),
            ('auto_restart', '自动重启'),
            ('manual_restart', '手动重启'),
            ('manual_check', '手动检查'),
            ('alert_sent', '发送告警'),
            ('cooling_wait', '冷却等待'),
        ]
    )

    status = models.CharField(
        '操作状态',
        max_length=20,
        choices=[
            ('started', '开始'),
            ('success', '成功'),
            ('failed', '失败'),
            ('skipped', '跳过'),
        ]
    )

    started_at = models.DateTimeField('开始时间', default=timezone.now)
    completed_at = models.DateTimeField('完成时间', blank=True, null=True)
    duration_ms = models.IntegerField('耗时(毫秒)', blank=True, null=True)

    trigger_condition = models.CharField('触发条件', max_length=200, blank=True, default='')
    result_message = models.TextField('结果消息', blank=True, default='')
    error_details = models.TextField('错误详情', blank=True, default='')

    performed_by = models.CharField('执行者', max_length=100, default='system')
    details = models.JSONField('详细信息', default=dict, blank=True)

    class Meta:
        db_table = 'service_action_logs'
        ordering = ['-started_at']
        verbose_name = '服务操作日志'
        verbose_name_plural = '服务操作日志'
        indexes = [
            models.Index(fields=['service', '-started_at']),
            models.Index(fields=['action_type', '-started_at']),
            models.Index(fields=['-started_at']),
        ]

    def __str__(self):
        return f"{self.service.display_name} - {self.get_action_type_display()} @ {self.started_at}"

    def save(self, *args, **kwargs):
        if self.completed_at and self.started_at:
            self.duration_ms = int(
                (self.completed_at - self.started_at).total_seconds() * 1000
            )
        super().save(*args, **kwargs)