from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.password_validation import validate_password
from django.db import transaction
from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from .models import CustomerSession
from .sessions import require_verified_user

User = get_user_model()


def normalize_email(value):
    return value.strip().lower()


class UniqueEmailMixin:
    def validate_email(self, value):
        value = normalize_email(value)
        users = User.objects.filter(email__iexact=value)
        if self.instance:
            users = users.exclude(pk=self.instance.pk)
        if users.exists():
            raise serializers.ValidationError('Этот email уже используется')
        return value


class RegisterSerializer(UniqueEmailMixin, serializers.ModelSerializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(write_only=True, trim_whitespace=False)
    password2 = serializers.CharField(write_only=True, trim_whitespace=False)

    class Meta:
        model = User
        fields = ('username', 'password', 'password2', 'email', 'first_name', 'last_name')

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({'password': 'Пароли не совпадают'})
        candidate = User(**{k: v for k, v in attrs.items() if k not in ('password', 'password2')})
        validate_password(attrs['password'], candidate)
        return attrs

    def create(self, validated_data):
        validated_data.pop('password2')
        return User.objects.create_user(**validated_data, is_active=False, is_email_verified=False)


class VerifyEmailPinSerializer(serializers.Serializer):
    email = serializers.EmailField()
    pin = serializers.RegexField(r'^\d{6}$')


class ResendEmailPinSerializer(serializers.Serializer):
    email = serializers.EmailField()


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(trim_whitespace=False, write_only=True)

    def validate(self, data):
        user = User.objects.filter(username=data['username']).first()
        if user is None or not user.check_password(data['password']):
            raise serializers.ValidationError('Неверные учетные данные')
        if not user.is_email_verified:
            raise serializers.ValidationError({'code': 'email_not_verified', 'detail': 'Email не подтвержден'})
        user = authenticate(username=data['username'], password=data['password'])
        if not user:
            raise serializers.ValidationError('Неверные учетные данные')
        return user


class UserSerializer(UniqueEmailMixin, serializers.ModelSerializer):
    email = serializers.EmailField(required=True)

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'date_joined', 'is_email_verified')
        read_only_fields = ('id', 'username', 'date_joined', 'is_email_verified')


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True, trim_whitespace=False)
    new_password = serializers.CharField(write_only=True, trim_whitespace=False)

    def validate_new_password(self, value):
        validate_password(value, self.context['request'].user)
        return value


class CustomerTokenRefreshSerializer(TokenRefreshSerializer):
    def validate(self, attrs):
        refresh = self.token_class(attrs['refresh'])
        with transaction.atomic():
            # Lock the user before the session, just as logout and profile updates do.
            user = User.objects.select_for_update().filter(pk=refresh.get('user_id')).first()
            if user is None:
                raise AuthenticationFailed('Сессия завершена')
            require_verified_user(user)
            session = CustomerSession.objects.select_for_update().filter(
                pk=refresh.get('sid'), user=user, revoked=False,
            ).first()
            if session is None:
                raise AuthenticationFailed('Сессия завершена')
            # Revalidates the blacklist after acquiring the lock, then rotates.
            return super().validate(attrs)
