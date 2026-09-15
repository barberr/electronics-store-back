"""Isolated customer-authentication tests; never connects to the application database."""
from .base import *  # noqa: F403

SECRET_KEY = 'isolated-authentication-test-signing-key'
SIMPLE_JWT = {**SIMPLE_JWT, 'SIGNING_KEY': SECRET_KEY}
DATABASES = {'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}}
INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'rest_framework',
    'rest_framework_simplejwt.token_blacklist',
    'apps.authentication',
]
ROOT_URLCONF = 'apps.authentication.urls'
MIDDLEWARE = []
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
PASSWORD_HASHERS = ['django.contrib.auth.hashers.MD5PasswordHasher']
