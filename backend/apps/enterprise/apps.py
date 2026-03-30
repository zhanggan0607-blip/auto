"""
SAAS企业资料库模块 - Django App配置
"""
from django.apps import AppConfig


class EnterpriseConfig(AppConfig):
    """
    企业资料库应用配置
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.enterprise'
    verbose_name = '企业资料库'
    
    def ready(self):
        """
        应用启动时的初始化
        """
        pass
