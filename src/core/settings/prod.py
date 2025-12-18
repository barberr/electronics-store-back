# src/core/settings/prod.py

import os
from pathlib import Path
from .base import *

DEBUG = False
ALLOWED_HOSTS = ['127.0.0.1']  # конкретные!

# Безопасная статика (см. ниже)
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATIC_URL = '/static/'

# Безопасный SECRET_KEY — только из env
SECRET_KEY = os.environ['SECRET_KEY']

# Отключить Browsable API в проде
REST_FRAMEWORK['DEFAULT_RENDERER_CLASSES'] = [
    'rest_framework.renderers.JSONRenderer',
]

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME', 'electronics_db'),
        'USER': os.getenv('DB_USER', 'electronics_user'),
        'PASSWORD': os.getenv('DB_PASSWORD', 'очень_надёжный_пароль'),
        'HOST': os.getenv('DB_HOST', 'localhost'),
        'PORT': os.getenv('DB_PORT', '5432'),
    }
}