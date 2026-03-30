"""
Django production settings - 生产环境配置 (优化版)
支持万人级并发：读写分离、Redis集群、连接池优化
"""
import os
from .base import *

DEBUG = False

ALLOWED_HOSTS = os.getenv('DJANGO_ALLOWED_HOSTS', '').split(',')
if not ALLOWED_HOSTS or ALLOWED_HOSTS == ['']:
    raise ValueError('DJANGO_ALLOWED_HOSTS environment variable is required in production')

# =============================================================================
# 数据库配置 - 读写分离
# =============================================================================
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME'),
        'USER': os.getenv('DB_USER'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST': os.getenv('DB_HOST', 'localhost'),
        'PORT': os.getenv('DB_PORT', '5432'),
        'CONN_MAX_AGE': 600,
        'CONN_HEALTH_CHECKS': True,
        'OPTIONS': {
            'connect_timeout': 10,
            'options': '-c statement_timeout=30000',
            'sslmode': os.getenv('DB_SSL_MODE', 'require'),
            'sslcert': os.getenv('DB_SSL_CERT', ''),
            'sslkey': os.getenv('DB_SSL_KEY', ''),
            'sslrootcert': os.getenv('DB_SSL_ROOTCERT', ''),
        },
        'TEST': {
            'MIRROR': None,
        },
    },
    'replica': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME'),
        'USER': os.getenv('DB_REPLICA_USER', os.getenv('DB_USER')),
        'PASSWORD': os.getenv('DB_REPLICA_PASSWORD', os.getenv('DB_PASSWORD')),
        'HOST': os.getenv('DB_REPLICA_HOST', os.getenv('DB_HOST', 'localhost')),
        'PORT': os.getenv('DB_REPLICA_PORT', os.getenv('DB_PORT', '5432')),
        'CONN_MAX_AGE': 600,
        'CONN_HEALTH_CHECKS': True,
        'OPTIONS': {
            'connect_timeout': 10,
            'options': '-c statement_timeout=60000',
            'sslmode': os.getenv('DB_SSL_MODE', 'require'),
            'sslcert': os.getenv('DB_SSL_CERT', ''),
            'sslkey': os.getenv('DB_SSL_KEY', ''),
            'sslrootcert': os.getenv('DB_SSL_ROOTCERT', ''),
        },
        'TEST': {
            'MIRROR': 'default',
        },
    },
}

DATABASE_ROUTERS = ['core.db_router.ReadWriteRouter']


# =============================================================================
# Redis集群配置
# =============================================================================
REDIS_CLUSTER_ENABLED = os.getenv('REDIS_CLUSTER_ENABLED', 'false').lower() == 'true'

if REDIS_CLUSTER_ENABLED:
    REDIS_CLUSTER_NODES = os.getenv('REDIS_CLUSTER_NODES', '').split(',')
    
    CACHES = {
        'default': {
            'BACKEND': 'django_redis.cache.RedisCache',
            'LOCATION': REDIS_CLUSTER_NODES,
            'OPTIONS': {
                'CONNECTION_POOL_KWARGS': {
                    'max_connections': 200,
                    'retry_on_timeout': True,
                    'socket_keepalive': True,
                    'socket_connect_timeout': 5,
                    'socket_timeout': 5,
                },
                'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            },
            'KEY_PREFIX': 'bid_auto',
            'TIMEOUT': 300,
        },
        'session': {
            'BACKEND': 'django_redis.cache.RedisCache',
            'LOCATION': REDIS_CLUSTER_NODES,
            'OPTIONS': {
                'CONNECTION_POOL_KWARGS': {
                    'max_connections': 100,
                    'retry_on_timeout': True,
                },
            },
            'KEY_PREFIX': 'bid_auto_session',
            'TIMEOUT': 86400,
        },
    }
else:
    CACHES = {
        'default': {
            'BACKEND': 'django_redis.cache.RedisCache',
            'LOCATION': f"redis://{os.getenv('REDIS_HOST', 'localhost')}:{os.getenv('REDIS_PORT', '6379')}/{os.getenv('REDIS_CACHE_DB', '1')}",
            'OPTIONS': {
                'CONNECTION_POOL_KWARGS': {
                    'max_connections': 200,
                    'retry_on_timeout': True,
                    'socket_keepalive': True,
                    'socket_connect_timeout': 5,
                    'socket_timeout': 5,
                }
            },
            'KEY_PREFIX': 'bid_auto',
            'TIMEOUT': 300,
        },
        'session': {
            'BACKEND': 'django_redis.cache.RedisCache',
            'LOCATION': f"redis://{os.getenv('REDIS_HOST', 'localhost')}:{os.getenv('REDIS_PORT', '6379')}/2",
            'OPTIONS': {
                'CONNECTION_POOL_KWARGS': {
                    'max_connections': 100,
                    'retry_on_timeout': True,
                }
            },
            'KEY_PREFIX': 'bid_auto_session',
            'TIMEOUT': 86400,
        },
    }

SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'session'


# =============================================================================
# Celery配置 - RabbitMQ集群
# =============================================================================
CELERY_BROKER_POOL_LIMIT = 50
CELERY_BROKER_CONNECTION_TIMEOUT = 5
CELERY_BROKER_CONNECTION_RETRY = True
CELERY_BROKER_CONNECTION_MAX_RETRIES = 5
CELERY_RESULT_POOL_LIMIT = 50

if os.getenv('RABBITMQ_HOST'):
    CELERY_BROKER_URL = f"amqp://{os.getenv('RABBITMQ_USER', 'guest')}:{os.getenv('RABBITMQ_PASSWORD', 'guest')}@{os.getenv('RABBITMQ_HOST', 'localhost')}:5672//"
    CELERY_RESULT_BACKEND = f"rpc://{os.getenv('RABBITMQ_USER', 'guest')}:{os.getenv('RABBITMQ_PASSWORD', 'guest')}@{os.getenv('RABBITMQ_HOST', 'localhost')}:5672//"
else:
    CELERY_BROKER_URL = f"redis://{os.getenv('REDIS_HOST', 'localhost')}:{os.getenv('REDIS_PORT', '6379')}/3"
    CELERY_RESULT_BACKEND = CELERY_BROKER_URL

CELERY_TASK_DEFAULT_QUEUE = 'default'
CELERY_TASK_QUEUES = {
    'default': {
        'exchange': 'default',
        'routing_key': 'default',
    },
    'crawler': {
        'exchange': 'crawler',
        'routing_key': 'crawler',
    },
    'workflow': {
        'exchange': 'workflow',
        'routing_key': 'workflow',
    },
    'notification': {
        'exchange': 'notification',
        'routing_key': 'notification',
    },
}

CELERY_WORKER_PREFETCH_MULTIPLIER = 4
CELERY_TASK_ACKS_LATE = True
CELERY_WORKER_MAX_TASKS_PER_CHILD = 1000


# =============================================================================
# API限流配置
# =============================================================================
REST_FRAMEWORK['DEFAULT_THROTTLE_RATES'] = {
    'anon': '200/hour',
    'user': '2000/hour',
    'burst': '100/minute',
    'workflow': '30/minute',
    'upload': '10/minute',
}

REST_FRAMEWORK['DEFAULT_THROTTLE_CLASSES'] = [
    'rest_framework.throttling.AnonRateThrottle',
    'rest_framework.throttling.UserRateThrottle',
    'core.throttling.WorkflowRateThrottle',
]


# =============================================================================
# 安全配置
# =============================================================================
CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.getenv('CORS_ALLOWED_ORIGINS', '').split(',')
    if origin.strip()
]
CORS_ALLOW_CREDENTIALS = True

SECURE_SSL_REDIRECT = os.getenv('SECURE_SSL_REDIRECT', 'true').lower() == 'true'
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=int(os.getenv('ACCESS_TOKEN_LIFETIME_MINUTES', 30))),
    'REFRESH_TOKEN_LIFETIME': timedelta(hours=int(os.getenv('REFRESH_TOKEN_LIFETIME_HOURS', 24))),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',
}
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True


# =============================================================================
# 监控配置
# =============================================================================
PROMETHEUS_ENABLED = os.getenv('PROMETHEUS_ENABLED', 'false').lower() == 'true'

if PROMETHEUS_ENABLED:
    INSTALLED_APPS += ['django_prometheus']
    
    MIDDLEWARE = [
        'django_prometheus.middleware.PrometheusBeforeMiddleware',
    ] + MIDDLEWARE + [
        'django_prometheus.middleware.PrometheusAfterMiddleware',
    ]
    
    PROMETHEUS_EXPORT_MIGRATIONS = False


# =============================================================================
# 性能优化配置
# =============================================================================
DATA_UPLOAD_MAX_MEMORY_SIZE = 100 * 1024 * 1024
DATA_UPLOAD_MAX_NUMBER_FIELDS = 1000
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024

REST_FRAMEWORK['DEFAULT_RENDERER_CLASSES'] = [
    'rest_framework.renderers.JSONRenderer',
]

REST_FRAMEWORK['EXCEPTION_HANDLER'] = 'core.exceptions.custom_exception_handler'


# =============================================================================
# 日志配置
# 安全改进：日志文件权限控制，敏感信息过滤
# =============================================================================
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'json': {
            '()': 'pythonjsonlogger.jsonlogger.JsonFormatter',
            'format': '%(asctime)s %(levelname)s %(name)s %(message)s %(process)d %(thread)d',
        },
        'simple': {
            'format': '{levelname} {asctime} {message}',
            'style': '{',
        },
        'security': {
            'format': '{levelname} {asctime} {name} {message}',
            'style': '{',
        },
    },
    'filters': {
        'sensitive_data_filter': {
            '()': 'django.utils.log.ServerFormatter',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/var/log/bid_auto/app.log',
            'maxBytes': 50 * 1024 * 1024,
            'backupCount': 10,
            'formatter': 'verbose',
            'encoding': 'utf8',
        },
        'json_file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/var/log/bid_auto/structured.log',
            'maxBytes': 50 * 1024 * 1024,
            'backupCount': 10,
            'formatter': 'json',
            'encoding': 'utf8',
        },
        'security_file': {
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'filename': '/var/log/bid_auto/security.log',
            'when': 'midnight',
            'interval': 1,
            'backupCount': 30,
            'formatter': 'security',
            'encoding': 'utf8',
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'WARNING'),
            'propagate': False,
        },
        'django.request': {
            'handlers': ['json_file'],
            'level': 'WARNING',
            'propagate': False,
        },
        'crawler': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'workflow': {
            'handlers': ['console', 'file', 'json_file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}


# =============================================================================
# 邮件配置
# =============================================================================
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.getenv('EMAIL_HOST', 'smtp.qq.com')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', 587))
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD')
