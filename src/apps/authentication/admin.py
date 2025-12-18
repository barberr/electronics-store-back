# src/apps/authentication/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import UserChangeForm, UserCreationForm
from django.utils.translation import gettext_lazy as _

from .models import CustomUser


class CustomUserCreationForm(UserCreationForm):
    """Форма для создания пользователя в админке"""
    class Meta(UserCreationForm.Meta):
        model = CustomUser
        fields = ('username', 'email')


class CustomUserChangeForm(UserChangeForm):
    """Форма для редактирования пользователя в админке"""
    class Meta(UserChangeForm.Meta):
        model = CustomUser


@admin.register(CustomUser)
class CustomUserAdmin(BaseUserAdmin):
    # Используем кастомные формы
    form = CustomUserChangeForm
    add_form = CustomUserCreationForm

    # Поля, отображаемые в списке пользователей
    list_display = (
        'username', 'email', 'first_name', 'last_name',
        'is_vendor', 'is_staff', 'is_active', 'date_joined'
    )
    list_filter = ('is_vendor', 'is_staff', 'is_superuser', 'is_active', 'date_joined')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ('-date_joined',)

    # Поля при редактировании (уже существующего пользователя)
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'email', 'phone', 'address')}),
        (_('Permissions'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        (_('Vendor status'), {'fields': ('is_vendor',)}),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )

    # Поля при **создании** нового пользователя (обязательно включить password1/password2!)
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'username', 'email',
                'password1', 'password2',
                'first_name', 'last_name', 'phone', 'address', 'is_vendor',
            ),
        }),
    )