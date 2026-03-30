"""
URL configuration for bid_auto_system project.
"""
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


def system_services_status(request):
    """
    系统服务状态检查端点
    检查所有相关服务的运行状态
    """
    from django.utils import timezone
    from celery import Celery
    from django_celery_beat.models import PeriodicTask

    services = []
    overall_status = 'healthy'

    services.append({
        'name': 'Django Server',
        'status': 'running',
        'message': f'服务正常，当前时间: {timezone.now().strftime("%Y-%m-%d %H:%M:%S")}'
    })

    try:
        with connection.cursor() as cursor:
            cursor.execute('SELECT 1')
        services.append({'name': 'PostgreSQL Database', 'status': 'running', 'message': '数据库连接正常'})
    except Exception as e:
        services.append({'name': 'PostgreSQL Database', 'status': 'error', 'message': f'连接失败: {str(e)}'})
        overall_status = 'unhealthy'

    try:
        cache.set('health_check', 'ok', 10)
        if cache.get('health_check') != 'ok':
            raise Exception('Cache not working')
        services.append({'name': 'Redis Cache', 'status': 'running', 'message': 'Redis连接正常'})
    except Exception as e:
        services.append({'name': 'Redis Cache', 'status': 'error', 'message': f'连接失败: {str(e)}'})
        overall_status = 'unhealthy'

    try:
        from config.celery import app as celery_app
        inspect = celery_app.control.inspect()
        stats = inspect.stats()
        active = inspect.active()

        if stats:
            worker_count = len(stats)
            services.append({
                'name': 'Celery Worker',
                'status': 'running',
                'message': f'Worker运行中 ({worker_count} 个进程)'
            })
        else:
            services.append({'name': 'Celery Worker', 'status': 'stopped', 'message': '无Worker运行'})
            overall_status = 'degraded'

        beat_info = cache.get('celerybeat_info')
        if beat_info:
            services.append({'name': 'Celery Beat', 'status': 'running', 'message': '调度器运行中'})
        else:
            try:
                periodic_tasks = PeriodicTask.objects.filter(enabled=True).count()
                services.append({
                'name': 'Celery Beat',
                'status': 'running',
                'message': f'调度器运行中 ({periodic_tasks} 个活跃任务)'
            })
            except:
                services.append({'name': 'Celery Beat', 'status': 'stopped', 'message': '调度器未运行'})
                overall_status = 'degraded'
    except Exception as e:
        services.append({'name': 'Celery Worker', 'status': 'error', 'message': f'检查失败: {str(e)}'})
        services.append({'name': 'Celery Beat', 'status': 'unknown', 'message': '无法确定状态'})

    try:
        from services.vector import document_vector_store
        count = document_vector_store.get_count()
        services.append({'name': 'Chroma VectorDB', 'status': 'running', 'message': f'向量库正常 ({count} 条数据)'})
    except Exception as e:
        services.append({'name': 'Chroma VectorDB', 'status': 'error', 'message': f'连接失败: {str(e)}'})
        overall_status = 'degraded'

    try:
        import redis
        r = redis.from_url('redis://localhost:6379/0')
        db_info = r.info('keyspace')
        redis_version = r.info('server').get('redis_version', 'unknown')
        services.append({
            'name': 'Redis Queue',
            'status': 'running',
            'message': f'Redis {redis_version}, DB: {db_info.get("db0", {}).get("keys", 0)} keys'
        })
    except Exception as e:
        services.append({'name': 'Redis Queue', 'status': 'error', 'message': f'连接失败: {str(e)}'})

    try:
        import pymilvus
        connections.connect(alias='default', host='localhost', port='19530', timeout=5)
        connections.connect(alias='default', host='localhost', port='19530', timeout=5)
        services.append({'name': 'Milvus VectorDB', 'status': 'running', 'message': 'Milvus连接正常'})
    except Exception as e:
        services.append({'name': 'Milvus VectorDB', 'status': 'stopped', 'message': 'Milvus未运行（可选服务）'})

    try:
        schedules_count = PeriodicTask.objects.filter(enabled=True).count()
        services.append({
            'name': 'Scheduled Tasks',
            'status': 'running',
            'message': f'{schedules_count} 个定时任务已配置'
        })
    except Exception as e:
        services.append({'name': 'Scheduled Tasks', 'status': 'unknown', 'message': f'检查失败: {str(e)}'})

    try:
        import urllib.request
        import ssl
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        req = urllib.request.Request('http://localhost:9000/minio/health/live', method='GET')
        with urllib.request.urlopen(req, timeout=5, context=ctx) as response:
            if response.status == 200:
                services.append({'name': 'MinIO Storage', 'status': 'running', 'message': '对象存储服务正常'})
            else:
                raise Exception(f'Status: {response.status}')
    except Exception as e:
        services.append({'name': 'MinIO Storage', 'status': 'stopped', 'message': f'MinIO未运行（可选服务）'})

    try:
        import urllib.request
        req = urllib.request.Request('http://localhost:11434/api/tags', method='GET')
        with urllib.request.urlopen(req, timeout=5) as response:
            if response.status == 200:
                import json
                data = json.loads(response.read().decode())
                models = data.get('models', [])
                services.append({
                    'name': 'Ollama AI',
                    'status': 'running',
                    'message': f'Ollama服务正常 ({len(models)} 个模型)'
                })
            else:
                raise Exception(f'Status: {response.status}')
    except Exception as e:
        services.append({'name': 'Ollama AI', 'status': 'stopped', 'message': f'Ollama未运行（AI功能不可用）'})

    try:
        from django.conf import settings
        frontend_url = getattr(settings, 'FRONTEND_DEV_URL', 'http://localhost:8081')
        import urllib.request
        req = urllib.request.Request(frontend_url, method='GET')
        with urllib.request.urlopen(req, timeout=5) as response:
            if response.status == 200:
                services.append({'name': 'Frontend Dev Server', 'status': 'running', 'message': '前端开发服务器正常'})
            else:
                raise Exception(f'Status: {response.status}')
    except Exception as e:
        services.append({'name': 'Frontend Dev Server', 'status': 'stopped', 'message': f'前端服务器未运行'})

    status_code = 200 if overall_status in ['healthy', 'degraded'] else 503

    return JsonResponse({
        'status': overall_status,
        'timestamp': timezone.now().isoformat(),
        'services': services
    }, status=status_code)


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


