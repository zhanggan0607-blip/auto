"""
Django base settings - 所有环境共享的配置
安全改进：生产环境强制检查密钥配置，禁止使用弱密码和默认密钥
"""
import os
import re
import secrets
from pathlib import Path
from datetime import timedelta

BASE_DIR = Path(__file__).resolve().parent.parent.parent

ENVIRONMENT = os.getenv('DJANGO_ENV', 'development')
DEBUG = os.getenv('DEBUG', 'True').lower() == 'true'

def _check_production_security():
    """
    生产环境安全检查
    检查密钥配置是否符合安全要求
    """
    if ENVIRONMENT != 'production':
        return

    errors = []

    secret_key = os.getenv('DJANGO_SECRET_KEY', '')
    if not secret_key or len(secret_key) < 50:
        errors.append('DJANGO_SECRET_KEY must be at least 50 characters long in production')
    if 'CHANGE-ME' in secret_key or 'CHANGE' in secret_key:
        errors.append('DJANGO_SECRET_KEY contains default/placeholder value')

    sensitive_key = os.getenv('SENSITIVE_DATA_ENCRYPTION_KEY', '')
    if not sensitive_key or len(sensitive_key) < 32:
        errors.append('SENSITIVE_DATA_ENCRYPTION_KEY must be at least 32 characters in production')
    if 'CHANGE-ME' in sensitive_key or 'CHANGE' in sensitive_key:
        errors.append('SENSITIVE_DATA_ENCRYPTION_KEY contains default/placeholder value')

    db_password = os.getenv('DB_PASSWORD', '')
    if len(db_password) < 12:
        errors.append('DB_PASSWORD must be at least 12 characters long in production')
    if not re.search(r'[A-Z]', db_password):
        errors.append('DB_PASSWORD must contain at least one uppercase letter')
    if not re.search(r'[a-z]', db_password):
        errors.append('DB_PASSWORD must contain at least one lowercase letter')
    if not re.search(r'[0-9]', db_password):
        errors.append('DB_PASSWORD must contain at least one digit')
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', db_password):
        errors.append('DB_PASSWORD must contain at least one special character')

    if errors:
        error_msg = '\n'.join([f'  - {e}' for e in errors])
        raise ValueError(f'Production security check failed:\n{error_msg}\nPlease fix your environment variables.')

if ENVIRONMENT == 'production':
    _check_production_security()
    load_dotenv = None
    SECRET_KEY = os.getenv('DJANGO_SECRET_KEY')
    if not SECRET_KEY:
        raise ValueError('DJANGO_SECRET_KEY environment variable is required in production')
else:
    from dotenv import load_dotenv
    load_dotenv()
    SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'dev-only-insecure-key-do-not-use-in-production')

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework_simplejwt.token_blacklist',
    'corsheaders',
    'django_filters',
    'drf_spectacular',
    'django_celery_beat',
    'common',
    'core',
    'apps.users',
    'apps.tenders',
    'apps.documents',
    'apps.bids',
    'apps.notifications',
    'apps.crawler',
    'apps.enterprise',
    'apps.openclaw',
    'apps.vectorlib',
    'apps.scheduler',
    'apps.knowledge',
    'apps.monitor',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'core.middleware.RequestLoggingMiddleware',
    'core.middleware_tenant.TenantBoundaryMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', 'OPTIONS': {'min_length': 8}},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'zh-hans'
TIME_ZONE = 'Asia/Shanghai'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

AUTH_USER_MODEL = 'users.User'

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'utils.authentication.CookieJWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
    ],
    'DEFAULT_PAGINATION_CLASS': 'core.pagination.StandardPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DATETIME_FORMAT': '%Y-%m-%d %H:%M:%S',
    'DATE_FORMAT': '%Y-%m-%d',
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/hour',
        'user': '1000/hour',
        'burst': '60/minute',
    },
    'EXCEPTION_HANDLER': 'core.exceptions.custom_exception_handler',
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=2),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'AUTH_HEADER_TYPES': ('Bearer',),
}

CELERY_BROKER_URL = f"redis://{os.getenv('REDIS_HOST', 'localhost')}:{os.getenv('REDIS_PORT', '6379')}/{os.getenv('REDIS_DB', '0')}"
CELERY_RESULT_BACKEND = CELERY_BROKER_URL
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE
CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'

ALIYUN_OCR_CONFIG = {
    'ACCESS_KEY_ID': os.getenv('ALIYUN_OCR_ACCESS_KEY_ID', ''),
    'ACCESS_KEY_SECRET': os.getenv('ALIYUN_OCR_ACCESS_KEY_SECRET', ''),
    'ENDPOINT': 'ocr-api.cn-hangzhou.aliyuncs.com',
}

DINGTALK_WEBHOOK_URL = os.getenv('DINGTALK_WEBHOOK_URL', '')

DINGTALK_SECRET = os.getenv('DINGTALK_SECRET', '')

CHROMA_CONFIG = {
    'PERSIST_DIRECTORY': BASE_DIR / 'chroma_db',
    'COLLECTION_NAME': 'enterprise_embeddings',
}

EMBEDDING_CONFIG = {
    'MODEL_TYPE': os.getenv('EMBEDDING_MODEL_TYPE', 'openai'),
    'OPENAI_API_KEY': os.getenv('OPENAI_API_KEY', ''),
    'OPENAI_EMBEDDING_MODEL': 'text-embedding-3-small',
    'LOCAL_MODEL': 'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2',
}

MINIO_CONFIG = {
    'ENDPOINT': os.getenv('MINIO_ENDPOINT', 'localhost:9000'),
    'ACCESS_KEY': os.getenv('MINIO_ACCESS_KEY'),
    'SECRET_KEY': os.getenv('MINIO_SECRET_KEY'),
    'SECURE': os.getenv('MINIO_SECURE', 'false').lower() == 'true',
    'BUCKET_NAME': os.getenv('MINIO_BUCKET_NAME', 'bid-documents'),
}

DEBUG = os.getenv('DEBUG', 'True').lower() == 'true'

if not MINIO_CONFIG['ACCESS_KEY'] or not MINIO_CONFIG['SECRET_KEY']:
    if DEBUG:
        import warnings
        warnings.warn(
            'MinIO 凭证未设置，开发环境使用默认凭证。生产环境必须设置强密码！',
            RuntimeWarning
        )
        MINIO_CONFIG['ACCESS_KEY'] = 'minioadmin'
        MINIO_CONFIG['SECRET_KEY'] = 'minioadmin'
    else:
        raise ValueError('MINIO_ACCESS_KEY 和 MINIO_SECRET_KEY 环境变量必须设置')

def _parse_pilot_websites():
    """
    解析PILOT_WEBSITES环境变量
    格式：名称:代码:URL|名称:代码:URL
    示例：上海市政府采购网:shanghai_gov:https://www.zfcg.sh.gov.cn/
    """
    import re
    websites_str = os.getenv('PILOT_WEBSITES', '')
    if not websites_str:
        return [{
            'name': '上海市政府采购网',
            'code': 'shanghai_gov',
            'base_url': 'https://www.zfcg.sh.gov.cn/',
            'enabled': True,
            'priority': 1,
        }]

    websites = []
    for i, site_str in enumerate(websites_str.split('|')):
        if not site_str.strip():
            continue
        match = re.match(r'^([^:]+):([^:]+):(.+)$', site_str.strip())
        if match:
            websites.append({
                'name': match.group(1),
                'code': match.group(2),
                'base_url': match.group(3).rstrip('/') + '/',
                'enabled': True,
                'priority': i + 1,
            })
    return websites if websites else []

PILOT_WEBSITES = _parse_pilot_websites()

CRAWLER_CONFIG = {
    'MAX_RETRIES': 3,
    'REQUEST_DELAY_MIN': 2.0,
    'REQUEST_DELAY_MAX': 5.0,
    'TIMEOUT': 60,
    'PROXY_ENABLED': os.getenv('PROXY_ENABLED', 'false').lower() == 'true',
    'PROXY_LIST': os.getenv('PROXY_LIST', '').split(',') if os.getenv('PROXY_LIST') else [],
    'FALLBACK_STRATEGY': ['api', 'headless', 'stealth'],
}

SPECTACULAR_SETTINGS = {
    'TITLE': '自动化投标系统 API',
    'DESCRIPTION': '覆盖招标项目筛选、投标文件生成与中标结果跟踪全流程',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
}

OPENCLAW_CONFIG = {
    'GATEWAY_HOST': os.getenv('OPENCLAW_GATEWAY_HOST', '127.0.0.1'),
    'GATEWAY_PORT': int(os.getenv('OPENCLAW_GATEWAY_PORT', '18789')),
    'LLM_PROVIDER': os.getenv('OPENCLAW_LLM_PROVIDER', 'ollama'),
    'LLM_BASE_URL': os.getenv('OPENCLAW_LLM_BASE_URL', 'http://localhost:11434'),
    'MAIN_MODEL': os.getenv('OPENCLAW_MAIN_MODEL', 'qwen2.5:14b'),
    'CODE_MODEL': os.getenv('OPENCLAW_CODE_MODEL', 'deepseek-coder-v2:lite'),
    'VISION_MODEL': os.getenv('OPENCLAW_VISION_MODEL', 'qwen2.5-vl:7b'),
    'EMBEDDING_MODEL': os.getenv('OPENCLAW_EMBEDDING_MODEL', 'bge-m3'),
    'MAX_AGENTS': int(os.getenv('OPENCLAW_MAX_AGENTS', '100')),
    'SESSION_TIMEOUT': int(os.getenv('OPENCLAW_SESSION_TIMEOUT', '3600')),
}

CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': f"redis://{os.getenv('REDIS_HOST', 'localhost')}:{os.getenv('REDIS_PORT', '6379')}/{os.getenv('REDIS_CACHE_DB', '1')}",
        'OPTIONS': {
            'CONNECTION_POOL_KWARGS': {
                'max_connections': 50,
                'retry_on_timeout': True,
            }
        },
        'KEY_PREFIX': 'bid_auto_cache',
        'TIMEOUT': 300,
    }
}

CACHE_TTL = {
    'DEFAULT': 300,
    'USER_PERMISSIONS': 60,
    'ENTERPRISE_INFO': 600,
    'TENDER_LIST': 120,
    'DOCUMENT_OPTIONS': 3600,
}

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {asctime} {message}',
            'style': '{',
        },
        'request': {
            'format': '{asctime} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs' / 'app.log',
            'maxBytes': 10 * 1024 * 1024,
            'backupCount': 5,
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'INFO'),
            'propagate': False,
        },
        'crawler': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}
