"""
Core应用配置
"""
from django.apps import AppConfig


class CoreConfig(AppConfig):
    """
    Core应用配置类
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'
    verbose_name = '核心功能'

    def ready(self):
        """
        应用启动时执行
        """
        from core import crawl_signals
