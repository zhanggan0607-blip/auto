"""
统一调度应用配置
"""
from django.apps import AppConfig


class SchedulerConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.scheduler'
    verbose_name = '统一调度管理'
