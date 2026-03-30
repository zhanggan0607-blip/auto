"""
投标文档向量库应用配置
"""
from django.apps import AppConfig


class VectorlibConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.vectorlib'
    verbose_name = '投标文档向量库'
