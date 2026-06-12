"""
Django settings for wm_backend project.
"""
from pathlib import Path
import os
from dotenv import load_dotenv
from datetime import timedelta


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

CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            "hosts": [(os.getenv('REDIS_HOST', '127.0.0.1'), 6379)],
        },
    },
}

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

CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': os.getenv('REDIS_URL', 'redis://127.0.0.1:6379/1'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
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

from datetime import timedelta

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_PAGINATION_CLASS': 'common.pagination.StandardResultsSetPagination',
    'EXCEPTION_HANDLER': 'common.exceptions.custom_exception_handler',
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=20),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
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
    "HOST": "jj8tk9yx2g.ap-south-1.aws.clickhouse.cloud",
    "PORT": 8443,
    "USERNAME": "default",
    "PASSWORD": "YOUR_ACTUAL_PASSWORD",
    "DATABASE": "wm_clickhouse",
    "SECURE": True,
}

# Qdrant Settings
QDRANT_SETTINGS = {
    'URL': os.getenv('QDRANT_URL', 'http://localhost:6333'),
    'API_KEY': os.getenv('QDRANT_API_KEY', ''),
}

# FastAPI AI Service settings
AI_SERVICE_SETTINGS = {
    'BASE_URL': os.getenv('AI_SERVICE_URL', 'http://localhost:8002'),
    'API_KEY': os.getenv('AI_SERVICE_API_KEY', ''),
}

# OCR Microservice settings
OCR_SERVICE_SETTINGS = {
    'BASE_URL': os.getenv('OCR_SERVICE_URL', 'http://localhost:8002'),
}

# Media File Storage Settings
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Celery Settings
CELERY_BROKER_URL = os.getenv('REDIS_URL', 'redis://127.0.0.1:6379/1')
CELERY_RESULT_BACKEND = os.getenv('REDIS_URL', 'redis://127.0.0.1:6379/1')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'

# JWT Settings
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=15),  
    'REFRESH_TOKEN_LIFETIME': timedelta(minutes=10),  
    'ROTATE_REFRESH_TOKENS': False,
    'BLACKLIST_AFTER_ROTATION': False,
    'UPDATE_LAST_LOGIN': False,
}

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