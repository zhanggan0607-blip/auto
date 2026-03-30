"""
OpenClaw App配置
"""
from django.apps import AppConfig


class OpenclawConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.openclaw'
    verbose_name = 'OpenClaw多Agent框架'
    
    def ready(self):
        """
        应用启动时初始化
        """
        try:
            from openclaw.skill_registry import skill_registry
            logger = __import__('logging').getLogger(__name__)
            logger.info(f"OpenClaw initialized with {len(skill_registry._skill_metadata)} skills")
        except Exception as e:
            __import__('logging').getLogger(__name__).warning(f"OpenClaw initialization warning: {e}")
