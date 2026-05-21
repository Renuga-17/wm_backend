"""
Django settings for wm_backend project.
"""
from pathlib import Path
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'django-insecure-default-secret-key-change-this-in-production')

DEBUG = os.getenv('DJANGO_DEBUG', 'True') == 'True'

ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', '*').split(',')

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Third party packages
    'rest_framework',
    'corsheaders',
    
    # Local apps
    'apps.users.apps.UsersConfig',
    'apps.warehouses.apps.WarehousesConfig',
    'apps.zones.apps.ZonesConfig',
    'apps.racks.apps.RacksConfig',
    'apps.bins.apps.BinsConfig',
    'apps.products.apps.ProductsConfig',
    'apps.inventory.apps.InventoryConfig',
    'apps.inbound.apps.InboundConfig',
    'apps.orders.apps.OrdersConfig',
    'apps.movements.apps.MovementsConfig',
    'apps.recommendations.apps.RecommendationsConfig',
    'apps.dashboards.apps.DashboardsConfig',
    'apps.audit_logs.apps.AuditLogsConfig',
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

AUTH_USER_MODEL = 'users.User'

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
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_PAGINATION_CLASS': 'common.pagination.StandardResultsSetPagination',
    'EXCEPTION_HANDLER': 'common.exceptions.custom_exception_handler',
}

# MongoDB Settings
MONGODB_SETTINGS = {
    'URI': os.getenv('MONGODB_URI', 'mongodb://localhost:27017/'),
    'DB_NAME': os.getenv('MONGODB_DB_NAME', 'wm_mongodb'),
}

# ClickHouse Settings
CLICKHOUSE_SETTINGS = {
    'HOST': os.getenv('CLICKHOUSE_HOST', 'localhost'),
    'PORT': int(os.getenv('CLICKHOUSE_PORT', '8123')),
    'USERNAME': os.getenv('CLICKHOUSE_USER', 'default'),
    'PASSWORD': os.getenv('CLICKHOUSE_PASSWORD', ''),
    'DATABASE': os.getenv('CLICKHOUSE_DB', 'wm_clickhouse'),
}

# Qdrant Settings
QDRANT_SETTINGS = {
    'URL': os.getenv('QDRANT_URL', 'http://localhost:6333'),
    'API_KEY': os.getenv('QDRANT_API_KEY', ''),
}

# FastAPI AI Service settings
AI_SERVICE_SETTINGS = {
    'BASE_URL': os.getenv('AI_SERVICE_URL', 'http://localhost:8001'),
    'API_KEY': os.getenv('AI_SERVICE_API_KEY', ''),
}
