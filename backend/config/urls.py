"""
URL configuration for bid_auto_system project.
"""
import threading
import time
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse
from django.db import connection
from django.core.cache import cache
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView
from core.constants_views import ConstantsAPIView, ConstantsDetailAPIView
from apps.openclaw.views import SystemModelsView
from apps.knowledge.views import ProjectKnowledgeView, ProjectContextView


_services_cache = {'data': None, 'expires': 0}
_services_cache_lock = threading.Lock()


def api_root(request):
    """
    API根路径视图 - 返回API信息
    """
    return JsonResponse({
        'name': '天齐AI大模型投标平台 API',
        'version': 'v1',
        'status': 'running',
        'endpoints': {
            'auth': '/api/v1/auth/',
            'tenders': '/api/v1/tenders/',
            'documents': '/api/v1/documents/',
            'bids': '/api/v1/bids/',
            'notifications': '/api/v1/notifications/',
            'crawler': '/api/v1/crawler/',
            'enterprise': '/api/v1/enterprise/',
            'openclaw': '/api/v1/openclaw/',
            'vectorlib': '/api/v1/vectorlib/',
            'scheduler': '/api/v1/scheduler/',
            'monitor': '/api/v1/monitor/',
            'progress': '/api/v1/progress/',
            'docs': '/api/v1/docs/',
            'redoc': '/api/v1/redoc/',
        }
    })


def health_check(request):
    """
    健康检查端点 - 用于Docker健康检查和负载均衡器探测
    检查数据库和缓存连接状态
    """
    health_status = {
        'status': 'healthy',
        'database': 'ok',
        'cache': 'ok',
    }

    try:
        with connection.cursor() as cursor:
            cursor.execute('SELECT 1')
    except Exception:
        health_status['database'] = 'error'
        health_status['status'] = 'unhealthy'

    try:
        cache.set('health_check', 'ok', 10)
        if cache.get('health_check') != 'ok':
            raise Exception('Cache not working')
    except Exception:
        health_status['cache'] = 'error'
        health_status['status'] = 'unhealthy'

    status_code = 200 if health_status['status'] == 'healthy' else 503
    return JsonResponse(health_status, status=status_code)


_services_cache = {'data': None, 'expires': 0}
_services_cache_lock = threading.Lock()

def system_services_status(request):
    """
    系统服务状态检查端点
    核心服务快速同步检查，可选服务异步检查，结果缓存10秒
    """
    from django.utils import timezone

    cache_key = 'system_services_status_cache'
    cached = cache.get(cache_key)
    if cached:
        return JsonResponse(cached)

    with _services_cache_lock:
        if _services_cache['data'] and _services_cache['expires'] > time.time():
            cache.set(cache_key, _services_cache['data'], 10)
            return JsonResponse(_services_cache['data'])

    services = []
    overall_status = 'healthy'
    services_lock = threading.Lock()

    service_name_to_id = {}
    display_name_to_db_name = {
        'Django Server': 'django_server',
        'PostgreSQL Database': 'postgresql_database',
        'Redis Cache': 'redis_cache',
        'Redis Queue': 'redis_cache',
        'Celery Worker': 'celery_worker',
        'Celery Beat': 'celery_beat',
        'Chroma VectorDB': 'chroma_vector_db',
        'Milvus VectorDB': 'milvus_vector_db',
        'MinIO Storage': 'minio_storage',
        'Ollama AI': 'ollama_ai',
        'Frontend Dev Server': 'frontend_dev_server',
        'Scheduled Tasks': 'scheduled_tasks',
    }

    try:
        from apps.monitor.models import MonitoredService
        for ms in MonitoredService.objects.all():
            service_name_to_id[ms.name] = ms.id
    except Exception:
        pass

    def add_service(name, status, message, db_id=None):
        db_name = display_name_to_db_name.get(name, name)
        with services_lock:
            services.append({
                'name': name,
                'status': status,
                'message': message,
                'id': db_id if db_id is not None else service_name_to_id.get(db_name)
            })

    add_service('Django Server', 'running', f'服务正常，当前时间: {timezone.now().strftime("%Y-%m-%d %H:%M:%S")}')

    try:
        with connection.cursor() as cursor:
            cursor.execute('SELECT 1')
        add_service('PostgreSQL Database', 'running', '数据库连接正常')
    except Exception as e:
        add_service('PostgreSQL Database', 'error', f'连接失败: {str(e)}')
        overall_status = 'unhealthy'

    try:
        cache.set('health_check', 'ok', 10)
        if cache.get('health_check') != 'ok':
            raise Exception('Cache not working')
        add_service('Redis Cache', 'running', 'Redis连接正常')
    except Exception as e:
        add_service('Redis Cache', 'error', f'连接失败: {str(e)}')
        overall_status = 'unhealthy'

    def check_celery_async():
        try:
            from config.celery import app as celery_app
            inspect = celery_app.control.inspect()
            stats = inspect.stats()
            if stats:
                worker_count = len(stats)
                add_service('Celery Worker', 'running', f'Worker运行中 ({worker_count} 个进程)')
            else:
                add_service('Celery Worker', 'stopped', '无Worker运行')
        except Exception as e:
            add_service('Celery Worker', 'error', f'检查失败: {str(e)}')

    celery_thread = threading.Thread(target=check_celery_async)
    celery_thread.daemon = True
    celery_thread.start()

    def check_chroma_async():
        try:
            from services.vector import document_vector_store
            count = document_vector_store.get_count()
            add_service('Chroma VectorDB', 'running', f'向量库正常 ({count} 条数据)')
        except Exception as e:
            add_service('Chroma VectorDB', 'error', f'连接失败: {str(e)}')

    chroma_thread = threading.Thread(target=check_chroma_async)
    chroma_thread.daemon = True
    chroma_thread.start()

    def check_optional_services():
        import urllib.request
        import ssl
        import logging

        logger = logging.getLogger(__name__)

        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE

        try:
            req = urllib.request.Request('http://localhost:9000/minio/health/live', method='GET')
            with urllib.request.urlopen(req, timeout=2, context=ctx) as response:
                if response.status == 200:
                    add_service('MinIO Storage', 'running', '对象存储服务正常')
                else:
                    raise Exception(f'Status: {response.status}')
        except Exception as e:
            logger.warning(f'MinIO检查失败: {e}')
            add_service('MinIO Storage', 'stopped', 'MinIO未运行（可选服务）')

        try:
            req = urllib.request.Request('http://localhost:11434/api/tags', method='GET')
            with urllib.request.urlopen(req, timeout=2) as response:
                if response.status == 200:
                    import json
                    data = json.loads(response.read().decode())
                    models = data.get('models', [])
                    add_service('Ollama AI', 'running', f'Ollama服务正常 ({len(models)} 个模型)')
                else:
                    raise Exception(f'Status: {response.status}')
        except Exception as e:
            logger.warning(f'Ollama检查失败: {e}')
            add_service('Ollama AI', 'stopped', 'Ollama未运行（AI功能不可用）')

        try:
            req = urllib.request.Request('http://localhost:9091/healthz', method='GET')
            with urllib.request.urlopen(req, timeout=5, context=ctx) as response:
                if response.status == 200:
                    add_service('Milvus VectorDB', 'running', '向量数据库服务正常')
                else:
                    raise Exception(f'Status: {response.status}')
        except Exception as e:
            logger.warning(f'Milvus检查失败: {e}')
            add_service('Milvus VectorDB', 'stopped', 'Milvus未运行（可选服务）')

    optional_thread = threading.Thread(target=check_optional_services)
    optional_thread.daemon = True
    optional_thread.start()

    try:
        from django_celery_beat.models import PeriodicTask
        schedules_count = PeriodicTask.objects.filter(enabled=True).count()
        add_service('Scheduled Tasks', 'running', f'{schedules_count} 个定时任务已配置')
    except Exception as e:
        add_service('Scheduled Tasks', 'unknown', f'检查失败: {str(e)}')

    celery_thread.join(timeout=2)
    chroma_thread.join(timeout=2)
    optional_thread.join(timeout=5)

    result = {
        'status': overall_status,
        'timestamp': timezone.now().isoformat(),
        'services': services
    }

    with _services_cache_lock:
        _services_cache['data'] = result
        _services_cache['expires'] = time.time() + 10

    cache.set(cache_key, result, 10)

    status_code = 200 if overall_status in ['healthy', 'degraded'] else 503

    return JsonResponse(result, status=status_code)


urlpatterns = [
    path('', api_root, name='api_root'),
    path('health/', health_check, name='health_check'),
    path('api/v1/system/services/', system_services_status, name='system_services'),
    path('admin/', admin.site.urls),
    path('api/v1/constants/', ConstantsAPIView.as_view(), name='constants'),
    path('api/v1/constants/<str:constant_type>/', ConstantsDetailAPIView.as_view(), name='constants_detail'),
    path('api/v1/auth/', include('apps.users.urls')),
    path('api/v1/tenders/', include('apps.tenders.urls')),
    path('api/v1/documents/', include('apps.documents.urls')),
    path('api/v1/bids/', include('apps.bids.urls')),
    path('api/v1/notifications/', include('apps.notifications.urls')),
    path('api/v1/crawler/', include('apps.crawler.urls')),
    path('api/v1/enterprise/', include('apps.enterprise.urls')),
    path('api/v1/openclaw/', include('apps.openclaw.urls')),
    path('api/v1/vectorlib/', include('apps.vectorlib.urls')),
    path('api/v1/scheduler/', include('apps.scheduler.urls')),
    path('api/v1/monitor/', include('apps.monitor.urls')),
    path('api/v1/progress/', include('core.progress_urls')),
    path('api/v1/knowledge/', ProjectKnowledgeView.as_view(), name='knowledge'),
    path('api/v1/knowledge/context/', ProjectContextView.as_view(), name='knowledge_context'),
    path('api/v1/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/v1/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/v1/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)


