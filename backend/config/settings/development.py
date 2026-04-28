"""
Django development settings - 开发环境配置
"""
from .base import *

DEBUG = True

ALLOWED_HOSTS = ['localhost', '127.0.0.1', '0.0.0.0']

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME', 'auto'),
        'USER': os.getenv('DB_USER', 'postgres'),
        'PASSWORD': os.getenv('DB_PASSWORD', '123456'),
        'HOST': os.getenv('DB_HOST', 'localhost'),
        'PORT': os.getenv('DB_PORT', '5432'),
        'CONN_MAX_AGE': 120,  # 修复：连接池保持 120 秒
        'CONN_HEALTH_CHECKS': True,  # 连接健康检查
        'OPTIONS': {
            'sslmode': os.getenv('DB_SSL_MODE', 'disable'),
        }
    }
}

CORS_ALLOWED_ORIGINS = [
    "http://localhost:9081",
    "http://localhost:8100",
    "http://127.0.0.1:9081",
    "http://127.0.0.1:8100",
]
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]
CORS_ALLOW_METHODS = [
    'DELETE',
    'GET',
    'OPTIONS',
    'PATCH',
    'POST',
    'PUT',
]

INTERNAL_IPS = [
    '127.0.0.1',
]

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'bid-auto-dev-cache',
        'TIMEOUT': 300,
        'OPTIONS': {
            'MAX_ENTRIES': 1000,
        }
    }
}

_dev_redis_password = os.getenv('REDIS_PASSWORD', '')
_dev_redis_auth = f":{_dev_redis_password}@" if _dev_redis_password else ""
CELERY_BROKER_URL = f"redis://{_dev_redis_auth}{os.getenv('REDIS_HOST', 'localhost')}:{os.getenv('REDIS_PORT', '6379')}/{os.getenv('REDIS_DB', '0')}"
CELERY_RESULT_BACKEND = CELERY_BROKER_URL
CELERY_TASK_ALWAYS_EAGER = False  # 修复：启用异步执行，避免阻塞 Web 请求
CELERY_EAGER_PROPAGATES_EXCEPTIONS = True
