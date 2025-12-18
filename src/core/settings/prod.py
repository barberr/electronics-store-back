# src/core/settings/prod.py
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