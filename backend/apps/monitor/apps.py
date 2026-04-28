"""
Monitor应用配置
"""
import os
import logging
from django.apps import AppConfig

logger = logging.getLogger(__name__)


class MonitorConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.monitor'
    verbose_name = '服务监控'

    def ready(self):
        import apps.monitor.signals  # noqa: F401

        if os.environ.get('RUN_MAIN', 'false') == 'true' or not os.environ.get('DJANGO_AUTORELOAD', False):
            self._register_default_services()

    def _register_default_services(self):
        """启动时自动注册默认服务"""
        from django.conf import settings

        if getattr(settings, 'SKIP_AUTO_REGISTER_SERVICES', False):
            return

        default_services = [
            {
                'name': 'django_server',
                'display_name': 'Django Server',
                'category': 'web',
                'health_check_type': 'http',
                'health_check_url': 'http://localhost:8100/health/',
                'description': 'Django后端服务',
                'is_critical': True,
                'auto_restart_enabled': False,
            },
            {
                'name': 'celery_worker',
                'display_name': 'Celery Worker',
                'category': 'queue',
                'health_check_type': 'celery',
                'description': 'Celery异步任务Worker，负责执行爬虫、数据处理等异步任务',
                'is_critical': True,
                'auto_restart_enabled': True,
            },
            {
                'name': 'celery_beat',
                'display_name': 'Celery Beat',
                'category': 'queue',
                'health_check_type': 'celery',
                'description': 'Celery定时任务调度器，负责触发定时任务',
                'is_critical': True,
                'auto_restart_enabled': True,
            },
            {
                'name': 'postgresql_database',
                'display_name': 'PostgreSQL Database',
                'category': 'database',
                'health_check_type': 'tcp',
                'health_check_port': 5432,
                'description': 'PostgreSQL主数据库',
                'is_critical': True,
                'auto_restart_enabled': False,
            },
            {
                'name': 'redis_cache',
                'display_name': 'Redis Cache',
                'category': 'cache',
                'health_check_type': 'tcp',
                'health_check_port': 6379,
                'description': 'Redis缓存和消息队列',
                'is_critical': True,
                'auto_restart_enabled': False,
            },
            {
                'name': 'chroma_vector_db',
                'display_name': 'Chroma VectorDB',
                'category': 'ai',
                'health_check_type': 'http',
                'health_check_url': 'http://localhost:8100/health/',
                'description': 'Chroma向量数据库',
                'is_critical': False,
                'auto_restart_enabled': False,
            },
            {
                'name': 'minio_storage',
                'display_name': 'MinIO Storage',
                'category': 'storage',
                'health_check_type': 'http',
                'health_check_url': 'http://localhost:9000/minio/health/live',
                'description': 'MinIO对象存储服务',
                'is_critical': False,
                'auto_restart_enabled': False,
            },
            {
                'name': 'ollama_ai',
                'display_name': 'Ollama AI',
                'category': 'ai',
                'health_check_type': 'http',
                'health_check_url': 'http://localhost:11434/api/tags',
                'description': 'Ollama本地AI模型服务',
                'is_critical': False,
                'auto_restart_enabled': False,
            },
        ]

        try:
            from apps.monitor.models import MonitoredService
            registered_count = 0
            for service_data in default_services:
                service_name = service_data.pop('name')
                _, created = MonitoredService.objects.update_or_create(
                    name=service_name,
                    defaults=service_data
                )
                if created:
                    registered_count += 1
                    logger.info(f"自动注册监控服务: {service_name}")

            if registered_count > 0:
                logger.info(f"成功自动注册 {registered_count} 个监控服务")
        except Exception:
            pass
