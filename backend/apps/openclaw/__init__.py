"""
OpenClaw Django App
"""
from django.apps import AppConfig


class OpenclawConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.openclaw'
    verbose_name = 'OpenClaw多Agent框架'
