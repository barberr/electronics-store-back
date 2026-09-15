# src/apps/authentication/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from datetime import timedelta
import secrets
import uuid
from django.db.models.functions import Lower


class CustomUser(AbstractUser):
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    is_vendor = models.BooleanField(default=False)
    is_email_verified = models.BooleanField(default=False)
    email_verification_pin = models.CharField(max_length=6, blank=True)
    email_verification_pin_expires_at = models.DateTimeField(null=True, blank=True)

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

    class Meta(AbstractUser.Meta):
        constraints = [
            models.UniqueConstraint(
                Lower('email'), condition=~models.Q(email=''), name='customer_email_ci_unique',
            ),
        ]

    def set_email_verification_pin(self, ttl_minutes=10):
        self.email_verification_pin = f"{secrets.randbelow(1000000):06d}"
        self.email_verification_pin_expires_at = timezone.now() + timedelta(minutes=ttl_minutes)

    def clear_email_verification_pin(self):
        self.email_verification_pin = ''
        self.email_verification_pin_expires_at = None

    def is_email_verification_pin_valid(self, pin):
        return bool(
            self.email_verification_pin
            and self.email_verification_pin == pin
            and self.email_verification_pin_expires_at
            and self.email_verification_pin_expires_at >= timezone.now()
        )

    def __str__(self):
        return self.email or self.username


class CustomerSession(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='customer_sessions')
    created_at = models.DateTimeField(auto_now_add=True)
    revoked = models.BooleanField(default=False)
