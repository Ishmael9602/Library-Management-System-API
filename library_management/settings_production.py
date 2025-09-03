from decouple import config
from .settings import *
import os

# Database configuration for MySQL
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': config('DB_NAME', default='library_management'),
        'USER': config('DB_USER', default='library_user'),
        'PASSWORD': config('DB_PASSWORD', default='mael@1234'),
        'HOST': config('DB_HOST', default='localhost'),
        'PORT': config('DB_PORT', default='3306'),
        'OPTIONS': {
            'sql_mode': 'traditional',
            'charset': 'utf8mb4',
            'init_command': "SET foreign_key_checks = 1;",
        }
    }
}


# Security settings for production
DEBUG = False
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost').split(',')

# Static files configuration
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Security headers
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# HTTPS settings (uncomment when using HTTPS)
# SECURE_SSL_REDIRECT = True
# SESSION_COOKIE_SECURE = True
# CSRF_COOKIE_SECURE = True
