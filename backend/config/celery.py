"""
Celery configuration for bid_auto_system project.
"""
import os
from celery import Celery
from kombu import Queue, Exchange

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')

app = Celery('bid_auto_system')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

CELERY_TASK_TRACK_STARTED = False
CELERY_TASK_TIME_LIMIT = 900
CELERY_TASK_SOFT_TIME_LIMIT = 720
CELERY_WORKER_PREFETCH_MULTIPLIER = 4
CELERY_WORKER_MAX_TASKS_PER_CHILD = 1000
CELERY_WORKER_DISABLE_RATE_LIMITS = True
CELERY_RESULT_EXPIRES = 3600

CELERY_TASK_QUEUES = (
    Queue('default', Exchange('default'), routing_key='default', max_priority=10),
    Queue('notification', Exchange('notification'), routing_key='notification.#', max_priority=9),
    Queue('workflow', Exchange('workflow'), routing_key='workflow.#', max_priority=8),
    Queue('crawler', Exchange('crawler'), routing_key='crawler.#', max_priority=6),
    Queue('vector', Exchange('vector'), routing_key='vector.#', max_priority=5),
)

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

CELERY_ACKS_LATE = True
CELERY_TASK_REJECT_ON_WORKER_LOST = True


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    import logging
    logging.getLogger(__name__).debug(f'Request: {self.request!r}')
