"""
Celery configuration for bid_auto_system project.
支持Redis Cluster作为消息队列
"""
import os
from celery import Celery
from kombu import Queue, Exchange

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('bid_auto_system')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

redis_cluster_hosts = [
    f"redis://{os.getenv('REDIS_CLUSTER_HOST_1', 'localhost')}:{os.getenv('REDIS_CLUSTER_PORT_1', '7000')}/0",
    f"redis://{os.getenv('REDIS_CLUSTER_HOST_2', 'localhost')}:{os.getenv('REDIS_CLUSTER_PORT_2', '7001')}/0",
    f"redis://{os.getenv('REDIS_CLUSTER_HOST_3', 'localhost')}:{os.getenv('REDIS_CLUSTER_PORT_3', '7002')}/0",
]

CELERY_TASK_TRACK_STARTED = False
CELERY_TASK_TIME_LIMIT = 3600
CELERY_TASK_SOFT_TIME_LIMIT = 3000
CELERY_WORKER_PREFETCH_MULTIPLIER = 4
CELERY_WORKER_MAX_TASKS_PER_CHILD = 1000
CELERY_WORKER_DISABLE_RATE_LIMITS = True

CELERY_TASK_QUEUES = [
    Queue('default', Exchange('default'), routing_key='default', max_priority=10),
    Queue('workflow', Exchange('workflow'), routing_key='workflow.#', max_priority=8),
    Queue('crawler', Exchange('crawler'), routing_key='crawler.#', max_priority=6),
    Queue('vector', Exchange('vector'), routing_key='vector.#', max_priority=5),
    Queue('notification', Exchange('notification'), routing_key='notification.#', max_priority=9),
]

CELERY_TASK_ROUTES = {
    'unified_scheduler.tender_scan': {'queue': 'crawler', 'routing_key': 'crawler.scan'},
    'unified_scheduler.bid_auto_submit': {'queue': 'workflow', 'routing_key': 'workflow.bid'},
    'unified_scheduler.result_check': {'queue': 'workflow', 'routing_key': 'workflow.result'},
    'unified_scheduler.vector_cleanup': {'queue': 'vector', 'routing_key': 'vector.cleanup'},
    'unified_scheduler.daily_summary': {'queue': 'notification', 'routing_key': 'notification.summary'},
    'crawler.tasks.*': {'queue': 'crawler', 'routing_key': 'crawler.tasks'},
    'apps.crawler.tasks.*': {'queue': 'crawler', 'routing_key': 'crawler.tasks'},
    'apps.openclaw.tasks.*': {'queue': 'workflow', 'routing_key': 'workflow.agents'},
    'services.vector.tasks.*': {'queue': 'vector', 'routing_key': 'vector.tasks'},
}

CELERY_TASK_DEFAULT_QUEUE = 'default'
CELERY_TASK_DEFAULT_EXCHANGE = 'default'
CELERY_TASK_DEFAULT_ROUTING_KEY = 'default'

CELERY_RESULT_BACKEND_TRANSPORT = 'redis'
CELERY_RESULT_BACKEND_TRANSPORT_OPTIONS = {
    'master_name': os.getenv('REDIS_CLUSTER_MASTER_NAME', 'mymaster'),
    'connections_per_node': 8,
    'cluster_retry_delay': 5,
    'max_retries': 3,
}

CELERY_ACKS_LATE = True
CELERY_TASK_REJECT_ON_WORKER_LOST = True


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
