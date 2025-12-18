# src/apps/authentication/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    is_vendor = models.BooleanField(default=False)

    # Явно переопределяем связи, чтобы избежать конфликта related_name
    groups = models.ManyToManyField(
        'auth.Group',
        related_name='customuser_set',  # ← уникальное имя для reverse-связи
        blank=True,
        help_text='The groups this user belongs to.',
        verbose_name='groups',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='customuser_permissions_set',  # ← тоже уникальное (можно и просто 'customuser_set', но лучше уточнить)
        blank=True,
        help_text='Specific permissions for this user.',
        verbose_name='user permissions',
    )

    def __str__(self):
        return self.email or self.username 