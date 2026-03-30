"""
SAAS企业资料库模块 - 企业信息管理应用
"""
from django.apps import AppConfig


class EnterpriseConfig(AppConfig):
    """
    企业资料库配置
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.enterprise'
    verbose_name = '企业资料库'
