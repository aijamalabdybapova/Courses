"""
Django settings for myproject project.
"""

import os
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings
SECRET_KEY = 'ваш-секретный-ключ'  # Измените на настоящий!
DEBUG = True
ALLOWED_HOSTS = ['localhost', '127.0.0.1','testserver']


# Application definition
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

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
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


# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'langdb1',
        'USER': 'postgres',
        'PASSWORD': '1',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}

# Для тестирования можно использовать SQLite
# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.sqlite3',
#         'NAME': BASE_DIR / 'db.sqlite3',
#     }
# }


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
LANGUAGE_CODE = 'ru-ru'
TIME_ZONE = 'Europe/Moscow'
USE_I18N = True
USE_TZ = True


# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles' 
STATICFILES_DIRS = [
    BASE_DIR / 'courses/static',
]



# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DATA_UPLOAD_MAX_NUMBER_FIELDS = 10240
MAX_UPLOAD_SIZE = 5242880  # 5MB

# Login/Logout redirects
LOGIN_REDIRECT_URL = 'dashboard'
LOGOUT_REDIRECT_URL = 'home'
LOGIN_URL = 'login'

# Session settings
SESSION_COOKIE_AGE = 1209600  # 2 недели
SESSION_SAVE_EVERY_REQUEST = True

SESSION_SERIALIZER = 'django.contrib.sessions.serializers.JSONSerializer'

# Security settings (для production)
if not DEBUG:
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'aijamal.4815sept@gmail.com'  # Ваш Gmail адрес
EMAIL_HOST_PASSWORD = 'qmwv cbvs aytc upya'  # НЕ ваш обычный пароль, а пароль приложения!
DEFAULT_FROM_EMAIL = 'LangLearn <aijamal.4815sept@gmail.com>'
EMAIL_USE_SSL = False  # Не используйте одновременно USE_TLS и USE_SSL
EMAIL_TIMEOUT = 60  # Таймаут в секундах

if DEBUG:
    # Показывать ошибки отправки email
    import logging
    logger = logging.getLogger('django')
    
    # Принудительно использовать реальную отправку даже в DEBUG
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

# ========== НАСТРОЙКИ ДЛЯ DJANGO DEBUG TOOLBAR ==========
# Для отладки и оптимизации SQL-запросов

INSTALLED_APPS += ['debug_toolbar']

MIDDLEWARE.insert(0, 'debug_toolbar.middleware.DebugToolbarMiddleware')

INTERNAL_IPS = [
    '127.0.0.1',
]

# Настройки отображения панели
DEBUG_TOOLBAR_CONFIG = {
    'SHOW_TOOLBAR_CALLBACK': lambda request: True,  # Показывать всегда
    'SHOW_COLLAPSED': False,  # Показывать развернутой
    'SQL_WARNING_THRESHOLD': 100,  # Порог предупреждения для SQL (мс)
}


# ========== НАСТРОЙКИ ДЛЯ КАСТОМНОЙ СТРАНИЦЫ 404 ==========
# Для инспектирования и обработки ошибок

# В режиме DEBUG=False будут использоваться кастомные шаблоны ошибок
# Для тестирования 404 временно установите DEBUG = False
# и добавьте ALLOWED_HOSTS = ['127.0.0.1']

# Кастомные обработчики ошибок (работают при DEBUG=False)
# В urls.py нужно добавить:
handler404 = 'courses.views.custom_404'
handler500 = 'courses.views.custom_500'


# ========== БЕЗОПАСНОСТЬ ==========
# Дополнительные настройки для защиты (для production)

# Безопасные заголовки
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# CSRF настройки
CSRF_COOKIE_SECURE = False  # True для HTTPS (для разработки False)
CSRF_COOKIE_HTTPONLY = False
CSRF_COOKIE_SAMESITE = 'Lax'

# Session настройки
SESSION_COOKIE_SECURE = False  # True для HTTPS (для разработки False)
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
