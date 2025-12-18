from .base import *

# DEBUG = True
# ALLOWED_HOSTS = ['*']

# Для разработки — можно использовать локальный ключ
SECRET_KEY = 'local-secret-key-for-electronics-store-dev'

# Доп. приложения для dev
INSTALLED_APPS += [
    'django_extensions',
]

# Media для загрузки изображений
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'