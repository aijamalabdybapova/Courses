"""
Django settings for myproject project.
"""

import os
from pathlib import Path
import dj_database_url

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# ========== БЕЗОПАСНОСТЬ ==========
# Секретный ключ - через переменную окружения на Render
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'ваш-секретный-ключ-для-разработки')

# Для Render обязательно меняем DEBUG на False
DEBUG = os.environ.get('DJANGO_DEBUG', 'False') == 'True'

# Разрешённые хосты - добавляем адрес Render
ALLOWED_HOSTS = [
    'localhost', 
    '127.0.0.1',
    'testserver',
    '.onrender.com',  # Разрешает все поддомены onrender.com
]


# ========== ПРИЛОЖЕНИЯ ==========
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Мои приложения
    'courses',

    'rest_framework',
    'drf_yasg',
]

# ========== МИДЛВЕРЫ (добавляем WhiteNoise) ==========
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # <-- ДОБАВЛЕНО для статики
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'myproject.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            BASE_DIR / 'courses/templates',
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'myproject.wsgi.application'


# ========== БАЗА ДАННЫХ (Рендер использует PostgreSQL) ==========
# База данных через переменную окружения DATABASE_URL (Render даст её автоматически)
# Для локальной разработки оставляем PostgreSQL (можно закомментировать и использовать SQLite)

DATABASES = {
    'default': dj_database_url.config(
        default='postgresql://postgres:1@localhost:5432/langdb1',  # Ваша локальная БД
        conn_max_age=600,
        ssl_require=False
    )
}

# Для локальной разработки с SQLite (раскомментируйте при необходимости):
# if DEBUG:
#     DATABASES = {
#         'default': {
#             'ENGINE': 'django.db.backends.sqlite3',
#             'NAME': BASE_DIR / 'db.sqlite3',
#         }
#     }


# ========== ВАЛИДАЦИЯ ПАРОЛЕЙ ==========
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


# ========== ЛОКАЛИЗАЦИЯ ==========
LANGUAGE_CODE = 'ru-ru'
TIME_ZONE = 'Europe/Moscow'
USE_I18N = True
USE_TZ = True


# ========== СТАТИЧЕСКИЕ ФАЙЛЫ (ВАЖНО ДЛЯ RENDER) ==========
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'  # Сюда собираются файлы
STATICFILES_DIRS = [
    BASE_DIR / 'courses/static',
]

# WhiteNoise для раздачи статики в production
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'


# ========== МЕДИА ФАЙЛЫ ==========
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'


# ========== ДОПОЛНИТЕЛЬНЫЕ НАСТРОЙКИ ==========
DATA_UPLOAD_MAX_NUMBER_FIELDS = 10240
MAX_UPLOAD_SIZE = 5242880  # 5MB


# ========== АУТЕНТИФИКАЦИЯ ==========
LOGIN_REDIRECT_URL = 'dashboard'
LOGOUT_REDIRECT_URL = 'home'
LOGIN_URL = 'login'


# ========== СЕССИИ ==========
SESSION_COOKIE_AGE = 1209600  # 2 недели
SESSION_SAVE_EVERY_REQUEST = True
SESSION_SERIALIZER = 'django.contrib.sessions.serializers.JSONSerializer'


# ========== EMAIL (опционально, для продакшена настройте через переменные) ==========
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', 'aijamal.4815sept@gmail.com')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = 'LangLearn <aijamal.4815sept@gmail.com>'
EMAIL_TIMEOUT = 60

# Для отладки email в разработке
if DEBUG:
    import logging
    logger = logging.getLogger('django')


# ========== БЕЗОПАСНОСТЬ ДЛЯ PRODUCTION ==========
# Автоматически включаем безопасные настройки, если не DEBUG
if not DEBUG:
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SESSION_COOKIE_SECURE = True   # Только HTTPS
    CSRF_COOKIE_SECURE = True      # Только HTTPS
    SECURE_HSTS_SECONDS = 31536000  # 1 год
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    X_FRAME_OPTIONS = 'DENY'
else:
    # Для локальной разработки
    CSRF_COOKIE_SECURE = False
    SESSION_COOKIE_SECURE = False
    CSRF_COOKIE_HTTPONLY = False
    SESSION_COOKIE_HTTPONLY = True
    CSRF_COOKIE_SAMESITE = 'Lax'
    SESSION_COOKIE_SAMESITE = 'Lax'


# ========== КАСТОМНЫЕ ОБРАБОТЧИКИ ОШИБОК ==========
# Для продакшена (при DEBUG=False)
handler404 = 'courses.views.custom_404'
handler500 = 'courses.views.custom_500'


# ========== ИНСТРУМЕНТЫ ОТЛАДКИ (только для разработки) ==========
if DEBUG:
    try:
        import debug_toolbar
        INSTALLED_APPS += ['debug_toolbar']
        MIDDLEWARE.insert(0, 'debug_toolbar.middleware.DebugToolbarMiddleware')
        INTERNAL_IPS = ['127.0.0.1']
        DEBUG_TOOLBAR_CONFIG = {
            'SHOW_TOOLBAR_CALLBACK': lambda request: True,
            'SHOW_COLLAPSED': False,
            'SQL_WARNING_THRESHOLD': 100,
        }
    except ImportError:
        pass  # debug_toolbar не установлен