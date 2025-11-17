import os
from decouple import config
from datetime import timedelta
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# -------------------------------------------------------------
# Core Security Settings
# -------------------------------------------------------------
SECRET_KEY = config('SECRET_KEY', default='')
DEBUG = config('DEBUG', default=True, cast=bool)
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1').split(',')

# -------------------------------------------------------------
# Installed Apps
# -------------------------------------------------------------
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third-party apps
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',

    # Local apps
    'authentication',
    'patients',
    'appointments',
    'electronic_records',
    'notifications',
    'audit_logs',
    'reporting',
]

# -------------------------------------------------------------
# Middleware
# -------------------------------------------------------------
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',

    # Custom sprint-2 security middleware
    'hcrm_backend.middleware.SecurityHeadersMiddleware',
    'hcrm_backend.middleware.SanitizeErrorMiddleware',
]

# -------------------------------------------------------------
# URL / Templates
# -------------------------------------------------------------
ROOT_URLCONF = 'hcrm_backend.urls'

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

WSGI_APPLICATION = 'hcrm_backend.wsgi.application'

# -------------------------------------------------------------
# Database
# -------------------------------------------------------------
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('DB_NAME', default='hcrm_db'),
        'USER': config('DB_USER', default='postgres'),
        'PASSWORD': config('DB_PASSWORD', default=''),
        'HOST': config('DB_HOST', default='localhost'),
        'PORT': config('DB_PORT', default='5432'),
        'OPTIONS': {'sslmode': 'prefer'},
    }
}

# -------------------------------------------------------------
# Django REST Framework
# -------------------------------------------------------------
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,

    # Sprint 2: custom exception handler
    'EXCEPTION_HANDLER': 'hcrm_backend.exceptions.custom_exception_handler',

    'NON_FIELD_ERRORS_KEY': 'error',
}

# -------------------------------------------------------------
# JWT
# -------------------------------------------------------------
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=24),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'ALGORITHM': 'HS256',
}

# -------------------------------------------------------------
# Security Headers
# -------------------------------------------------------------
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# -------------------------------------------------------------
# CORS
# -------------------------------------------------------------
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
]

# -------------------------------------------------------------
# User Model
# -------------------------------------------------------------
AUTH_USER_MODEL = 'authentication.User'

# ensure logs directory exists so file handlers can open the log file
LOG_DIR = BASE_DIR / "logs"
try:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
except Exception:
    # If the directory can't be created for some reason (permissions),
    # fall back silently — logging handlers will raise an error later
    pass


# -------------------------------------------------------------
# Logging
# -------------------------------------------------------------
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,

    'formatters': {
        'json': {
            'format': '{"time": "%(asctime)s", "level": "%(levelname)s", "message": "%(message)s"}',
        },
    },

    'handlers': {
    'file': {
        'level': 'INFO',
        'class': 'logging.handlers.RotatingFileHandler',
        'filename': str(LOG_DIR / 'hcrm.log'),   # NOTE: use str() when passing Path to logging config
        'maxBytes': 1024 * 1024 * 15,
        'backupCount': 5,
        'formatter': 'json',
        },
    },


    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}

# -------------------------------------------------------------
# Time / Static
# -------------------------------------------------------------
USE_TZ = True
TIME_ZONE = 'Asia/Kolkata'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
STATIC_URL = '/static/'

# -------------------------------------------------------------
# Encryption Key (canonical)
# -------------------------------------------------------------
# Canonical key for ALL encryption, including files & PHI
HCRM_ENCRYPTION_KEY = config("HCRM_ENCRYPTION_KEY", default=None)

# Backwards compatibility: MY_FERNET_KEY points to same key
MY_FERNET_KEY = HCRM_ENCRYPTION_KEY
