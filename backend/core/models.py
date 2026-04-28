from django.db import models


class AuditLog(models.Model):
    event_type = models.CharField(max_length=50, db_index=True)
    user_id = models.IntegerField(null=True, blank=True, db_index=True)
    username = models.CharField(max_length=150, blank=True, default='')
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True, default='')
    action = models.CharField(max_length=200, blank=True, default='')
    resource_type = models.CharField(max_length=50, blank=True, null=True)
    resource_id = models.CharField(max_length=100, blank=True, null=True)
    status = models.CharField(max_length=20, default='success')
    request_data = models.JSONField(blank=True, null=True)
    response_data = models.JSONField(blank=True, null=True)
    error_message = models.TextField(blank=True, null=True)
    risk_level = models.CharField(max_length=20, default='info', db_index=True)
    metadata = models.JSONField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = '审计日志'
        verbose_name_plural = '审计日志'
        indexes = [
            models.Index(fields=['event_type', '-created_at']),
            models.Index(fields=['user_id', '-created_at']),
            models.Index(fields=['risk_level', '-created_at']),
        ]

    def __str__(self):
        return f'[{self.event_type}] {self.username} - {self.action}'


class EventStore(models.Model):
    event_id = models.CharField(max_length=36, unique=True, db_index=True)
    event_type = models.CharField(max_length=200, db_index=True)
    source = models.CharField(max_length=50)
    data = models.JSONField(default=dict)
    metadata = models.JSONField(default=dict, blank=True)
    priority = models.IntegerField(default=1)
    correlation_id = models.CharField(max_length=36, null=True, blank=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'event_store'
        ordering = ['-created_at']
