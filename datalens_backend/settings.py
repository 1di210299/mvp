"""
Django settings for DataLens Backend project.
Optimizado para evitar error 431 (Request Header Fields Too Large)
"""

import os
from pathlib import Path
from datetime import timedelta
import environ

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Environment variables
env = environ.Env(
    DEBUG=(bool, True),  # Development default
    SECRET_KEY=(str, 'django-insecure-change-in-production'),
    ALLOWED_HOSTS=(list, ['localhost', '127.0.0.1', '0.0.0.0']),
    DATABASE_URL=(str, f'sqlite:///{BASE_DIR}/db.sqlite3'),
    PORT=(int, 8080),
    HOST=(str, '0.0.0.0'),
)

# Read .env file if it exists
environ.Env.read_env(os.path.join(BASE_DIR, '.env'))

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env('SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env('DEBUG')

# ALLOWED_HOSTS configuration
ALLOWED_HOSTS = env('ALLOWED_HOSTS')

# Add testserver for Django test client
if DEBUG:
    ALLOWED_HOSTS.extend(['testserver'])

# Production settings
if not DEBUG:
    # In production, allow all hosts (Railway/Render will provide domain)
    ALLOWED_HOSTS.extend(['*'])
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

# Application definition
DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

THIRD_PARTY_APPS = [
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',
    'drf_spectacular',
    'django_extensions',
]

LOCAL_APPS = [
    'authentication',
    'inventory',
    'forecasting',
    'alerts',
    'reports',
    'data_import',  # Nueva app para importación de datos
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

# MIDDLEWARE - Optimizado para prevenir error 431
MIDDLEWARE = [
    # NUEVO: Middleware para detectar headers grandes (solo en DEBUG)
    'datalens_backend.middleware.HeaderSizeDebugMiddleware' if DEBUG else None,
    'corsheaders.middleware.CorsMiddleware',
    'datalens_backend.middleware.DevelopmentOptimizationMiddleware',  # Middleware personalizado para timeouts
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# Filtrar None values del middleware
MIDDLEWARE = [m for m in MIDDLEWARE if m is not None]

ROOT_URLCONF = 'datalens_backend.urls'

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

WSGI_APPLICATION = 'datalens_backend.wsgi.application'

# Database - Updated for production
if DEBUG:
    DATABASES = {
        'default': env.db()
    }
else:
    # Production database (PostgreSQL from Railway/Render)
    try:
        import dj_database_url
        DATABASES = {
            'default': dj_database_url.config(
                default=env('DATABASE_URL'),
                conn_max_age=600,
                conn_health_checks=True,
            )
        }
    except ImportError:
        # Fallback to environment database if dj_database_url not available
        DATABASES = {
            'default': env.db()
        }

# Django REST Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    # TEMPORAL: Comentado para desarrollo sin autenticación
    # 'DEFAULT_PERMISSION_CLASSES': [
    #     'rest_framework.permissions.IsAuthenticated',
    # ],
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 50,  # Reducido de 20 a 50 para balance performance/usabilidad
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    # Configuración de throttling para evitar sobrecarga
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle'
    ] if not DEBUG else [],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '1000/hour',
        'user': '2000/hour'
    } if not DEBUG else {},
    # Parser classes optimizados
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
        'rest_framework.parsers.FormParser',
        'rest_framework.parsers.MultiPartParser',
    ],
}

# JWT Settings - Optimizado para tokens más pequeños
SIMPLE_JWT = {
    # Tiempos de vida más largos para mejor UX
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=2),  # 2 horas en lugar de 1
    'REFRESH_TOKEN_LIFETIME': timedelta(days=30),  # 30 días en lugar de 7
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'VERIFYING_KEY': None,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    # NUEVAS configuraciones para tokens más pequeños
    'INCLUDE_JTI': False,  # Reduce el tamaño del token
    'UPDATE_LAST_LOGIN': False,  # Evita actualizar last_login en cada request
    
    # **NUEVAS CONFIGURACIONES PARA RENOVACIÓN AUTOMÁTICA**
    'SLIDING_TOKEN_REFRESH_EXP_CLAIM': 'refresh_exp',
    'SLIDING_TOKEN_LIFETIME': timedelta(hours=2),
    'SLIDING_TOKEN_REFRESH_LIFETIME': timedelta(days=30),
    
    # **Configuraciones de seguridad mejoradas**
    'TOKEN_OBTAIN_SERIALIZER': 'authentication.serializers.CustomTokenObtainPairSerializer',
    'TOKEN_REFRESH_SERIALIZER': 'rest_framework_simplejwt.serializers.TokenRefreshSerializer',
    'TOKEN_VERIFY_SERIALIZER': 'rest_framework_simplejwt.serializers.TokenVerifySerializer',
}

# Spectacular settings (OpenAPI documentation)
SPECTACULAR_SETTINGS = {
    'TITLE': 'DataLens API',
    'DESCRIPTION': 'API for DataLens inventory management and analytics platform',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'COMPONENT_SPLIT_REQUEST': True,
}

# CORS SETTINGS - CONFIGURACIÓN ULTRA-OPTIMIZADA PARA EVITAR ERROR 431
if DEBUG:
    # Configuración extremadamente minimalista para desarrollo
    CORS_ALLOW_ALL_ORIGINS = True
    CORS_ALLOW_CREDENTIALS = False  # CRÍTICO: Evita envío automático de cookies
    CORS_PREFLIGHT_MAX_AGE = 0  # Sin cache de preflight para evitar acumulación
    
    # SOLO los headers absolutamente esenciales
    CORS_ALLOWED_HEADERS = [
        'content-type',
        'authorization',
    ]
    
    # NO exponer headers adicionales
    CORS_EXPOSE_HEADERS = []
    
    # Métodos mínimos necesarios
    CORS_ALLOW_METHODS = [
        'GET',
        'POST',
        'OPTIONS',
    ]
    
    # Configuraciones adicionales para reducir headers
    CORS_ALLOW_PRIVATE_NETWORK = False
else:
    # Configuración para producción
    CORS_ALLOWED_ORIGINS = [
        "https://your-app.github.io",
        "https://your-app.netlify.app", 
        "https://your-app.vercel.app",
    ]
    CORS_ALLOW_CREDENTIALS = True
    
    CORS_ALLOWED_HEADERS = [
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
    
    CORS_EXPOSE_HEADERS = [
        'Content-Type',
        'X-CSRFToken',
    ]
    
    CORS_ALLOW_METHODS = [
        'DELETE',
        'GET',
        'OPTIONS',
        'PATCH',
        'POST',
        'PUT',
    ]

# Password validation
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

# Internationalization
LANGUAGE_CODE = 'es-pe'
TIME_ZONE = 'America/Lima'
USE_I18N = True
USE_TZ = True

# Static files - Updated for production
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
] if (BASE_DIR / 'static').exists() else []

if not DEBUG:
    # Production static files serving
    STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Custom user model
AUTH_USER_MODEL = 'authentication.User'

# Server Configuration
SERVER_PORT = env('PORT')
SERVER_HOST = env('HOST')

# Celery Configuration (Redis) - Configuración mejorada
REDIS_URL = env('REDIS_URL', default='redis://localhost:6379/0')
CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = REDIS_URL

# In production, disable Celery if Redis not available
if not DEBUG:
    try:
        import redis
        r = redis.from_url(REDIS_URL)
        r.ping()
    except:
        # Disable Celery in production if Redis not available
        CELERY_TASK_ALWAYS_EAGER = True
        CELERY_TASK_EAGER_PROPAGATES = True

CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE

# Configuración adicional para mejorar conectividad
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True
CELERY_BROKER_CONNECTION_RETRY = True
CELERY_BROKER_CONNECTION_MAX_RETRIES = 10
CELERY_BROKER_TRANSPORT_OPTIONS = {
    'retry_policy': {
        'timeout': 5.0
    }
}
CELERY_RESULT_BACKEND_TRANSPORT_OPTIONS = {
    'retry_policy': {
        'timeout': 5.0
    }
}
CELERY_WORKER_PREFETCH_MULTIPLIER = 1
CELERY_TASK_ACKS_LATE = True
CELERY_WORKER_DISABLE_RATE_LIMITS = True
CELERY_TASK_ALWAYS_EAGER = False
CELERY_TASK_EAGER_PROPAGATES = False

# Email configuration
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = env('EMAIL_HOST', default='localhost')
EMAIL_PORT = env('EMAIL_PORT', default=587)
EMAIL_USE_TLS = env('EMAIL_USE_TLS', default=True)
EMAIL_HOST_USER = env('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL', default='noreply@datalens.com')

# Twilio Configuration for WhatsApp
TWILIO_ACCOUNT_SID = env('TWILIO_ACCOUNT_SID', default='')
TWILIO_AUTH_TOKEN = env('TWILIO_AUTH_TOKEN', default='')
TWILIO_WHATSAPP_FROM = env('TWILIO_WHATSAPP_FROM', default='whatsapp:+14155238886')  # Twilio Sandbox number

# Notification Configuration
NOTIFICATION_SETTINGS = {
    'email_enabled': env('EMAIL_NOTIFICATIONS_ENABLED', default=True),
    'whatsapp_enabled': env('WHATSAPP_NOTIFICATIONS_ENABLED', default=True),
    'default_country_code': env('DEFAULT_COUNTRY_CODE', default='+51'),  # Perú
}

# CONFIGURACIÓN CRÍTICA PARA EVITAR ERROR 431
if DEBUG:
    # Límites más estrictos para desarrollo para detectar problemas temprano
    DATA_UPLOAD_MAX_NUMBER_FIELDS = 1000  # Reducido de 10000
    DATA_UPLOAD_MAX_MEMORY_SIZE = 50 * 1024 * 1024  # 50MB (reducido de 100MB)
    FILE_UPLOAD_MAX_MEMORY_SIZE = 50 * 1024 * 1024  # 50MB
    
    # Configuración ultra-minimalista de sesiones para desarrollo
    SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
    SESSION_COOKIE_AGE = 1800  # 30 minutos (reducido de 3600)
    SESSION_SAVE_EVERY_REQUEST = False
    SESSION_EXPIRE_AT_BROWSER_CLOSE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SECURE = False
    SESSION_COOKIE_SAMESITE = None
    SESSION_COOKIE_NAME = 'sid'  # Nombre ultra-corto
    
    # Nombres de cookies ultra-cortos
    CSRF_COOKIE_NAME = 'csrf'
    LANGUAGE_COOKIE_NAME = 'lang'
    
    # Headers de seguridad desactivados en desarrollo
    SECURE_PROXY_SSL_HEADER = None
    SECURE_BROWSER_XSS_FILTER = False
    SECURE_CONTENT_TYPE_NOSNIFF = False
    X_FRAME_OPTIONS = 'SAMEORIGIN'
    
    # Cache optimizado para sesiones
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            'LOCATION': 'datalens-cache',
            'OPTIONS': {
                'MAX_ENTRIES': 100,  # Límite bajo para evitar consumo excesivo
                'CULL_FREQUENCY': 3,  # Limpiar cache frecuentemente
            }
        }
    }
else:
    # Configuración normal para producción
    DATA_UPLOAD_MAX_NUMBER_FIELDS = 10000
    DATA_UPLOAD_MAX_MEMORY_SIZE = 100 * 1024 * 1024  # 100MB
    FILE_UPLOAD_MAX_MEMORY_SIZE = 100 * 1024 * 1024  # 100MB
    
    SESSION_ENGINE = 'django.contrib.sessions.backends.db'
    SESSION_COOKIE_AGE = 86400
    SESSION_SAVE_EVERY_REQUEST = False
    SESSION_EXPIRE_AT_BROWSER_CLOSE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SECURE = not DEBUG
    SESSION_COOKIE_SAMESITE = 'Lax'
    SESSION_COOKIE_NAME = 'dlsid'

# Configuración de seguridad para headers
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https') if not DEBUG else None

# Configuración de timeout y conexiones para desarrollo
if DEBUG:
    # Configuración de timeouts para evitar errores
    import socket
    socket.setdefaulttimeout(30)
    
    # Configuración adicional del servidor de desarrollo
    CONN_MAX_AGE = 0  # Cerrar conexiones después de cada request
    
    # Configuración de la base de datos para evitar locks
    if 'default' in DATABASES:
        DATABASES['default']['OPTIONS'] = {
            'timeout': 20,
            'check_same_thread': False,  # Para SQLite
        }

# CONFIGURACIÓN DE LOGGING MEJORADA PARA DETECTAR HEADERS GRANDES
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
        'header_debug': {
            'format': '🔍 HEADERS: {levelname} {asctime} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'django.log',
            'formatter': 'verbose',
        },
        'console': {
            'level': 'DEBUG' if DEBUG else 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'simple' if DEBUG else 'verbose',
        },
        'header_console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'header_debug',
        },
    },
    'loggers': {
        'django.server': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.request': {
            'handlers': ['console', 'file'],
            'level': 'ERROR',
            'propagate': False,
        },
        'corsheaders': {
            'handlers': ['console'],
            'level': 'DEBUG' if DEBUG else 'WARNING',
            'propagate': False,
        },
        # NUEVO: Logger específico para headers
        'headers_debug': {
            'handlers': ['header_console', 'file'],
            'level': 'DEBUG' if DEBUG else 'WARNING',
            'propagate': False,
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'INFO',
    },
}

# Machine Learning Configuration
ML_MODELS_PATH = BASE_DIR / 'models' / 'ml_models'
ML_EXPERIMENTS_PATH = BASE_DIR / 'experiments'
ML_PLOTS_PATH = MEDIA_ROOT / 'ml_plots'

# Asegura que los directorios ML existen
os.makedirs(ML_MODELS_PATH, exist_ok=True)
os.makedirs(ML_EXPERIMENTS_PATH, exist_ok=True)
os.makedirs(ML_PLOTS_PATH, exist_ok=True)

# Configuración de pronósticos
FORECASTING_CONFIG = {
    'default_horizon_days': 30,
    'max_horizon_days': 365,
    'min_training_data_points': 30,
    'default_confidence_interval': 95,
    'auto_retrain_threshold_days': 7,
    'hyperparameter_optimization_timeout': 3600,  # 1 hora
    'parallel_training_workers': 3,
}

# Configuración de algoritmos ML
ML_ALGORITHMS_CONFIG = {
    'prophet': {
        'enabled': True,
        'default_hyperparameters': {
            'seasonality_mode': 'additive',
            'changepoint_prior_scale': 0.05,
            'seasonality_prior_scale': 10.0,
            'yearly_seasonality': 'auto',
            'weekly_seasonality': 'auto',
            'daily_seasonality': 'auto'
        }
    },
    'arima': {
        'enabled': True,
        'default_hyperparameters': {
            'auto_arima': True,
            'seasonal': True,
            'stepwise': True,
            'max_p': 5,
            'max_d': 2,
            'max_q': 5,
            'information_criterion': 'aic'
        }
    },
    'ensemble': {
        'enabled': True,
        'default_hyperparameters': {
            'voting_method': 'weighted_average',
            'auto_weight_calculation': True,
            'min_models': 2
        }
    }
}

# Configuración de evaluación de modelos
MODEL_EVALUATION_CONFIG = {
    'default_evaluation_period_days': 30,
    'min_evaluation_data_points': 10,
    'performance_metrics': ['mae', 'mape', 'rmse', 'r2', 'directional_accuracy'],
    'auto_evaluation_schedule_hours': 24,  # Evaluar cada 24 horas
    'performance_alert_threshold_mape': 25,  # Alertar si MAPE > 25%
}

# Configuración de OpenAI
OPENAI_API_KEY = env('OPENAI_API_KEY', default='')

# Configuración de campos personalizados
CUSTOM_FIELDS_CONFIG = {
    'max_fields_per_model': 50,
}

# CONFIGURACIONES ADICIONALES PARA PREVENIR ERROR 431
if DEBUG:
    # Configuración específica para el servidor de desarrollo de Django
    import os
    
    # Variables de entorno para el servidor de desarrollo
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'datalens_backend.settings')
    
    # Configuración adicional de límites
    HTTP_REQUEST_MAX_SIZE = 10 * 1024 * 1024  # 10MB máximo para requests
    
    # Configuración para detectar y prevenir headers grandes
    HEADER_SIZE_LIMITS = {
        'max_total_header_size': 8192,  # 8KB total
        'max_individual_header_size': 2048,  # 2KB por header
        'max_cookie_size': 4096,  # 4KB para cookies
        'warn_threshold': 4096,  # Advertir si headers > 4KB
    }
    
    # Configuración de respuesta para debugging
    DEBUG_HEADERS = True  # Agregar headers de debug en responses
    SHOW_HEADER_SIZE_INFO = True  # Mostrar info de tamaño en logs

# Crear directorio de logs si no existe
os.makedirs(BASE_DIR / 'logs', exist_ok=True)