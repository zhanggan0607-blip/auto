"""
初始化监控服务数据
"""
from django.core.management.base import BaseCommand
from apps.monitor.models import MonitoredService


class Command(BaseCommand):
    help = '初始化默认的监控服务配置'

    def handle(self, *args, **options):
        default_services = [
            {
                'name': 'postgresql_database',
                'display_name': 'PostgreSQL 数据库',
                'category': 'database',
                'description': '主数据库服务',
                'health_check_type': 'tcp',
                'health_check_port': 5432,
                'is_critical': True,
            },
            {
                'name': 'redis_cache',
                'display_name': 'Redis 缓存',
                'category': 'cache',
                'description': 'Redis缓存服务',
                'health_check_type': 'tcp',
                'health_check_port': 6379,
                'is_critical': True,
            },
            {
                'name': 'celery_worker',
                'display_name': 'Celery Worker',
                'category': 'queue',
                'description': '异步任务执行器，支持实时检测Worker数量、活跃任务、注册任务',
                'health_check_type': 'celery',
                'is_critical': True,
            },
            {
                'name': 'celery_beat',
                'display_name': 'Celery Beat',
                'category': 'queue',
                'description': '任务调度器，管理系统定时任务',
                'health_check_type': 'celery',
                'is_critical': True,
            },
            {
                'name': 'chroma_vector_db',
                'display_name': 'Chroma 向量数据库',
                'category': 'ai',
                'description': '向量数据库服务',
                'health_check_type': 'http',
                'health_check_url': 'http://localhost:8100/health/',
                'is_critical': False,
            },
            {
                'name': 'minio_storage',
                'display_name': 'MinIO 对象存储',
                'category': 'storage',
                'description': '文件存储服务',
                'health_check_type': 'http',
                'health_check_url': 'http://localhost:9000/minio/health/live',
                'is_critical': False,
            },
            {
                'name': 'ollama_ai',
                'display_name': 'Ollama AI 服务',
                'category': 'ai',
                'description': '本地LLM推理服务',
                'health_check_type': 'http',
                'health_check_url': 'http://localhost:11434/api/tags',
                'is_critical': True,
            },
            {
                'name': 'frontend_dev_server',
                'display_name': '前端开发服务器',
                'category': 'web',
                'description': 'Vue前端开发服务器',
                'health_check_type': 'http',
                'health_check_url': 'http://localhost:9081',
                'is_critical': False,
            },
            {
                'name': 'milvus_vector_db',
                'display_name': 'Milvus 向量数据库',
                'category': 'ai',
                'description': '向量数据库服务（Docker容器）',
                'health_check_type': 'tcp',
                'health_check_port': 19530,
                'is_critical': False,
            },
        ]

        created_count = 0
        updated_count = 0

        for service_data in default_services:
            service, created = MonitoredService.objects.update_or_create(
                name=service_data['name'],
                defaults=service_data
            )
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'创建服务: {service.display_name}')
                )
            else:
                updated_count += 1
                self.stdout.write(
                    self.style.WARNING(f'更新服务: {service.display_name}')
                )

        self.stdout.write(
            self.style.SUCCESS(
                f'\n初始化完成: 创建 {created_count} 个，更新 {updated_count} 个'
            )
        )