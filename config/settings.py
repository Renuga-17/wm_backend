"""
Django settings for wm_backend project.
"""
from pathlib import Path
import os
from dotenv import load_dotenv
from datetime import timedelta
import socket


# Load environment variables
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'django-insecure-default-secret-key-change-this-in-production')

DEBUG = os.getenv('DJANGO_DEBUG', 'True') == 'True'

ALLOWED_HOSTS = ['testserver', 'localhost', '127.0.0.1']

INSTALLED_APPS = [
    'daphne',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Third party packages
    'rest_framework',
    'corsheaders',
    'channels',
    
    # Local apps
    'apps.identity.apps.IdentityConfig',
    'apps.warehouse.apps.WarehouseConfig',
    'apps.inventory.apps.InventoryConfig',
    'apps.orders.apps.OrdersConfig',
    'apps.inbound.apps.InboundConfig',
    'apps.outbound.apps.OutboundConfig',
    'apps.recommendations.apps.RecommendationsConfig',
    'apps.ai.apps.AIConfig',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
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
ASGI_APPLICATION = 'config.asgi.application'

DB_ENGINE = os.getenv('DB_ENGINE', 'sqlite' if not os.getenv('DB_HOST') else 'postgresql')

if DB_ENGINE == 'sqlite':
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.getenv('DB_NAME', 'wm_db'),
            'USER': os.getenv('DB_USER', 'postgres'),
            'PASSWORD': os.getenv('DB_PASSWORD', 'postgres'),
            'HOST': os.getenv('DB_HOST', 'localhost'),
            'PORT': os.getenv('DB_PORT', '5432'),
        }
    }

def _is_redis_running():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(0.2)
        s.connect((os.getenv('REDIS_HOST', '127.0.0.1'), 6379))
        s.close()
        return True
    except Exception:
        return False

if _is_redis_running():
    CHANNEL_LAYERS = {
        'default': {
            'BACKEND': 'channels_redis.core.RedisChannelLayer',
            'CONFIG': {
                "hosts": [(os.getenv('REDIS_HOST', '127.0.0.1'), 6379)],
            },
        },
    }
    CACHES = {
        'default': {
            'BACKEND': 'django_redis.cache.RedisCache',
            'LOCATION': os.getenv('REDIS_URL', 'redis://127.0.0.1:6379/1'),
            'OPTIONS': {
                'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            }
        }
    }
else:
    CHANNEL_LAYERS = {
        'default': {
            'BACKEND': 'channels.layers.InMemoryChannelLayer',
        },
    }
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            'LOCATION': 'unique-snowflake',
        }
    }

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

AUTH_USER_MODEL = 'identity.User'

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'common.authentication.LocalDevAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.AllowAny',
    ),
    'DEFAULT_PAGINATION_CLASS': 'common.pagination.StandardResultsSetPagination',
    'EXCEPTION_HANDLER': 'common.exceptions.custom_exception_handler',
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=15),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': False,
    'BLACKLIST_AFTER_ROTATION': False,
    'UPDATE_LAST_LOGIN': False,
}

# MongoDB Settings
MONGODB_SETTINGS = {
    'URI': os.getenv('MONGODB_URI', 'mongodb://localhost:27017/'),
    'DB_NAME': os.getenv('MONGODB_DB_NAME', 'wm_mongodb'),
}

# ClickHouse Settings
CLICKHOUSE_SETTINGS = {
    "HOST": os.getenv('CLICKHOUSE_HOST', 'jj8tk9yx2g.ap-south-1.aws.clickhouse.cloud'),
    "PORT": int(os.getenv('CLICKHOUSE_PORT', '8443')),
    "USERNAME": os.getenv('CLICKHOUSE_USER', 'default'),
    "PASSWORD": os.getenv('CLICKHOUSE_PASSWORD', 'YOUR_ACTUAL_PASSWORD'),
    "DATABASE": os.getenv('CLICKHOUSE_DB', 'wm_clickhouse'),
    "SECURE": os.getenv('CLICKHOUSE_SECURE', 'True') == 'True',
}

# Qdrant Settings
QDRANT_SETTINGS = {
    'URL': os.getenv('QDRANT_URL', 'https://8154ed87-b188-4ddc-996e-d80d11e64562.eu-west-2-0.aws.cloud.qdrant.io/'),
    'API_KEY': os.getenv('QDRANT_API_KEY', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIiwic3ViamVjdCI6ImFwaS1rZXk6ZTAxYTczZjMtNjE4Ny00NDNmLTljMjMtZjJiNDBjOGFkNTBhIn0.9EnkXICnLSqMY5T-vQlyVoZ5Xh4HU3vyav0m3uxadNc'),
}

# FastAPI AI Service settings
AI_SERVICE_SETTINGS = {
    'BASE_URL': os.getenv('AI_SERVICE_URL', 'http://localhost:8002'),
    'API_KEY': os.getenv('AI_SERVICE_API_KEY', ''),
}

GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')

# OCR Microservice settings
OCR_SERVICE_SETTINGS = {
    'BASE_URL': os.getenv('OCR_SERVICE_URL', 'http://localhost:8002'),
}

# RAG Microservice settings
# RAG service URL — set AI_SERVICE_URL/RAG_BASE_URL env var
RAG_BASE_URL = os.getenv('AI_SERVICE_URL', os.getenv('RAG_BASE_URL', 'http://localhost:8002'))
try:
    RAG_TIMEOUT = int(os.getenv('RAG_TIMEOUT', '30'))
except ValueError:
    RAG_TIMEOUT = 30


# Media File Storage Settings
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Celery Settings
if _is_redis_running():
    CELERY_BROKER_URL = os.getenv('REDIS_URL', 'redis://127.0.0.1:6379/1')
    CELERY_RESULT_BACKEND = os.getenv('REDIS_URL', 'redis://127.0.0.1:6379/1')
else:
    CELERY_BROKER_URL = 'memory://'
    CELERY_RESULT_BACKEND = None
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_TASK_ALWAYS_EAGER = os.getenv('CELERY_TASK_ALWAYS_EAGER', 'True') == 'True'

# Redirect Django migrations to the Clean Architecture Infrastructure layer
MIGRATION_MODULES = {
    'identity': 'apps.identity.infrastructure.persistence.migrations',
    'warehouse': 'apps.warehouse.infrastructure.persistence.migrations',
    'inventory': 'apps.inventory.infrastructure.persistence.migrations',
    'orders': 'apps.orders.infrastructure.persistence.migrations',
    'inbound': 'apps.inbound.infrastructure.persistence.migrations',
    'outbound': 'apps.outbound.infrastructure.persistence.migrations',
}

# Storage Recommendation Settings
WAREHOUSE_MIN_FREE_CAPACITY = int(os.getenv('WAREHOUSE_MIN_FREE_CAPACITY', 10))
WAREHOUSE_RECOMMENDATION_USE_ML = os.getenv('WAREHOUSE_RECOMMENDATION_USE_ML', 'False') == 'True'
ML_MODEL_PATH = os.getenv('ML_MODEL_PATH', '')

# Centralized Warehouse Defaults
from decimal import Decimal
DEFAULT_BIN_LENGTH = Decimal(os.getenv('DEFAULT_BIN_LENGTH', '20.0'))
DEFAULT_BIN_WIDTH = Decimal(os.getenv('DEFAULT_BIN_WIDTH', '15.0'))
DEFAULT_BIN_HEIGHT = Decimal(os.getenv('DEFAULT_BIN_HEIGHT', '10.0'))

# CORS configuration to allow local frontend access
CORS_ALLOW_ALL_ORIGINS = True
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
    'x-mock-user-email',
    'x-mock-user-role',
]
